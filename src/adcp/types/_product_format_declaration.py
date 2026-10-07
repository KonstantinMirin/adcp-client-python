"""Schema-derived cross-field rules for the generated authoring union."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator
from pydantic_core import PydanticCustomError

from adcp.types.domains.core.product_format_declaration import (
    ProductFormatDeclaration as _GeneratedProductFormatDeclaration,
)
from adcp.validation.schema_loader import get_named_validator


def _check_declaration_rules(data: Any) -> Any:
    if isinstance(data, BaseModel):
        # Defaults that were never supplied are absent on the wire. Explicit
        # nulls retain their presence: root rules test required, not truthiness.
        document = data.model_dump(mode="json", exclude_unset=True, exclude_none=False)
    elif isinstance(data, dict):
        document = data
    else:
        return data

    validator = get_named_validator("core/product-format-declaration.json")
    if validator is None:
        raise RuntimeError("Bundled product-format-declaration schema is unavailable")
    # Each lookup supplies an independent resolver over cached schema data.
    # Evolving it preserves reference resolution and format checking, while
    # selecting only the normative root rules codegen cannot express.
    rules = validator.evolve(schema={"allOf": validator.schema.get("allOf", [])})
    error = next(rules.iter_errors(document), None)
    if error is not None:
        raise PydanticCustomError(str(error.validator), error.message)

    # Preserve the public declaration's credential screening without imposing
    # it on generated classes or changing their definition site.
    from adcp.types.canonical_creative import _walk_for_credential_keys

    known_fields = set(validator.schema.get("properties", {})) | {"format_kind", "params"}
    for bag_name, bag in (
        ("params", document.get("params")),
        ("extras", {key: value for key, value in document.items() if key not in known_fields}),
    ):
        found = _walk_for_credential_keys(bag, path=bag_name)
        if found is not None:
            raise ValueError(
                f"{found!r} matches a credential-shaped key suffix and cannot "
                "be stored in a product format declaration"
            )
    return data


ProductFormatDeclaration = Annotated[
    _GeneratedProductFormatDeclaration, BeforeValidator(_check_declaration_rules)
]
