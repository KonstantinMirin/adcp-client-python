"""The signed AdCP 3.2.3 release is the live default and retains historical bundles.

Release identity values below come from the signed 3.2.3 release and its
``schemas/releases/3.2.3.json`` pin. Until they are filled in, every test that
depends on them fails loudly instead of passing vacuously.

3.2.3 is signed from the ``3.2.x`` maintenance branch rather than ``main``, so
the certificate identity asserted below differs from 3.2.1's. That is the whole
reason ``load_release_pin`` derives a release line's own branch instead of
listing one arm per line.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from importlib.resources import files

import pytest
from jsonschema.validators import validator_for
from pydantic import TypeAdapter

from adcp._version import get_supported_adcp_versions, resolve_adcp_version
from adcp.exceptions import ConfigurationError
from adcp.reporting.feed import InMemoryReportingFeedStore
from adcp.reporting.receipts import ReportingReceiptHandler
from adcp.server.mcp_tools import MCPToolSet
from adcp.types import OptimizationGoal
from adcp.validation import schema_loader

VERSION = "3.2.3"
WIRE_VERSION = "3.2"
_TODO = "TODO: fill from the signed 3.2.3 release"
# v3.2.3 tag commit (schemas/releases/3.2.3.json source_commit).
SOURCE = "dfc6ad602780c1cff4fe23e16e30a570900c89d7"
# SHA-256 of https://adcontextprotocol.org/protocol/3.2.3.tgz.
BUNDLE = "cad841ddef4617fdb6eda130be7b471d9028123489b1384a7ca843ea97fd4ba5"
# The 3.2.x maintenance branch, not main — see the module docstring.
CERTIFICATE_IDENTITY = (
    "https://github.com/adcontextprotocol/adcp/.github/workflows/release.yml@refs/heads/3.2.x"
)
# SHA-256 of test-vectors/reporting-summary/complete-summary.json. Unchanged
# from 3.2.1: the reporting vectors are byte-identical across the two releases.
SUMMARY_SHA = "b72eabbc00b70c1993d53140a2427ac3208e224107c66659f5f25545fb2314e0"
# Counts from _compliance/3.2.3 after the pinned sync. Both file counts are
# 3.2.1's plus exactly 33 — the a2a/ request-signing vector family the A2A
# operation-resolution erratum adds. The schema count does not move, which is
# the same fact the schema-surface comparison reports from the other side.
MANIFEST_FILE_COUNT: int | None = 4215
PROVENANCE_FILE_COUNT: int | None = 203
PROVENANCE_SCHEMA_COUNT: int | None = 1625
SUMMARY_CASE_COUNT: int | None = 22
ROOT = files("adcp").joinpath("_compliance", VERSION)

#: Every compliance tree the wheel SHIPS, keyed by release, with the identity it
#: must still prove. 3.2.1 is no longer the pin but is still packaged (MANIFEST.in
#: and the package-data globs name both), and a packaged tree nobody grades is a
#: contract nobody is holding — so the shared half of the check runs over both.
#: Values: (source_commit, bundle sha256, certificate identity branch, manifest
#: file_count, provenance file count).
_RELEASE_IDENTITY: dict[str, tuple[str, str, str, int, int]] = {
    "3.2.1": (
        "c32bd78c5389753e3b8f3ffd8a1c04b777854d83",
        "00b682c32a36dcc439ccc5e4f5a842f1e08e7b71c85dbbb033a5544365f90287",
        "main",
        4182,
        170,
    ),
    VERSION: (SOURCE, BUNDLE, "3.2.x", MANIFEST_FILE_COUNT, PROVENANCE_FILE_COUNT),
}
# The live pin is one of the shipped trees, and the table is the only list of them.
assert VERSION in _RELEASE_IDENTITY


def _pinned(value):
    """Fail loudly while a release identity value is still a placeholder."""
    if value is None or (isinstance(value, str) and value.startswith("TODO")):
        pytest.fail(f"3.2.3 release identity placeholder not filled in: {value!r}")
    return value


def test_current_pin_and_historical_roots():
    assert files("adcp").joinpath("ADCP_VERSION").read_text().strip() == VERSION
    assert resolve_adcp_version(None) == resolve_adcp_version(VERSION) == WIRE_VERSION
    assert resolve_adcp_version(WIRE_VERSION) == WIRE_VERSION
    assert set(get_supported_adcp_versions()) == {"3.0", "3.1", WIRE_VERSION, "3.2-rc.7"}
    assert schema_loader._resolve_schema_root(WIRE_VERSION) is not None
    for previous in ("3.2.0-rc.3", "3.2.0-rc.6", "3.2.0-rc.7"):
        assert schema_loader._resolve_schema_root(previous) is not None
        if previous == "3.2.0-rc.7":
            assert resolve_adcp_version(previous) == WIRE_VERSION
        else:
            with pytest.raises(ConfigurationError):
                resolve_adcp_version(previous)


@pytest.mark.parametrize("release", sorted(_RELEASE_IDENTITY))
def test_signed_release_and_package_bytes(release: str):
    """Every shipped compliance tree still proves its own signed identity."""
    source, bundle, branch, manifest_files, provenance_files = _RELEASE_IDENTITY[release]
    root = files("adcp").joinpath("_compliance", release)
    provenance = json.loads(root.joinpath("provenance.json").read_bytes())
    assert provenance["release"]["source_commit"] == _pinned(source)
    assert provenance["release"]["artifacts"][release + ".tgz"]["sha256"] == _pinned(bundle)
    assert provenance["release"]["certificate_identity"] == (
        f"https://github.com/adcontextprotocol/adcp/.github/workflows/release.yml@refs/heads/{branch}"
    )
    manifest = json.loads(root.joinpath("bundle-manifest.json").read_bytes())
    assert manifest["adcp_version"] == manifest["published_version"] == release
    assert manifest["file_count"] == _pinned(manifest_files)
    assert len(provenance["files"]) == _pinned(provenance_files)
    assert len(provenance["schemas"]) == _pinned(PROVENANCE_SCHEMA_COUNT)
    assert provenance["files"], "a release with no recorded files proves nothing"
    for relative, expected in provenance["files"].items():
        body = root.joinpath(relative).read_bytes()
        assert len(body) == expected["bytes"], relative
        assert hashlib.sha256(body).hexdigest() == expected["sha256"], relative


def test_live_release_is_the_bytes_in_the_schema_cache():
    """Only the PIN's provenance describes the cache; a retained release does not.

    Stable bundles cache under their wire key ("3.2"), not the release name, so
    there is one cache and the live release owns it. Checking a retained release
    against it would assert that two different releases produced the same bytes.
    """
    provenance = json.loads(ROOT.joinpath("provenance.json").read_bytes())
    assert provenance["release"]["version"] == VERSION
    assert provenance["release"]["certificate_identity"] == CERTIFICATE_IDENTITY
    schema_root = schema_loader._resolve_schema_root(WIRE_VERSION)
    assert schema_root is not None
    assert provenance["schemas"], "a release with no recorded schemas proves nothing"
    for relative, expected in provenance["schemas"].items():
        body = (schema_root.root / relative).read_bytes()
        assert len(body) == expected["cache_bytes"], relative
        assert hashlib.sha256(body).hexdigest() == expected["cache_sha256"], relative


@pytest.mark.parametrize(
    "relative",
    [
        "media-buy/get-reporting-status-response.json",
        "bundled/media-buy/get-reporting-status-response.json",
        "mcp/2026-07-28/profiles/production/media-buy/get-reporting-status-response.json",
    ],
)
def test_signed_reporting_summary_vectors_on_live_schema(relative):
    summary_bytes = ROOT.joinpath(
        "test-vectors/reporting-summary/complete-summary.json"
    ).read_bytes()
    assert hashlib.sha256(summary_bytes).hexdigest() == _pinned(SUMMARY_SHA)
    summary = json.loads(summary_bytes)
    assert len(summary["cases"]) == _pinned(SUMMARY_CASE_COUNT)
    validator = schema_loader.get_named_validator(relative, version=VERSION)
    assert validator is not None
    for case in summary["cases"]:
        payload = deepcopy(summary["response"])
        for operation in case["patch"]:
            parts = [
                part.replace("~1", "/").replace("~0", "~")
                for part in operation["path"].split("/")[1:]
            ]
            parent = payload
            for part in parts[:-1]:
                parent = parent[part]
            if operation["op"] == "remove":
                del parent[parts[-1]]
            else:
                assert operation["op"] in {"add", "replace"}
                parent[parts[-1]] = deepcopy(operation["value"])
        assert validator.is_valid(payload) is case["valid"], (relative, case["name"])


def test_viewable_rate_requires_a_standard_and_bounded_rate():
    validator = schema_loader.get_named_validator("core/optimization-goal.json", version=VERSION)
    assert validator is not None
    goal = {
        "kind": "metric",
        "metric": "viewable_rate",
        "standard": "mrc",
        "target": {"kind": "threshold_rate", "value": 0.7},
    }
    validator.validate(goal)
    assert (
        TypeAdapter(OptimizationGoal)
        .validate_python(goal)
        .model_dump(mode="json", exclude_none=True)
        == goal
    )
    for changed in (
        {**goal, "standard": None},
        {key: value for key, value in goal.items() if key != "standard"},
        {**goal, "target": {"kind": "threshold_rate", "value": 1.1}},
        {**goal, "metric": "clicks"},
    ):
        assert not validator.is_valid(changed)


def test_default_reporting_mount_uses_current_status_schema():
    async def resolve_account(reference, context, consumer):
        return reference["account_id"]

    handler = ReportingReceiptHandler(InMemoryReportingFeedStore(), resolve_account=resolve_account)
    assert handler.get_adcp_version() == WIRE_VERSION
    tools = MCPToolSet(handler)
    output = next(
        tool["outputSchema"]
        for tool in tools.tool_definitions
        if tool["name"] == "get_reporting_status"
    )
    signed = json.loads(
        ROOT.joinpath("test-vectors/reporting-summary/complete-summary.json").read_bytes()
    )
    mounted = validator_for(output)(output)
    assert mounted.is_valid(signed["response"])
    old_periods = deepcopy(signed["response"])
    old_periods_case = next(
        case
        for case in signed["cases"]
        if case["name"] == "complete periods view retains its existing field restriction"
    )
    for operation in old_periods_case["patch"]:
        parts = operation["path"].split("/")[1:]
        parent = old_periods
        for part in parts[:-1]:
            parent = parent[part]
        if operation["op"] == "remove":
            del parent[parts[-1]]
        else:
            parent[parts[-1]] = operation["value"]
    assert not mounted.is_valid(old_periods)
