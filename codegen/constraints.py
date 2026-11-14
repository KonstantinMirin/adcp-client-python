"""D5's third rung: the aliases that belong to no document, and their one module.

``docs/plan/rebuild-plan.md`` D5 says a constrained type is **named once and
referenced**, and gives the resolution order the walk follows for every
constrained scalar it meets:

1. **a type the bundle itself names** -- a titled root carrying those
   constraints, reached ``by $ref as an import``.  That already works and needs
   nothing here: ``compiler.lower_node``'s ``$ref`` arm binds the target's module
   and names its symbol, and nothing of the target's own schema is copied (P2).
   An INLINE declaration is not that case and must not be turned into one.
   Measured over the bundle: 229 titled scalar roots, and rewriting an inline
   site into an import of a content-equal one would invent a reference the
   citing document does not state AND would put the target root's own
   ``description`` into the citing field's rendered schema, which is a fact the
   citing document does not state.  Rung 1 is reached through a ``$ref`` or not
   at all.
2. **a type pydantic names**, and only where it states the document's own facts
   AND accepts the document's own set.  :func:`standard` is that rule, with both
   measurements in its docstring.
3. **otherwise an alias we emit**, named by :func:`symbol` and declared in
   ``adcp.types.constraints``.

**An alias has no document, so it has no domain.**  Every other type this
pipeline emits is reachable through the module of its OWN DOCUMENT, at the
document's path under ``adcp.types._schemas`` (D1 gives the derivation; the
module tree is where it resolves, and D1's public per-domain re-export is a goal
rather than a surface -- ``docs/plan/unimplemented.md`` A-2).  A type derived
from a constraint belongs to no document, so there is no such module for it, and
inventing a domain would be naming it after a concept, which D5 forbids.  One
module holds them all, it is PUBLIC (a consumer annotating application code
imports from it), and it is named for what it holds rather than for
``Annotated``, which is only the mechanism.

**AN ALIAS'S NAME IS THE BUNDLE'S WHERE THE BUNDLE NAMES IT, THE CONSTRAINT IN
WORDS WHERE IT HAS WORDS, AND ITS DECLARING POSITION OTHERWISE** -- §4's three
ordered steps, and there is no fourth.  ``catalogue.collect_scalars`` is the
derivation, because steps 1 and 3 are readings of the BUNDLE and this module is
handed one node at a time; :func:`symbol` is step 2 alone and :func:`resolve`
asks the layer first.

**This replaces a content DIGEST, which §4 rules a defect**: "a minted name says
what the type constrains.  A digest fails that and is a defect, and
insertion-stability is not the test."  The argument the digest rested on is
intact -- a regular expression has no readable name that is not a concept, and
``^[A-Z]{3}$`` is stated at 86 positions for ``currency`` and for
``airport_code`` alike, so naming it ``CurrencyCode`` would be a lie at most of
them.  What was wrong was the conclusion: a constraint the bundle does not name
is **pending a name**, and the position that declares it is what §1 names it by
until upstream does.  :func:`record` still makes two constraints deriving one
symbol a build failure rather than a shared alias.

**EVERY constrained scalar is named, not only a repeating one, and that is a
decision with a measured reason.**  Naming only the shapes that repeat needs a
census over the run's whole population, and a census makes one module's text a
function of which OTHER documents are in the run: the README's one-document
command would then emit ``Annotated[int, Field(ge=1)]`` where the full run emits
``IntMin1``, for the same document and the same bundle.  P7 permits it -- the
document set is an input -- but only the full population is byte-compared, so
the disagreement would be latent.  A name that is a pure function of the
constraint has no such coupling.  Measured on the tree this lands on: 57
distinct constrained-scalar shapes over 278 sites, of which 29 shapes over 250
sites repeat at 2+ and 28 occur once.

**A constrained CONTAINER is here too, and it is GENERIC, which is what makes it
nameable.**  A bound on a list is a bound on the FIELD holding it wherever there IS
a field (``codegen.lower.containers``, and ``ir.TypeRef`` carries no constraints
for a container), so ``Annotated[list[str], Field(min_length=1)]`` is already the
correct form at a PROPERTY: measured on the tree this lands on, 21 such shapes over
30 sites, 2 of them repeating (``list[str]`` at 8 sites and ``list[RightUse]`` at
3), all of them field-bound and none of them reaching this module.

An ELEM, a MAPV and a union BRANCH have no field, and section 5 puts the bound on
the array's own type AT EVERY POSITION -- on a branch emphatically, because the
field holds the other branches and a bound there refuses values the document
accepts.  An earlier revision of this docstring declined to name such a type on the
ground that the symbol would need the ELEMENT type -- ``list[RightUse]`` and
``list[str]`` are different types -- and an element type is a domain word.  That
holds for a NON-generic alias, and it is the premise that changed: a type PARAMETER
is not a domain word, so ``NonEmptyList[T]`` is correct for every ``T`` at once and
the use site supplies the element.  :data:`CONTAINER` is the parameters each
container word is generic over, and :data:`NAMED_CONTAINERS` is the one shape
section 5 spells itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from codegen import compiler, ir
from codegen.refusal import BuildFailure

#: The module an emitted alias is reachable at, and the only path to one: there is
#: no flat root and no second spelling.  PUBLIC, unlike ``adcp.types._schemas``,
#: so an emitted module names it absolutely rather than by the depth-dependent
#: relative spelling ``emit.relative_module`` derives for a sibling (P8's reason
#: for a relative import is that ``_schemas`` is private, and this is not).
MODULE = "adcp.types.constraints"

#: One resolved shape, as this module records and declares it: the document's own type
#: word, its constraint keywords in the document's spelling, and its ``format`` where
#: one is part of the shape.  The ``format`` is a THIRD member rather than a key in the
#: constraints, because an ``ir.TypeRef`` carries it in its own slot -- it becomes
#: ``json_schema_extra`` and not a ``Field`` bound -- and folding it in would make every
#: reader of a shape unfold it again.
Shape = tuple[str, dict[str, Any], str | None]

#: **A ``format: uri`` field's type FOLLOWS THE DOCUMENT'S OWN PATTERN** (D5), so
#: there are two of them and :func:`url_type` chooses.  Both are decisions rather
#: than derivations, so both are declared whatever the run met.
#:
#: ``AdCPUrl`` is ours: ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]``,
#: named for provenance rather than after a standard, because pydantic exports 22
#: URL types and none is https-only -- a name like ``HttpsUrl`` would read as an
#: upstream export a reader cannot find.
#: The STATEMENT it declares is ``render.URL_LINE``: a line of Python is text, and §7
#: puts every one of those behind ``render.py``.
URL = "AdCPUrl"

#: ``HttpUrl`` is pydantic's own, RE-EXPORTED here rather than imported from
#: ``pydantic`` at each site.  The import is the declaration: no assignment, so
#: nothing in this package restates what pydantic defines.  It is here and not
#: left to ``pydantic`` because the SDK's ``uri`` decision is a SPLIT, and a
#: consumer reading a module that declared only ``AdCPUrl`` would read the
#: https-only arm as the whole rule.  One place names both arms.
HTTP_URL = "HttpUrl"

#: **THE GENERAL URL FORM, and it is ``AnyUrl`` because a bare ``format: uri`` is RFC
#: 3986** (``adcp-client-python-dza0``, the owner's ruling of 2026-11-11, and
#: ``docs/plan/rebuild-plan.md`` §4 as corrected at 53efa7cf5).
#:
#: It was :data:`HTTP_URL`, and that was a REFUSAL the SDK made of values its own
#: documents admit.  ``core/app-item.json#/properties/deep_link_url`` is
#: ``{"type": "string", "format": "uri"}`` and its own description supplies the value:
#: *"Falls back to URI scheme (e.g., 'acmegames://level/5') when universal links are not
#: configured."*  Measured on 2.13.5 -- ``HttpUrl`` REFUSES ``acmegames://level/5``,
#: ``AdCPUrl`` refuses it, and ``AnyUrl`` admits it and parses it
#: (``scheme='acmegames'``, ``host='level'``, ``path='/5'``).  Live at **335 field
#: positions over 121 modules** before this, which is the one direction §2 forbids
#: outright: a class narrower than its document.
#:
#: Pydantic's own, RE-EXPORTED like :data:`HTTP_URL` and for the same reason: the import
#: IS the declaration, so nothing here restates what pydantic defines.
#:
#: **§4's "exactly two URL types and there will not be a third" holds with the same
#: count**, because ``AdCPUrl`` is ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=
#: ["https"])]`` -- a DESCENDANT of this one.  The general form and its https-pinned
#: descendant are the two, and only the general form's name moved: from the one that
#: narrows to the one that does not.
ANY_URL = "AnyUrl"

#: **THE GENERAL URL FORM: ``HostedUrl``, which is ``AnyUrl`` with a host required**
#:
#: **THE NAME IS THE CONSTRAINT AND NOT THE PROTOCOL, which is this module's own rule and
#: the reason ``AdCPUri`` was withdrawn** (the owner's correction of 2026-11-11).  Every
#: alias here is "named for the constraint it carries", and the constraint this one
#: carries is the required HOST.  Scheme-freedom needs no name, because it is what
#: ``format: uri`` already means.
#:
#: And ``AdCPUrl`` / ``AdCPUri`` differ by ONE LETTER: a reader cannot tell which is which,
#: and a typo selects the wrong one SILENTLY -- both are a ``UrlConstraints`` refinement of
#: one runtime type, so no checker and no validator downstream catches the swap.
#: (``adcp-client-python-dza0``, the owner's ruling of 2026-11-11 as corrected the same
#: day).  Ours, so the name carries our provenance for :data:`URL`'s own reason -- pydantic
#: exports 22 URL types and none of them is this one, so a name like ``HierarchicalUrl``
#: would read as an upstream export a reader cannot find.
#:
#: **IT IS NEITHER OF THE TWO THINGS TRIED BEFORE IT, and both failed in a measurable
#: direction.**  ``HttpUrl`` REFUSED values the documents admit: ``core/app-item.json``'s
#: ``deep_link_url`` is a bare ``format: uri`` whose own description supplies
#: ``acmegames://level/5``, and that is a class narrower than its document at 335 field
#: positions over 121 modules.  Bare ``AnyUrl`` went too far the other way: it admits
#: ``data:text/plain,hi`` and ``tel:+15551234`` at a webhook-endpoint field, and it leaves
#: ``.host`` possibly ``None``, so an application cannot rely on the parsed object it was
#: given a URL type for.
#:
#: Measured on 2.13.5, both edges:
#:
#: =============================  ========  =============  =======
#: value                          AnyUrl    host_required  HttpUrl
#: =============================  ========  =============  =======
#: ``acmegames://level/5``        admit     admit          REFUSE
#: ``ui://si/session-abc123``     admit     admit          REFUSE
#: ``https://hooks.acme/x``       admit     admit          admit
#: ``data:text/plain,hi``         admit     REFUSE         REFUSE
#: ``tel:``/``urn:``/``mailto:``  admit     REFUSE         REFUSE
#: =============================  ========  =============  =======
#:
#: **AND THE NARROWING IT TAKES HAS ZERO SITES, derived over the bundle**: of the 227 bare
#: ``format: uri`` nodes, 0 state prose naming a non-hierarchical scheme and exactly 1
#: names a non-http hierarchical one.  So ``host_required`` refuses nothing any document
#: states, and it admits the one thing ``HttpUrl`` wrongly refused.
#:
#: **IT IS A FUNCTION OF THE KEYWORD AND NOT AN ALLOWLIST.**  Every bare ``format: uri``
#: node takes this annotation, derived from ``format: uri`` alone.  ``deep_link_url`` is
#: what PROVED the http narrowing unsafe; it is not what the rule is keyed on, and nothing
#: in this compiler reads a description to decide a type.
HIERARCHICAL = "HostedUrl"



#: The one pattern that restricts a ``uri`` node's SCHEME to https and says nothing
#: else, which is the gate D5 states and the one it counts: ``^https://`` at **47
#: of the bundle's 300 ``uri`` positions**.  Compared for EQUALITY and not by
#: prefix, because 47 is the figure the plan states and a prefix test matches 72 --
#: the other 25 are patterns that pin a host, forbid userinfo, or exclude
#: ``localhost`` and IP literals as well, and at those the document already refuses
#: every non-https value, so the type's own scheme rule changes no accepted set at
#: the entry point.  A literal to compare against can be audited; a predicate that
#: tried to decide "does this regex restrict the scheme" could not.
HTTPS_ONLY = "^https://"


def url_type(node: Mapping[str, Any]) -> str:
    """Which URL type a ``format: uri`` node selects, from the DOCUMENT (D5).

    :data:`URL` where the document's own ``pattern`` PINS ``^https://``, because there the
    type and the document agree about the scheme; :data:`HIERARCHICAL` everywhere else,
    because ``format: uri`` is RFC 3986 and a bare ``{"type": "string", "format": "uri"}``
    pins no scheme at all.

    **Both are ``AnyUrl`` with ``UrlConstraints``, which is why §4's "exactly two URL types
    and there will not be a third" holds with the same count**: the general form requires a
    HOST and the other adds the scheme the document pinned, so one is the other's
    descendant.  :data:`HIERARCHICAL` carries why the host is required and why bare
    ``AnyUrl`` was not the answer.

    **THE GENERAL ARM WAS ``HttpUrl`` AND THAT WAS A REFUSAL, NOT A CEILING**
    (``adcp-client-python-dza0``).  What stood here read "``HttpUrl``'s own two ceilings
    are named at D5 and are accepted deliberately: it still refuses ``urn:`` and
    ``file:``, leaving 227 of 300 positions narrower than their document".  Naming a
    refusal does not make it faithful, and the bundle states a refused value in its own
    prose: ``core/app-item.json#/properties/deep_link_url`` says *"Falls back to URI
    scheme (e.g., 'acmegames://level/5')"*, and ``HttpUrl`` refuses exactly that.  **335
    field positions over 121 modules** were narrower than their documents.  ``AnyUrl``
    admits everything RFC 3986 does and is still a parsed URL object, so the owner's
    ruling -- every URL in the schema is a URL type, so an application never converts or
    compares strings -- is kept by the type that does not narrow.

    **AND THE SELECTOR IS THE https PREFIX, not equality with** :data:`HTTPS_ONLY`
    (``adcp-client-python-6eez``).  The equality test was about whether the type EXPRESSES
    the pattern well enough for the keyword to be dropped; the pattern is not dropped any
    more -- it is chained beside the type -- so the question the equality answered is
    gone.  What remains is the SCHEME, and a pattern pinning ``^https://`` as a prefix
    pins the scheme whatever else it pins after it.

    **ONE NODE OF THE BUNDLE PINS NO SUCH PREFIX AND SO TAKES THE GENERAL ARM**, which is
    this function's own rule and not an exception to it: ``core/macro-bearing-url.json``
    at ``#/anyOf/1`` states ``^https?://…``, which ADMITS ``http://``.  :data:`URL` there
    would refuse a value the document admits, and the chained pattern would not catch it
    because the pattern itself permits the scheme.  Measured over the 1,059 portable
    documents: 28 ``uri`` nodes state a pattern, 27 pin the prefix and this one does not.
    """
    pattern = node.get("pattern")
    pins_https = isinstance(pattern, str) and pattern.startswith(HTTPS_ONLY)
    return f"{MODULE}.{URL if pins_https else HIERARCHICAL}"


def narrowed_by_url_type(selected: str) -> dict[str, object]:
    """The bounds the URL type ``selected`` ADDS of its own, which no document states.

    **DERIVED FROM THE TYPE AND NEVER LISTED HERE**, which is what keeps the declaration
    true across a pydantic bump: the answer is read off the type's own published JSON
    schema, so if ``UrlConstraints``' default cap moves, the declaration moves with it.  A
    list would go stale silently and the declaration would then say the wrong number while
    still reading as declared.

    Measured on pydantic 2.13.5: ``AdCPUrl`` publishes ``maxLength: 2083`` and
    ``minLength: 1``; ``HostedUrl`` publishes ``minLength: 1``.  Those are the two facts
    ``codegen/narrowings.py`` records as "the registered part" of the registry it replaced,
    and the cap is the one ``docs/plan/rebuild-plan.md`` §2 accepts in capitals.

    ``format`` is NOT returned.  A URL type does narrow the string it admits -- it refuses
    ``mailto:`` at a bare ``format: uri`` node and normalises the host -- but ``format`` is
    a keyword the DOCUMENT states at these nodes, so a declaration naming it would read as
    a widening's ``fact`` (a document statement the annotation dropped) when it is the
    opposite.  The scheme and the normalisation are decided in §2 by the choice of type and
    belong to that decision, not to a per-node bound.
    """
    import typing

    from pydantic import TypeAdapter
    from pydantic.networks import UrlConstraints

    from adcp.types import constraints as emitted

    name = selected.rsplit(".", 1)[-1]
    chosen = getattr(emitted, name)
    published = TypeAdapter(chosen).json_schema()
    added: dict[str, object] = {
        keyword: published[keyword]
        for keyword in ("maxLength", "minLength")
        if keyword in published
    }
    # **AND THE TWO NARROWINGS THAT DO NOT RENDER, which is why reading the published
    # schema alone was not enough.**  ``UrlConstraints``' ``host_required`` and
    # ``allowed_schemes`` refuse strings the document admits and appear in NO JSON Schema
    # keyword, so a reader comparing our schema to the bundle cannot see them and the
    # first version of this function missed both.
    #
    # Measured: 790 pairs reported ``model_refused_admitted`` on ``url_parsing`` with the
    # witness ``"urn:ietf:rfc:3986"`` -- a valid URI under ``format: uri``, with no host,
    # which ``HostedUrl`` refuses with "empty host".  The refusal is CORRECT and decided:
    # §2's table defines ``HostedUrl`` as ``host_required=True``.  Declared under
    # ``format``, which is the keyword the document states at these nodes and the one
    # ``harness._NARROWED_CAUSES`` maps to ``url_parsing``, ``url_scheme`` and
    # ``url_syntax_violation``.
    for piece in typing.get_args(chosen):
        if not isinstance(piece, UrlConstraints):
            continue
        refuses = {
            key: value
            for key, value in (
                ("host_required", piece.host_required),
                ("allowed_schemes", piece.allowed_schemes),
            )
            if value
        }
        if refuses:
            added["format"] = refuses
    return added


def expressed_by_url_type(node: Mapping[str, Any]) -> frozenset[str]:
    """Which of ``node``'s own constraint keywords the URL type :func:`url_type` picks
    ALREADY STATES.

    **The question a format can only answer per NODE, which is why it is here beside
    :func:`url_type` and not a set beside :data:`URL`.**  ``AdCPUrl`` is
    ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]`` and the one node it is
    chosen at is the node whose own ``pattern`` is :data:`HTTPS_ONLY` -- so there the type
    and the ``pattern`` are the SAME assertion stated once, and the keyword is EXPRESSED
    rather than dropped.  That is :func:`url_type`'s own derivation read from the other
    side: the type is chosen BY the pattern, so the type carries it.

    ``HttpUrl`` expresses no constraint keyword at all.  ``UrlConstraints`` has no slot for
    a regular expression and pydantic refuses to apply a string constraint to a URL type --
    measured on 2.13.5, ``Annotated[HttpUrl, Field(pattern=...)]`` raises ``TypeError:
    Unable to apply constraint 'pattern' to supplied value ... for schema of type
    'function-wrap'``, and the ``pattern`` is absent from that annotation's rendered schema
    as well.  So at every other ``uri`` pattern the type and the pattern are TWO assertions
    and the type can carry only one of them.

    Read by ``codegen.lower.scalars.selects_a_url_type``, the one function that decides
    whether a ``uri`` selects its type here or takes the row's own fallback.

    The comparison is for EQUALITY against :data:`HTTPS_ONLY` for that constant's own
    stated reason: a prefix test would claim ``allowed_schemes`` expresses a pattern that
    also pins a host or forbids userinfo, which it does not.

    **``adcp-client-python-6eez`` CHANGES THIS AND IS NOT LANDED HERE.**  Once the
    document's ``pattern`` is CHAINED beside the type rather than dropped, the question
    this function answers -- does the type state the keyword well enough for the keyword to
    be dropped -- is gone, and the answer becomes ``{"pattern"}`` at every ``uri`` node.
    That row is open; this function is what it moves.
    """
    return frozenset({"pattern"}) if node.get("pattern") == HTTPS_ONLY else frozenset()


#: The constraint keywords a SCALAR can carry, in the order a symbol spells them,
#: each with the word it contributes.  The ORDER is fixed here and not read off a
#: document, so the name is a function of the constraint SET rather than of the
#: order a schema author happened to write it in.  ``minItems``, ``maxItems`` and
#: ``uniqueItems`` are absent because they are an array's and an array's bound
#: rides on the field (see the module docstring).
SPELLING: tuple[tuple[str, str], ...] = (
    ("minimum", "Min"),
    ("exclusiveMinimum", "Gt"),
    ("maximum", "Max"),
    ("exclusiveMaximum", "Lt"),
    ("multipleOf", "MultipleOf"),
    ("minLength", "MinLen"),
    ("maxLength", "MaxLen"),
    ("pattern", "Matching"),
)

#: The bound keywords a CONTAINER can carry, in the order a symbol spells them, keyed
#: by the container's own type word.  The order is fixed here for :data:`SPELLING`'s
#: reason: the name is a function of the constraint SET and not of the order a schema
#: author wrote it in.  The word is the document's own keyword, pascal-cased, because
#: the alias names the constraint and the document is where a reader goes to check it
#: -- ``ListMaxItems32`` against ``maxItems: 32``, with no abbreviation to decode.
CONTAINER_SPELLING: dict[str, tuple[tuple[str, str], ...]] = {
    "array": (("minItems", "MinItems"), ("maxItems", "MaxItems")),
    "object": (("minProperties", "MinProperties"), ("maxProperties", "MaxProperties")),
}

#: The word a container ``type`` contributes, and the PARAMETERS its alias is generic
#: over.  **A container alias is GENERIC and that is what makes it nameable at all.**
#: The element type cannot go in the symbol -- ``list[RightUse]`` and ``list[str]`` are
#: different types, and an element type is a domain word, which section 2's naming rule
#: forbids -- so a non-generic container alias has no name this module may give it.  A
#: parameter is not a domain word: ``NonEmptyList[T]`` is correct for every ``T`` at
#: once, and the use site supplies the element (``NonEmptyList[MediaBuyStatus]``).
CONTAINER: dict[str, tuple[str, tuple[str, ...]]] = {
    "array": ("List", ("T",)),
    "object": ("Dict", ("K", "V")),
}

#: The one container shape the plan NAMES instead of leaving to the derivation above.
#: Section 5's ``minItems``/``maxItems`` row: "``constraints`` declares the recurring
#: case once as ``type NonEmptyList[T] = Annotated[list[T], Field(min_length=1)]``".
#:
#: A hand-written row beside a derivation, which is the same arrangement :func:`standard`
#: already is -- rung 2 is a named type for a shape where one says exactly this, and
#: this is that one level up.  It is a DECISION and so is declared whatever the run met,
#: for ``render.URL_LINE``'s reason: the plan names it, and a consumer annotating their own
#: non-empty list imports it from here.  Keyed by the constraint, so the name is still a
#: function of the constraint alone.
NAMED_CONTAINERS: dict[tuple[str, tuple[tuple[str, Any], ...]], str] = {
    ("array", (("minItems", 1),)): "NonEmptyList",
}

#: The word a scalar ``type`` contributes, in the document's own vocabulary.
#: ``boolean`` is absent: a boolean carries no constraint keyword, so no shape
#: reaches this module for one.
BASE = {"string": "Str", "integer": "Int", "number": "Float"}


def standard(kind: str, constraints: Mapping[str, Any]) -> str | None:
    """D5's rung 2: the pydantic type for this shape, where one QUALIFIES.

    **Both halves are required: the type must state the document's own facts and
    accept the document's own set.**  That is a rule and not a list of blessed
    names, and ``harness.check_accepts`` puts the second half to every pair -- an
    instance drawn from the document, offered to the class -- so a type admitted
    here cannot quietly refuse a value its own document accepts.  Re-measured on
    pydantic 2.13.5, rendering through ``TypeAdapter(T).json_schema()`` and
    acceptance through ``validate_python``:

    * ``NonNegativeInt`` for ``{integer, minimum: 0}`` renders
      ``{"type": "integer", "minimum": 0}`` and accepts ``0``, ``1``, ``7`` while
      refusing ``-1``.  Both halves hold, so it QUALIFIES.
    * ``NonNegativeFloat`` for ``{number, minimum: 0}`` renders
      ``{"type": "number", "minimum": 0}`` and accepts ``0.0``, ``0.5``, ``7.0``
      while refusing ``-0.5``.  Both halves hold, so it QUALIFIES.
    * ``PositiveInt`` for ``{integer, minimum: 1}`` renders
      ``{"type": "integer", "exclusiveMinimum": 0}`` -- the same integers, a
      DIFFERENT fact -- so half one fails and it does not qualify.
    * ``PositiveFloat`` for ``{number, minimum: 1}`` renders
      ``{"type": "number", "exclusiveMinimum": 0}`` and **accepts 0.5, which the
      document refuses**.  A widening, so it is banned rather than merely
      unqualified.
    * ``AnyUrl`` fails half one for a bare ``format: uri`` document: it renders a
      ``minLength: 1`` no such document states.  ``AdCPUrl`` is rung 3 for that
      reason and :data:`URL` carries it.

    So exactly one shape qualifies at each of the two numeric types, and the
    admission test is written as the shape rather than as a table of names: a new
    standard type is admitted here only by adding its two measurements above.
    """
    if sorted(constraints) != ["minimum"] or constraints["minimum"] != 0:
        return None
    return {"integer": "pydantic.NonNegativeInt", "number": "pydantic.NonNegativeFloat"}.get(kind)


def _number(value: Any) -> str:
    """One bound, spelled so the symbol is an identifier and stays readable.

    ``-90`` is ``Neg90`` because a hyphen is not an identifier character, and
    ``0.5`` is ``0p5`` for the same reason about the point.  An integral float is
    spelled as the integer it is, so ``{number, minimum: 0}`` and
    ``{integer, minimum: 0}`` contribute the same word -- which is right: the
    TYPE word already distinguishes them, and two spellings of one bound would
    make the name a function of how the schema author wrote the zero.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "".join(c for c in str(value) if c.isalnum()) or "X"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).replace("-", "Neg", 1).replace(".", "p")
    return text


