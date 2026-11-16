"""Tests for issue #641 — canceled: Literal[True] = True destructive default.

UpdateMediaBuyRequest and PackageUpdate previously had ``canceled: Literal[True] = True``,
meaning any call that omitted the field silently triggered irreversible cancellation.
The fix widens the type to ``Literal[True] | None = None`` so omission is non-destructive.
"""

from __future__ import annotations

import pytest


class TestUpdateMediaBuyRequestCanceledDefault:
    """UpdateMediaBuyRequest.canceled must default to None (non-destructive)."""

    _ACCOUNT_KWARGS = {
        "account": {"account_id": "acc_test_001"},
        "media_buy_id": "mbuy-123",
        "idempotency_key": "a" * 16,
    }

    def test_canceled_defaults_to_none_when_omitted(self) -> None:
        from adcp.types.domains.media_buy.update_media_buy_request import (
            UpdateMediaBuyRequest,
        )

        req = UpdateMediaBuyRequest(**self._ACCOUNT_KWARGS)
        assert req.canceled is None

    def test_canceled_true_still_accepted(self) -> None:
        from adcp.types.domains.media_buy.update_media_buy_request import (
            UpdateMediaBuyRequest,
        )

        req = UpdateMediaBuyRequest(**self._ACCOUNT_KWARGS, canceled=True)
        assert req.canceled is True

    def test_canceled_none_excluded_from_wire_payload(self) -> None:
        """When canceled is None, model_dump(exclude_none=True) omits it — no cancellation on wire."""
        from adcp.types.domains.media_buy.update_media_buy_request import (
            UpdateMediaBuyRequest,
        )

        req = UpdateMediaBuyRequest(**self._ACCOUNT_KWARGS)
        payload = req.model_dump(mode="json", exclude_none=True)
        assert "canceled" not in payload

    def test_canceled_true_present_in_wire_payload(self) -> None:
        """Explicit canceled=True must appear in the wire payload to trigger cancellation."""
        from adcp.types.domains.media_buy.update_media_buy_request import (
            UpdateMediaBuyRequest,
        )

        req = UpdateMediaBuyRequest(**self._ACCOUNT_KWARGS, canceled=True)
        payload = req.model_dump(mode="json", exclude_none=True)
        assert payload["canceled"] is True

    def test_canceled_false_rejected(self) -> None:
        """Literal[True] still rejects False — the field is a one-way commit signal."""
        from pydantic import ValidationError

        from adcp.types.domains.media_buy.update_media_buy_request import (
            UpdateMediaBuyRequest,
        )

        with pytest.raises(ValidationError):
            UpdateMediaBuyRequest(**self._ACCOUNT_KWARGS, canceled=False)  # type: ignore[arg-type]


class TestPackageUpdateCanceledDefault:
    """PackageUpdate.canceled must default to None (non-destructive)."""

    def test_canceled_defaults_to_none_when_omitted(self) -> None:
        from adcp.types.domains.media_buy.package_update import PackageUpdate

        pkg = PackageUpdate(package_id="pkg-1")
        assert pkg.canceled is None

    def test_canceled_true_still_accepted(self) -> None:
        from adcp.types.domains.media_buy.package_update import PackageUpdate

        pkg = PackageUpdate(package_id="pkg-1", canceled=True)
        assert pkg.canceled is True

    def test_canceled_none_excluded_from_wire_payload(self) -> None:
        from adcp.types.domains.media_buy.package_update import PackageUpdate

        pkg = PackageUpdate(package_id="pkg-1")
        payload = pkg.model_dump(mode="json", exclude_none=True)
        assert "canceled" not in payload

    def test_canceled_true_present_in_wire_payload(self) -> None:
        from adcp.types.domains.media_buy.package_update import PackageUpdate

        pkg = PackageUpdate(package_id="pkg-1", canceled=True)
        payload = pkg.model_dump(mode="json", exclude_none=True)
        assert payload["canceled"] is True


class TestTheWalkEmitsTheNonDestructiveShape:
    """The shape is the walk's own output, not a regex applied after it.

    There is no ``scripts/post_generate_fixes.py`` in this emission, so there is
    no ``_CANCELED_FIELD_RE`` to run twice and no idempotence to grade. The two
    tests that stood here exercised that regex against synthesized source.

    What decides the shape is the document: ``canceled`` is ``{"type":
    "boolean", "const": true}`` and is NOT in ``required``, so an optional
    property compiles to ``Literal[True] | None = None`` -- the pinned-default
    rule applies only to a REQUIRED property the document pins (decision index,
    ``verdicts/a-pinned-default-is-the-documents-own.md``). The emitted
    annotation is read here so the two facts stay side by side.
    """

    def test_the_document_states_an_optional_pinned_boolean(self) -> None:
        import json
        from pathlib import Path

        from adcp.validation.version import resolve_bundle_key

        repo_root = Path(__file__).resolve().parent.parent
        bundle = resolve_bundle_key((repo_root / "src/adcp/ADCP_VERSION").read_text().strip())
        document = json.loads(
            (repo_root / "schemas/cache" / bundle / "media-buy/package-update.json").read_text()
        )

        assert document["properties"]["canceled"] == {
            "type": "boolean",
            "const": True,
            "description": document["properties"]["canceled"]["description"],
        }
        assert "canceled" not in document["required"]

    def test_the_emitted_annotation_is_literal_true_or_none(self) -> None:
        import inspect

        from adcp.types.domains.media_buy.package_update import PackageUpdate

        [line] = [
            line
            for line in inspect.getsource(PackageUpdate).splitlines()
            if line.lstrip().startswith("canceled:")
        ]
        assert "Literal[True] | None" in line
        assert line.rstrip().endswith("= None")
