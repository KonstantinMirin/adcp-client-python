"""**A BARE ``format: uri`` PINS NO SCHEME, SO THE TYPE MUST NOT PIN ONE EITHER.**

``adcp-client-python-dza0``, the owner's ruling of 2026-11-11: the general URL form is a
HIERARCHICAL url -- ``Annotated[AnyUrl, UrlConstraints(host_required=True)]`` -- and not
``HttpUrl``, which refused values the documents admit, and not bare ``AnyUrl``, which
admits ``data:`` and ``tel:`` at a webhook field and leaves ``.host`` possibly ``None``.
**Both edges are gated here**, because a clause that only widened would pass on bare
``AnyUrl`` too.

**THE TYPE IS A FUNCTION OF THE KEYWORD AND NOT OF A DOCUMENT.**  Every bare
``format: uri`` node takes the same annotation, derived from ``format: uri`` alone.
``deep_link_url`` is named below because it is what PROVED the http narrowing unsafe --
not because anything is keyed on it, and nothing in the compiler or in this file reads a
description to decide a type.

**THE CASE THE BUNDLE SUPPLIES ITSELF, and it is named here for that reason.**
``core/app-item.json#/properties/deep_link_url`` is ``{"type": "string", "format":
"uri"}`` and its own description says:

    *"Deep link URI for re-engagement campaigns targeting existing users.  Use Universal
    Links (iOS) or App Links (Android) where available (e.g.,
    https://acmegames.com/app/level/5).  **Falls back to URI scheme (e.g.,
    'acmegames://level/5')** when universal links are not configured."*

``HttpUrl`` refuses ``acmegames://level/5``.  So the SDK refused a payload the document
admits, at the field whose own prose supplies it -- a class narrower than its document,
which is the one direction ``docs/plan/final-state.md`` reading 2 forbids outright, and it
was live at **335 field positions over 121 modules**.  :func:`test_the_named_case` is that
value, by name, and is the clause a future reader needs to see rather than a derived
census: a figure moves with the bundle and this one sentence of this one document is why
the ruling exists.

**STATED WITH ``jsonschema`` FIRST AND THE CLASS ASKED TO AGREE**, which is
``tests_emit/test_a_property_that_admits_nothing.py``'s discipline: the claim "the
document admits this" is a fact about the DOCUMENT, so the document's own validator says
it and the class is then required to agree.  A test that asserted only the class would be
asserting this file's opinion about RFC 3986.

**AND THE POPULATION IS DERIVED, over every portable document, with no list.**  Every
``format: uri`` node that states no ``pattern`` -- the patterned ones are
``adcp-client-python-6eez``'s and take ``AdCPUrl``, whose ``allowed_schemes`` is the
document's own pinned scheme.  Measured: **227 bare nodes in 127 documents**.
"""

from __future__ import annotations

import json

import fresh
import jsonschema
import pytest
from nodeset import claimed
from pydantic import TypeAdapter, ValidationError

from adcp.types.constraints import AdCPUrl, HostedUrl, HttpUrl
from codegen import bundle

#: One spelling of the bundle, re-exported from ``tests_emit/fresh.py``: a file that spells
#: its own path can come to range over a different bundle from the tree it reads.
BUNDLE = fresh.BUNDLE

#: The document and pointer the ruling is ABOUT, and the value its own description states.
#: Written out because this is the WITNESS and not a sample: the figure beside it moves with
#: the bundle, and this sentence of this document is the reason the general form changed.
THE_NAMED_CASE = ("core/app-item.json", "/properties/deep_link_url")
THE_NAMED_VALUE = "acmegames://level/5"

#: Values RFC 3986 admits whose scheme is not http or https, one per shape of the grammar
#: that a URL type can get wrong: a URN with no authority, a mailto with no slashes, a file
#: with an empty authority, a scheme with no authority at all, an opaque data payload, and
#: the bundle's own custom app scheme.  Offered to the DOCUMENT first at every node, so a
#: value this list has wrong shows up as the document refusing it rather than as a verdict
#: about the class.
HIERARCHICAL_NON_HTTP = (
    "ui://si/session-abc123",
    THE_NAMED_VALUE,
)

#: A value RFC 3986 admits and the general form REFUSES, because it names no host.  The
#: narrowing is deliberate and its sites are zero: of the 227 bare nodes, none states prose
#: naming a non-hierarchical scheme.  Asserted so that the widening clause above cannot be
#: read as "a bare uri admits everything" -- the type is a hierarchical url, not AnyUrl.
NOT_HIERARCHICAL = "data:text/plain,hi"


def _bare_uri_nodes() -> dict[tuple[str, str], dict]:
    """Every ``format: uri`` node of the portable population that states no ``pattern``.

    Off the bundle and keyed by ``(document, pointer)``, so the population is the
    predicate's and not a list this file maintains.  A node stating a ``pattern`` is
    ``adcp-client-python-6eez``'s: there the document pins the scheme and ``AdCPUrl``
    states it, which :func:`test_a_pinned_scheme_keeps_the_https_type` holds the line on.
    """
    out: dict[tuple[str, str], dict] = {}
    for document in sorted(bundle.portable(BUNDLE)):
        doc = bundle.read(BUNDLE, document)
        for pointer, node in bundle.nodes(doc):
            if isinstance(node, dict) and node.get("format") == "uri" and "pattern" not in node:
                out[(document, pointer)] = node
    return out


def test_the_bundle_states_bare_uri_nodes() -> None:
    """The population, asserted before anything is asserted over it.

    ``final-state.md``: a reading over an empty set passes every clause below while saying
    nothing, and the predicate here is two keyword tests over a node walk -- exactly the
    shape that silently empties when a keyword is renamed.
    """
    nodes = claimed("bare format: uri nodes of the portable population", _bare_uri_nodes())
    assert len({d for d, _ in nodes}) > 1, sorted({d for d, _ in nodes})