#: The constraint keyword that has NO SPELLING IN WORDS, so §4's step 2 cannot answer for
#: a shape carrying one and :func:`symbol` returns ``None`` there.
#:
#: **This used to contribute eight hex digits of the pattern's SHA-256, and
#: ``docs/plan/rebuild-plan.md`` §4 rules that a defect** (2026-11-04): "A MINTED NAME SAYS
#: WHAT THE TYPE CONSTRAINS.  A DIGEST FAILS THAT AND IS A DEFECT, and insertion-stability
#: is not the test. ``StrMatching02AE7B1E`` is stable -- derived from the constraint set,
#: so adding a scalar renames nothing -- and it is still not a name: a consumer imports it
#: and annotates with it, and it tells that consumer nothing about what it admits."
#:
#: The argument the digest rested on is intact and is the reason it is not replaced by a
#: concept HERE: a regular expression has no readable name that is not a concept, and
#: calling ``^[A-Z]{3}$`` ``CurrencyCode`` "names the idea three of its sites happen to
#: share and would be a lie at the fourth" -- measured, that pattern is stated at 86
#: positions in 62 documents for ``currency`` AND ``airport_code``.  What was wrong was the
#: conclusion: the name a constraint with no words takes is the BUNDLE's, where the bundle
#: names its subject, and its DECLARING POSITION's otherwise -- §4's steps 1 and 3, which
#: ``catalogue.collect_scalars`` derives over the bundle and :func:`resolve` reads.  "A
#: digest is what the compiler writes INSTEAD of filing that ask."
UNSPELLABLE = frozenset({"pattern"})


