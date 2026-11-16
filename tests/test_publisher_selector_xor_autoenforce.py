"""Auto-enforcement of the PublisherPropertySelector XOR constraint at Pydantic parse time.

Closes adcp-client-python#759. The patch in ``adcp.types.aliases`` uses
``pydantic._internal._decorators`` (private API but stable across
Pydantic 2.x point releases) to attach a ``model_validator(mode='after')``
to the generated selector classes. The first three tests verify the
behavior; the last test is a **drift sentinel** that fails loudly if
Pydantic's internal decorator registration ever changes shape so the
issue surfaces in CI rather than as silent validation regressions.

Upstream 3.0.10+ dropped the ``publisher_domains[]`` compact form from
``core/publisher-property-selector.json`` (see issue #771). The generated
Pydantic models no longer carry the field, so the four ``compact_form``
/ ``bare_construct`` cases here can't exercise the XOR path — the
field-required check on ``publisher_domain`` dominates. The SDK-side
dict-layer enforcement in ``adcp.validation.legacy.validate_publisher_properties_item``
still implements the contract for adopters consuming raw adagents.json
bytes (see ``tests/test_adagents.py::TestPublisherDomainsCompactForm``).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

_COMPACT_FORM_DROPPED = pytest.mark.skip(
    reason=(
        "Upstream 3.0.10+ dropped publisher_domains[] from the generated "
        "selector schema (issue #771). The Pydantic-layer XOR auto-enforce "
        "patch has nothing to fire on; SDK-layer enforcement lives in "
        "adcp.validation.legacy.validate_publisher_properties_item."
    )
)


class TestSelectorXorAutoEnforce:
    """Direct construction of an XOR-violating selector must fail."""

    @_COMPACT_FORM_DROPPED
    def test_selector1_rejects_bare_construct(self):
        # selection_type='all' with neither publisher_domain nor publisher_domains
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector1,
        )

        with pytest.raises(ValidationError, match="exactly one"):
            PublisherPropertySelector1(selection_type="all")

    def test_selector1_rejects_both_publisher_fields(self):
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector1,
        )

        # The reason is the DOCUMENT's keyword, not a sentence this SDK wrote.
        # ``not`` is what refuses the pair, and the message names both
        # properties: "'publisher_domain', 'publisher_domains' are present
        # together, which the document forbids". "mutually exclusive" was the
        # aliases patch's own prose and no document contains it.
        with pytest.raises(ValidationError) as raised:
            PublisherPropertySelector1(
                selection_type="all",
                publisher_domain="cnn.com",
                publisher_domains=["espn.com"],
            )
        (error,) = raised.value.errors()
        assert error["type"] == "not"
        assert "publisher_domain" in error["msg"] and "publisher_domains" in error["msg"]

    def test_selector1_accepts_singular_form(self):
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector1,
        )

        s = PublisherPropertySelector1(selection_type="all", publisher_domain="cnn.com")
        assert s.publisher_domain == "cnn.com"

    @_COMPACT_FORM_DROPPED
    def test_selector1_accepts_compact_form(self):
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector1,
        )

        s = PublisherPropertySelector1(
            selection_type="all", publisher_domains=["a.example", "b.example"]
        )
        assert s.publisher_domains is not None
        assert [str(d.root) for d in s.publisher_domains] == ["a.example", "b.example"]

    @_COMPACT_FORM_DROPPED
    def test_selector3_rejects_bare_construct(self):
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector3,
        )

        with pytest.raises(ValidationError, match="exactly one"):
            PublisherPropertySelector3(selection_type="by_tag", property_tags=["ctv"])

    @_COMPACT_FORM_DROPPED
    def test_selector3_accepts_compact_form_with_required_tags(self):
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector3,
        )

        s = PublisherPropertySelector3(
            selection_type="by_tag",
            property_tags=["ctv"],
            publisher_domains=["a.example", "b.example"],
        )
        assert s.publisher_domains is not None
        assert [str(d.root) for d in s.publisher_domains] == ["a.example", "b.example"]

    def test_selector2_unpatched_passes_valid_input(self):
        # by_id selector has no XOR — only publisher_domain is allowed,
        # publisher_domains is rejected at the JSON-schema level. The
        # auto-enforce patch correctly leaves this class alone.
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector2,
        )

        s = PublisherPropertySelector2(
            selection_type="by_id",
            property_ids=["p1"],
            publisher_domain="cnn.com",
        )
        assert s.publisher_domain == "cnn.com"


class TestPydanticInternalApiDriftSentinel:
    """If Pydantic ever changes the shape of ``_internal._decorators``
    the patch in ``adcp.types.aliases`` silently no-ops and selector
    validation regresses. This test imports the same private surface
    the patch uses and verifies the API still exists. CI failure here
    is the canary for "rework the patch or pin Pydantic".
    """

    def test_decorator_class_present(self):
        from pydantic._internal._decorators import Decorator  # noqa: F401

    def test_model_validator_decorator_info_present(self):
        from pydantic._internal._decorators import (  # noqa: F401
            ModelValidatorDecoratorInfo,
        )

    def test_selector1_has_registered_validator(self):
        # The rule lands at class-build time. If the registration shape
        # changes and it silently no-ops, this catches it.
        #
        # The validator is the EMITTER's, not the aliases patch's.
        # ``core/publisher-property-selector.json`` states the XOR itself —
        # a ``not`` over the pair and an ``anyOf`` over the two singleton
        # required groups — and §2 lowers both to ``_adcp_rules``, which
        # ``RuleBound._enforce_adcp_rules`` reads. ``_selector_xor_validate``
        # was the hand-written patch that stood in before the document's own
        # keyword compiled, and nothing re-attaches it.
        from adcp.types.domains.core.publisher_property_selector import (
            PublisherPropertySelector1,
        )

        from adcp.types._runtime import ForbiddenGroups

        validators = PublisherPropertySelector1.__pydantic_decorators__.model_validators
        assert "_enforce_adcp_rules" in validators, (
            "rule validator missing from PublisherPropertySelector1 — the "
            "emitted _adcp_rules are not being enforced."
        )
        forbidden = [
            rule
            for rule in PublisherPropertySelector1._adcp_rules
            if isinstance(rule, ForbiddenGroups)
        ]
        assert [rule.groups for rule in forbidden] == [
            (("publisher_domain", "publisher_domains"),)
        ]