def test_the_named_case() -> None:
    """``core/app-item.json``'s ``deep_link_url`` admits ``acmegames://level/5``.

    The document says so in its own description, ``jsonschema`` says so about its own
    node, and the type the emitter selects for it must say so too.  ``HttpUrl`` and
    ``AdCPUrl`` are asserted to REFUSE it in the same breath -- not to grade pydantic, but
    because the ruling is a CHOICE BETWEEN THEM and a clause that did not show the
    rejected arm failing would pass just as well if the choice were reverted.
    """
    document, pointer = THE_NAMED_CASE
    node = bundle.node_at(bundle.read(BUNDLE, document), pointer)
    assert node.get("format") == "uri" and "pattern" not in node, node
    assert "acmegames://level/5" in json.dumps(node), (
        "the description that supplies this value is the reason this clause is by name; "
        "if the document stopped stating it, this clause is what should be revisited"
    )

    # (1) THE DOCUMENT, through its own validator.
    jsonschema.Draft7Validator(node).validate(THE_NAMED_VALUE)

    # (2) THE TYPE THE EMITTER SELECTS, which must agree.
    got = TypeAdapter(HostedUrl).validate_python(THE_NAMED_VALUE)
    assert not isinstance(got, str), type(got)
    assert got.scheme == "acmegames", got

    # (3) THE ARM THAT WAS REJECTED, failing -- which is what makes (2) a choice.
    for refusing in (HttpUrl, AdCPUrl):
        with pytest.raises(ValidationError):
            TypeAdapter(refusing).validate_python(THE_NAMED_VALUE)

    # (4) THE OTHER EDGE, at this same node: the document admits a schemeless-host value
    # and the general form REFUSES it, because it is a HIERARCHICAL url and not AnyUrl.
    jsonschema.Draft7Validator(node).validate(NOT_HIERARCHICAL)
    with pytest.raises(ValidationError):
        TypeAdapter(HostedUrl).validate_python(NOT_HIERARCHICAL)


def test_every_bare_uri_node_admits_every_non_http_scheme_its_document_admits() -> None:
    """The obligation, over all 227 nodes and both edges.

    **The DOCUMENT is the gate on which pairs count.**  A value this file offers that the
    node refuses is skipped -- it is a statement about the value, not about the class --
    and the pairs that survive are the ones where the document has said "I admit this".
    Those the class must admit, and a failure names the pointer and the value.

    The type is read off the EMITTER (``constraints.url_type``) rather than written here,
    so a run that changed the selection reddens instead of being graded against the answer
    this file expects.
    """
    from codegen import constraints as constraints_module

    nodes = _bare_uri_nodes()
    assert nodes, "the population is empty"
    offered = 0
    narrower: dict[str, str] = {}
    for (document, pointer), node in sorted(nodes.items()):
        selected = constraints_module.url_type(node)
        assert selected.endswith(f".{constraints_module.HIERARCHICAL}"), (
            f"{document}{pointer} selects {selected}, and a bare format: uri is RFC 3986"
        )
        for value in HIERARCHICAL_NON_HTTP:
            try:
                jsonschema.Draft7Validator(node).validate(value)
            except jsonschema.ValidationError:
                continue
            offered += 1
            try:
                got = TypeAdapter(HostedUrl).validate_python(value)
            except ValidationError as why:
                narrower[f"{document}{pointer} <- {value}"] = str(why.errors()[0]["msg"])
                continue
            if isinstance(got, str):
                narrower[f"{document}{pointer} <- {value}"] = "constructed a str, not a URL"
    assert not narrower, narrower
    claimed("(node, non-http value) pairs the document admits", range(offered))


def test_a_pinned_scheme_keeps_the_https_type() -> None:
    """The other side of the split, so the ruling cannot be read as "every uri is AnyUrl".

    Where the document PINS ``^https://`` the type states the document's own scheme, and
    ``AdCPUrl`` is that type.  Asserted off the emitter's own selector over the patterned
    nodes, which is ``adcp-client-python-6eez``'s population: this clause holds the line
    that ``dza0`` moved only the GENERAL arm.

    **One node of the bundle pins no such prefix and takes the general arm**, and it is
    named by its pattern rather than by its path: ``core/macro-bearing-url.json`` at
    ``#/anyOf/1`` states ``^https?://…``, which admits ``http://`` -- so ``AdCPUrl`` would
    refuse a value that document admits, and the pattern itself would not catch it.
    """
    from codegen import constraints as constraints_module

    patterned = {}
    for document in sorted(bundle.portable(BUNDLE)):
        doc = bundle.read(BUNDLE, document)
        for pointer, node in bundle.nodes(doc):
            if isinstance(node, dict) and node.get("format") == "uri" and "pattern" in node:
                patterned[(document, pointer)] = node
    claimed("format: uri nodes that also state a pattern", patterned)
    pinned = {
        site: node
        for site, node in patterned.items()
        if str(node["pattern"]).startswith(constraints_module.HTTPS_ONLY)
    }
    assert pinned, "no patterned node pins the https prefix"
    assert len(pinned) < len(patterned), (
        "every patterned node pins the prefix, so the general-arm clause below is vacuous"
    )
    for site, node in sorted(pinned.items()):
        selected = constraints_module.url_type(node)
        assert selected.endswith(f".{constraints_module.URL}"), (site, selected)
    for site in sorted(set(patterned) - set(pinned)):
        selected = constraints_module.url_type(patterned[site])
        assert selected.endswith(f".{constraints_module.HIERARCHICAL}"), (site, selected)
