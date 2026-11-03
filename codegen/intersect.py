"""§2's intersection rule, as pure functions over two DECLARATIONS.

``docs/plan/architecture.md`` §6 is the sentence that puts them in a module of their own:
"``restatement``, ``intersection`` and ``at_least_as_tight`` are pure functions over two
nodes and stay so", and §5 says why that makes a module rather than a region of one -- "a
pure function over two declarations lives in a module of its own, because purity is
exactly the property that makes it gradeable alone".

**What one subject this module states.**  §2 computes an intersection over DECLARATIONS
and not over decided types: a property two conjuncts declare is ONE field, so the rule
merges the two declarations and hands the merged one back to ``parse``
(:func:`_parsed_property`) rather than composing two lowerings.  Everything here is that
merge or a reading it compares: :func:`declaring` and :func:`_constraining` are what a
declaration SAYS, :func:`_at_least_as_tight` and :func:`_restatement` are whether one
declaration subsumes another, :func:`_intersection` is the merged declaration, and
:func:`_provably_empty` is the one case where the merge admits nothing.

**Two residents are not pure, and that is a layout question this row did not open.**
:func:`_the_conjuncts_own_type` takes a :class:`codegen.compiler.Target` and returns an
:class:`codegen.ir.Decided`, and :func:`intersected_at_a_branch` takes a
:class:`codegen.compiler.Module` and calls the field builder.  Both are §5's ``$ref`` row
at CONJ -- the intersection applied where the composing node declares no field set of its
own -- so they read the same declarations as the rest of this module and were placed with
the rule they apply.  ``adcp-client-python-g4z`` is where the measurement sits.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from enum import StrEnum
from typing import Any

from codegen import compiler, ir, keywords
from codegen.keywords import Position
from codegen.lower import objects
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes
from codegen.schema import parse as schema


def declaring(node: Mapping[str, Any], position: Position) -> dict[str, Any]:
    """``node`` less every key that annotates without constraining.

    One reading for the four callers that used to subtract a hand-written annotation
    set and the ``x-`` prefix by hand.
    """
    return {k: v for k, v in node.items() if keywords.declares(k, position)}


def _constraining(node: Mapping[str, Any]) -> dict[str, Any]:
    """What a declaration says about the INSTANCE.

    ``default``, ``description`` and every other key whose CELL carries nothing
    annotate the node without constraining anything, so a declaration holding only
    those says nothing and cannot narrow.  That is precisely the shadow: the three
    ``responsive_creative.json`` restatements are a ``default`` plus a
    ``description`` and nothing else.

    Read at PROP, which is the position every caller asks it at: a restatement is a
    property's declaration against the base's.

    Typed over ``Mapping`` because :func:`declaring` -- its one delegate, and the only
    thing it does -- already is: a caller holding a conjunct as a ``Mapping[str, Any]``
    was §14 step 6's fourth error, and narrowing the CALLER would have been a claim about
    a value this function never writes to.
    """
    return declaring(node, Position.PROP)


#: The annotations a FIELD renders, so the two a restatement can differ about in a way
#: a READER sees.  :func:`fields` reads exactly these off the declaration --
#: ``description`` into ``Field(description=...)`` and ``default`` into the field's
#: default -- and the rest of the keys whose cell carries nothing (``title``,
#: ``$comment``,
#: ``$schema``) reach nothing on a field, so a restatement differing only in one of
#: those renders the same field and states nothing to anyone.
RENDERED = ("default", "description")


def _annotates_differently(child: dict, base: dict) -> bool:
    """Would the two declarations render a different FIELD?

    Asked only of a restatement that says the same thing about the instance, where it
    is the whole of the difference.  An annotation the child does not state counts as
    a difference, because the child's silence is itself an answer: the field then
    carries whatever its own node resolves -- for a bare ``$ref``, the target's --
    and not the base's.
    """
    return any(child.get(k) != base.get(k) for k in RENDERED)


#: The ordering keywords, READ OFF the declaration (:data:`keywords.RANGES`) rather than
#: listed: a narrower restatement of a FLOOR states a LARGER number and a narrower
#: restatement of a CEILING a smaller one, which is :func:`keywords.pins_a_floor`'s one
#: bit.  ``exclusiveMinimum``/``exclusiveMaximum`` are draft-07's numeric form and compare
#: the same way as the inclusive pair, which is why the declaration's EXCLUSIVE column is
#: not read here; draft-04's boolean form does not appear in this bundle and would not
#: compare, so a non-number refuses below.
#:
#: It was a literal of ten entries, and the verifier held the same fact in two more
#: (``adcp-client-python-3be.8``).  §9's reason for one declaration is the one that bit:
#: "both halves must read the same declaration or the grade means nothing" -- and the two
#: had drifted, this one carrying ``minProperties``/``maxProperties`` where
#: ``harness._tighter`` did not.
_BOUNDS = keywords.FLOORS | keywords.CEILINGS


class Holds(StrEnum):
    """How a subschema-valued keyword holds the subschemas it holds."""

    #: One subschema, which is the whole value: ``items`` in draft-07's single-schema
    #: form.
    ONE = "one"
    #: One subschema per NAME: ``properties``, whose value is a key -> schema map.
    PER_KEY = "per key"


#: **The subschema-valued keywords §2's intersection rule recurses into, and how each
#: holds its subschemas.**  §2's "this holds at ANY DEPTH, including an overlay under
#: ``items``" and §5's ``properties`` row are the two sentences, and this is the ONE
#: declaration the readers take them from: :func:`_at_least_as_tight`, which asks whether
#: the pair at such a keyword composes, and :func:`_intersection`, which writes the
#: composition at both of them.  The pair of keywords was spelled in both functions,
#: which is the second copy of one keyword decision ``docs/plan/architecture.md`` §3
#: forbids.
#:
#: **The GAP at ``items`` is CLOSED** (``adcp-client-python-10l.21``, seventh
#: instalment).  The predicate recursed there and the merge took the CHILD's element
#: declaration whole, so a base that declares its element as a ``$ref`` had the
#: reference dropped and the restatement's bare overlay stood alone -- 14 sites share
#: ``items`` with different values and 8 of them lost a base's element declaration that
#: way, which refused ``core/assets/vast-asset.json``,
#: ``core/assets/daast-asset.json`` and the 9 documents chained behind them.
#: :func:`_intersection` writes the composition at ``Holds.ONE`` now, the base's
#: reference survives it as a ``$ref`` CONJUNCT where both sides declare an object, and
#: §8's pairing carries the enclosing statement DOWN by key instead of dropping it at
#: the first hop that moves to another instance (``adcp.types._base.applied_schema``) so
#: that the composition can be graded.  Measured: emitted 897 -> 908, 0 documents
#: stopped, 0 previously-emitted module modified, 0 pairs red.
#:
#: Not the table's ``descends`` column, which is a wider reading: that column answers
#: where the subschemas a structural keyword holds SIT (``codegen.keywords.descends_at``,
#: for the parser and the reference walk), and it holds ``patternProperties``,
#: ``definitions``, the combinators and the conditionals too -- keywords §2's rule has
#: no recursion for, and whose values this rule would then have to tell apart by shape
#: anyway.  What this names is the narrower fact: the two keywords whose composition IS
#: the rule applied one level down.
HOLDS: Mapping[str, Holds] = {"items": Holds.ONE, "properties": Holds.PER_KEY}


def _at_least_as_tight(
    keyword: str, c: Any, b: Any, resolve: Callable[[str], dict | None] | None = None
) -> bool:
    """Does ``c`` say at least what ``b`` says about the instance, at ``keyword``?

    Section 2's intersection rule, per keyword and in the three spellings it names: "an enum
    is the intersection of the members, a bound is the tighter one, a ``const`` must
    agree", plus "this holds at ANY DEPTH, including an overlay under ``items``".  The
    predicate is what :func:`_restatement` needs and all it needs: where the child's
    statement subsumes the base's, the child IS the intersection and the field decided
    from it carries it.

    Equality first, because it is the dominant case and because every rung below is a
    statement about two DIFFERENT values.  A keyword this cannot read is not tight
    enough and the caller refuses -- never admitted on the ground that it is probably
    fine, which would be a model wider than its document at a keyword nobody looked at.
    """
    if c == b:
        return True
    if keyword == "enum":
        return (
            isinstance(c, list) and isinstance(b, list) and all(member in b for member in c)
        )
    if keyword == "additionalProperties":
        # **``false`` IS THE TIGHTEST VALUE THIS KEYWORD TAKES, and §5's own row at CONJ
        # is what says so** (``adcp-client-python-10l.101``): "``true`` is the identity and
        # contributes nothing, ``false`` on any conjunct closes the composed object, and
        # two typed ones intersect their value schemas; a typed conjunct beside a ``true``
        # one is a widening and refuses."  A conjunct that closes the composed object
        # admits a subset of what any other value admits, so a child stating ``false``
        # says at least what the base says at this keyword, whatever the base says -- and
        # :func:`_intersection` then keeps the child's ``false``, which is the row's
        # "closes the composed object" written as a merge.
        #
        # **MEASURED with ``Draft7Validator`` on the one live pair** --
        # ``media-buy/get-reporting-status-response.json`` at
        # ``/oneOf/1/oneOf/0/properties/adcp_error``, whose restatement is
        # ``{type: object, properties: {code: {const: NOT_FOUND}, message: {const: …}},
        # required: [code, message], additionalProperties: false}`` over
        # ``core/error.json``'s 11 properties and ``additionalProperties: true``.  The
        # restatement admits exactly ONE object (both keys required, no other key
        # admitted); ``core/error.json`` accepts that object; and it refuses every payload
        # with a twelfth key that the base accepts.  So the child's accepted set is a
        # SUBSET of the base's and the pair is ordered -- the refusal's own sentence,
        # "neither declaration narrows the other", was false of this document at this
        # keyword.
        #
        # ``True`` and a TYPED value both fall through to the closing ``False``, which is
        # the row's other three readings and none of them is written: a child stating
        # ``true`` over a base's ``false`` or typed value is the widening §2 forbids, and
        # two typed value schemas intersect by a rule no row has. ``{}`` IS ``true`` (§5)
        # and is answered by the same fall-through, since it is not ``False``.
        return c is False
    if keyword == "required":
        # **A ``required`` pair is ALWAYS ordered, because its composition is the UNION
        # and neither side can loosen it** -- which is §2's intersection rule read at this
        # keyword and not a new rung.  ``required`` names the keys an instance must
        # supply, ``allOf`` applies both conjuncts to that same instance, so an instance
        # satisfying the composition supplies every key EITHER list names: the composed
        # accepted set is the intersection of the two, spelled as the union of the two
        # lists (:func:`_intersection`'s own arm, which is where the union is written).
        #
        # So a child naming FEWER keys than the base is not a loosening, for exactly the
        # reason silence is not one (:func:`_restatement`): under ``allOf`` the base's
        # ``required`` applies wherever the child's does not name a key.  Without this
        # arm two different lists share a keyword neither ordering reads, the pair is
        # unordered and the caller refuses a document whose composition §2 decides.
        #
        # Measured over the 1,054 portable documents: it is the whole of what refused
        # ``brand/verify-brand-claim-response.json`` and
        # ``brand/verify-brand-claims-response.json`` at
        # ``/definitions/signed_response/allOf/1/properties/payload`` -- the restatement
        # requires ``task`` and ``response``, ``core/response-payload-jws-envelope.json``'s
        # ``response_payload`` requires eight, and ``properties`` and ``type`` both
        # ordered (``adcp-client-python-97w``).
        #
        #
        # **It is also the only keyword that blocked the ``action_binding`` restatement in
        # ``core/audience-evidence-selection.json`` and
        # ``governance/check-governance-response.json``** (``adcp-client-python-10l.82``),
        # whose refusals were REPORTED on ``anyOf`` and on ``additionalProperties``
        # because :func:`_disagreeing` names the first key of the whole disagreeing set
        # and the base states both of those where the child is silent -- silence that is
        # not a loosening and was never the obstruction.  One shape under two keyword
        # headings, which is why a row grouped by ``Refusal.keyword`` is grouped by a
        # report and not by a cause.
        #
        # A non-list is draft-07-invalid at this keyword and falls to False with
        # everything else this predicate cannot read.
        return isinstance(c, list) and isinstance(b, list)
    # **``contains`` HAS NO ARM, DELIBERATELY, and that is the one clause of §5's "Two
    # ARRAY declarations under one ``allOf``" this compiler does not write**
    # (``adcp-client-python-10l.83``).  The row: "Every ``contains`` is kept: two
    # ``contains`` predicates are two independent ``AtLeastOne`` rules over the same
    # value, never merged into one, because ``contains: A`` and ``contains: B`` demand a
    # member satisfying each and a single merged predicate would demand one member
    # satisfying both."
    #
    # A DECLARATION holds one ``contains`` key, so two facts cannot be spelled in the
    # merged declaration :func:`_intersection` hands back to the parser; keeping both
    # means ``lower.rules.on_a_value`` taking several predicates where its signature takes
    # one (``contains: Any = None``).  Falling through to the closing ``False`` is
    # therefore the right answer for now and not an oversight: the caller refuses BY NAME
    # on this keyword -- which keeps both facts visible and merges nothing, the
    # prohibition the clause exists for -- rather than taking either predicate and
    # dropping the other silently.
    #
    # **Measured over the 1,054 portable documents: 0 property pairs state ``contains`` on
    # both sides**, so the signature change would be a derivation matching nothing.  The
    # bundle's only two declarations of one ``contains`` are at
    # ``creative/preview-creative-request.json#/allOf/6/not/anyOf/2/properties/requests``,
    # under a ``not`` -- a RULE position §5's ``not`` row owns and this rule never
    # reaches.  The first document to compose two is what buys the change.
    if keyword in _BOUNDS:
        if isinstance(c, bool) or isinstance(b, bool):
            return False  # draft-04's boolean exclusiveMinimum: a different keyword
        if not isinstance(c, int | float) or not isinstance(b, int | float):
            return False
        return c >= b if keywords.pins_a_floor(keyword) else c <= b
    if keyword == "$ref":
        # **Two whole-content references are ordered by their TARGETS and by nothing
        # else**, which is :meth:`Module.resolve_node`'s one documented site: "two
        # declarations that are each a bare ``$ref`` state the same KIND of thing about
        # an instance and whether one narrows the other is a fact about the two TARGETS,
        # which no amount of reading the two references can answer."
        #
        # :func:`_restatement` reads a bare reference through :func:`_dereferenced`
        # before it compares anything, so at the NODE level this question is already
        # answered.  It arrives here from one level down: :func:`_intersection`'s
        # composition at ``items`` meets two element declarations that are each a bare
        # reference, and the keyword they SHARE is ``$ref`` itself.  Without this arm the
        # pair is unordered, the loop takes the BASE's reference as the tighter value,
        # and the composition is LOOSER than the restatement -- measured on
        # ``core/media-buy-frequency-cap-requirement.json``, whose
        # ``/allOf/1/properties/supported_control_modes/items`` references a one-member
        # enumeration where the base it composes references a three-member one: the
        # field left the class entirely, and three emitted modules changed.  6 sites,
        # all in that document.
        #
        # ``None`` from the resolver is every undecidable case at once -- a URI naming no
        # document, a pointer naming no node, a target that refused, a reference local to
        # the document being written -- and it answers False here, which is this
        # predicate's own rule: "a keyword this cannot read is not tight enough and the
        # caller refuses."  A FRAGMENT and a pointer local to a BASE's document are no
        # longer in that list and are read like any other reference
        # (:meth:`Module.resolve_node`, ``adcp-client-python-10l.72``).
        if resolve is None or not isinstance(c, str) or not isinstance(b, str):
            return False
        target_c, target_b = resolve(c), resolve(b)
        return (
            isinstance(target_c, dict)
            and isinstance(target_b, dict)
            and _restatement(target_c, target_b, resolve) is not None
        )
    held = HOLDS.get(keyword)
    if held is not None:
        # **An overlay under a SUBSCHEMA-VALUED keyword: the rule holds at any depth,
        # and the recursion is the rule rather than a second one** (§2, "this holds at
        # ANY DEPTH, including an overlay under ``items``"; §5's ``properties`` row at
        # CONJ, "A property two conjuncts declare is one field: its constraints intersect
        # by §2, and two object declarations compose as an ``allOf`` of the two at that
        # property").  So the question asked of each held subschema is the question asked
        # of the node: is the child's declaration compatible with the base's.
        #
        # A key only the CHILD declares says something more about the same instance, and
        # a key only the BASE declares is one the child is silent about -- and silence is
        # not a loosening under ``allOf`` (:func:`_restatement`), because the base's
        # declaration applies wherever the child is quiet.  Neither can make the
        # composition looser, so only the shared keys are asked about.
        #
        # A LIST-valued ``items`` is draft-07's tuple form, where position matters and
        # two different lists are not ordered by this predicate -- so it falls through
        # to False with every other non-mapping value.
        if not isinstance(c, dict) or not isinstance(b, dict):
            return False
        pairs = [(c, b)] if held is Holds.ONE else [(c[k], b[k]) for k in set(c) & set(b)]
        return all(
            isinstance(x, dict)
            and isinstance(y, dict)
            and _restatement(x, y, resolve) is not None
            for x, y in pairs
        )
    return False


def _intersection(
    child: dict, base: dict, resolve: Callable[[str], dict | None] | None = None
) -> dict:
    """The declaration a NARROWING restatement's field is decided from.

    Section 2 in its own words: "where composed schemas constrain the same property, the field
    carries the INTERSECTION".  Under ``allOf`` both declarations apply to the same
    instance, so every keyword either one states is the composed node's -- the child's
    value where both state one (:func:`_restatement` has already decided it is at least
    as tight), the base's where only the base does.

    **The RENDERED annotations compose the same way, and §6's own rule says which wins:**
    the child's where it states one (a document's own declaration carries the
    description at its own pointer) and the base's where it is silent (clause 3, "silence
    inherits").  That is the gap-fill ``harness._composed`` performs on the DOCUMENT side,
    so reading it the other way here is the compiler disagreeing with the document's own
    composition: measured on ``core/forecast-rate-range.json``, whose
    ``low``/``mid``/``high`` narrow ``core/forecast-range.json``'s bounds and state no
    description, where the child alone dropped the base's three descriptions.

    **"Silent" means silent AFTER RESOLUTION, and that is the whole of §6's clause 2.**
    A child that is a bare ``$ref`` states no description in the document's TEXT and
    states its target's at that very pointer, because ``bundle.record``
    inlines the target there -- so gap-filling the base's over it puts a description the
    document does not carry at a pointer the document declares itself.  Measured at 17
    pointers, every one ``/properties/context/description``: a response root composing
    ``core/protocol-envelope.json``, whose envelope states the long "Relationship to
    per-task body-level ``context`` declarations" text as a ``$ref`` sibling while the
    document's own node resolves to ``core/context.json``'s own short text.
    :func:`_dereferenced` is what makes the two readings one.

    **This is a no-op at every site that narrowed before section 2's intersection rule landed**,
    and that is why it is safe: the old predicate required the child to state every
    keyword the base states, so ``{**base, **child}`` was ``child``.  What it changes is
    the newly-admitted narrowings, where the two state DIFFERENT keywords and the child
    alone would be wider than the document: measured on
    ``core/product-execution-requirement.json`` at
    ``/oneOf/2/properties/connection/allOf/1/properties/required_for``, whose
    restatement is a bare ``{"contains": {"const": "create_media_buy"}}`` over a base's
    ``{"type": "array", "items": {...}, "uniqueItems": true}`` -- decided alone it is a
    TYPELESS node the array row cannot read, and decided as the intersection it is an
    array that carries the ``contains`` (``lower.containers._ARRAY_CLAIMS``).

    **A keyword is dropped from the base where the child states the same AXIS and not
    only the same KEY**, which is :data:`_AXES` and is what keeps the merge from writing
    a node no row can read.  ``core/canonical-media-buy-action.json`` at
    ``/oneOf/0/properties/task`` is the measured one: the base states
    ``{"type": "string", "enum": [3 members]}`` and the branch restates
    ``{"const": "control_media_buy"}``, and a key-wise merge keeps BOTH -- a wide
    ``enum`` beside the ``const`` that narrows it, which is a shape no document states
    and which refused on ``const`` with "a later row does".
    """
    c, b = _constraining(child), _constraining(base)
    covered = set(c)
    for axis in _AXES:
        if covered & axis:
            covered |= axis
    if covered - {"$ref"}:
        # **A ``$ref`` is not merged into a child that constrains the instance
        # itself, and that is §9's rule rather than a preference.**  A ``$ref`` is
        # the WHOLE schema of the node it sits at, so it is not one axis beside
        # another: merging the base's into a child stating a ``const`` writes
        # ``{"$ref": T, "const": v}``, which draft-07 reads as ``T`` ALONE.  That is a
        # node no document states, and §9 names it twice -- "never refuse a keyword the
        # walk itself inserted" and "do not decide a position the bundle does not hold
        # from a view of it".
        #
        # The consequence used to be a REFUSAL on the inserted co-occurrence: the
        # 5 documents the epic lists as "const beside $ref" refused as verdicts at a
        # pointer whose own node states no ``$ref`` at all --
        # ``core/compact-task-submitted.json#/properties/status`` is
        # ``{"type": "string", "const": "submitted"}``, and the ``$ref`` came from
        # ``core/protocol-envelope.json``'s declaration of the same key.  With §5's
        # ``$ref`` row now compiling a constraining sibling to nothing, the same merge
        # DROPS the ``const`` instead, losing the document's own fact at that very
        # pointer -- measured on all 5.
        #
        # So the base's ``$ref`` is left out and the field is decided from the child's
        # own declaration.  The model is then LOOSER than the base's conjunct and §2
        # permits exactly that ("a model may be looser than its document without being
        # wrong, because the schema half already refused the payload"); what it forbids
        # is tighter, and dropping a base's reference cannot tighten anything.
        covered.add("$ref")
    merged = {**{k: v for k, v in b.items() if k not in covered}, **c}
    # **At a keyword BOTH state, the TIGHTER value and not the child's**, which is what
    # makes this function symmetric in its constraining content rather than only in the
    # direction :func:`_restatement` admits.  ``declare`` asks the predicate in both
    # directions and then merges in whichever one narrowed, so a merge that preferred the
    # first argument would make the result a function of which view the walk read first
    # -- the "last wins" this rule exists to have no reading of.
    for kw in set(c) & set(b):
        if (
            HOLDS.get(kw) is Holds.PER_KEY
            and isinstance(c[kw], dict)
            and isinstance(b[kw], dict)
        ):
            # **At ``properties`` neither value is the tighter one WHOLESALE, and §5's
            # row at CONJ says why: "two object declarations compose as an ``allOf`` of
            # the two at that property".**  The composition is therefore taken PER KEY
            # -- this same intersection, one level down -- and a key only one of them
            # declares is carried through as it stands, because under ``allOf`` every
            # key either object declares constrains the same instance.
            #
            # Taking the child's object whole is what this arm replaces, and it is the
            # shadow §2 forbids: ``core/assets/url-asset.json`` restates ``location`` as
            # ``{"properties": {"field": {"const": "url"}}}`` over
            # ``core/macro-declaration.json``'s three-property object, so the child's
            # object alone drops ``occurrence`` and ``context`` -- two properties the
            # base REQUIRES -- and the model would accept a payload the document
            # refuses.  Per key, ``field`` intersects to ``{"type": "string", "const":
            # "url"}`` (``"url"`` is a member of the base's five-member ``enum``, so
            # ``_AXES`` lets the ``const`` replace it), and the other two are the
            # base's.
            merged[kw] = {
                **b[kw],
                **c[kw],
                **{
                    k: _intersection(c[kw][k], b[kw][k], resolve)
                    for k in set(c[kw]) & set(b[kw])
                    if isinstance(c[kw][k], dict) and isinstance(b[kw][k], dict)
                },
            }
        elif (
            HOLDS.get(kw) is Holds.ONE
            and isinstance(c[kw], dict)
            and isinstance(b[kw], dict)
        ):
            # **At ``items`` the composition is written too, for the reason the
            # ``properties`` arm above gives**: §2's intersection rule "holds at ANY
            # DEPTH, including an overlay under ``items``", so the element declaration
            # of the composition is the intersection of the two element declarations
            # and not the tighter one WHOLESALE.  :data:`HOLDS` is the one declaration
            # of which keywords recurse and the two arms are now the same rule read at
            # ``Holds.ONE`` and at ``Holds.PER_KEY``.
            #
            # Taking the child's element whole is what this arm replaces, and it is the
            # same shadow: ``core/assets/vast-asset.json``'s ``/oneOf/0`` restates
            # ``macro_declarations`` as ``{"items": {"properties": {"location": ...}}}``
            # over the root's ``{"items": {"$ref": T}}``, so the child's element alone
            # is a TYPELESS node declaring one property -- every fact behind ``T``
            # dropped -- and the array row refuses it on ``properties``.  Measured
            # before this arm: 14 sites share ``items`` with different values and 8 of
            # them lose a base's element declaration, which refused
            # ``core/assets/vast-asset.json``, ``core/assets/daast-asset.json`` and the
            # 9 documents chained behind them.
            #
            # A LIST-valued ``items`` is draft-07's tuple form, where position matters
            # and the two lists are not composed by this rule, so it falls through to
            # the tightness arm below with every other non-mapping value.
            merged[kw] = _intersection(c[kw], b[kw], resolve)
        elif kw == "required" and isinstance(c[kw], list) and isinstance(b[kw], list):
            # **At ``required`` neither value is the tighter one either, and the
            # composition is the UNION** -- §2's intersection rule read at the one keyword
            # whose value is a set of KEYS rather than a constraint on one instance.
            # ``allOf`` applies both conjuncts to the same instance, so an instance
            # satisfying the composition supplies every key either list names, and the
            # union is what the composed declaration states.
            #
            # **This is the arm the predicate's own ``required`` rung needs beside it**
            # (:func:`_at_least_as_tight`): that rung says the pair is always ordered, and
            # it is only sound because the composition written here is the union.  Left to
            # the tightness fallback below, the merge would take the BASE's list and drop
            # the keys the child requires -- a model looser than its document at the
            # keyword the document was most explicit about.  Measured on
            # ``brand/verify-brand-claim-response.json``, whose restatement requires
            # ``task`` and ``response`` over ``response_payload``'s eight: the union is
            # ten, the base's alone is eight, and the child's alone is two
            # (``adcp-client-python-97w``).
            #
            # The BASE's order first and the child's new keys appended, so the composed
            # list is document-ordered and a key either side already named keeps its
            # place.  A non-list falls to the tightness arm with every other value this
            # rule has no composition for.
            merged[kw] = [*b[kw], *(k for k in c[kw] if k not in b[kw])]
        elif kw == "uniqueItems":
            # **``uniqueItems`` HOLDS WHERE EITHER CONJUNCT STATES IT** -- §5's "Two ARRAY
            # declarations under one ``allOf``" (decided 2026-10-29), "because a
            # conjunction of constraints is satisfied only by an instance satisfying
            # both".  So it is an OR and neither value is "the tighter one": the tightness
            # fallthrough below reads an unordered pair as the BASE's, which takes
            # ``false`` over a base's ``true`` in one direction and is the one direction
            # §2 forbids -- a model admitting duplicates the document refuses.
            #
            # The ASYMMETRIC case needs no arm and never did: a key only one declaration
            # states is carried through by the merge above, so the OR already held
            # wherever one side was silent.  Measured over the 1,054 portable documents:
            # **0 property pairs state the keyword on both sides**, so this arm is the one
            # written for the first one rather than a derivation matching something.
            merged[kw] = bool(c[kw]) or bool(b[kw])
        elif not _at_least_as_tight(kw, c[kw], b[kw], resolve):
            merged[kw] = b[kw]
    # **The base's reference SURVIVES as a ``$ref`` CONJUNCT where both declarations
    # declare ``properties``**, which is §5's ``properties`` row at CONJ read where the
    # base spells its whole content as a reference: "two object declarations compose as
    # an ``allOf`` of the two at that property".  The arm above drops the base's
    # ``$ref`` because draft-07 reads ``{"$ref": T, "const": v}`` as ``T`` alone -- and
    # that is right for a child constraining the instance ITSELF, where there is no
    # spelling of the conjunction at the node.  Where both sides declare an object there
    # is one, and it is the document's own: an ``allOf`` member.
    #
    # Appended BESIDE the child's own keywords, ``{**child, "allOf": [*child's
    # conjuncts, base]}``, and never as ``{"allOf": [base, child]}``.  Wrapped the other
    # way the child's declarations sit under a synthetic ``…/allOf/1`` and every nested
    # class is stamped at a pointer the document does not have, so
    # ``adcp.types._base.applied_schema`` raises ``KeyError: 'allOf'`` when the pair is
    # graded.  Appended, only the conjunct's OWN index is synthetic and that costs
    # nothing: a bare ``$ref`` conjunct declares no class, so no pointer below it is
    # ever stamped.
    #
    # The measured site is ``core/assets/vast-asset.json`` and
    # ``core/assets/daast-asset.json`` at ``/oneOf/N/properties/macro_declarations``,
    # whose element overlay ``{"properties": {"location": ...}}`` composes with the
    # root's ``{"$ref": core/macro-declaration.json}``.
    # ``core/assets/display-tag-asset.json`` is the control: it SPELLS the same
    # composition in its own branch text (:func:`_conjoins`), its element declares
    # ``allOf`` and not ``properties``, so this arm does not fire and the document's own
    # conjunct list is what stands.
    #
    # **"Declares an object" is not "declares ``properties``", and reading it that way
    # left the arm's own rule unwritten for two further shapes** (``…10l.82``).  The
    # clause is about a CONTAINER the two declarations agree on -- §5's ``properties``
    # row at CONJ for an object, §2's "this holds at ANY DEPTH, including an overlay
    # under ``items``" for an array -- and a container is declared by any of its
    # keywords, not by one of them.  :func:`_container_kind` is the reading, and it is
    # what makes the two measured shapes below the same site as the two above:
    #
    # * ``core/signal-coverage-forecast.json`` at
    #   ``/properties/points/items/allOf/1/properties/dimensions``, whose restatement is
    #   a bare ``{"contains": {...}}`` over ``core/forecast-point.json``'s ``{"$ref":
    #   core/forecast-point-dimensions.json}``.  Both declare an ARRAY; the reference
    #   dropped, the merge is a TYPELESS node and the ``contains`` row refused it for
    #   having no type to lower onto -- a type the document states behind the reference.
    # * ``media-buy/get-reporting-status-response.json`` at
    #   ``/oneOf/0/oneOf/1/properties/pagination``, whose restatement is ``{"type":
    #   "object", "required": ["has_more", "total_count"]}`` over a base's bare
    #   reference.  Both declare an OBJECT and neither name is a property the merge
    #   declares, so §5's ``required`` row refused it as "a presence rule with no field"
    #   -- the two fields being behind the dropped reference.
    #
    # The ``const``-beside-``$ref`` five are the control and are UNCHANGED: a ``{"type":
    # "string", "const": v}`` restatement declares no container, so the arm does not
    # fire, the reference is dropped as the paragraph above decides, and the model is
    # looser than the base's conjunct where §2 permits it.
    conjoined_the_reference = (
        set(b) == {"$ref"}
        and "$ref" not in merged
        and _container_kind(c) is not None
        and _container_kind(c) == _container_kind(_constraining(_dereferenced(base, resolve)))
    )
    # **The APPEND IS IDEMPOTENT, because ``allOf`` is: a conjunct already in the list
    # states nothing a second time.**  §2's rule is "composition merges by intersection"
    # and §5's ``allOf`` row reads every member as applying to the same instance, so
    # ``A ∧ A`` is ``A`` and a conjunct list that names one member twice says exactly
    # what the list naming it once says.  The list is still a LIST and not a set -- the
    # paragraph above decides the ORDER, and the pointer a nested class is stamped at
    # depends on it -- so what is written here is idempotence at the one member this arm
    # appends, not a dedup of the list.
    #
    # **Why the arm fires twice at one node, which is the defect this clause closes**
    # (``adcp-client-python-10l.98``).  Two declarations can reach one node with the SAME
    # bare reference at the same key, and each is a separate, correct merge: the node's
    # OWN declaration meets a conjunct's in :func:`declare`, and the result then meets the
    # INHERITED one in the restatement loop.  Both merges see ``b == {"$ref": T}``, both
    # satisfy the gate -- the first append leaves the reference under ``allOf`` and not
    # under ``$ref``, so ``"$ref" not in merged`` still holds -- and the second wrote
    # ``{"allOf": [{"$ref": T}, {"$ref": T}]}``.
    #
    # That is a node NO DOCUMENT STATES, and §9 is why it must not be written rather than
    # repaired downstream: "do not decide a position the bundle does not hold from a view
    # of it".  Its visible consequence was a base list naming one class twice, which
    # Python refuses to build -- but the base list is the SYMPTOM and the declaration is
    # the defect, so a dedup beside ``dispatching_bases`` would have left the malformed
    # declaration for §8's document-side fold and for every refusal pointer below it.
    #
    # Measured over the 1,054 portable documents: the arm fired on an already-present
    # conjunct at 4 merges, over 2 nodes, both of them ``core/indicator.json`` reached
    # through ``core/indicator-bearing.json`` beside a node that declares the same
    # ``items`` reference itself --
    # ``creative/list-creatives-response.json#/properties/creatives/items/properties/assignments/properties/assigned_packages/items``
    # and
    # ``media-buy/get-media-buys-response.json#/properties/media_buys/items/properties/packages/items/properties/creative_approvals/items``.
    # The second is not in the committed tree, which is why one unimportable module was
    # found and not two.
    #
    # The equality is on the CONJUNCT this arm would write and not on the target it names:
    # the claim is "this arm has already written this member", which is the one claim
    # idempotence needs.  A conjunct carrying the same reference with a SIBLING is a
    # different declaration and §5's ``$ref`` row reads it differently; 0 of the 4
    # measured sites is that shape, so no site rests on the wider reading.
    if conjoined_the_reference:
        own_conjuncts = merged.get("allOf")
        own_conjuncts = own_conjuncts if isinstance(own_conjuncts, list) else []
        if {"$ref": b["$ref"]} not in own_conjuncts:
            merged["allOf"] = [*own_conjuncts, {"$ref": b["$ref"]}]
    resolved = _dereferenced(child, resolve)
    # **The BASE is gap-filled THROUGH ITS OWN REFERENCE, for the same reason the child
    # is read through one.**  §6's description-authority clause 3 is "silence
    # inherits", and silence means silent AFTER RESOLUTION on both sides: a base
    # declaring a key as a bare ``$ref`` states its target's annotations at that
    # pointer, because ``bundle.record`` inlines the target there and
    # ``harness._composed`` folds the conjunct in -- so reading the base's own TEXT
    # alone drops a description the composed document states.
    #
    # Measured on ``media-buy/control-media-buy-response.json`` at
    # ``/oneOf/0/properties/warnings/items/properties/code``: ``core/warning.json``
    # declares ``code`` as ``{"$ref": "enums/warning-code.json"}`` and nothing else, the
    # conjunct restates ``{"const": "inventory_shortfall_forecast"}``, and the
    # description the composed document states at that pointer is
    # ``warning-code.json``'s own root one.  2 pairs, both of them
    # ``/properties/code/description``.
    # Gated on the base's reference having been DROPPED above, and the gate is
    # measured: read unconditionally, the base's target annotations also reach a
    # restatement whose own node resolves to something of its own, which is §6 clause
    # 2's case and the 17 pointers :func:`_restatement` records.  Where the reference
    # was dropped there is nothing of the base's left for the child to disagree with,
    # so the annotation is the only thing the base still contributes.
    # **And the base's OWN annotation sibling wins over its target's**, which is §5's
    # ``$ref`` row ("an annotation sibling → the sibling's description wins") and
    # architecture §13 item 2's settled reading, applied one level up.  Measured on
    # ``core/protocol-envelope.json``, whose ``status`` is
    # ``{"$ref": "core/task-status.json", "description": "Current AdCP task state or
    # structured outcome..."}``: read target-first, 11 pairs reported the TARGET's
    # description where the composed document states the envelope's own.
    # The gate reads "the base's reference reaches the composed node NOWHERE", so the
    # conjunct arm above satisfies it the way a surviving ``$ref`` key does: where the
    # reference is still there, the base's own declaration is what applies and the
    # child has something to disagree with, which is this gate's own reason.
    based = (
        {**_dereferenced(base, resolve), **base}
        if "$ref" in b and "$ref" not in merged and not conjoined_the_reference
        else base
    )
    annotated = {
        **{k: v for k, v in based.items() if k in RENDERED and k not in resolved},
        **{k: v for k, v in child.items() if k not in merged},
    }
    return {**annotated, **merged}


#: Keywords that say the SAME KIND of thing about an instance, so a child stating one of
#: them answers for every member of the set and the base's are not merged in beside it.
#:
#: One set, ``{"const", "enum"}``: a ``const`` is a one-member vocabulary (the rewrite
#: :func:`_as_enum` makes for the tightness predicate), so a ``const`` that narrows a
#: base's ``enum`` REPLACES it rather than joining it.  The bounds are deliberately NOT
#: axes: ``minItems`` and ``maxItems`` constrain the same instance from opposite sides
#: and a child stating one says nothing about the other, so merging the base's is
#: correct and is what section 2's "a bound is the tighter one" means per keyword.
_AXES: tuple[frozenset[str], ...] = (frozenset({"const", "enum"}),)


#: **The keywords that DECLARE a container, by the container they declare it to be.**
#: §5's object and array sections are the two lists and this is a reading of them: every
#: keyword whose row constrains an object is in the first set and every keyword whose row
#: constrains an array is in the second, so a declaration stating any of them has said
#: which container the instance is -- as surely as a ``type`` word does.
#:
#: Read by :func:`_container_kind` and by nothing else.  Not a second copy of
#: :data:`HOLDS`, which names the two keywords §2's intersection RECURSES into; this names
#: the wider fact that a keyword belongs to a container's row group, which is what decides
#: whether two declarations are two declarations of ONE container.
#:
#: **It is now that reading and no longer a transcription of it**
#: (``adcp-client-python-3be.8``): :func:`keywords.constrains_container` is the projection
#: of the grid family and :data:`keywords.ARM` together, and the two sets it returns are
#: the two written here, with ONE difference -- ``additionalItems`` is gone.  That keyword
#: has no ROW, so a declaration stating one refuses by name at the screen long before this
#: predicate is asked, and bundle 3.2 states **0 of them** (measured over the cache; the
#: verifier's descent records the same 0 for its own reason).  A list naming a keyword the
#: table does not is the drift this row exists to remove: it reads as a decision about
#: ``additionalItems`` and there is none.
_CONTAINER_KEYWORDS: Mapping[str, frozenset[str]] = {
    word: keywords.constrains_container(word) for word in ("object", "array")
}


def _container_kind(constraining: Mapping[str, Any]) -> str | None:
    """Which container a declaration declares -- ``"object"``, ``"array"`` or neither.

    The ``type`` word where it states one, and otherwise the keyword group its own
    keywords fall in (:data:`_CONTAINER_KEYWORDS`): a node stating ``contains`` has said
    the instance is an array as surely as ``type: array`` does, and draft-07's keyword
    groups are what make that an entailment rather than a guess.

    ``None`` where the declaration names neither container and where it names BOTH --
    a ``type`` list spanning the two, or a node stating ``properties`` beside ``items``.
    Both are declarations this cannot read as one container, and the caller's rule is
    that two declarations compose as a conjunct only where they agree on which container
    they are about.
    """
    words = _type_words(constraining.get("type")) & {"object", "array"}
    if len(words) == 1:
        return next(iter(words))
    if words:
        return None
    found = {kind for kind, group in _CONTAINER_KEYWORDS.items() if group & set(constraining)}
    return next(iter(found)) if len(found) == 1 else None


def _type_words(stated: Any) -> frozenset[str]:
    """A ``type`` keyword's words as a set: one word, a list of words, or nothing.

    ``frozenset()`` for a ``type`` the node does not state and for one whose value is
    neither a word nor a list of them, which is what makes :func:`_provably_empty`
    answer "not provably" rather than "empty" for a malformed declaration.
    """
    if isinstance(stated, str):
        return frozenset({stated})
    if isinstance(stated, list):
        return frozenset(w for w in stated if isinstance(w, str))
    return frozenset()


def _provably_empty(child: dict, base: dict) -> str | None:
    """The keyword at which two declarations of ONE property intersect to NOTHING, or
    ``None`` where this cannot prove they do.

    §5's ``$ref`` row at CONJ, distribution clause: "A distributed branch whose
    intersection is EMPTY is DROPPED ... **The emptiness must be PROVED from the pins the
    two sides state** -- disjoint ``const``\\ s, disjoint ``enum``\\ s, disjoint type
    words -- which is the same test the empty-intersection row names; an intersection
    this compiler cannot compute is the restatement row and not this one."

    **That last clause is the whole of why this is a predicate of its own and not
    ``_restatement(...) is None``.**  :func:`_restatement` answers ``None`` for every
    pair it cannot ORDER, which is a strictly larger set than the pairs it can prove
    admit nothing -- its own docstring names the case: "a shared keyword where the CHILD
    is LOOSER refuses, where §2 would have the field carry the base's", and
    ``minimum: 1`` beside a base's ``minimum: 3`` admits every value from 3 up.  A branch
    dropped on that answer would be dropped for a conjunction that admits something,
    which is a model NARROWER than its document -- the one direction §2 forbids outright
    and the defect this whole clause is fenced against.  So the two questions are asked
    by two functions: "can I order these" is :func:`_restatement`'s and "do these admit
    nothing" is this one's, and nothing here is reused to answer the other.

    Two proofs, and deliberately no third:

    * **Disjoint vocabularies.**  Read through :func:`_as_enum`, which is the same
      rewrite :func:`_at_least_as_tight` compares through -- a ``const`` is a one-member
      ``enum`` -- so ``const`` against ``const``, ``const`` against ``enum`` and ``enum``
      against ``enum`` are one reading and not three.  No member in common means no
      instance satisfies both, which is a proof and not an estimate.
    * **Disjoint type words.**  draft-07's ``type`` is the instance's JSON type, so two
      sets of words with no word in common admit no instance between them.  A node
      stating no ``type`` states nothing to be disjoint FROM, which is why
      :func:`_type_words` answers with an empty set and an empty set proves nothing.

    A bound, a pattern, a ``required`` naming a key the other forbids: each of these CAN
    make a conjunction empty and none of them is read here, because the reading would be
    an inference rather than a pin.  This function being incomplete is safe in exactly
    one direction -- a branch it fails to drop is kept, and a kept branch that admits
    nothing is a model WIDER than its document, which §2 permits and ``strict_validate``
    refuses the payload for.
    """
    c, b = _as_enum(_constraining(child)), _as_enum(_constraining(base))
    if isinstance(c.get("enum"), list) and isinstance(b.get("enum"), list):
        if not [member for member in c["enum"] if member in b["enum"]]:
            return "enum"
    words_c, words_b = _type_words(c.get("type")), _type_words(b.get("type"))
    if words_c and words_b and not words_c & words_b:
        return "type"
    return None


def _restatement(
    child: dict, base: dict, resolve: Callable[[str], dict | None] | None = None
) -> bool | None:
    """The merge rule as one decision about one restated property.

    ``True`` -- it NARROWS: everything ``base`` says about the instance it says at
    least as tightly (:func:`_at_least_as_tight`), and it says something more.  The
    subclass states it, and what it states IS the intersection.

    ``False`` -- it says nothing, or says exactly the same thing.  The field is
    inherited and the subclass declares no field at all.

    ``None`` -- it is INCOMPATIBLE: at a keyword BOTH state it says something that is
    not at least as tight.  Under ``allOf`` both declarations apply, so the effective
    accepted set is their intersection, and a declaration that LOOSENS one the base
    already made is a statement the document does not make at that pointer.  The caller
    refuses.

    **This predicate was keyword-value EQUALITY and section 2's rule is not.**  "The field
    carries the intersection -- an enum is the intersection of the members, a bound is
    the tighter one, a ``const`` must agree" admits narrowings an equality test reads as
    a conflict, and they go live the moment the conjunct cases land:
    ``core/product-execution-requirement.json`` at
    ``/oneOf/2/properties/connection/allOf/1/properties/status`` restates
    ``{"const": "unknown"}`` over a base's ``{"enum": [...], "type": "string"}``, and
    its ``required_for`` restates a bare ``{"contains": {...}}`` over a base's
    ``{"type": "array", "items": {...}, "uniqueItems": true}``.  Both reported "neither
    matches nor narrows".

    **KNOWN CEILING: a shared keyword where the CHILD is LOOSER refuses, where section 2 would
    have the field carry the base's.**  "A bound is the tighter one" says the
    intersection of ``minimum: 1`` over a base's ``minimum: 3`` is 3, and the
    document-side reading reads it that way too (``harness._tighter``), so such a pair
    is gradeable and could be inherited.  It refuses because the arm has no site.

    **RE-MEASURED at ``adcp-client-python-97w``, and the three documents the comment here
    named are gone from it.**  The old sentence read "3 of the 1,054 portable documents
    are refused by this predicate -- ``governance/check-governance-response.json``'s
    ``action_binding``, ``media-buy/get-media-buys-response.json``'s ``indicators`` and
    ``signals/get-signals-response.json``'s ``range``".  Probed by recording which pairs
    reach the shared-keyword loop's ``None``: immediately before this row, **6
    documents** -- the two it named last are not among them, because each now refuses
    earlier in its own chain and never reaches this predicate -- and **5 of the 6 were
    one keyword, ``required``**, which is the rung this row wrote (the arm above).  After
    it: **1**, ``core/postal-area.json`` at ``enum``, and that document is refused on
    ``title`` at ``/anyOf/0`` regardless, so the arm is the SOLE reason for none.

    So the ceiling stands and the reason does: the one live pair is not a looser bound
    either, and an arm for a looser bound would still be a derivation matching nothing.
    What the stale count hid was a keyword that measured FIVE documents, which is the
    lesson rather than the number -- a population named once and not re-probed stops
    being a measurement.

    **SILENCE IS NOT A LOOSENING, and that half had to wait for the output to be the
    intersection.**  The old rule demanded the child keep every keyword the base states,
    for a sound reason at the time: the field was decided from the CHILD ALONE, so a
    keyword the child did not restate was a keyword the annotation dropped.  Now
    :func:`_intersection` is what the field is decided from, every keyword either
    declaration states reaches it, and the demand measures nothing -- under ``allOf``
    the base's statement applies wherever the child is quiet.  The two halves are one
    change and neither is correct without the other.
    """
    # Both declarations read through :func:`_dereferenced`, and EVERY comparison below
    # made on that same reading -- including the novelty test, which is the one that
    # went wrong when it was not.  Comparing a RAW intersection against a DEREFERENCED
    # base made two ``$ref``s to one target read as a narrowing, and the field then
    # carried the base's annotation at a pointer the document declares itself: measured
    # at 17 pointers, every one ``/properties/context/description``, which is §6's
    # description-authority clause 2 and the 15 facts it was written for.
    dc, db = _dereferenced(child, resolve), _dereferenced(base, resolve)
    c, b = _as_enum(_constraining(dc)), _as_enum(_constraining(db))
    # **A ``const`` is a one-member ``enum``, and that is a rewrite rather than a rung**
    # (:func:`_as_enum`, applied before anything is compared).  section 2's "a ``const`` must
    # agree" is the intersection of a pinned value with a vocabulary, and writing the
    # two into one spelling is what lets ONE predicate answer ``const`` vs ``const``,
    # ``const`` vs ``enum`` and ``enum`` vs ``enum``.  Toward ``enum`` and not toward
    # ``const`` because a ``const`` is the degenerate case: folding the other way has
    # nothing to say about a two-member vocabulary.
    if not c:
        return False
    if _conjoins(child, base):
        # **The restatement SPELLS the composition itself, so it says everything the
        # base says by construction**: draft-07 applies every conjunct of an ``allOf``
        # to the same instance, so a conjunct list holding the base's own declaration
        # says at least what that declaration says, and the rest of the list is what it
        # adds.  :func:`_conjoins` carries the measurement and why the question has to
        # be asked of the base's OWN declaration rather than of its dereferenced
        # reading.
        return True
    if "$ref" in b and b.get("$ref") != c.get("$ref"):
        # **The base's whole constraining content is a ``$ref`` this predicate could
        # NOT resolve, so whether the restatement narrows it is unanswerable** -- and
        # :func:`_at_least_as_tight`'s own rule decides that: "a keyword this cannot
        # read is not tight enough and the caller refuses -- never admitted on the
        # ground that it is probably fine, which would be a model wider than its
        # document at a keyword nobody looked at."  ``$ref`` was the one keyword that
        # escaped it, because an unresolved reference leaves the two declarations
        # SHARING NO KEYWORD at all: the loop below then has nothing to range over, the
        # novelty test says the child adds something, and the field is decided from the
        # child alone with every fact behind the reference dropped.
        #
        # **RE-MEASURED over the 1,054 portable documents: 0 sites, down from 3, and the
        # 3 were one defect** (``adcp-client-python-10l.72``).  The comment here read
        # "1 site" and named one of them; the arm had 3, and every one was a pointer
        # LOCAL TO THE BASE'S OWN DOCUMENT:
        #
        # * ``core/tracker-execution-selector.json`` at ``/oneOf/1``, whose
        #   ``vast_versions``, ``vast_event``, ``target`` and ``offset`` each name a node
        #   of ``core/vast-tracker-constraints.json`` ABSOLUTELY where the base it
        #   composes declares the same four as ``{"$ref": "#/definitions/…"}``.  THE SAME
        #   NODE, written once absolutely and once relative to the base's own document --
        #   so the pair was never unreadable, it was unread.
        # * ``brand/verify-brand-claim-response.json`` and
        #   ``brand/verify-brand-claims-response.json`` at
        #   ``/definitions/signed_response``, whose conjunct restates ``payload`` with two
        #   properties over ``core/response-payload-jws-envelope.json``'s ``{"$ref":
        #   "#/definitions/response_payload"}``.
        #
        # :meth:`Module.resolve_node` reads both spellings now, so no pair in this bundle
        # reaches this clause.  **It stays, and a population of 0 is not "a derivation
        # matching nothing" here**: it is not an arm producing an outcome for a shape no
        # document has, it is the one place :func:`_at_least_as_tight`'s refuse-what-you-
        # cannot-read rule is spelled for ``$ref``, and deleting it ADMITS the unreadable
        # pair rather than refusing it -- :func:`_intersection` then drops the base's
        # reference (its ``covered`` arm) and the field is decided from the child alone
        # with every fact behind the reference gone.  Measured before the resolver read
        # the two spellings: emitted, the brand class dropped 6 of the 8 properties
        # ``payload`` requires, which is a model wider than its document.
        #
        # **The two ``brand`` documents EMIT now, and they left through the clause below
        # rather than through this one** (``adcp-client-python-97w``).  Once the base
        # dereferenced to its object, ``properties`` composed per key and ``type``
        # matched; what was left unordered was ``required``, and the rung for it is in
        # :func:`_at_least_as_tight` where §2 already put it.
        return None
    if not all(_at_least_as_tight(k, c[k], b[k], resolve) for k in set(c) & set(b)):
        return None
    # It narrows when the INTERSECTION says more than the base does.  Asked of the
    # intersection and not of the child, because that is what the field carries: a
    # child restating a strict SUBSET of the base's keywords with the same values
    # intersects to the base itself, states no new fact, and is the inherited field
    # (``_annotates_differently`` then decides whether the annotations differ).
    return _as_enum(_constraining(_intersection(dc, db, resolve))) != b


def _conjoins(child: dict, base: dict) -> bool:
    """Is ``child`` a CONJUNCTION one of whose conjuncts is ``base``'s own declaration,
    with something beside it?

    Then it narrows, and the answer costs no comparison: ``allOf`` applies every
    conjunct to the same instance, so the list says at least what the conjunct that IS
    the base says, and the other conjuncts are what it says more.  ``something beside
    it`` is what makes it a narrowing rather than a restatement of nothing -- a list
    holding the base and no other constraining conjunct says exactly what the base says,
    which is :func:`_restatement`'s ``False``.

    **Asked of the base's OWN declaration and never of its dereferenced reading**, which
    is the whole point of the arm.  The conjunct and the base here are the SAME ``$ref``,
    and :func:`_dereferenced` replaces the base's with the target's whole schema -- the
    target's own ``allOf`` of conditionals included.  The predicate then meets two values
    at ``allOf`` that have nothing to say to each other, ``_at_least_as_tight`` has no
    ordering for a conjunct list, and the document is refused for restating the reference
    VERBATIM.

    Measured over the 1,054 portable documents: **1 site**,
    ``core/assets/display-tag-asset.json`` at ``/oneOf/0/properties/macro_declarations``,
    whose branch spells in full the composition ``vast-asset.json`` and
    ``daast-asset.json`` spell as a bare overlay --
    ``{"items": {"allOf": [{"$ref": T}, {"properties": ...}]}}`` over the root's
    ``{"items": {"$ref": T}}``, where ``T`` is ``core/macro-declaration.json`` and its
    own root carries six ``if``/``then`` conjuncts.  It was the only ``allOf`` pair
    ``_at_least_as_tight`` was ever asked about and the only one it answered False for.
    """
    conjuncts = _constraining(child).get("allOf")
    if not isinstance(conjuncts, list):
        return False
    stated = [_constraining(c) for c in conjuncts if isinstance(c, dict)]
    b = _constraining(base)
    return b in stated and any(s and s != b for s in stated)


def _dereferenced(
    declaration: dict, resolve: Callable[[str], dict | None] | None
) -> dict:
    """A declaration that is nothing but a ``$ref``, read as what it references.

    For the PREDICATE and never for the field: :func:`Module.resolve_node` says why, and
    the asymmetry is the point -- whether one declaration narrows another is a fact
    about the two TARGETS, while the field is an IMPORT of the symbol the document
    names (P2).

    Only a declaration whose whole constraining content is the reference.  A ``$ref``
    with a constraint beside it is draft-07 ignoring its sibling, which the whole
    pipeline refuses by name rather than reading two ways (:func:`lower_node`,
    :func:`lower_composition`'s sibling arm), so there is nothing here to resolve.
    """
    if resolve is None:
        return declaration
    content = _constraining(declaration)
    if set(content) != {"$ref"}:
        return declaration
    target = resolve(content["$ref"])
    return target if isinstance(target, dict) else declaration


def declares_an_array(declaration: Any, resolve: compiler.Resolver = None) -> bool:
    """Does this DECLARATION put an ARRAY at the instance it describes?

    §5's ``uniqueItems`` row's gate, and the one reading of it.  draft-07 asserts
    ``uniqueItems`` about an array and IGNORES it for every other instance, so whether
    the keyword constrains anything at a position is exactly this question -- and a
    declaration may answer it through a COMPOSITION rather than with a ``type`` word of
    its own.

    **§2's clause of 2026-10-29 is why this reads a conjunct rather than the rule moving
    to the value's own type**: "A composing DECLARATION is not a position where no class
    encloses the value.  A property whose declaration is an ``allOf`` still sits in the
    class that holds the property, so the clause above is unchanged and the rule is
    declared there -- the reader that writes it must see through the composition rather
    than the rule move to the value's own type."  So the gate sees through, and §2's
    "a rule on the nearest class" is unchanged.

    **The direction this is conservative in is the one that matters.**  Answering
    ``True`` where the instance need not be an array would put a
    :class:`adcp.types._runtime.UniqueItems` on a class for a value draft-07 ignores the
    keyword for -- a model NARROWER than its document, which §2 forbids outright.  So
    every arm asserts the array rather than failing to exclude it: a ``type`` word that
    IS ``"array"``, and an ``allOf`` CONJUNCT that declares one, because draft-07 holds
    every conjunct against the same instance and one of them demanding an array is
    enough.  A ``type`` LIST including ``"array"`` is NOT an arm, deliberately: it
    admits a non-array, so the keyword is ignored for some instance the declaration
    admits.  Answering ``False`` where the instance is an array loses no fact silently:
    the keyword is then neither lowered nor stripped, and the handler that claimed it
    reports or refuses.

    Two readers, in the two spellings they hold: ``lower.rules._distinct``, which has
    the property's DECLARATION out of :attr:`codegen.schema.nodes.Base.declared`, and
    :func:`lower_composition`'s ``uniqueItems`` arm, which holds the same declaration as
    a parsed node and asks :func:`a_conjunct_declares_an_array` of its conjunct list.
    One reading, because a gate that claimed the keyword and an arm that refused it
    would be §3's "a keyword whose cell lowers must be claimed by its handler" read two
    ways at one node -- which is exactly the hole this closes.
    """
    if not isinstance(declaration, Mapping):
        return False
    if declaration.get("type") == "array":
        return True
    conjuncts = declaration.get("allOf")
    return isinstance(conjuncts, list) and a_conjunct_declares_an_array(conjuncts, resolve)


def a_conjunct_declares_an_array(conjuncts: Iterable[Any], resolve: compiler.Resolver = None) -> bool:
    """:func:`declares_an_array`, asked of a raw CONJUNCT LIST.

    The same question in the spelling :func:`lower_composition` holds it -- that row has
    the conjuncts as :class:`codegen.schema.nodes.Conjunct` values and no declaration to
    put them back into, and §9 forbids deciding a position from a view of one the bundle
    does not hold, so the list is asked rather than a ``{"allOf": […]}`` rebuilt around
    it.

    A conjunct that is nothing but a ``$ref`` is read as its TARGET, through
    :func:`_dereferenced` and therefore by the same rule §2's intersection already reads
    one by: whether the composed instance is an array is a fact about the TARGET, which
    no amount of reading the reference can answer.  ``None`` from the resolver leaves the
    conjunct as written, which states no ``type`` and so answers ``False`` -- the safe
    direction, and the same one :meth:`Module.resolve_node`'s undecidable arm points.
    """
    return any(declares_an_array(_dereferenced(c, resolve), resolve) for c in conjuncts)


#: The draft-07 type word each JSON value has.  ``bool`` before ``int`` because
#: ``isinstance(True, int)`` is true in Python and ``true`` is not an integer in JSON.
_JSON_TYPES: tuple[tuple[type | tuple[type, ...], str], ...] = (
    (bool, "boolean"),
    (int, "integer"),
    (float, "number"),
    (str, "string"),
    (list, "array"),
    (dict, "object"),
)


def _entailed_type(members: list) -> str | None:
    """The one ``type`` every member of a vocabulary has, or ``None``.

    An enumerated value set ENTAILS a type: ``{"const": "unknown"}`` says the instance
    is a string as surely as ``{"type": "string"}`` does.  Deriving it is what lets a
    ``const`` restatement be read as keeping a base's ``type`` instead of dropping it --
    without it, ``{"const": "unknown"}`` over ``{"enum": [...], "type": "string"}``
    reads as incompatible for a fact it states by implication.  Measured on the bundle's
    own documents: 832 typeless ``const`` nodes.
    """
    found = {
        word for member in members for cls, word in _JSON_TYPES if isinstance(member, cls)
    }
    # One word, and the FIRST match per member: ``_JSON_TYPES`` is ordered so a bool
    # answers ``boolean`` and not ``integer``, and the set comprehension above would
    # collect both -- so a bool present at all makes this ambiguous rather than wrong.
    if not members or (any(isinstance(m, bool) for m in members) and len(found) > 1):
        return None
    return next(iter(found)) if len(found) == 1 else None


def _as_enum(constraining: dict) -> dict:
    """``{"const": v}`` read as ``{"enum": [v]}`` plus the ``type`` it entails.

    So ONE predicate answers ``const`` against ``const``, ``const`` against ``enum``
    and ``enum`` against ``enum``, and a vocabulary is read as stating the type its
    members have (:func:`_entailed_type`).

    The ``const`` rewrite applies only where the declaration does not state both: a
    node stating ``const`` AND ``enum`` says two things, and collapsing them would drop
    one.  draft-07 permits it and this bundle has none, so such a node keeps both keys
    and compares by equality.
    """
    out = constraining
    if "const" in out and "enum" not in out:
        out = {**{k: v for k, v in out.items() if k != "const"}, "enum": [out["const"]]}
    if "type" not in out and isinstance(out.get("enum"), list):
        word = _entailed_type(out["enum"])
        if word is not None:
            out = {**out, "type": word}
    return out


def _disagreeing(
    child: dict, base: dict, resolve: Callable[[str], dict | None] | None = None
) -> str:
    """The keyword a refusal is reported on: **the first SHARED one the restatement does
    not say at least as much at**, read through the same two lenses
    :func:`_restatement` compares through.

    **It was ``min()`` over every key the two differ about, and that set contains keys
    only the BASE states -- which can never be the obstruction** (``10l.92``).  Under
    ``allOf`` the base's declaration applies wherever the child is quiet, so the child's
    silence at a keyword is not a loosening and :func:`_restatement` does not read it as
    one: the predicate ranges over ``set(c) & set(b)`` alone.  A refusal naming a
    base-only key therefore attributes itself to a keyword nothing looked at.

    **Measured, and it cost a whole row its shape** (``adcp-client-python-10l.82``).
    ``core/audience-evidence-selection.json`` and
    ``governance/check-governance-response.json`` restate one property, ``action_binding``,
    and were blocked by one keyword, ``required`` -- and reported under ``anyOf`` and
    under ``additionalProperties``, both base-only keys that sort first.  The row was
    handed to a lane as two keyword headings and is one shape.  The three that still
    refuse here all reported ``$ref``, because ``$`` sorts before every letter and the
    base's whole content is a bare reference that :func:`_dereferenced` RESOLVES before
    anything is compared -- so the reported keyword was one :func:`_restatement` never
    reads.
    Their obstructions, measured and now reported: ``required`` for both
    ``brand/verify-brand-claim-response.json`` and
    ``brand/verify-brand-claims-response.json`` (the restatement requires two names where
    the base's target requires eight), and ``additionalProperties`` for
    ``media-buy/get-reporting-status-response.json``'s ``adcp_error`` (``false`` over the
    target's ``true``).

    **The fallback is one arm and not a guess.** :func:`_restatement` answers ``None`` at
    exactly two places: the tightness loop, which by construction leaves a failing shared
    keyword for this to find, and the arm for a base whose whole content is a ``$ref``
    this could not resolve -- where there is no shared keyword at all, the obstruction
    really is the unreadable reference, and the union reading below names it.
    """
    dc, db = _dereferenced(child, resolve), _dereferenced(base, resolve)
    c, b = _as_enum(_constraining(dc)), _as_enum(_constraining(db))
    failing = sorted(k for k in set(c) & set(b) if not _at_least_as_tight(k, c[k], b[k], resolve))
    if failing:
        return failing[0]
    return min({k for k in set(c) | set(b) if c.get(k) != b.get(k)} or {"allOf"})


def _parsed_property(declaration: Any, at: str, mod: compiler.Module) -> nodes.Node | Refusal:
    """One property DECLARATION as the node it states, at the pointer it was declared at.

    The shape guard that stood inside :func:`fields` -- "property is not a schema" -- is
    here, because a property map reaching that function is a map of NODES now and a node
    is a schema by construction.  A VERDICT: a property that is not a schema is a
    malformed document, which is a property of the document (§4).
    """
    if not isinstance(declaration, Mapping):
        return Refusal("properties", at, "property is not a schema", kind=Kind.VERDICT)
    return schema.parse(declaration, pointer=at, position=Position.PROP, source=mod.source)


#: **Which of §5's non-class targets this one IS**, for a refusal at CONJ that has to name
#: it.  The row names four -- "a scalar, an enum, a container, or a union root, whose
#: instance is one of its branches" -- and :class:`TargetKind` tells the union root from
#: the other three, so the sentence states the kind rather than asserting flatly that the
#: target "is not a class".  That assertion is false for a union root, which is a class
#: (``BranchDispatchMixin`` plus the model base), and it is the same misreading
#: ``adcp-client-python-10l.55`` found one position over in ``lower.union._inherited``.
_NOT_A_BASE: Mapping[compiler.TargetKind, str] = {
    compiler.TargetKind.UNION: "is a union root, whose instance is one of its branches and which "
    "is therefore not a class a model can extend",
    compiler.TargetKind.ANNOTATION: "is a scalar, an enumeration, a container or a root model, "
    "which declares no field set a model can inherit",
}


def _distributes(
    where: str,
    branches: compiler.TargetBranches,
    fields_declared: Collection[str],
    conj: Kind,
) -> compiler.TargetBranches | Refusal:
    """§5's DISTRIBUTION clause, and the arms that no longer stand in front of it.

    "(A | B) and C is (A and C) | (B and C), and the node is a union whose branches each
    take one of the target's branches as a base and add the node's own fields."  The
    distribution puts the node's fields on the BASE and the branch's on the branch, which
    is two classes and one instance -- so the node's statements have to be the NODE'S OWN.
    The refusal is a DEFERRAL off ``allOf``'s own cell at CONJ: what obstructs it is
    unwritten code and not anything a document did (§9's first rule).

    **A key the node and a BRANCH both declare used to refuse here and is WRITTEN**
    (``adcp-client-python-10l.76``, and §5's own clause at ``d504150d``): "A property the
    node and the target's branch BOTH declare is one field taking §2's intersection ...
    the node's declaration does not shadow the branch's."  The screen's reading of the
    defect was right -- the base's field is the one the MRO finds, so the branch's own
    declaration was shadowed and ``core/audience-evidence.json``'s three branches all
    pinned ``type: 'resource'``, which made the base's own dispatch raise "Value
    'resource' for discriminator 'type' mapped to multiple choices".  What it had wrong is
    that there was "nothing here to intersect": the branch's DECLARATION crosses the
    module boundary on :attr:`Shape.properties`, beside the symbol and the field set, so
    §2's intersection has both sides and :func:`intersected_at_a_branch` computes it with
    the same two functions every other restatement passes through.

    **2. A SECOND ARM STOOD HERE AND IS GONE, because the pairing gap it named is
    closed** (``adcp-client-python-10l.37``'s fourth fix, lifted here by
    ``adcp-client-python-10l.76``).  It refused a node carrying a field its OWN
    declaration does not state -- one a sibling conjunct or a base contributes -- on the
    ground that "``_base.applied_schema`` drops the outer conjunct siblings at a second
    cut", so the field was on the class and the schema half it is graded against did not
    reach it.  That sentence was true of the walk and is not true of it now:
    the drop is scoped to a second ``allOf`` CUT, and a ``oneOf``/``anyOf``/``then``/
    ``else`` hop moves to no other instance, so the sibling conjunct holds against the
    branch in the spelling it already has.  §8's third pairing rule followed as far as the
    pointer goes, which is what the ``not same_instance`` arm beside it already did
    through a KEY hop.

    **Measured by ABLATION rather than by reading the sentence**, which is what this arm
    cost twice over: emitted with the screen lifted, all **14 pairs of
    ``core/vendor-pricing-option.json``'s closure pass all three checks**, five of them
    distributed branch pairs.  With the ``applied_schema`` scope put back and nothing
    else changed, the same five report exactly what this arm claimed --
    ``accepts:model_refused_valid``, the class refusing an instance its document admits
    -- and the other nine still pass.  So the arm's population was one document, its
    reason was one line of the verifier, and the two are the same fact seen from both
    sides.

    The ``bases`` half of that arm is lifted on the same reason and has **population 0**:
    no node of the bundle reaches this function with a base and no restated key
    (``core/postal-area.json`` at ``/anyOf/0/allOf/0`` carries one and is claimed by arm 1
    above).  A base's fields come from a sibling ``$ref`` conjunct, which
    ``bundle.record`` inlines, so the walk conjoins them at the branch's pointer by the
    same descent -- and the first document to state one is graded rather than
    refused by a guess, which is loud in the direction §2 wants: a class refusing what
    its document accepts is never declarable, and every emitted class is drawn against
    its own document.

    **BOTH ARMS ARE GONE, each for its own measured reason, and they left by different
    merges.**  Arm 1 refused a property this node and a target branch both declare,
    because "the branch's declaration is the target's rather than this module's, so there
    is nothing here to intersect".  ``adcp-client-python-10l.74`` computes that
    intersection (``_restatement`` decides, ``_intersection`` computes, asked in both
    directions as ``declare`` already does), so the premise is false and the refusal is
    replaced by the answer §2 always gave.  Arm 2 left for the reason above.  Nothing
    screens this clause now: a node reaching it distributes, and what it distributes TO is
    graded pair by pair.

    ``core/package-signal-targeting.json`` and ``core/product-filters.json``'s
    ``/properties/signal_targeting/items`` reached neither arm and grade clean;
    ``core/vendor-pricing-option.json`` and ``core/audience-evidence.json`` each reached
    one, and both emit.
    """
    return branches


def _the_conjuncts_own_type(
    node: nodes.Base,
    conjoined: Sequence[tuple[str, compiler.Target, nodes.Base]],
    *,
    fields_declared: Collection[str],
    bases: Sequence[ir.TypeRef],
    rule_nodes: Sequence[Mapping[str, Any]],
    facts: Mapping[str, Any],
    record: Mapping[str, Any] | None = None,
) -> ir.Decided | Refusal | compiler.TargetBranches:
    """§5's ``$ref`` row at CONJ where the target is NOT a class: the node's own TYPE.

    "Where it is not -- a scalar, an enum, a container, or a union root, whose instance
    is one of its branches -- it is not a class a model can extend: the target is this
    node's own TYPE, and the other conjuncts and the ``allOf``'s siblings constrain it,
    which is §2's intersection at a node that declares no fields of its own."

    So the answer is the target's symbol as this node's type, and the clause's own last
    phrase is the whole of the screen below: the row holds **at a node that declares no
    fields of its own**.  A node declaring one is a different shape -- the instance must
    be the target AND carry those properties, and a Python type that is the target
    cannot state a property.  **WHAT THE NODE DECLARES sorts the two arms, and the
    target's KIND does not** -- a census here would say which documents reached each arm
    on the day it was taken, and this one moved twice before the reading was written down.
    The two arms are:

    * the node declares no fields -- the target is this node's own type, which is the
      clause above.  An ANNOTATION target is always here, because it has no field set to
      compose with;
    * the node declares fields -- §5's distribution clause, because a UNION root has one
      field set per branch and conjunction distributes over disjunction.

    **``facts`` IS "the ``allOf``'s siblings constrain it", read at the siblings that are
    BOUNDS** (:attr:`codegen.schema.nodes.Composition.facts`, and §5's group (a): "the
    refusals reading '*X* is not a class, so it cannot be a base' are the unimplemented
    half of that sentence").  §2 binds a constraint to the TYPE, and the type here is the
    target's symbol -- so the bound rides on the :class:`codegen.ir.Decided` beside it, in the one
    carrier ``lower.objects.fields`` already folds into :attr:`codegen.ir.TypeRef.facts` for
    every other node's constraints, and the position's own cell is what says where it
    lands: ``minItems`` at PROP is "-> on the field", ``minLength`` at PROP is
    "``min_length`` / ``max_length`` on the type".  A position with NO field of its own
    asks :func:`carried`, which refuses where ``codegen.constraints`` has no spelling for
    the shape -- so nothing is dropped at any of the nine.

    It is EXACT and owes no declaration: draft-07 holds every conjunct and every sibling
    against the same instance, so the model states the conjunction the document states.

    The two documents with a population, measured over the 1,054 portable documents:
    ``core/catalog-selection.json`` at ``/properties/query``, a ``minLength: 1`` beside a
    ``$ref`` to ``core/catalog.json#/properties/query``, and
    ``trusted-match/context-match-response.json`` at
    ``/properties/signals_by_provider/additionalProperties/properties/targeting_kvs``, a
    ``minItems: 1`` beside a local ``$ref`` to an array definition.

    **THE 4 DISTRIBUTE, and §5's ``$ref`` row says so** (53cb6100, and
    ``adcp-client-python-10l.68``) -- 2 of them all the way, and 2 as far as
    :func:`_distributes`' two screens, which name what each still waits on: "A UNION root
    beside a node that DOES declare fields
    distributes: conjunction distributes over disjunction, so ``(A | B) and C`` is
    ``(A and C) | (B and C)``, and the node is a union whose branches each take one of the
    target's branches as a base and add the node's own fields.  Each branch of a union
    root is a class declaring fields, so this is the CONJ rule above applied once per
    branch and not a second answer."  So the answer for that shape is neither a type nor a
    refusal: it is the target's BRANCHES, handed back to :func:`lower_composition`, which
    declares this node as a union base over one subclass per branch.  Every branch takes a
    TARGET BRANCH as its base and never the union base -- subclassing the base alone is
    the widening row ``.59`` measured, because §4 part 3 gives a class that inherits
    ``_branch_models`` its OWN plain schema, so ``PackageSignalTargeting
    (SignalTargetingExpression)`` would accept ``{}`` where every branch requires
    ``signal_ref``, ``value_type`` and ``value``.

    A union target with NO branch list is the one shape left here, and it refuses by name:
    the distribution needs the branches and :attr:`Target.branches` is where the declaring
    module puts them, so an empty one is a target this run did not resolve as a union base.

    **The kind every refusal here carries is the CELL's** (``docs/plan/architecture.md``
    §3, "a refusal's kind is derived from the cell and never chosen at a raise site").
    ``allOf``'s cell at CONJ is a lowering effect -- "the same rule applied to the
    conjunct's own conjuncts" -- so :func:`kind_for` answers DEFERRED, and all four raise
    sites below read it once rather than each naming a kind.  **Two of the four hand-wrote
    ``Kind.VERDICT`` and that was §9's first mistake**: a verdict minted for unwritten code
    reports clearable work as finished, and the one for a union root beside declared fields
    carried chained verdicts with it (``adcp-client-python-10l.38``).  The other two
    hand-wrote the answer the cell gives, so their reading is unchanged and now has one
    source.

    Two more screens, each for a shape §5 decides elsewhere:

    * **TWO non-class targets** would be §2's intersection of two Python types, and §2
      computes an intersection over DECLARATIONS rather than over decided types -- there
      is no slot on an :class:`codegen.ir.TypeRef` for the conjunction of two.  0 nodes
      over the population, and the two that used to reach it were the intersection asked
      of the wrong thing: ``core/targeting.json`` and ``core/targeting-input.json``
      compose two roots stating ``if``/``then`` and nothing else, so what each contributes
      is a RULE and :func:`_a_rule_the_target_states` is where §2's intersection over
      declarations reads them.
    * **A conjunct stating a RULE beside the type** is §2's "where a rule hangs", and it
      is WRITTEN: with no class above the value the rule hangs off the value's own
      annotated type, which is :attr:`codegen.ir.TypeRef.validators`, and ``lower.rules``
      is asked both of §2's questions so that nothing here decides which half a keyword
      takes.  Re-measured over the 1,054 portable documents at
      ``adcp-client-python-10l.59``: **11 of the 35 nodes** that reach this row state a
      rule beside the type -- 10 of them a ``not``, in the three shapes §5's ``not`` row
      already separates, and 1 an inline ``if``/``then`` conjunct --
      ``core/localized-creative-asset.json`` at ``/allOf/0``, beside a ``$ref`` to
      ``AssetVariant`` -- which takes the same second half as the third shape below.  The
      three shapes, as the row that wrote them measured each:

      - **6 over a ``const`` or an ``enum``** -- a ``$ref`` to an enumeration beside
        ``not: {enum: [...]}`` -- which is a ``NotValue`` on the value's own type and the
        half this row writes.  ``core/agent-notification-config.json`` and
        ``core/agent-notification-config-state.json`` (``event_types`` items),
        ``core/assets/vast-tracker-asset.json``, ``core/assets/daast-tracker-asset.json``,
        ``core/macro-resolution-capability.json`` and
        ``core/delivery-metric-aggregate.json``.
      - **2 over ``required``** -- ``core/canonical-product.json`` and
        ``core/product.json``, whose ``publisher_properties`` items state
        ``not: {"required": ["publisher_domains"]}`` beside a union root -- which §5's row
        decides as ``ForbiddenGroups``, a rule on a CLASS this node does not have.  **§2's
        clause of 2026-10-28 is what these two were waiting for** and it is not a fourth
        kind: "a value-level rule may state which KEYS the value supplied, and the three
        kinds above are not the limit ... at a position with no class above it, the value
        *is* the object, so ``ForbiddenGroups``, ``RequiredGroups`` and ``PresenceGroups``
        are admissible there as ``_runtime.ValueRule``s".  So the rule hangs on
        ``PublisherPropertySelector``, this node's own type, and
        ``lower.rules.as_the_object`` is the one reading of which of a class's rules may
        -- ``isinstance(rule, ValueRule)``, a property of the kind.  The refusal these two
        carried asked for "a value-level presence kind that section 2 does not name";
        nothing was missing but the sentence (``adcp-client-python-10l.63``).
      - **1 over another shape** -- ``core/budget-allocation.json``'s
        ``optimization_goals`` items -- which is §5's ``not`` row's own last clause,
        "nothing on the model; the schema half answers and the ceiling is named", and the
        same answer ``lower.scalars`` gives the same statement beside a scalar's own type.
    """
    conj = compiler.kind_for("allOf", Position.CONJ)
    if len(conjoined) > 1:
        return Refusal(
            "allOf",
            conjoined[1][0],
            "two conjuncts resolve to something that is not a class a model can extend -- "
            + ", ".join(f"{t.symbol} ({t.kind})" for _, t, _n in conjoined)
            + " -- so section 5's $ref row at CONJ makes each of them this node's own "
            "TYPE and the node has one type: the conjunction of two decided types is "
            "section 2's intersection, which is computed over DECLARATIONS and has no "
            "slot on an ir.TypeRef",
            kind=conj,
        )
    where, target, _reference = conjoined[0]
    symbol = target.symbol
    if fields_declared or bases:
        # **§5's DISTRIBUTION clause, and the kind of the target is what selects it.**
        # A union root is the one non-class target whose own content is a DISJUNCTION, so
        # it is the one the conjunction can be distributed over; a scalar, an enumeration
        # and a container state one thing about the instance and there is nothing to
        # distribute, which is why the sentence below still refuses those.
        if target.kind is compiler.TargetKind.UNION and target.branches is not None:
            if facts:
                # A BOUND beside a node that DISTRIBUTES.  The clause's sibling has a type
                # to constrain only where the answer IS a type; the distribution's answer
                # is a union base over one class per branch, and a ``minLength`` says
                # nothing about an instance of a class -- so the bound would be dropped,
                # which §2 forbids by silence.  0 sites over the portable population:
                # both nodes stating one compose a single non-class target and declare no
                # fields, so this is written so the first one is loud.
                return Refusal(
                    min(facts),
                    where,
                    f"this node states {sorted(facts)} beside {symbol}, a union root "
                    "section 5's $ref row DISTRIBUTES over: the distribution's answer is "
                    "one class per branch, and a bound on a string or a list says nothing "
                    "about an instance of a class, so the sibling has no type to "
                    "constrain and dropping it would lose the document's own bound",
                    kind=compiler.kind_for(min(facts), node.position),
                )
            return _distributes(where, target.branches, fields_declared, conj)
        return Refusal(
            "allOf",
            where,
            f"{symbol} {_NOT_A_BASE[target.kind]}, so section 5's $ref row at CONJ makes "
            f"it this node's own TYPE -- and that clause holds at a node declaring no "
            f"fields of its own, where this node declares {sorted(fields_declared)} and "
            f"composes {[b.path for b in bases]}: the instance must be {symbol} AND carry "
            "those properties, and a Python type that IS the target has no slot for a "
            "property",
            kind=conj,
        )
    # **§2's "Where a rule hangs", read at CONJ**: one conjunct states the TYPE and
    # another a RULE, so §2's intersection has to compose the two before either reaches
    # a :class:`codegen.ir.TypeRef` -- and with no class above the value, the half that
    # answers is "the rule hangs off the value's own annotated type as an
    # after-validator", which is :attr:`codegen.ir.TypeRef.validators`.
    #
    # **``lower.rules`` is asked BOTH of §2's questions and nothing here decides which
    # half a keyword takes**, which is that module's own rule ("one reader decides which
    # of the two a document's statement reaches and the two cannot both claim it") and
    # is why there is no reading of the ``not`` in this function: :func:`rules_at` is the
    # class half and ``on_a_value`` is the value half, and the answer is which of them
    # came back non-empty.  The deferred import is :func:`rules_at`'s own, for the cycle
    # D13 fixes.
    from codegen.lower import rules as lower_rules

    beside: dict[str, Any] = {}
    for one in rule_nodes:
        for key, stating in one.items():
            if key == "additionalProperties" and stating is True:
                # §5's ``additionalProperties`` row at CONJ: "``true`` is the identity and
                # contributes nothing".  The conjunct arm above admits no other value.
                continue
            if key in beside:
                # Two conjuncts stating one rule keyword: the merge is §2's intersection
                # of two rule statements, which no row writes -- and taking either would
                # DROP the other silently, which §2 forbids ("nothing is approximated by
                # silence").  0 sites over the portable population; written so the first
                # one is loud.
                return Refusal(
                    "allOf",
                    where,
                    f"two conjuncts state {key!r} beside {symbol}, this node's own TYPE "
                    "(section 5's $ref row at CONJ): the conjunction of two rule "
                    "statements about one value is section 2's intersection, which is "
                    "computed over DECLARATIONS, and reading either alone would drop the "
                    "other without declaring it",
                    kind=conj,
                )
            beside[key] = stating
    if beside:
        # §2's clause of 2026-10-28, which is what this position needed and the reason
        # the two documents below stopped refusing: "a value-level rule may state which
        # KEYS the value supplied, and the three kinds above are not the limit ... at a
        # position with no class above it, the value IS the object, so ForbiddenGroups,
        # RequiredGroups and PresenceGroups are admissible there as _runtime.ValueRules
        # -- 'a callable on the value, and all it is' -- without a new kind".  So a rule
        # the CLASS half wrote still hangs here, on the value's own annotated type, and
        # ``lower.rules.as_the_object`` is the one reading of which of them may: the test
        # is ``isinstance(rule, ValueRule)``, a property of the KIND, so this arm carries
        # no list of the kinds §2's clause names.
        #
        # 2 sites over the portable population, both a ``$ref`` to
        # ``core/publisher-property-selector.json`` beside
        # ``not: {"required": ["publisher_domains"]}``:
        # ``core/canonical-product.json`` and ``core/product.json``, at
        # ``/properties/publisher_properties/items/allOf/0``, each now carrying
        # ``ForbiddenGroups((('publisher_domains',),))`` on ``PublisherPropertySelector``.
        at_the_value = lower_rules.as_the_object(
            compiler.rules_at(node, *rule_nodes, position=node.position, root=record).rules
        )
        if at_the_value.declined:
            # A kind that is NOT a callable on the value: it reads the keys an instance
            # supplied through a class, so it has nowhere to live at a position with no
            # class, and §2 admits no drop by silence.  0 sites over the portable
            # population -- every rule this arm lowers is one of §2's clause's three --
            # so this is written so the first one is loud, exactly as the two-conjuncts
            # arm above is.  ``UniqueItems`` is the instructive one: it names a SIBLING
            # field's array, which is a name the VALUE supplied and not the value.
            return Refusal(
                "allOf",
                where,
                f"{symbol} is this node's own TYPE (section 5's $ref row at CONJ) and a "
                f"conjunct states {sorted(beside)} beside it, which lowers to "
                f"{', '.join(sorted(type(r).__name__ for r in at_the_value.declined))} -- "
                "a rule on a CLASS, and this node has none.  Section 2's value-level "
                "clause admits a rule on the value's own annotated type where the KIND "
                "is a callable on the value, and this one is not: it reads the keys an "
                "instance supplied through a class, so hanging it here would drop it",
                kind=conj,
            )
        # §2's SECOND half, which is the one this position takes: the rule hangs off the
        # value's own annotated type.  An empty tuple here is §5's ``not`` row's own last
        # clause -- "Any other shape -> nothing on the model; the schema half answers and
        # the ceiling is named" -- and is the same answer ``lower.scalars`` already gives
        # for the same statement beside a scalar's own type: nothing on the model states
        # ``not`` at this pointer and the document's own ``strict_validate`` is what
        # enforces it.
        #
        # The two orders are CONCATENATED and not merged, because the two halves are
        # disjoint per keyword shape and one of them is always empty: ``on_a_value``
        # reads a statement about a VALUE (a ``not`` over a ``const`` or an ``enum``, a
        # ``contains``) and ``as_the_object`` carries a statement about which KEYS
        # arrived, and the reductions in ``lower.rules`` are what split them.  Each half
        # is already a function of the document's content (P7).
        #
        # ``facts`` rides in the OTHER slot, for §2's reason rather than for symmetry: a
        # rule is a callable bound to the annotated type and a bound is a value the field
        # or the alias states, so the two have different carriers and a node may state
        # both.  :attr:`codegen.ir.Decided.constraints` is the one the walk already folds into
        # :attr:`ir.TypeRef.facts`.
        return ir.Decided(
            ir.TypeRef(
                symbol,
                local=True,
                validators=(
                    *lower_rules.on_a_value(beside, contains=beside.get("contains")),
                    *at_the_value.carried,
                ),
            ),
            dict(facts),
        )
    return ir.Decided(ir.TypeRef(symbol, local=True), dict(facts))


def intersected_at_a_branch(
    asserted: Mapping[str, list[dict]],
    declares: compiler.Shape,
    symbol: str,
    pointer: str,
    inherited_required: Collection[str],
    mod: compiler.Module,
) -> list[ir.Field] | Refusal:
    """The fields ONE branch WITH TWO BASES declares of its own: §2's intersection of
    what the node asserts with what the branch declares, at every key both state.

    §5's ``$ref`` row at CONJ: "A property the node and the target's branch BOTH declare
    is one field taking §2's intersection, exactly as the ``properties`` row at CONJ
    states it for two conjuncts -- **the node's declaration does not shadow the
    branch's**, and two ``const``\\ s intersect to the pin where they agree and to
    nothing where they differ."

    **Why the field has to be on the BRANCH and cannot be left to the two bases.**  Such
    a branch's bases are ``(the node's own class, the target)`` in that order, so the MRO
    finds the NODE's field and the branch's own declaration is shadowed -- which is the
    one defect §2's restatement rule exists to make unspellable, and which is measurable:
    before this, ``core/audience-evidence.json`` pinned ``type: 'resource'`` on all three
    branches and the base's dispatch raised "Value 'resource' for discriminator 'type'
    mapped to multiple choices".  Declaring the intersection on the branch is what beats
    both bases with the one declaration the document actually states there.

    **ONE READING FOR BOTH TWO-BASE SITES**, which is why it takes a :class:`Shape` and a
    symbol rather than a :class:`Target`: §5's distribution builds such a branch from a
    ``$ref`` CONJUNCT whose target is a union root (:func:`_distribute`), and §4's union
    row builds one from a bare ``$ref`` BRANCH of a union
    (``lower.union.lower_union``'s "§4's two bases").  The arrangement is the same at
    both -- the node's class first, the target second -- so the shadow is the same and
    the answer has to be.  Read only at the first, the second emitted
    ``media-buy/refine-proposals-response.json``'s ``/anyOf/1`` with the ROOT's
    ``status: Status | None`` where its target states ``Literal['submitted']``, required
    (``adcp-client-python-82m.23``, direction 2).

    **The decision is :func:`_restatement`'s and the value is :func:`_intersection`'s**,
    which are the same two functions every other restatement in this module passes
    through -- so a shared key at a two-base branch and a shared key at a flat base
    cannot come to disagree about what §2's intersection IS.  The answers:

    * the BRANCH's declaration NARROWS the node's -- the field is declared here, decided
      from the intersection, because the node's class is the FIRST base and its wider
      declaration is what the MRO would find;
    * the declarations agree, or the branch says nothing, AND the branch's REQUIREDNESS is
      no stronger -- no field, and the shadow is harmless because the node's field and the
      branch's are then one field.  ``type`` at ``core/audience-evidence.json`` is this
      case: the node states ``{const: resource}`` and the branch ``{type: string, const:
      resource}``;
    * they agree BUT THE BRANCH REQUIRES THE KEY AND THE INHERITED FIELD IS OPTIONAL --
      the field is declared anyway.  ``required`` is not part of a property's own
      declaration, so :func:`_restatement` cannot see it and reads such a pair as
      identical; the shadow is then NOT harmless, because the field the MRO finds carries
      the node's requiredness and the branch's is what the document states at that
      pointer.  Measured: ``task_id`` at
      ``media-buy/refine-proposals-response.json#/anyOf/1``, whose target requires it and
      whose declaration of it is the root's own plus a description, so the branch admitted
      a payload omitting it; 3 of the bundle's 145 two-base branches reach this arm, on
      ``status`` and ``task_id`` (``decline-proposals-response#/anyOf/1``,
      ``refine-proposals-response#/anyOf/1``, ``request-proposals-response#/anyOf/3``);
    * it is INCOMPATIBLE -- the caller refuses, and it must NOT drop the branch.
      :func:`_provably_empty` is what licenses a drop and its docstring says why this is
      not that question: an intersection this compiler cannot ORDER is §5's restatement
      row, and a branch dropped for one admits instances the document admits, which is a
      model narrower than its document.

    **THE NODE'S DECLARATION BEING THE NARROWER ONE IS NOT AN ARM, and the asymmetry is
    the MRO's.**  The node's class is the first base, so its field is already the one the
    branch gets and there is nothing here to rescue -- while re-deciding the key from the
    merged declaration would import whatever the TARGET states BESIDE the constraint.
    Measured: ``replayed`` at all three ``*-proposals-response#/anyOf/*`` submitted
    branches, where the root pins ``{const: true}`` and the target's envelope states
    ``{type: boolean, default: false}``, so the merged field would default to a value its
    own ``Literal[True]`` refuses and every dump of an untouched instance would state it.
    ``_distribute`` reaches this case 0 times over the portable population and the union
    row 3, so the one reading is what both get.

    ``inherited_required`` is what the FIRST base requires -- the shadowing one -- and the
    requiredness the field is decided with is the union of that with the branch's own, so
    a caller cannot pass a pair of the two that disagree.

    A key more than one view of the node asserts would need those views merged before
    this intersection, which is §2's intersection one level up and which no caller
    computes: 0 sites over the portable population, so it refuses rather than reading the
    first view and dropping the rest.
    """
    required = frozenset(inherited_required) | declares.required
    out: list[ir.Field] = []
    for key in declares.properties:
        views = asserted.get(key)
        if not views:
            continue
        if len(views) > 1:
            return Refusal(
                "properties",
                f"{pointer}/properties/{key}",
                f"{len(views)} declarations of {key!r} reach this node, and a branch with "
                f"two bases intersects ONE of them with {symbol}'s: merging them first "
                "is section 2's intersection one level up, which no row computes here",
                kind=compiler.kind_for("properties", Position.CONJ),
            )
        stated, theirs = views[0], declares.properties[key]
        # **The predicate is asked in BOTH directions, and only ONE of the two answers
        # declares a field** -- the asymmetry is the MRO's and the docstring's fourth
        # paragraph carries it.  ``_restatement`` itself is symmetric, so asking both ways
        # is still how "incompatible" is told from "the node is the tighter one".
        if _restatement(theirs, stated, mod.resolve_node):
            # **The BRANCH's declaration is the tighter one, and the field is declared
            # here.**  §2 has the field carry the intersection, which at this position the
            # branch already states -- but the two-base class's FIRST base is this node's,
            # so the node's wider declaration is what the MRO finds and the branch's
            # narrowing would be lost.  Declaring the intersection on the branch is what
            # keeps it.  Measured: ``core/postal-area.json#/anyOf/0`` declares ``system``
            # as a ``$ref`` to the whole ``postal-system`` enumeration and each of the
            # target's ten branches narrows it to that country's own members --
            # ``{"enum": ["zip", "zip_plus_four"]}`` for ``PostalCountrySystemUS`` -- so
            # without this arm every branch would carry the full vocabulary.
            intersected = _intersection(theirs, stated, mod.resolve_node)
        elif _restatement(stated, theirs, mod.resolve_node) is None:
            return Refusal(
                _disagreeing(stated, theirs),
                f"{pointer}/properties/{key}",
                f"what this node asserts about {key!r} and {symbol}'s declaration "
                "of it neither match nor narrow one another in either direction, so "
                "section 2's intersection of the two is not computable -- and a branch is "
                "DROPPED only where the intersection is PROVABLY empty (disjoint consts, "
                "enums or type words), which this is not: dropping it would refuse "
                "instances the document admits",
                kind=compiler.kind_for("properties", Position.CONJ),
            )
        elif key in declares.required and key not in inherited_required:
            # The declarations agree and the REQUIREDNESS does not: the arm above this
            # docstring's third bullet names.  The intersection is either declaration --
            # they say the same thing -- and it is the REQUIRED argument below that the
            # field exists for.
            intersected = _intersection(theirs, stated, mod.resolve_node)
        else:
            # Says the same thing, or nothing, and requires no more: the node's field and
            # the branch's are one field, so the base's shadowing the branch's loses
            # nothing.
            continue
        merged = _parsed_property(intersected, f"{pointer}/properties/{key}", mod)
        if isinstance(merged, Refusal):
            return merged
        decided = objects.fields({key: merged}, [key] if key in required else (), pointer, mod)
        if isinstance(decided, Refusal):
            return decided
        out += decided
    return out
