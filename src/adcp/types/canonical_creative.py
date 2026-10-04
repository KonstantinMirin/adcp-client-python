"""Canonical-first creative models for the Python 7 public API.

The generated protocol models intentionally remain wire-faithful through the
AdCP 3.x transition and therefore contain legacy named-format identity.  They
are exposed from :mod:`adcp.types.legacy`.  This module provides the primary
application-facing models: legacy identity is absent from their declared
fields, JSON Schema, and serialized output at every nesting depth.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable, Sequence
from typing import Annotated, Any, ClassVar, Protocol, TypeVar, cast

from pydantic import (
    ConfigDict,
    Field,
    GetJsonSchemaHandler,
    PrivateAttr,
    SerializerFunctionWrapHandler,
    WithJsonSchema,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic.json_schema import GenerateJsonSchema
from pydantic_core import CoreSchema

from adcp.types.base import AdCPBaseModel
from adcp.types.generated_poc.core.canonical_format_kind import CanonicalFormatKind
from adcp.types.generated_poc.core.creative_asset import CreativeAsset as _CanonicalCreativeWire
from adcp.types.generated_poc.core.creative_filters import CreativeFilters as _LegacyCreativeFilters
from adcp.types.generated_poc.core.creative_manifest import (
    CreativeManifest as _CanonicalCreativeManifestWire,
)
from adcp.types.generated_poc.core.creative_variant import CreativeVariant as _LegacyCreativeVariant
from adcp.types.generated_poc.core.package import Package as _LegacyPackage
from adcp.types.generated_poc.core.placement import Placement as _LegacyPlacement
from adcp.types.generated_poc.core.platform_extension_ref import PlatformExtensionReference
from adcp.types.generated_poc.core.pricing_option import PricingOption as _LegacyPricingOption
from adcp.types.generated_poc.core.product import Product as _LegacyProduct
from adcp.types.generated_poc.core.product_filters import ProductFilters as _LegacyProductFilters
from adcp.types.generated_poc.core.product_format_declaration import SellerPreference
from adcp.types.generated_poc.creative.get_creative_delivery_response import (
    Creative as _LegacyDeliveryCreative,
)
from adcp.types.generated_poc.creative.get_creative_delivery_response import (
    GetCreativeDeliveryResponse as _LegacyGetCreativeDeliveryResponse,
)
from adcp.types.generated_poc.creative.list_creatives_request import (
    ListCreativesRequest as _LegacyListCreativesRequest,
)
from adcp.types.generated_poc.creative.list_creatives_response import (
    Creatives1 as _CanonicalListedCreative,
)
from adcp.types.generated_poc.creative.list_creatives_response import (
    ListCreativesResponse as _LegacyListCreativesResponse,
)
from adcp.types.generated_poc.creative.sync_creatives_request import (
    SyncCreativesRequest as _LegacySyncCreativesRequest,
)
from adcp.types.generated_poc.enums.channels import MediaChannel
from adcp.types.generated_poc.media_buy.create_media_buy_request import (
    CreateMediaBuyRequest as _LegacyCreateMediaBuyRequest,
)
from adcp.types.generated_poc.media_buy.create_media_buy_response import (
    CreateMediaBuyResponse1 as _LegacyCreateMediaBuyResponse1,
)
from adcp.types.generated_poc.media_buy.create_media_buy_response import (
    CreateMediaBuyResponse2 as _LegacyCreateMediaBuyResponse2,
)
from adcp.types.generated_poc.media_buy.create_media_buy_response import (
    CreateMediaBuyResponse3 as _LegacyCreateMediaBuyResponse3,
)
from adcp.types.generated_poc.media_buy.get_media_buy_delivery_response import (
    GetMediaBuyDeliveryResponse as _LegacyGetMediaBuyDeliveryResponse,
)
from adcp.types.generated_poc.media_buy.get_media_buys_response import (
    GetMediaBuysResponse as _LegacyGetMediaBuysResponse,
)
from adcp.types.generated_poc.media_buy.get_media_buys_response import (
    MediaBuy as _LegacyMediaBuy,
)
from adcp.types.generated_poc.media_buy.get_media_buys_response import (
    Package as _LegacyMediaBuyPackage,
)
from adcp.types.generated_poc.media_buy.get_products_request import (
    GetProductsRequest as _LegacyGetProductsRequest,
)
from adcp.types.generated_poc.media_buy.get_products_response import (
    GetProductsResponse as _LegacyGetProductsResponse,
)
from adcp.types.generated_poc.media_buy.package_request import (
    PackageRequest as _LegacyPackageRequest,
)
from adcp.types.generated_poc.media_buy.package_update import PackageUpdate as _LegacyPackageUpdate
from adcp.types.generated_poc.media_buy.update_media_buy_request import (
    UpdateMediaBuyRequest as _LegacyUpdateMediaBuyRequest,
)
from adcp.types.generated_poc.media_buy.update_media_buy_response import (
    UpdateMediaBuyResponse1 as _LegacyUpdateMediaBuyResponse1,
)
from adcp.types.generated_poc.media_buy.update_media_buy_response import (
    UpdateMediaBuyResponse2 as _LegacyUpdateMediaBuyResponse2,
)
from adcp.types.generated_poc.media_buy.update_media_buy_response import (
    UpdateMediaBuyResponse3 as _LegacyUpdateMediaBuyResponse3,
)
from adcp.types.legacy import LegacyFormatId
from adcp.types.media_buy_status_helpers import (
    MEDIA_BUY_LEGACY_STATUS_VALUES,
    unwrap_enum_value,
)
from adcp.types.variants import SchemaVariant

_OpenCanonicalFormatKind = Annotated[
    CanonicalFormatKind | str,
    Field(union_mode="left_to_right"),
]

_LEGACY_IDENTITY_KEY = re.compile(r"(^|_)(?:format_ids?|v1_format_ref)($|_)")
_CREDENTIAL_SHAPED_KEY_SUFFIXES = (
    "credential",
    "credentials",
    "token",
    "secret",
    "api_key",
    "apikey",
    "password",
    "bearer",
)


def _walk_for_credential_keys(value: Any, *, path: str = "") -> str | None:
    """Return the first credential-shaped key path under ``value``."""

    if isinstance(value, dict):
        for key, nested in value.items():
            nested_path = f"{path}.{key}" if path else str(key)
            if isinstance(key, str) and any(
                key.lower().endswith(suffix) for suffix in _CREDENTIAL_SHAPED_KEY_SUFFIXES
            ):
                return nested_path
            found = _walk_for_credential_keys(nested, path=nested_path)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            found = _walk_for_credential_keys(nested, path=f"{path}[{index}]")
            if found is not None:
                return found
    elif isinstance(value, AdCPBaseModel):
        return _walk_for_credential_keys(value.model_dump(mode="python"), path=path)
    return None


class _JsonSchemaHandlerWithGenerator(Protocol):
    """The concrete handler pydantic passes in carries the active generator.

    ``GetJsonSchemaHandler`` is the documented protocol and does not declare
    ``generate_json_schema``; the object pydantic actually supplies does, and
    reaching it is how a nested definition registry gets sanitized.
    """

    generate_json_schema: GenerateJsonSchema


def is_legacy_creative_identity_key(key: object) -> bool:
    """Return whether *key* names legacy creative routing identity."""

    return isinstance(key, str) and bool(_LEGACY_IDENTITY_KEY.search(key))


def _is_format_scoped_agent_tuple(value: dict[Any, Any], *, path: str) -> bool:
    """Recognize legacy format owners, including tuples with extension keys."""

    keys = set(value)
    if not {"agent_url", "id"} <= keys:
        return False
    # Several protocol surfaces intentionally carry ordinary agent, signal,
    # and list descriptors with the same structural pair. Match RC3's explicit
    # non-creative contexts; unknown extension paths fail closed because a
    # LegacyFormatId may itself contain extension keys.
    path_segment = re.sub(r"\[\d+\]$", "", path.rsplit(".", 1)[-1]).lower()
    noncreative_agent = not re.search(
        r"(^|_)(?:creative|format|legacy)($|_)", path_segment
    ) and bool(re.search(r"(^|_)(?:agents?|agent_details|agent_info)($|_)", path_segment))
    noncreative_signal = value.get("source") == "agent" and bool(
        re.search(r"(^|_)signal_ids?($|_)", path_segment)
    )
    noncreative_list = isinstance(value.get("list_id"), str) and bool(
        re.search(r"(^|_)(?:property_list|collection_list|list_ref)($|_)", path_segment)
    )
    if noncreative_agent or noncreative_signal or noncreative_list:
        return False
    return True


def strip_legacy_creative_identity(
    value: Any,
    *,
    _path: str = "$",
    _format_scope: bool = False,
) -> Any:
    """Recursively remove legacy creative identity from a serialized value.

    This is deliberately a runtime boundary rather than a typing convention.
    Unknown extension bags are traversed too, so ``extra='allow'`` can never be
    used to smuggle ``format_id`` or ``format_ids`` through a primary model.
    """

    if isinstance(value, dict):
        legacy_tuple = _is_format_scoped_agent_tuple(
            value,
            path=_path,
        )
        return {
            key: strip_legacy_creative_identity(
                item,
                _path=f"{_path}.{key}",
                _format_scope=_format_scope or (isinstance(key, str) and "format" in key.lower()),
            )
            for key, item in value.items()
            if not is_legacy_creative_identity_key(key)
            and not (legacy_tuple and key == "agent_url")
        }
    if isinstance(value, list):
        return [
            strip_legacy_creative_identity(
                item,
                _path=f"{_path}[{index}]",
                _format_scope=_format_scope,
            )
            for index, item in enumerate(value)
        ]
    if isinstance(value, tuple):
        return tuple(
            strip_legacy_creative_identity(
                item,
                _path=f"{_path}[{index}]",
                _format_scope=_format_scope,
            )
            for index, item in enumerate(value)
        )
    return value


def _legacy_creative_identity_path(
    value: Any,
    *,
    path: str = "$",
    allow_root_v1_ref: bool = False,
    format_scope: bool = False,
) -> str | None:
    """Locate legacy creative identity in model input without mutating it."""

    if isinstance(value, AdCPBaseModel):
        value = value.model_dump(mode="python")
    if isinstance(value, dict):
        if _is_format_scoped_agent_tuple(value, path=path):
            return f"{path}.agent_url"
        for key, nested in value.items():
            if is_legacy_creative_identity_key(key):
                if allow_root_v1_ref and path == "$" and key == "v1_format_ref":
                    continue
                return f"{path}.{key}"
            found = _legacy_creative_identity_path(
                nested,
                path=f"{path}.{key}",
                format_scope=format_scope or (isinstance(key, str) and "format" in key.lower()),
            )
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            found = _legacy_creative_identity_path(
                nested,
                path=f"{path}[{index}]",
                format_scope=format_scope,
            )
            if found is not None:
                return found
    return None


def _looks_like_legacy_format_tuple(schema: dict[str, Any], properties: dict[str, Any]) -> bool:
    keys = set(properties)
    title = str(schema.get("title", "")).lower()
    return {"agent_url", "id"} <= keys and (
        "format" in title or keys <= {"agent_url", "id", "width", "height", "duration_ms"}
    )


def _sanitize_schema_node(value: Any) -> Any:
    if isinstance(value, list):
        return [_sanitize_schema_node(item) for item in value]
    if not isinstance(value, dict):
        return value

    node = {key: _sanitize_schema_node(item) for key, item in value.items()}
    properties = node.get("properties")
    removed: set[str] = set()
    if isinstance(properties, dict):
        legacy_tuple = _looks_like_legacy_format_tuple(node, properties)
        cleaned: dict[str, Any] = {}
        for key, item in properties.items():
            if is_legacy_creative_identity_key(key) or (legacy_tuple and key == "agent_url"):
                removed.add(key)
                continue
            cleaned[key] = item
        node["properties"] = cleaned

    required = node.get("required")
    if isinstance(required, list):
        node["required"] = [
            key
            for key in required
            if key not in removed and not is_legacy_creative_identity_key(key)
        ]
    return node


def sanitize_canonical_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a defensive deep copy with legacy identity removed."""

    sanitized: dict[str, Any] = _sanitize_schema_node(copy.deepcopy(schema))
    return sanitized


