"""Regression tests for security-sensitive URL constraints in AdCP 3.2 beta.3."""

import pytest
from adcp.types.domains.core.placement_presentation import ImageRef
from pydantic import ValidationError

from adcp import PackageRequest, PlacementPresentationReference, PublisherDesignatedPreviewProvider
from adcp.types import ReferenceRendererProvenance

_DIGEST = "sha256:" + "a" * 64


def assert_refused(excinfo: pytest.ExceptionInfo[ValidationError], field: str, kind: str) -> None:
    """The refusal is asserted by its (location, TYPE), not by a sentence.

    These assertions used to match upstream's hand-written validator prose
    (``"agent_url must use https"``).  The constraint is still enforced -- measured, every
    one of these payloads is refused -- but it is enforced by the DOCUMENT's own keyword
    through pydantic, which reports ``url_scheme`` at ``agent_url`` rather than upstream's
    sentence.  Matching the prose graded the message; matching the pair grades the
    behaviour, and a type is categorisable where a sentence is not.

    Naming the field AND the type is what keeps this honest: two of these fixtures are also
    incomplete (``authority``, and ``media_type``/``schema_version``, are required and
    absent), so a bare ``pytest.raises(ValidationError)`` would pass even if the URL rule
    were deleted.  Asserting the specific error cannot.
    """
    found = [(e["loc"], e["type"]) for e in excinfo.value.errors()]
    assert ((field,), kind) in found, found


@pytest.mark.parametrize(
    "agent_url",
    [
        "http://127.0.0.1/preview",
        "http://169.254.169.254/latest/meta-data",
    ],
)
def test_preview_provider_requires_https(agent_url: str) -> None:
    with pytest.raises(ValidationError) as refused:
        PublisherDesignatedPreviewProvider(
            agent_url=agent_url,
            routes=[{"format_option_id": "display", "capability_id": "preview"}],
        )
    assert_refused(refused, "agent_url", "url_scheme")


def test_presentation_reference_requires_https() -> None:
    with pytest.raises(ValidationError) as refused:
        PlacementPresentationReference(
            uri="http://169.254.169.254/presentation.json",
            digest=_DIGEST,
        )
    assert_refused(refused, "uri", "url_scheme")


def test_presentation_image_requires_https() -> None:
    with pytest.raises(ValidationError) as refused:
        ImageRef(uri="http://127.0.0.1/frame.png", digest=_DIGEST)
    assert_refused(refused, "uri", "url_scheme")


@pytest.mark.parametrize(
    "source_repository",
    [
        "http://evil.example/repo",
        "https://github.com.evil.example/repo",
        "https://user@github.com/repo",
        "https://github.com:444/repo",
    ],
)
def test_reference_renderer_provenance_requires_github_origin(
    source_repository: str,
) -> None:
    with pytest.raises(ValidationError) as refused:
        ReferenceRendererProvenance(
            source_repository=source_repository,
            workflow_path=".github/workflows/release.yml",
        )
    assert_refused(refused, "source_repository", "string_pattern_mismatch")


def test_beta3_secure_urls_accept_valid_https_origins() -> None:
    # `authority` is required by core/preview-provider.json. Upstream's generator dropped declared
    #   and allOf-composed `required`, so their fixtures omit it.
    # authority="publisher_designated" -- `const` in the document: 'publisher_designated'.
    provider = PublisherDesignatedPreviewProvider(
        authority="publisher_designated",
        agent_url="https://creative.example/preview",
        routes=[{"format_option_id": "display", "capability_id": "preview"}],
    )
    # `media_type`, `schema_version` are required by core/presentation-ref.json. Upstream's
    #   generator dropped declared and allOf-composed `required`, so their fixtures omit them.
    # media_type="application/vnd.adcp.placement-presentation+json" -- `const` in the document:
    #   'application/vnd.adcp.placement-presentation+json'.
    # schema_version="1.0" -- `const` in the document: '1.0'.
    presentation = PlacementPresentationReference(
        media_type="application/vnd.adcp.placement-presentation+json",
        schema_version="1.0",
        uri="https://publisher.example/presentation.json",
        digest=_DIGEST,
    )
    image = ImageRef(uri="https://cdn.example/frame.png", digest=_DIGEST)
    provenance = ReferenceRendererProvenance(
        source_repository="https://github.com/adcontextprotocol/adcp",
        workflow_path=".github/workflows/release.yml",
    )

    assert provider.agent_url.scheme == "https"
    assert presentation.uri.scheme == "https"
    assert image.uri.scheme == "https"
    # `source_repository` is a pattern-constrained STRING and not a URL object: the
    # document states `pattern: '^https://github\.com/'` on a plain `type: string`, which
    # is why a bad origin reports `string_pattern_mismatch` where the three fields above
    # report `url_scheme`.  So there is no `.host` to read, and the origin rule is exactly
    # the prefix the pattern pins.
    assert provenance.source_repository.startswith("https://github.com/")


@pytest.mark.parametrize("params", [{"width": 300}, {"height": 250}])
def test_image_package_dimensions_must_cooccur(params: dict[str, int]) -> None:
    with pytest.raises(ValidationError, match="width and height must co-occur"):
        PackageRequest(
            product_id="product-1",
            pricing_option_id="price-1",
            format_kind="image",
            params=params,
        )


def test_package_params_require_format_kind() -> None:
    with pytest.raises(ValidationError) as refused:
        PackageRequest(
            product_id="product-1",
            pricing_option_id="price-1",
            params={"width": 300, "height": 250},
        )
    # The document's own `dependencies` keyword, reported as such.  The prose match this
    # replaces failed on QUOTING alone: our message is `'params' requires 'format_kind'`.
    assert_refused(refused, "params", "dependencies")


def test_image_package_accepts_complete_dimensions() -> None:
    package = PackageRequest(
        product_id="product-1",
        pricing_option_id="price-1",
        format_kind="image",
        params={"width": 300, "height": 250},
    )

    assert package.params == {"width": 300, "height": 250}