def _container_symbol(kind: str, constraints: Mapping[str, Any]) -> str | None:
    """The alias name for a bounded CONTAINER, derived from the bound.

    :data:`NAMED_CONTAINERS` first, which is the one shape the plan spells itself, and
    the derivation otherwise.  ``None`` for a keyword no container spelling names --
    ``uniqueItems`` is the case, and it is a RULE rather than a bound (section 5), so
    an alias claiming to carry it would drop it.
    """
    spelling = CONTAINER_SPELLING[kind]
    if set(constraints) - {kw for kw, _ in spelling}:
        return None
    named = NAMED_CONTAINERS.get((kind, tuple(sorted(constraints.items()))))
    if named is not None:
        return named
    parts = [word + _number(constraints[kw]) for kw, word in spelling if kw in constraints]
    name = CONTAINER[kind][0] + "".join(parts)
    return name if name.isidentifier() else None


def symbol(
    kind: str,
    constraints: Mapping[str, Any],
    *,
    format: str | None = None,  # the JSON Schema keyword's own name
) -> str | None:
    """**§4's STEP 2: the constraint, in words** -- ``StrMaxLen100``, ``NonEmptyList``.

    ``None`` where the shape has no spelling here -- an unknown ``type``, no
    constraint at all, a keyword :data:`SPELLING` does not name, or a keyword with no
    spelling in words at all (:data:`UNSPELLABLE`) -- and §4's step 3 then answers
    from the DECLARING POSITION (``catalogue.collect_scalars``).  Returning a name for
    a keyword this module cannot spell would be the one failure mode that matters: an
    alias whose annotation drops a fact, which is exactly what a name spelling only the
    ``maxLength`` of a shape that also carries a ``pattern`` would be.

    ``format`` contributes a word of its own, and it is spelled FIRST so the common
    case reads as what it is: ``StrFormatHostname``.  **It is here because a format
    is a CONSTRAINT at the positions that ask for a name.**  Section 5's ``format``
    row selects a TYPE where one is named for the format and the draft asserts it, and
    rides on the FIELD as ``json_schema_extra`` otherwise -- and a field is exactly
    what an ELEM, a MAPV and a BRANCH do not have.  Naming it is the row's own answer
    for those three ("ELEM / MAPV with no type selected -> a named alias carries it"),
    and the word is the format's, so the alias still names a constraint and not a
    concept.
    """
    if kind in CONTAINER:
        return None if format is not None else _container_symbol(kind, constraints)
    base = BASE.get(kind)
    if base is None or not (constraints or format):
        return None
    if set(constraints) - {kw for kw, _ in SPELLING} or set(constraints) & UNSPELLABLE:
        return None
    parts = [word + _number(constraints[kw]) for kw, word in SPELLING if kw in constraints]
    if format is not None:
        parts.insert(0, "Format" + compiler.class_name(format))
    name = base + "".join(parts)
    return name if name.isidentifier() else None


