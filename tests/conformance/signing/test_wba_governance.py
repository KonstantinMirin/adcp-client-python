"""The governance-token issuer check that runs after Web Bot Auth verification.

``verify_wba_governance_issuer`` checks that a governance token's key is in
the ``iss`` origin's key directory and that ``iss`` is the buyer's governance
agent. It is an AdCP-layer check, not part of the WBA profile, so its vectors
live apart from the profile's (``vectors/wba-governance``).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from adcp.signing.crypto import private_key_from_jwk
from adcp.signing.wba import WbaGovernanceError, verify_wba_governance_issuer
from tests.conformance.signing.test_wba_profile import _vector_resolver

ROOT = Path(__file__).parents[1] / "vectors" / "wba-governance"
KEYS = {key["kid"]: key for key in json.loads((ROOT / "keys.json").read_text())["keys"]}
VECTORS = sorted(ROOT.glob("0*.json"))
GOVERNANCE_KID = "1XlJ3EIte7bPOEqKQtKrKNTNy5hywTyrwFXWrMbXKqE"


def test_vendored_vectors_match_recorded_provenance():
    upstream = json.loads((ROOT / "UPSTREAM.json").read_text())
    assert upstream["commit"] == "e24eeb090c4365707641099cbbb45f9945c6d6e0"
    vendored = {path.name for path in ROOT.iterdir() if path.name != "UPSTREAM.json"}
    assert vendored == set(upstream["sha256"])
    for name, digest in upstream["sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("path", VECTORS, ids=lambda p: p.name)
async def test_governance_vectors(path):
    vector = json.loads(path.read_text())

    async def verify():
        return await verify_wba_governance_issuer(
            vector["jws"],
            signer_keys=_vector_resolver(vector, KEYS),
            governance_agents=vector["role_listing"]["adcp:governance"],
            now=vector["reference_now"],
        )

    expected = vector["expected_outcome"]
    if expected["success"]:
        assert await verify() == expected["issuer"]
        return
    with pytest.raises(WbaGovernanceError) as caught:
        await verify()
    assert caught.value.code == expected["error_code"]


def _governance_token(header_extra=None, claims_extra=None, *, iss=None):
    from joserfc import jws as jose_jws
    from joserfc.jwk import OKPKey

    from adcp.governance import _governance_jws_registry

    identity = iss or KEYS[GOVERNANCE_KID]["identity"]
    header = {
        "alg": "EdDSA",
        "typ": "adcp-gov+jws",
        "jku": identity + "/.well-known/http-message-signatures-directory",
        "kid": GOVERNANCE_KID,
        **(header_extra or {}),
    }
    claims = {"iss": identity, "aud": "https://seller-7k3q.com/mcp/", "iat": 1000, "exp": 1600}
    claims.update(claims_extra or {})
    private = private_key_from_jwk(KEYS[GOVERNANCE_KID], d_field="_private_d_for_test_only")
    return jose_jws.serialize_compact(
        header,
        json.dumps(claims).encode(),
        OKPKey.import_key(private),
        registry=_governance_jws_registry("EdDSA"),
    )


@pytest.mark.parametrize("markers", ["matched", "claim_without_marker", "task_without_hash"])
async def test_governance_action_binding_markers(markers):
    """Action-authorizing tokens carry crit markers (security.mdx checklist step 4)."""
    vector = json.loads((ROOT / "001-governance-token.json").read_text())
    binding = {"authorized_task": "create_media_buy", "authorized_payload_hash": "h"}
    header = {"crit": list(binding), **{name: True for name in binding}}
    if markers == "claim_without_marker":
        header = {}
    claims = dict(binding)
    if markers == "task_without_hash":
        header = {"crit": ["authorized_task"], "authorized_task": True}
        claims = {"authorized_task": "create_media_buy"}
    token = _governance_token(header, claims)

    async def verify():
        return await verify_wba_governance_issuer(
            token,
            signer_keys=_vector_resolver(vector, KEYS),
            governance_agents=vector["role_listing"]["adcp:governance"],
            now=1100,
        )

    if markers == "matched":
        assert await verify() == "https://governance-7k3q.com"
        return
    with pytest.raises(WbaGovernanceError) as caught:
        await verify()
    assert caught.value.code == "governance_token_invalid"


async def test_governance_issuer_is_checked_before_key_discovery():
    token = _governance_token(iss="https://buyer-7k3q.com")

    async def resolve(keyid, *, signer_origin=None):
        pytest.fail("an unlisted issuer must not trigger key discovery")

    with pytest.raises(WbaGovernanceError) as caught:
        await verify_wba_governance_issuer(
            token,
            signer_keys=resolve,
            governance_agents=["https://governance-7k3q.com"],
            now=1100,
        )
    assert caught.value.code == "governance_issuer_not_authorized"
