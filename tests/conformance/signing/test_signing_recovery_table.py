"""``SIGNING_RECOVERY`` is the pinned schema's classification, not a copy of it.

``enums/request-signing-error-code.json`` ships in the same wheel as
:mod:`adcp.signing.errors`, and its ``enumMetadata`` block's own ``$comment``
is addressed at SDKs: "SDKs MUST consume this block instead of parsing
enumDescriptions or inferring from code names." Three obligations follow, and
the tests below are one each:

* **Every code the package can raise is classified.** The anchor is the set of
  request-family code constants the package DECLARES, which is independent of
  the schema document — so a release that drops a code from the enum while the
  verifier still raises it shows up here, where a schema-against-itself
  comparison would agree with whatever the schema said.
* **An unclassified code raises.** A code the enum declares and the metadata
  does not classify is an inconsistent bundle. Defaulting it would publish an
  invented classification under the name of a normative one, so the build is
  the place that fails, not the adopter's retry logic.
* **``_TRANSIENT_CODES`` is a view, not a second table.** The private constant
  predates the public one and used to be hand-transcribed. Its membership is
  graded against the document directly and through the attribute
  ``SignatureVerificationError`` actually sets, so a re-transcription — the
  exact regression this change removes — goes red twice.
"""

from __future__ import annotations

from typing import Any

import pytest

from adcp.signing import SIGNING_RECOVERY, errors, recovery_for
from adcp.signing.errors import (
    _SIGNING_ERROR_CODE_ENUM,
    _TRANSIENT_CODES,
    SignatureVerificationError,
    _build_signing_recovery,
)
from adcp.types import Recovery
from adcp.validation.schema_loader import get_named_schema_document


def _pinned_document() -> dict[str, Any]:
    document = get_named_schema_document(_SIGNING_ERROR_CODE_ENUM)
    assert document is not None, f"{_SIGNING_ERROR_CODE_ENUM} is missing from the bundle"
    return document


def _declared_request_family_codes() -> frozenset[str]:
    """Every request-family code string the package declares as a constant.

    Read off the module rather than written out: the module is the authority on
    what the verifier can raise, and introspection cannot fall behind a new
    constant the way a list in this file would.
    """
    return frozenset(
        value
        for name, value in vars(errors).items()
        if name.isupper() and isinstance(value, str) and value.startswith("request_")
    )


def test_every_declared_request_family_code_is_classified() -> None:
    assert set(SIGNING_RECOVERY) == _declared_request_family_codes()


def test_every_classification_is_a_recovery_member() -> None:
    assert {type(value) for value in SIGNING_RECOVERY.values()} == {Recovery}
    assert set(SIGNING_RECOVERY.values()) == set(Recovery)


def test_the_table_matches_the_pinned_metadata_row_by_row() -> None:
    metadata = _pinned_document()["enumMetadata"]
    assert SIGNING_RECOVERY == {
        code: Recovery(metadata[code]["recovery"]) for code in _pinned_document()["enum"]
    }


def test_the_published_table_is_read_only() -> None:
    with pytest.raises(TypeError):
        SIGNING_RECOVERY["request_signature_invalid"] = Recovery.terminal  # type: ignore[index]


def test_recovery_for_serves_the_table_and_refuses_anything_else() -> None:
    for code, recovery in SIGNING_RECOVERY.items():
        assert recovery_for(code) is recovery
    # The webhook profile declares no enum document and no ``enumMetadata``
    # block, so it has no classification to serve.
    with pytest.raises(KeyError):
        recovery_for("webhook_signature_invalid")


def test_a_code_the_metadata_does_not_classify_fails_the_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = _pinned_document()
    orphan = document["enum"][0]
    del document["enumMetadata"][orphan]
    monkeypatch.setattr(
        "adcp.validation.schema_loader.get_named_schema_document",
        lambda *args, **kwargs: document,
    )

    with pytest.raises(RuntimeError) as excinfo:
        _build_signing_recovery()

    assert orphan in str(excinfo.value)
    assert "inconsistent" in str(excinfo.value)


def test_a_code_classified_with_a_foreign_value_fails_the_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = _pinned_document()
    code = document["enum"][0]
    document["enumMetadata"][code] = {"recovery": "retry_later"}
    monkeypatch.setattr(
        "adcp.validation.schema_loader.get_named_schema_document",
        lambda *args, **kwargs: document,
    )

    with pytest.raises(RuntimeError) as excinfo:
        _build_signing_recovery()

    assert code in str(excinfo.value)
    assert "retry_later" in str(excinfo.value)


def test_an_absent_bundle_fails_the_build(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "adcp.validation.schema_loader.get_named_schema_document",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(RuntimeError, match="inconsistent"):
        _build_signing_recovery()


def test_transient_codes_is_the_schemas_transient_set() -> None:
    document = _pinned_document()
    metadata = document["enumMetadata"]
    assert _TRANSIENT_CODES == {
        code for code in document["enum"] if metadata[code]["recovery"] == "transient"
    }


def test_the_raised_error_defaults_transient_from_the_schema() -> None:
    document = _pinned_document()
    metadata = document["enumMetadata"]
    for code in document["enum"]:
        expected = metadata[code]["recovery"] == "transient"
        assert SignatureVerificationError(code).transient is expected, code
