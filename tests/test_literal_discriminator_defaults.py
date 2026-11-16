"""Tests for the single-value ``Literal`` discriminators on the asset
documents, and for the fact that they are REQUIRED.

Upstream's generator turned every ``const`` into a pydantic default, so
``TextContent(content='x')`` constructed there without the tag. We do not
add those defaults back. Two documents say why:

* `docs/reading-a-document.md` §3 — **a discriminator's tag is extracted
  BEFORE defaults apply**, so a default cannot rescue an absent
  discriminator under a field-name discriminator at all; the measurement
  there is 277 discriminator positions, all 277 required.
* `docs/migration-from-upstream.md` "Worked example 2" — a class that
  supplies a required ``const`` for you admits a payload the document
  refuses, and the branch classes exist precisely so that they do not.

So these tests pin the documents' own ``required``: the tag is written
out, its value is the one the class's name already tells you, and the
``Literal`` refuses any other.
"""

from __future__ import annotations

import pytest


class TestAssetContentDiscriminatorsAreRequired:
    """``core/assets/{text,html,css,javascript,url}-asset.json`` each name
    ``asset_type`` in their own ``required`` and pin it with ``const``.
    Required-and-pinned: the caller states it, and may state nothing else."""

    def test_text_content_requires_and_pins_asset_type(self) -> None:
        from pydantic import ValidationError

        from adcp.types import TextContent

        t = TextContent(asset_type="text", content="hello")
        assert t.asset_type == "text"
        assert t.content == "hello"

        # core/assets/text-asset.json required: ['asset_type', 'content']
        with pytest.raises(ValidationError):
            TextContent(content="hello")  # type: ignore[call-arg]

    def test_html_content_requires_and_pins_asset_type(self) -> None:
        from adcp.types import HtmlContent

        h = HtmlContent(asset_type="html", content="<p>x</p>")
        assert h.asset_type == "html"

    def test_css_content_requires_and_pins_asset_type(self) -> None:
        from adcp.types import CssContent

        c = CssContent(asset_type="css", content="body{}")
        assert c.asset_type == "css"

    def test_javascript_content_requires_and_pins_asset_type(self) -> None:
        from adcp.types import JavascriptContent

        j = JavascriptContent(asset_type="javascript", content="alert(1)")
        assert j.asset_type == "javascript"

    def test_url_content_requires_and_pins_asset_type(self) -> None:
        from adcp.types import UrlContent

        u = UrlContent(asset_type="url", url="https://example.com/asset.jpg")
        assert u.asset_type == "url"


class TestVastDaastDiscriminators:
    """VAST/DAAST have two discriminators, and their requiredness is a
    CONJUNCTION: ``core/assets/vast-asset.json`` states
    ``required: ['asset_type']`` at its root and
    ``required: ['delivery_type', 'url']`` at ``#/oneOf/0``, each with a
    ``const`` and no ``default`` anywhere.

    Upstream named the two arms ``UrlVastAsset``/``InlineVastAsset``; those
    names have no schema subject here (``adcp.types.aliases.__adcp_refused__``
    serves them as an ``AttributeError`` saying so). The branch classes are
    ``VASTAssetUrl``/``VASTAssetInline`` on ``adcp.types.core``.
    """

    def test_url_vast_asset_states_both_discriminators(self) -> None:
        from adcp.types.core import VASTAsset, VASTAssetUrl

        a = VASTAssetUrl(
            asset_type="vast",
            delivery_type="url",
            url="https://vast.example.com/ad.xml",
        )
        assert a.asset_type == "vast"
        assert a.delivery_type == "url"
        assert isinstance(a, VASTAsset)

    def test_inline_vast_asset_states_both_discriminators(self) -> None:
        from adcp.types.core import VASTAsset, VASTAssetInline

        a = VASTAssetInline(asset_type="vast", delivery_type="inline", content="<VAST>...</VAST>")
        assert a.asset_type == "vast"
        assert a.delivery_type == "inline"
        assert isinstance(a, VASTAsset)

    def test_url_daast_asset_states_both_discriminators(self) -> None:
        from adcp.types.core import DAASTAsset, DAASTAssetUrl

        a = DAASTAssetUrl(
            asset_type="daast",
            delivery_type="url",
            url="https://daast.example.com/ad.xml",
        )
        assert a.asset_type == "daast"
        assert a.delivery_type == "url"
        assert isinstance(a, DAASTAsset)

    def test_vast_branch_omitting_a_discriminator_is_refused(self) -> None:
        """Both ``const`` discriminators are required, and that is the
        document rather than us."""
        from pydantic import ValidationError

        from adcp.types.core import VASTAssetUrl

        with pytest.raises(ValidationError) as excinfo:
            VASTAssetUrl(url="https://vast.example.com/ad.xml")  # type: ignore[call-arg]

        missing = {
            error["loc"][0] for error in excinfo.value.errors() if error["type"] == "missing"
        }
        assert missing == {"asset_type", "delivery_type"}

    def test_the_union_parses_either_arm_from_the_payload(self) -> None:
        """A consumer does not pick the branch — the payload does."""
        from adcp.types.core import VASTAsset, VASTAssetInline, VASTAssetUrl

        parsed_url = VASTAsset.model_validate(
            {
                "asset_type": "vast",
                "delivery_type": "url",
                "url": "https://vast.example.com/ad.xml",
            }
        )
        assert isinstance(parsed_url, VASTAssetUrl)

        parsed_inline = VASTAsset.model_validate(
            {"asset_type": "vast", "delivery_type": "inline", "content": "<VAST/>"}
        )
        assert isinstance(parsed_inline, VASTAssetInline)


