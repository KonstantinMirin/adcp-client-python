"""Tests for code generation from schemas.

This test suite validates that the code generation pipeline works correctly:
1. Schemas can be downloaded
2. Types can be generated from schemas
3. Generated code is valid Python
4. Generated types can be imported
"""

from __future__ import annotations


def test_generated_types_can_import():
    """Test that generated types module can be imported."""
    from adcp.types import _generated as generated

    # Should have a reasonable number of exported symbols
    symbols = dir(generated)
    assert len(symbols) > 100, f"Expected >100 symbols, got {len(symbols)}"

    # Check for key types that should always exist
    assert hasattr(generated, "Product")
    assert hasattr(generated, "Format")
    assert hasattr(generated, "MediaBuy")
    assert hasattr(generated, "Property")


def test_generated_poc_types_can_import():
    """Test that generated_poc types can be imported."""
    from adcp.types import _generated as generated_poc

    # The generated_poc package should exist
    assert generated_poc is not None


def test_product_type_structure():
    """Test that Product type has expected structure."""
    from adcp import Product

    # Product should be a Pydantic model
    assert hasattr(Product, "model_validate")
    assert hasattr(Product, "model_dump")

    # Check for key fields
    model_fields = Product.model_fields
    assert "product_id" in model_fields
    assert "name" in model_fields
    assert "description" in model_fields
    assert "publisher_properties" in model_fields


def test_format_type_structure():
    """Test that Format type has expected structure."""
    from adcp import Format

    # Format should be a Pydantic model
    assert hasattr(Format, "model_validate")
    assert hasattr(Format, "model_dump")

    # Check for key fields
    model_fields = Format.model_fields
    assert "format_id" in model_fields
    assert "name" in model_fields
    assert "description" in model_fields


def test_no_request_response_rootmodels():
    """Guard: Request/Response types must NOT be RootModel classes.

    Pydantic 2 forbids model_config overrides on RootModel subclasses,
    which blocks consumers who subclass library types with extra='forbid'
    or custom fields. All Request/Response union types should be unwrapped
    to plain Union type aliases in post_generate_fixes.py.

    If this test fails after a schema update, add the new type to
    _UNWRAP_TO_UNION in scripts/post_generate_fixes.py.

    See: https://github.com/adcontextprotocol/adcp-client-python/issues/155
    """
    import types as builtin_types

    from pydantic import RootModel

    from adcp.types import _generated as gen

    # Scan all exported Request/Response types
    rootmodel_violations = []
    for name in dir(gen):
        if not (name.endswith("Request") or name.endswith("Response")):
            continue
        obj = getattr(gen, name)
        # Skip Union type aliases (these are the correctly unwrapped ones)
        if isinstance(obj, builtin_types.UnionType):
            continue
        # Skip non-classes
        if not isinstance(obj, type):
            continue
        # Flag RootModel subclasses wrapping unions (the problematic pattern)
        if issubclass(obj, RootModel):
            rootmodel_violations.append(name)

    assert rootmodel_violations == [], (
        f"These Request/Response types are RootModel classes, which blocks "
        f"consumer subclassing. Add them to _UNWRAP_TO_UNION in "
        f"scripts/post_generate_fixes.py: {rootmodel_violations}"
    )
