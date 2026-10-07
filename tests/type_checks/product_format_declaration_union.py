"""Authoring declarations bind the generated union; consumer formats stay open."""

from typing import Any

from pydantic import BaseModel, TypeAdapter
from typing_extensions import assert_type

from adcp.canonical_formats import project_declaration_to_v1, project_v1_format_to_declaration
from adcp.types import Format, ProductFormatDeclaration


class ProductCatalog(BaseModel):
    format_options: list[ProductFormatDeclaration]


def read_kind(declaration: ProductFormatDeclaration) -> str:
    kind: str = declaration.format_kind
    return kind


def read_parameter_model(declaration: ProductFormatDeclaration) -> object:
    return declaration.params


adapter: TypeAdapter[Any] = TypeAdapter(ProductFormatDeclaration)
catalog = ProductCatalog.model_validate(
    {"format_options": [{"format_kind": "image", "params": {"width": 300}}]}
)
assert_type(read_kind(catalog.format_options[0]), str)

consumer = Format(format_kind="future_kind", params={})
assert_type(consumer.format_kind, str)
projection = project_v1_format_to_declaration({})
assert_type(projection.declaration, Format | None)
project_declaration_to_v1(consumer)