class TestUpstreamsArmNamesHaveNoSubject:
    """Reading 10: a name with no schema subject gets a migration note and
    never a class. The four VAST/DAAST arm names are upstream's names for
    ONE BRANCH of a document whose root we emit, and the refusal carries
    the reason."""

    @pytest.mark.parametrize(
        "name",
        ["UrlVastAsset", "InlineVastAsset", "UrlDaastAsset", "InlineDaastAsset"],
    )
    def test_arm_name_is_refused_with_its_reason(self, name: str) -> None:
        import adcp.types.aliases as aliases

        with pytest.raises(AttributeError, match="no subject in the pinned bundle"):
            getattr(aliases, name)


class TestPinsPreserveValidation:
    """A ``const`` states exactly one value, so the ``Literal`` refuses any
    OTHER value passed explicitly."""

    def test_wrong_explicit_asset_type_rejected(self) -> None:
        from pydantic import ValidationError

        from adcp.types import TextContent

        with pytest.raises(ValidationError):
            TextContent(asset_type="html", content="x")  # type: ignore[arg-type]

    def test_wrong_explicit_delivery_type_rejected(self) -> None:
        from pydantic import ValidationError

        from adcp.types.core import VASTAssetUrl

        with pytest.raises(ValidationError):
            VASTAssetUrl(
                asset_type="vast",
                delivery_type="inline",  # type: ignore[arg-type]
                url="https://vast.example.com/ad.xml",
            )


class TestWireFormat:
    """Validating a dict (wire format) answers with the document's
    ``required`` in both directions."""

    def test_text_content_from_wire_dict(self) -> None:
        from adcp.types import TextContent

        t = TextContent.model_validate({"asset_type": "text", "content": "hi"})
        assert t.asset_type == "text"
        assert t.content == "hi"

    def test_text_content_from_wire_dict_without_asset_type_is_refused(self) -> None:
        """A payload omitting a required property is refused with the
        document's own ``required`` keyword — no default rescues it."""
        from pydantic import ValidationError

        from adcp.types import TextContent

        with pytest.raises(ValidationError) as excinfo:
            TextContent.model_validate({"content": "hi"})

        assert [error["loc"] for error in excinfo.value.errors() if error["type"] == "missing"] == [
            ("asset_type",)
        ]

    def test_the_dump_carries_the_tag_back_out(self) -> None:
        from adcp.types.core import DAASTAssetUrl

        asset = DAASTAssetUrl(
            asset_type="daast",
            delivery_type="url",
            url="https://daast.example.com/ad.xml",
        )
        assert asset.model_dump(exclude_none=True) == {
            "asset_type": "daast",
            "delivery_type": "url",
            "url": "https://daast.example.com/ad.xml",
        }
