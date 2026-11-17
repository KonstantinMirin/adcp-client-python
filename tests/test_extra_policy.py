"""Tests for AdCPBaseModel extra field policy.

Validates that:
- AdCPBaseModel defaults to extra='ignore' (forward-compatible)
- Generated types with open or typed additionalProperties override to extra='allow'
- Generated types with x-adcp-open-payload: true preserve open payload fields
- Types without additionalProperties inherit ignore from base
- Consumer subclasses can override extra policy freely
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from adcp.types.domains.core.media_buy_features import MediaBuyFeatures
from adcp.types.domains.governance.check_governance_request import CheckGovernanceRequest
from pydantic import ConfigDict, ValidationError

from adcp._version import _read_packaged_version
from adcp.types.base import AdCPBaseModel
from adcp.validation.version import resolve_bundle_key

_BUNDLE_KEY = resolve_bundle_key(_read_packaged_version())
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas" / "cache" / _BUNDLE_KEY
# `adcp.types.domains` is a compatibility mirror holding one `__init__.py`;
# the compiler writes the tree at `adcp.types._schemas`, which is what a
# sweep over the emitted files has to read.
EMITTED_DIR = Path(__file__).parent.parent / "src" / "adcp" / "types" / "_schemas"


def test_base_model_config_is_ignore() -> None:
    """Sanity check: AdCPBaseModel must have extra='ignore'."""
    assert AdCPBaseModel.model_config.get("extra") == "ignore", (
        f"AdCPBaseModel.model_config is {AdCPBaseModel.model_config!r} — "
        "is the package installed from the correct branch?"
    )


class TestBaseModelDefault:
    """AdCPBaseModel defaults to extra='ignore'."""

    def test_base_model_drops_extra_fields(self) -> None:
        """Unknown fields are silently dropped, not stored or rejected."""

        class DefaultType(AdCPBaseModel):
            name: str

        obj = DefaultType(name="test", unknown_field="dropped")
        assert obj.name == "test"
        assert not hasattr(obj, "unknown_field")

    def test_base_model_accepts_known_fields(self) -> None:
        class DefaultType(AdCPBaseModel):
            name: str

        obj = DefaultType(name="test")
        assert obj.name == "test"


class TestGeneratedTypeOverrides:
    """Generated types with additionalProperties override to extra='allow'."""

    def test_allow_override_stores_extra_fields(self) -> None:
        class ExtensibleType(AdCPBaseModel):
            model_config = ConfigDict(extra="allow")
            name: str

        obj = ExtensibleType(name="test", extra_field="stored")
        assert obj.name == "test"
        assert obj.extra_field == "stored"  # type: ignore[attr-defined]

    def test_ignore_inherited_without_explicit_config(self) -> None:
        """A subclass without its own model_config inherits ignore from base."""

        class InheritedType(AdCPBaseModel):
            name: str
            value: int

        obj = InheritedType(name="test", value=1, surprise="dropped")
        assert obj.name == "test"
        assert not hasattr(obj, "surprise")

    def test_open_payload_field_preserves_extension_data(self) -> None:
        """x-adcp-open-payload fields keep arbitrary structured payload data."""
        payload = {
            "package_id": "pkg_1",
            "custom_targeting": {"segments": ["sports_fans"], "score": 0.92},
        }

        # REQUIREDNESS IS A CONJUNCTION. `check-governance-request.json` states
        # `if {required: [payload]} then {required: [plan_id, tool, target_agent]}`,
        # so supplying `payload` makes the other three required -- and the
        # fixture carried only `plan_id`. Read off the document rather than from
        # one node: `_refuse_at` resolves the conjunction.
        obj = CheckGovernanceRequest(
            plan_id="plan_1",
            caller="https://buyer.example",
            tool="get_products",
            target_agent="https://seller.example",
            payload=payload,
        )

        assert obj.payload == payload

    def test_typed_additional_properties_are_preserved_and_validated(self) -> None:
        """Schema-valued additionalProperties retain their generated value type."""
        features = MediaBuyFeatures(seller_extension=True)

        assert features.seller_extension is True
        with pytest.raises(ValidationError, match="bool_type"):
            MediaBuyFeatures(seller_extension=[])


class TestConsumerSubclassing:
    """Consumers can override extra policy on subclasses."""

    def test_consumer_can_forbid_on_allow_parent(self) -> None:
        """Consumer subclass can tighten from allow to forbid."""

        class LibraryType(AdCPBaseModel):
            model_config = ConfigDict(extra="allow")
            name: str

        class ConsumerType(LibraryType):
            model_config = ConfigDict(extra="forbid")

        with pytest.raises(ValidationError, match="extra_forbidden"):
            ConsumerType(name="test", unknown="rejected")

    def test_consumer_can_forbid_on_ignore_parent(self) -> None:
        """Consumer subclass can tighten from ignore to forbid (dev/CI pattern)."""

        class LibraryType(AdCPBaseModel):
            name: str

        class ConsumerType(LibraryType):
            model_config = ConfigDict(extra="forbid")

        with pytest.raises(ValidationError, match="extra_forbidden"):
            ConsumerType(name="test", unknown="rejected")

    def test_consumer_base_class_pattern(self) -> None:
        """Consumer can use a base class to batch-apply extra policy."""

        class LibraryType(AdCPBaseModel):
            model_config = ConfigDict(extra="allow")
            name: str

        class StrictBase(LibraryType):
            model_config = ConfigDict(extra="forbid")

        class ConsumerType(StrictBase):
            pass

        with pytest.raises(ValidationError, match="extra_forbidden"):
            ConsumerType(name="test", unknown="rejected")


class TestGeneratedCodeMatchesSchemas:
    """CI guard: generated extra='allow' must be backed by schema open-payload policy."""

    @staticmethod
    def _schema_allows_extra(
        obj: Any, all_schemas: dict[str, Any], active: frozenset[int] = frozenset()
    ) -> bool:
        """Check if a schema allows extra fields, following $ref chains.

        Recursively walks the full schema tree, stopping only reference cycles
        on the current path so an open sibling remains discoverable.
        Non-structural keys are safe because
        non-structural keys (description, title, examples) contain strings
        or simple arrays, never dicts with additionalProperties.
        """
        if isinstance(obj, (dict, list)):
            if id(obj) in active:
                return False
            active = active | {id(obj)}
        if isinstance(obj, dict):
            open_payload = obj.get("x-adcp-open-payload")
            if open_payload is False:
                return False
            if open_payload is True:
                return True
            additional_properties = obj.get("additionalProperties")
            if additional_properties is True or isinstance(additional_properties, dict):
                return True
            # Follow $ref to check composed schemas
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if ref_path.startswith(("http://", "https://")):
                    from urllib.parse import urlsplit

                    ref_path = urlsplit(ref_path).path
                ref_normalized = ref_path.replace("-", "_").lstrip("./")
                # Strip versioned prefix like /schemas/3.0.0_rc.2/ to get relative key
                ref_stripped = re.sub(r"^/?schemas/[^/]+/", "", ref_normalized)
                for key in all_schemas:
                    if (
                        key in (ref_normalized, ref_stripped)
                        or key.endswith("/" + ref_normalized)
                        or key.endswith("/" + ref_stripped)
                    ):
                        if TestGeneratedCodeMatchesSchemas._schema_allows_extra(
                            all_schemas[key], all_schemas, active
                        ):
                            return True
            return any(
                TestGeneratedCodeMatchesSchemas._schema_allows_extra(v, all_schemas, active)
                for k, v in obj.items()
                if k != "$schema"
            )
        if isinstance(obj, list):
            return any(
                TestGeneratedCodeMatchesSchemas._schema_allows_extra(item, all_schemas, active)
                for item in obj
            )
        return False

    @staticmethod
    def _load_schemas() -> dict[str, Any]:
        """Load all schemas with underscore-normalized keys for lookup."""
        all_schemas: dict[str, Any] = {}
        for schema_file in SCHEMAS_DIR.rglob("*.json"):
            if schema_file.name == "index.json":
                continue
            with open(schema_file) as f:
                schema = json.load(f)
            rel = str(schema_file.relative_to(SCHEMAS_DIR))
            underscore_key = rel.replace("-", "_")
            all_schemas[underscore_key] = schema
        return all_schemas

    def test_no_spurious_extra_allow(self) -> None:
        """Generated types with extra='allow' must have schema support for open extras."""
        all_schemas = self._load_schemas()
        schema_allows = {
            key: self._schema_allows_extra(schema, all_schemas)
            for key, schema in all_schemas.items()
        }

        spurious = []
        for py_file in sorted(EMITTED_DIR.rglob("*.py")):
            if py_file.name == "__init__.py":
                continue
            content = py_file.read_text()
            if "extra='allow'" not in content and 'extra="allow"' not in content:
                continue
            m = re.search(r"filename:\s+(.+)", content)
            if m:
                schema_name = m.group(1).strip()
                if schema_name in schema_allows and not schema_allows[schema_name]:
                    spurious.append(f"{py_file.name} <- {schema_name}")

        assert (
            not spurious
        ), "Generated files have extra='allow' without schema support:\n" + "\n".join(
            f"  {s}" for s in spurious
        )

    def test_open_payload_true_allows_extra_even_without_additional_properties(self) -> None:
        """x-adcp-open-payload is an authoritative open-payload signal."""
        assert self._schema_allows_extra({"x-adcp-open-payload": True}, {})

    def test_closed_recursive_references_do_not_allow_extras(self) -> None:
        schemas = {
            "first.json": {"$ref": "second.json", "additionalProperties": False},
            "second.json": {"items": {"$ref": "first.json"}},
        }
        assert not self._schema_allows_extra(schemas["first.json"], schemas)

    def test_recursive_reference_does_not_hide_a_reachable_open_sibling(self) -> None:
        schemas = {
            "first.json": {"allOf": [{"$ref": "second.json"}, {"$ref": "open.json"}]},
            "second.json": {"$ref": "first.json"},
            "open.json": {"x-adcp-open-payload": True},
        }
        assert self._schema_allows_extra(schemas["first.json"], schemas)
        assert self._schema_allows_extra(schemas["second.json"], schemas)

    def test_recursive_references_do_not_hide_reachable_open_payloads(self) -> None:
        schemas = {
            "a.json": {"$ref": "b.json"},
            "b.json": {"$ref": "a.json", "properties": {"extension": {"type": "string"}}},
        }
        assert not self._schema_allows_extra(schemas["a.json"], schemas)
        schemas["b.json"]["properties"]["extension"] = {"additionalProperties": True}
        assert self._schema_allows_extra(schemas["a.json"], schemas)

    def test_typed_additional_properties_allows_extra(self) -> None:
        """A schema-valued additionalProperties keyword is an open object contract."""
        assert self._schema_allows_extra(
            {"additionalProperties": {"type": "boolean"}},
            {},
        )

    def test_open_payload_false_wins_over_additional_properties(self) -> None:
        """x-adcp-open-payload false prevents accidental widening of structured objects."""
        assert not self._schema_allows_extra(
            {"x-adcp-open-payload": False, "additionalProperties": True},
            {},
        )