def resolve(
    kind: str,
    constraints: Mapping[str, Any],
    *,
    format: str | None = None,  # the JSON Schema keyword's own name
    named: Mapping[object, str] = {},
) -> str | None:
    """The dotted path this shape's named type is reachable at, or ``None``.

    Rung 2 before rung 3, which is D5's own order, and rung 1 is not here: it is
    reached through a ``$ref`` in the walk's own per-node entry and never by matching an
    inline declaration against another document's content (see the module
    docstring).

    Rung 2 is SKIPPED where a ``format`` is in the shape, and the reason is rung 2's
    own admission test rather than caution: a standard type qualifies only where it
    states the document's own facts, and no pydantic type states ``format: hostname``
    beside ``minimum: 0``.  ``standard`` would be asked about a shape it does not see
    and would answer for the constraints alone, which is an alias dropping a fact.

    ``named`` is **§3a's layer L1, as a table** (``catalogue.Scalars.table``): shape ->
    the symbol §4's three steps derive over the BUNDLE.  It is asked BEFORE
    :func:`symbol` because it already holds :func:`symbol`'s own answer at step 2 and
    holds the two answers :func:`symbol` cannot give -- the bundle's own name for the
    subject, and the declaring position.  It is read the way
    ``compiler.Module.value_lists`` is: a plain mapping handed in by the run, empty for
    a document lowered outside one, and §9-safe because the layer is collected over the
    bundle and never over the run's document set.
    """
    if not constraints and format is None:
        return None
    if format is None:
        found = standard(kind, constraints)
        if found is not None:
            return found
    # The three keys ``catalogue.Scalars.table`` answers at, in its own order: the exact
    # shape, the shape with the ``format`` dropped (a ``uri`` that SELECTS a URL type
    # leaves the bound behind without it), and the constraint set alone (an ``allOf``
    # intersection composes a set no single node of the bundle writes).  Only the first
    # is unconditional; the other two are in the table only where ONE entry wants them,
    # so a relaxed hit can never be another constraint's name.
    spelled = tuple(sorted(constraints.items()))
    name = None
    for key in ((kind, spelled, format), (kind, spelled, None), spelled):
        name = named.get(key)
        if name is not None:
            break
    name = name or symbol(kind, constraints, format=format)
    return None if name is None else f"{MODULE}.{name}"


