"""What became of the RootModel ``__getattr__`` proxy.

Issue #145 asked that a union element not oblige a caller to write ``.root``,
and the answer then was a proxy on the wrapper. Section 4 removes the wrapper
instead: a union is a base plus one child per branch, so an element IS the
branch and the question the proxy answered no longer arises. These tests pin
that -- attribute access reaches the fields directly, ``root`` is absent, and
``isinstance`` holds against the union base.

See: https://github.com/adcontextprotocol/adcp-client-python/issues/145
"""

from __future__ import annotations

import pytest

from adcp.types import (
    DeliveryMeasurement,
    DeliveryType,
    Format,
    Product,
    ReportingCapabilities,
)
from adcp.types.domains.core.pricing_option import (
    PricingOptionCpm,
    PricingOptionFlatRate,
)


@pytest.fixture
def product_with_pricing() -> Product:
    """Create a Product with pricing options for testing.

    ``Product.pricing_options`` states ``core/pricing_option.json``, so its
    elements are THAT union's branches. The flat ``CpmPricingOption`` /
    ``FlatRatePricingOption`` name a different subject -- the standalone
    ``pricing-options/cpm-option.json`` document -- and a value built from one
    of those is not a value this field admits.
    """
    return Product(
        product_id="test",
        name="Test Product",
        description="A test product",
        publisher_properties=[{"publisher_domain": "example.com", "selection_type": "all"}],
        format_options=[Format(format_kind="image", params={"width": 300, "height": 250})],
        delivery_type=DeliveryType.guaranteed,
        delivery_measurement=DeliveryMeasurement(provider="Test"),
        reporting_capabilities=ReportingCapabilities(
            available_metrics=[],
            available_reporting_frequencies=["daily"],
            date_range_support="date_range",
            expected_delay_minutes=60,
            supports_webhooks=False,
            timezone="UTC",
        ),
        pricing_options=[
            PricingOptionFlatRate(
                pricing_option_id="flat_1",
                pricing_model="flat_rate",
                fixed_price=100.0,
                currency="USD",
            ),
            PricingOptionCpm(
                pricing_option_id="cpm_1",
                pricing_model="cpm",
                floor_price=2.50,
                currency="USD",
            ),
        ],
    )


def test_pricing_option_attribute_access(product_with_pricing: Product):
    """PricingOption RootModel proxies attribute access to the inner type."""
    po = product_with_pricing.pricing_options[0]

    assert po.pricing_option_id == "flat_1"
    assert po.pricing_model == "flat_rate"
    assert po.fixed_price == 100.0
    assert po.currency == "USD"


def test_cpm_variant_attribute_access(product_with_pricing: Product):
    """CPM variant attributes are accessible through the proxy."""
    po = product_with_pricing.pricing_options[1]

    assert po.pricing_model == "cpm"
    assert po.floor_price == 2.50
    assert po.pricing_option_id == "cpm_1"


def test_pricing_option_is_the_branch_itself(product_with_pricing: Product):
    """A union root publishes its branches, so an element has no wrapper to unwrap."""
    po = product_with_pricing.pricing_options[0]

    assert type(po) is PricingOptionFlatRate
    assert not hasattr(po, "root")


def test_pricing_option_iteration(product_with_pricing: Product):
    """Can iterate pricing options and access attributes directly."""
    models = [po.pricing_model for po in product_with_pricing.pricing_options]
    assert models == ["flat_rate", "cpm"]


def test_pricing_option_missing_attribute_raises(product_with_pricing: Product):
    """Accessing a non-existent attribute still raises AttributeError."""
    po = product_with_pricing.pricing_options[0]

    with pytest.raises(AttributeError):
        po.nonexistent_field


def test_pricing_option_private_attribute_raises(product_with_pricing: Product):
    """Private/dunder attributes are not proxied to root."""
    po = product_with_pricing.pricing_options[0]

    with pytest.raises(AttributeError):
        po._nonexistent


def test_pricing_option_serialization_roundtrip(product_with_pricing: Product):
    """Serialization and validation are unaffected by the __getattr__ proxy."""
    po = product_with_pricing.pricing_options[0]

    dumped = po.model_dump(mode="json")
    assert dumped["pricing_option_id"] == "flat_1"
    assert dumped["pricing_model"] == "flat_rate"

    # Round-trip through validation
    restored = type(po).model_validate(dumped)
    assert restored.pricing_option_id == "flat_1"
    assert restored.pricing_model == "flat_rate"


def test_a_union_another_union_discriminates_against_keeps_no_wrapper_either():
    """The last wrapper is gone too, so there is no proxy left to need.

    ``AssetVariant`` discriminates on ``asset_type`` and the VAST branch was the
    case that used to keep a ``RootModel`` around its target. Section 4 emits a
    union as a base plus one child per branch, so the branch IS the model: there
    is no ``root`` to unwrap, attribute access needs no ``__getattr__``, and
    ``isinstance`` holds against the union base.
    """
    from adcp.types.domains.core.assets.asset_union import AssetVariant, AssetVariantVast

    branch = AssetVariantVast(
        asset_type="vast", delivery_type="url", asset_id="a-1", url="https://cdn.test/v.xml"
    )

    assert isinstance(branch, AssetVariant)
    assert not hasattr(branch, "root")
    assert branch.asset_type == "vast"
    assert branch.delivery_type == "url"
    assert branch.asset_id == "a-1"

    # And the base dispatches a payload to that branch, which is the fact the
    # wrapper used to stand in for.
    dispatched = AssetVariant.model_validate(
        {
            "asset_type": "vast",
            "delivery_type": "url",
            "asset_id": "a-1",
            "url": "https://cdn.test/v.xml",
        }
    )
    assert isinstance(dispatched, AssetVariantVast)