def _serialize_canonical_model(
    self: CanonicalBoundaryModel,
    handler: SerializerFunctionWrapHandler,
) -> Any:
    """Enforce the boundary for nested and TypeAdapter serialization too."""

    return strip_legacy_creative_identity(
        handler(self),
        _format_scope=self.__class__.__name__ == "Format",
    )


class CanonicalBoundaryModel(AdCPBaseModel):
    """Base class enforcing the primary canonical runtime boundary.

    Every canonical model is a real subclass of the generated wire model it
    refines, so each one inherits the generated model's fields, its injected
    ``model_validator``s, and its envelope ancestry. Two concerns that used to
    be re-attached per class by ``create_model`` are therefore declared once,
    here, and inherited:

    * ``_serialize_canonical`` — the wrap serializer that strips legacy creative
      identity from nested and ``TypeAdapter`` serialization.
    * ``__pydantic_init_subclass__`` — the one declared field removal. Legacy
      creative identity must be absent from a canonical model's *declared*
      fields, which is the single thing inheritance alone cannot express; the
      rule reads the same :func:`is_legacy_creative_identity_key` predicate that
      governs the input validator, the schema sanitizer and the serializer, so
      there is one strip predicate for all four.

    ``CanonicalBoundaryModel`` is listed LAST among a canonical model's bases.
    Pydantic merges ``model_config`` across bases left to right, so the
    right-most base wins; the generated wire model inherits
    :class:`AdCPBaseModel`'s ``extra`` policy and would otherwise override this
    class's ``extra="allow"`` and start dropping caller-supplied extension keys.
    """

    model_config = ConfigDict(extra="allow", defer_build=True)
    __adcp_canonical_creative_model__: ClassVar[bool] = True

    _serialize_canonical = model_serializer(mode="wrap")(_serialize_canonical_model)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Remove inherited legacy creative identity from the declared fields.

        Each removed name is then bound as a plain class attribute holding
        ``None`` — which is the removal's own truth, and which the inherited
        validators need. A generated model can carry an injected validator that
        READS the removed field: ``list-creatives-response.json``'s
        ``_validate_format_reference_xor`` evaluates
        ``(self.format_id is None) == (self.format_kind is None)``. Inheritance
        is the point of this layer, so that validator now runs on the canonical
        model, and with the field merely deleted it raised ``AttributeError``.
        With the name reading ``None`` the XOR reduces to exactly the invariant
        the canonical model should hold — ``format_kind`` must be set — which is
        the same thing the canonical declaration states by making it required.

        Binding happens AFTER class creation, so pydantic never considers the
        name a field candidate; ``model_fields``, the JSON schema and the wire
        are all unaffected. Measured scope: one such validator, on one model.
        """

        removed = [name for name in cls.model_fields if is_legacy_creative_identity_key(name)]
        for name in removed:
            del cls.model_fields[name]
            cls.__annotations__.pop(name, None)
            setattr(cls, name, None)
        if removed:
            cls.model_rebuild(force=True)

    @model_validator(mode="before")
    @classmethod
    def _reject_legacy_creative_identity(cls, value: Any) -> Any:
        found = _legacy_creative_identity_path(
            value,
            allow_root_v1_ref=cls.__name__ == "Format",
            format_scope=cls.__name__ == "Format",
        )
        if found is not None:
            raise ValueError(
                f"{found} contains legacy creative identity; use an explicit Legacy* model"
            )
        return value

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("serialize_as_any", False)
        stripped: dict[str, Any] = strip_legacy_creative_identity(
            super().model_dump(**kwargs),
            _format_scope=self.__class__.__name__ == "Format",
        )
        return stripped

    def model_dump_json(self, **kwargs: Any) -> str:
        kwargs.setdefault("serialize_as_any", False)
        raw = super().model_dump_json(**kwargs)
        clean = strip_legacy_creative_identity(
            json.loads(raw),
            _format_scope=self.__class__.__name__ == "Format",
        )
        indent = kwargs.get("indent")
        return json.dumps(
            clean,
            ensure_ascii=False,
            indent=indent,
            separators=None if indent is not None else (",", ":"),
        )

    @classmethod
    def model_json_schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return sanitize_canonical_schema(super().model_json_schema(*args, **kwargs))

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> dict[str, Any]:
        """Enforce the boundary for TypeAdapter and containing-model schemas."""

        schema = sanitize_canonical_schema(handler(core_schema))
        # TypeAdapter assembles shared definitions outside the model's returned
        # node. Mutate the active generator's definition registry as well so
        # unreachable generated legacy definitions cannot leak into the final
        # recursive schema document.
        generator = cast(_JsonSchemaHandlerWithGenerator, handler).generate_json_schema
        for key, definition in list(generator.definitions.items()):
            generator.definitions[key] = sanitize_canonical_schema(definition)
        return schema


def _inherit(source: type[AdCPBaseModel], name: str) -> Any:
    """Return a copy of ``source``'s ``name`` field for a retyped redeclaration.

    A canonical model that narrows an inherited field's *annotation* still wants
    the generated field's constraints, description and default. Redeclaring with
    this as the assigned value keeps every one of them, where a bare ``Field()``
    would silently drop ``min_length`` and friends. The return type is ``Any``
    because a ``FieldInfo`` is what pydantic expects on the right-hand side of an
    annotated field declaration — the same reason ``Field()`` itself is ``Any``.
    """

    return copy.deepcopy(source.model_fields[name])


_CanonicalParamsT = TypeVar("_CanonicalParamsT", bound=AdCPBaseModel)
CanonicalPricingOption = Annotated[
    _LegacyPricingOption,
    WithJsonSchema(
        {
            "type": "object",
            "description": "Pricing option; legacy format-scoped vendor fields are unavailable.",
        }
    ),
]


class Format(CanonicalBoundaryModel):
    """Canonical format declaration exposed as ``adcp.Format``."""

    format_option_id: str | None = Field(
        default=None,
        description="Stable option identifier within the product or publisher namespace.",
    )
    publisher_domain: str | None = Field(
        default=None,
        pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$",
    )
    display_name: str | None = None
    applies_to_channels: list[MediaChannel] | None = None
    seller_preference: SellerPreference | None = None
    canonical_formats_only: bool | None = None
    experimental: bool | None = None
    format_shape: str | None = None
    format_schema: PlatformExtensionReference | None = None
    format_kind: CanonicalFormatKind
    params: dict[str, Any]

    _legacy_format_refs: list[LegacyFormatId] = PrivateAttr(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _reject_legacy_conflicts_and_credentials(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("canonical_formats_only") is True and data.get("v1_format_ref"):
            raise ValueError(
                "canonical_formats_only=True is mutually exclusive with legacy v1_format_ref"
            )
        for bag_name, bag in (
            ("params", data.get("params")),
            (
                "extras",
                {
                    key: value
                    for key, value in data.items()
                    if key not in cls.model_fields and key != "v1_format_ref"
                },
            ),
        ):
            found = _walk_for_credential_keys(bag, path=bag_name)
            if found is not None:
                raise ValueError(
                    f"{found!r} matches a credential-shaped key suffix and cannot "
                    "be stored in a canonical format declaration"
                )
        return data

    def __init__(self, **data: Any) -> None:
        refs = data.get("v1_format_ref")
        if "capability_id" in data and "format_option_id" not in data:
            data["format_option_id"] = data.pop("capability_id")
        super().__init__(**data)
        if self.__pydantic_extra__ is not None:
            self.__pydantic_extra__.pop("v1_format_ref", None)
        if refs:
            self._legacy_format_refs = [
                LegacyFormatId.model_validate(copy.deepcopy(ref)) for ref in refs
            ]

    @property
    def legacy_format_refs(self) -> tuple[LegacyFormatId, ...]:
        """Original tuples retained only for an explicit compatibility adapter."""

        return tuple(copy.deepcopy(ref) for ref in self._legacy_format_refs)

    def params_as(self, canonical_type: type[_CanonicalParamsT]) -> _CanonicalParamsT:
        """Validate the open parameter bag against a typed canonical model."""

        return canonical_type.model_validate(self.params)

    @model_validator(mode="after")
    def _validate_custom_shape(self) -> Format:
        if self.format_kind is CanonicalFormatKind.custom:
            if not self.format_shape:
                raise ValueError("custom formats require format_shape")
            if self.format_schema is None:
                raise ValueError("custom formats require format_schema")
        elif self.format_shape is not None or self.format_schema is not None:
            raise ValueError("format_shape and format_schema are only valid for custom formats")
        return self


ProductFormatDeclaration = Format


class Placement(_LegacyPlacement, CanonicalBoundaryModel):
    """Canonical placement; ``format_options`` are canonical declarations."""

    format_options: SchemaVariant[list[Format] | None] = Field(default=None, min_length=1)


class Product(_LegacyProduct, CanonicalBoundaryModel):
    """Canonical product; formats, placements and pricing are canonical."""

    format_options: SchemaVariant[list[Format]] = Field(
        min_length=1, description="Canonical creative formats accepted by this product."
    )
    placements: SchemaVariant[list[Placement] | None] = Field(default=None, min_length=1)
    pricing_options: list[CanonicalPricingOption] = Field(min_length=1)


class CreativeAsset(_CanonicalCreativeWire, CanonicalBoundaryModel):
    """Canonical creative asset; the format kind is required, not optional."""

    format_kind: CanonicalFormatKind


class Creative(_CanonicalListedCreative, CanonicalBoundaryModel):
    """Canonical listed creative; the format kind is required, not optional."""

    format_kind: CanonicalFormatKind


class CreativeManifest(_CanonicalCreativeManifestWire, CanonicalBoundaryModel):
    """Canonical manifest accepting the SDK's public standalone asset models.

    The 3.2 aggregate asset-union schema currently generates structurally
    duplicate Pydantic classes. Convert public ``ImageContent``/``UrlContent``
    (and peers) back to their wire dictionaries before the aggregate union
    validates them. This keeps the public constructors composable without
    relaxing the on-wire discriminator checks.
    """

    @model_validator(mode="before")
    @classmethod
    def _normalize_standalone_assets(cls, data: Any) -> Any:
        if not isinstance(data, dict) or not isinstance(data.get("assets"), dict):
            return data

        def wire_value(value: Any) -> Any:
            if isinstance(value, AdCPBaseModel):
                return value.model_dump(mode="json", exclude_none=True)
            if isinstance(value, list):
                return [wire_value(item) for item in value]
            return value

        return {
            **data,
            "assets": {key: wire_value(value) for key, value in data["assets"].items()},
        }


class CreativeVariant(_LegacyCreativeVariant, CanonicalBoundaryModel):
    """Canonical creative variant whose manifest is the canonical manifest."""

    manifest: CreativeManifest | None = None


class _DeliveryCreativeManifest(_CanonicalCreativeManifestWire, CanonicalBoundaryModel):
    """Tolerant served output, deliberately not a subtype of the strict input."""

    format_kind: SchemaVariant[_OpenCanonicalFormatKind | None] = _inherit(
        _CanonicalCreativeManifestWire, "format_kind"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_readback(cls, data: Any) -> Any:
        if isinstance(data, AdCPBaseModel) and not isinstance(data, cls):
            data = data.model_dump(mode="python")
        # Pydantic binds the validator to a descriptor proxy on the class.
        normalize = cast(Callable[[Any], Any], CreativeManifest._normalize_standalone_assets)
        return normalize(data)


class _DeliveryCreativeVariant(_LegacyCreativeVariant, CanonicalBoundaryModel):
    """A delivery row whose rendered manifest may use a future format kind."""

    manifest: _DeliveryCreativeManifest | None = _inherit(_LegacyCreativeVariant, "manifest")

    @model_validator(mode="before")
    @classmethod
    def _normalize_readback(cls, data: Any) -> Any:
        if isinstance(data, AdCPBaseModel) and not isinstance(data, cls):
            return data.model_dump(mode="python")
        return data


def _revalidate_subclass_instances_of_strict_base(tolerant: type[AdCPBaseModel]) -> None:
    """Stop a tolerant delivery model passing as the strict wire model it refines.

    These two models are deliberately NOT subtypes of the strict creative input -- they
    accept a ``format_kind`` the pinned enum does not know -- but they subclass the
    generated wire model to inherit its fields and validators. Pydantic's default
    ``revalidate_instances="never"`` skips validation for an instance of ANY subclass,
    so ``WireCreativeManifest.model_validate(delivery_manifest)`` would hand the
    tolerant instance straight back and the future ``format_kind`` would reach creative
    input -- the exact weakening #1241 exists to prevent.

    ``"subclass-instances"`` revalidates only a subclass instance, so an exact-class
    instance still passes through untouched and composing a model into a field keeps
    its identity (``tests/test_composability_invariant.py``). The base is read off
    ``__bases__`` rather than named, so it follows the declaration above.

    Graded by ``tests/test_delivery_manifest_readback.py``.
    """
    for base in tolerant.__bases__:
        if base is CanonicalBoundaryModel or not issubclass(base, AdCPBaseModel):
            continue
        if base.model_config.get("revalidate_instances") == "subclass-instances":
            continue
        base.model_config = ConfigDict(
            **{**base.model_config, "revalidate_instances": "subclass-instances"}
        )
        base.model_rebuild(force=True)


for _tolerant in (_DeliveryCreativeManifest, _DeliveryCreativeVariant):
    _revalidate_subclass_instances_of_strict_base(_tolerant)


class DeliveryCreative(_LegacyDeliveryCreative, CanonicalBoundaryModel):
    """Canonical served creative; variants are the tolerant delivery rows."""

    format_kind: _OpenCanonicalFormatKind | None = None
    variants: SchemaVariant[list[_DeliveryCreativeVariant]] = _inherit(
        _LegacyDeliveryCreative, "variants"
    )


class CreativeFilters(_LegacyCreativeFilters, CanonicalBoundaryModel):
    """Canonical creative filters; legacy identity selection is unavailable."""


class ProductFilters(_LegacyProductFilters, CanonicalBoundaryModel):
    """Canonical product filters; legacy identity selection is unavailable."""


class PackageRequest(_LegacyPackageRequest, CanonicalBoundaryModel):
    """Canonical package request preserving beta.3 selector constraints."""

    creatives: list[CreativeAsset] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_format_params(self) -> PackageRequest:
        if self.params is not None and self.format_kind is None:
            raise ValueError("params requires format_kind")
        if self.params is not None and self.format_kind == "image":
            if ("width" in self.params) != ("height" in self.params):
                raise ValueError("image params width and height must co-occur")
        return self


class PackageUpdate(_LegacyPackageUpdate, CanonicalBoundaryModel):
    """Canonical package update; creatives are canonical assets."""

    creatives: SchemaVariant[list[CreativeAsset] | None] = Field(default=None, min_length=1)


class Package(_LegacyPackage, CanonicalBoundaryModel):
    """Canonical package; legacy format identity is absent."""


class GetProductsRequest(_LegacyGetProductsRequest, CanonicalBoundaryModel):
    """Canonical discovery request with legacy response-field selection rejected."""

    filters: ProductFilters | None = None

    @field_validator("fields")
    @classmethod
    def _reject_legacy_fields(cls, value: Any) -> Any:
        if value and any(
            is_legacy_creative_identity_key(getattr(item, "value", item)) for item in value
        ):
            raise ValueError(
                "format_id and format_ids are unavailable on the canonical get_products API"
            )
        return value


class GetProductsResponse(_LegacyGetProductsResponse, CanonicalBoundaryModel):
    """Canonical discovery response; products are canonical products."""

    products: SchemaVariant[list[Product] | None] = None


class CreateMediaBuyRequest(_LegacyCreateMediaBuyRequest, CanonicalBoundaryModel):
    """Canonical create request; packages are canonical package requests."""

    packages: list[PackageRequest] | None = None


class UpdateMediaBuyRequest(_LegacyUpdateMediaBuyRequest, CanonicalBoundaryModel):
    """Canonical update request; both package lists are canonical."""

    packages: list[PackageUpdate] | None = None
    new_packages: SchemaVariant[list[PackageRequest] | None] = None


class CreateMediaBuyResponse1(_LegacyCreateMediaBuyResponse1, CanonicalBoundaryModel):
    """Canonical create response preserving the 3.x legacy-status normalizer."""

    packages: SchemaVariant[list[Package]]

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_status(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw_status = unwrap_enum_value(data.get("status"))
        media_buy_status = unwrap_enum_value(data.get("media_buy_status"))
        if raw_status is None or raw_status == "completed":
            return {**data, "status": "completed"}
        if media_buy_status is None and raw_status in MEDIA_BUY_LEGACY_STATUS_VALUES:
            return {**data, "media_buy_status": raw_status, "status": "completed"}
        if media_buy_status is not None and raw_status == media_buy_status:
            return {**data, "status": "completed"}
        return data


class CreateMediaBuyResponse2(_LegacyCreateMediaBuyResponse2, CanonicalBoundaryModel):
    """Canonical create-media-buy error arm."""


class CreateMediaBuyResponse3(_LegacyCreateMediaBuyResponse3, CanonicalBoundaryModel):
    """Canonical create-media-buy submitted arm."""


CreateMediaBuyResponse = CreateMediaBuyResponse1 | CreateMediaBuyResponse2 | CreateMediaBuyResponse3


class UpdateMediaBuyResponse1(_LegacyUpdateMediaBuyResponse1, CanonicalBoundaryModel):
    """Canonical update response preserving the 3.x legacy-status normalizer."""

    affected_packages: Sequence[Package] | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_status(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw_status = unwrap_enum_value(data.get("status"))
        media_buy_status = unwrap_enum_value(data.get("media_buy_status"))
        if raw_status is None or raw_status == "completed":
            return {**data, "status": "completed"}
        if media_buy_status is None and raw_status in MEDIA_BUY_LEGACY_STATUS_VALUES:
            return {**data, "media_buy_status": raw_status, "status": "completed"}
        if media_buy_status is not None and raw_status == media_buy_status:
            return {**data, "status": "completed"}
        return data


class UpdateMediaBuyResponse2(_LegacyUpdateMediaBuyResponse2, CanonicalBoundaryModel):
    """Canonical update-media-buy error arm."""


class UpdateMediaBuyResponse3(_LegacyUpdateMediaBuyResponse3, CanonicalBoundaryModel):
    """Canonical update-media-buy submitted arm."""


UpdateMediaBuyResponse = UpdateMediaBuyResponse1 | UpdateMediaBuyResponse2 | UpdateMediaBuyResponse3


class SyncCreativesRequest(_LegacySyncCreativesRequest, CanonicalBoundaryModel):
    """Canonical creative sync request; creatives are canonical assets."""

    creatives: SchemaVariant[list[CreativeAsset]] = Field(min_length=1)


class ListCreativesRequest(_LegacyListCreativesRequest, CanonicalBoundaryModel):
    """Canonical creative read request with legacy field selection rejected."""

    filters: CreativeFilters | None = None

    @field_validator("fields")
    @classmethod
    def _reject_legacy_fields(cls, value: Any) -> Any:
        if value and any(
            is_legacy_creative_identity_key(getattr(item, "value", item)) for item in value
        ):
            raise ValueError(
                "format_id and format_ids are unavailable on the canonical list_creatives API"
            )
        return value


class ListCreativesResponse(_LegacyListCreativesResponse, CanonicalBoundaryModel):
    """Canonical creative listing; rows are canonical listed creatives."""

    creatives: SchemaVariant[list[Creative]]


class MediaBuyPackage(_LegacyMediaBuyPackage, CanonicalBoundaryModel):
    """Canonical media-buy package row; legacy format identity is absent."""


class MediaBuy(_LegacyMediaBuy, CanonicalBoundaryModel):
    """Canonical media buy; packages are canonical package rows."""

    packages: Sequence[MediaBuyPackage]


class GetMediaBuysResponse(_LegacyGetMediaBuysResponse, CanonicalBoundaryModel):
    """Canonical media-buy listing; rows are canonical media buys."""

    media_buys: Sequence[MediaBuy]


class GetMediaBuyDeliveryResponse(_LegacyGetMediaBuyDeliveryResponse, CanonicalBoundaryModel):
    """Canonical media-buy delivery response."""


class GetCreativeDeliveryResponse(_LegacyGetCreativeDeliveryResponse, CanonicalBoundaryModel):
    """Canonical creative delivery response; rows are tolerant delivery creatives."""

    creatives: Sequence[DeliveryCreative]


PRIMARY_CANONICAL_MODELS: tuple[type[CanonicalBoundaryModel], ...] = (
    Format,
    Product,
    Placement,
    CreativeAsset,
    Creative,
    CreativeManifest,
    CreativeVariant,
    DeliveryCreative,
    CreativeFilters,
    ProductFilters,
    PackageRequest,
    PackageUpdate,
    Package,
    GetProductsRequest,
    GetProductsResponse,
    CreateMediaBuyRequest,
    CreateMediaBuyResponse1,
    CreateMediaBuyResponse2,
    CreateMediaBuyResponse3,
    UpdateMediaBuyRequest,
    UpdateMediaBuyResponse1,
    UpdateMediaBuyResponse2,
    UpdateMediaBuyResponse3,
    SyncCreativesRequest,
    ListCreativesRequest,
    ListCreativesResponse,
    GetMediaBuysResponse,
    MediaBuy,
    MediaBuyPackage,
    GetMediaBuyDeliveryResponse,
    GetCreativeDeliveryResponse,
)


__all__ = [
    "CanonicalBoundaryModel",
    "CreateMediaBuyRequest",
    "CreateMediaBuyResponse",
    "CreateMediaBuyResponse1",
    "CreateMediaBuyResponse2",
    "CreateMediaBuyResponse3",
    "Creative",
    "CreativeAsset",
    "CreativeFilters",
    "CreativeManifest",
    "CreativeVariant",
    "DeliveryCreative",
    "Format",
    "GetCreativeDeliveryResponse",
    "GetMediaBuyDeliveryResponse",
    "GetMediaBuysResponse",
    "GetProductsRequest",
    "GetProductsResponse",
    "ListCreativesRequest",
    "ListCreativesResponse",
    "MediaBuy",
    "MediaBuyPackage",
    "Package",
    "PackageRequest",
    "PackageUpdate",
    "Placement",
    "PRIMARY_CANONICAL_MODELS",
    "Product",
    "ProductFilters",
    "ProductFormatDeclaration",
    "SyncCreativesRequest",
    "UpdateMediaBuyRequest",
    "UpdateMediaBuyResponse",
    "UpdateMediaBuyResponse1",
    "UpdateMediaBuyResponse2",
    "UpdateMediaBuyResponse3",
    "is_legacy_creative_identity_key",
    "sanitize_canonical_schema",
    "strip_legacy_creative_identity",
]