class AliasCollision(BuildFailure):
    """Two distinct constraints derive one alias name.

    A BUILD FAILURE and not a ``Refusal``, on ``emit.AmbiguousRoot``'s reasoning:
    a refusal is the designed outcome of a keyword this emitter does not lower,
    and this is the emitter disagreeing with itself about what a name MEANS.
    Recording it as a refusal would file it against a document, where it would
    read as the bundle's fault, and the build would pass.

    **It is one of the two instances ``docs/plan/architecture.md`` §2 names**, which is
    why it subclasses :class:`codegen.refusal.BuildFailure` rather than ``Exception``
    directly: §2 gives the compiler ONE exception type for its own defects, and a reader
    asking "what stops this build" reads one name.  The specific class is kept because
    the message a reader of a collision needs is this one and a test names it.
    """


def record(
    into: dict[str, Shape],
    name: str,
    kind: str,
    constraints: Mapping[str, Any],
    *,
    format: str | None = None,  # the JSON Schema keyword's own name
) -> None:
    """Record one resolved shape under its name, refusing a collision.

    **The check is at the ASSIGNMENT and it has to be.**  The names are derived,
    so two distinct constraints deriving one name is possible in principle -- a
    SHA-256 prefix collision is the realistic way -- and the damage would be the
    worst kind: two fields annotated with one alias, one of them stating a
    constraint its own document does not. A dict keyed by name cannot catch that
    AFTER the fact, because the second write silently replaces the first and any
    later check then re-derives the survivor and agrees with itself. So every
    write goes through here, from the walk and from the run's union alike.

    A value comparison and not an identity one, so ``{"minimum": 0}`` and
    ``{"minimum": 0.0}`` are the same shape -- which is right: they are the same
    accepted set, and :func:`_number` deliberately spells an integral float as
    the integer it is so the name does not depend on how the author wrote the
    zero.
    """
    shape = (kind, dict(constraints), format)
    found = into.get(name)
    if found is not None and found != shape:
        raise AliasCollision(
            f"{name!r} is derived by two distinct constraints, {found} and {shape}, so one "
            "alias would annotate two fields and state a constraint one document does not"
        )
    into[name] = shape


def _annotation(kind: str, constraints: Mapping[str, Any]) -> ir.TypeRef:
    """The type an alias's annotation wraps: a scalar, or a container over its
    PARAMETERS.

    A container alias is generic (see :data:`CONTAINER`), so what goes inside
    ``list[...]`` / ``dict[..., ...]`` is the type variable and not a decided type.  It
    is an :class:`codegen.ir.TypeRef` like any other -- ``local`` because the variable is
    a name this module declares, so the renderer adds no import for it -- which is what
    keeps the annotation the renderer's on this path too.
    """
    if kind not in CONTAINER:
        return ir.TypeRef(SCALAR_PATH[kind])
    params = [ir.TypeRef(p, local=True) for p in CONTAINER[kind][1]]
    if kind == "array":
        return ir.TypeRef(container="list", of=tuple(params))
    return ir.TypeRef(container="dict", of=(params[1],), key=params[0])


def declarations(shapes: Mapping[str, Shape]) -> tuple[dict[str, ir.AliasDecl], list[str]]:
    """The alias DECLARATIONS a run's shapes come to, and the type variables they need.

    :data:`NAMED_CONTAINERS` is declared whatever the run met, because it is a DECISION
    rather than a derivation: section 5 names ``NonEmptyList[T]`` and a consumer
    annotating a non-empty list of their own imports it from here.  The derived aliases
    are exactly the shapes the run resolved, so the module is a function of the run and
    holds no alias nothing names.  (:data:`URL` is the other such decision and its
    statement is ``render.URL_LINE``, because the type it wraps is pydantic's own and has
    no shape to derive.)

    A generic alias needs its type VARIABLES declared, and exactly the ones its lines use
    are: ``T`` is always one, because ``NonEmptyList`` is always declared, and ``K``/``V``
    arrive with the first bounded mapping.  Derived rather than always written, so the
    module holds no name nothing in it reads.

    **The bound and the format ride on the alias's own TYPE** (section 2, and
    ``ir.TypeRef.facts``), which is the same carrier a class property's type is, so a
    ``minLength`` on an alias here and a ``minLength`` on a property there cannot come to
    be spelled two different ways.  ``render.constraints_module`` writes the module around
    them; nothing here is text.
    """
    shaped: dict[str, Shape] = {
        **{name: (kind, dict(cons), None) for (kind, cons), name in NAMED_CONTAINERS.items()},
        **shapes,
    }
    declared: dict[str, ir.AliasDecl] = {}
    variables: list[str] = []
    for name in sorted(shaped):
        kind, cons, fmt = shaped[name]
        variables += [p for p in CONTAINER.get(kind, ("", ()))[1] if p not in variables]
        declared[name] = ir.AliasDecl(
            name,
            replace(_annotation(kind, cons), facts=dict(cons), format=fmt),
        )
    return declared, sorted(variables)


#: ``compiler.SCALAR`` keyed by the document's own word, which is what this module
#: is handed.  Named here rather than inverted at the call site so the two
#: spellings of a scalar type have one mapping between them.
SCALAR_PATH = {"string": "str", "integer": "int", "number": "float"}
