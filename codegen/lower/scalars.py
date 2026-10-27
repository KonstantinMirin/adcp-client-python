"""§5's scalar rows: one ``type`` word, ``null``, and a node with no kind at all.

Three of ``docs/plan/architecture.md`` §5's twelve arms, and the three that were the
tail of ``emit._decide`` rather than a lowering of their own: a SCALAR carries its
constraint facts in the document's spelling and its ``format``, a ``null`` node carries
nothing, and a TYPELESS node is "a ``not`` over a value, or nothing".

**``format`` selects a type and the alias module names a constrained one, so this module
owns both tables.**  They were ``emit``'s because the scalar tail was, and §14 step 5
moves a handler to ``lower/<kind>.py``; nothing about either changed in the move, and the
reasoning each carries is the measurement that put it there.

:func:`name_the_constraint` is read by ``compiler.carried`` for the three positions with
no field of their own -- an array's ELEM, a mapping's MAPV and a union BRANCH -- which is
why it is here beside the resolution it shares rather than in the module that asks.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any

from codegen import compiler, ir
from codegen import constraints as constraints_module
from codegen.keywords import Position
from codegen.compiler import SCALAR, Decided, Module, check_keywords
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes

#: **``format`` SELECTS A TYPE, and the schema half asserts it** (D5).
#:
#: ``format: date-time`` references RFC 3339, where the time offset is MANDATORY,
#: so the document itself requires a timezone and ``AwareDatetime`` states the
#: document's own rule rather than a stricter one.  That reading only holds
#: because the schema half now PASSES A FORMAT CHECKER (``_base._refuse``,
#: ``harness._validating``): a draft-07 ``format`` that nothing checks asserts
#: nothing, and a type derived from one would be narrower than its document as
#: graded -- which is the state a previous lane correctly backed these types out
#: of, and the apparent disagreement was the grader rather than the types.
#: Measured both ways on the same checker: of six RFC 3339 edge values --
#: offsetless, lowercase ``t``/``z``, a leap second, a ``+05:30`` offset,
#: nanosecond precision -- ``AwareDatetime`` and ``rfc3339-validator`` agree on
#: all six, including refusing the leap second.
#:
#: A row exists only where the draft's own checker can DECIDE the format, which
#: :func:`asserted_formats` reads off the document's declared draft.  So removing
#: ``rfc3339-validator`` from the dependencies does not leave an unasserted
#: narrowing behind: the row stops selecting and the node falls back to its own
#: scalar type with the format as an annotation.
#:
#: **``uri`` SELECTS ITS TYPE FROM THE NODE, which is why this table holds
#: choosers rather than paths.**  D5 makes a ``format: uri`` field's type follow the
#: DOCUMENT'S OWN PATTERN -- ``AdCPUrl`` where the document restricts the scheme to
#: https, ``HttpUrl`` everywhere else -- so the answer is a function of the node and
#: not of the format alone.  ``date-time`` and ``date`` ignore their node, and they
#: are expressed as choosers too rather than as a second shape beside one: a table
#: with two kinds of value is a table every reader has to case-split.
#:
#: The former entry read ``uri`` -> ``AdCPUrl`` and it was WRONG, measured. D5 now
#: records the whole of it; the short form is below.
#:
#: **``AdCPUrl`` everywhere narrowed the SDK below the pinned spec.**  ``format: uri``
#: references RFC 3986, which admits every scheme, so a bare
#: ``{"type": "string", "format": "uri"}`` admits ``https://``, ``http://``, ``urn:``
#: and ``file:///`` alike -- and ``AdCPUrl`` refuses three of the four. Measured at
#: **228 of the bundle's 300 ``uri`` positions, in 128 of 160 documents**, and at
#: **26 of 27** positions in documents the emitter emits. End to end on a shipped
#: class: ``core/placement-evidence.json#/properties/url`` states only the bare pair,
#: the document admits ``{"url": "http://x.example/p"}``, and
#: ``PlacementEvidence.strict_validate`` raised ``URL scheme should be 'https'``.
#:
#: **No check saw it**, which is why it stood: ``allowed_schemes`` has no rendering in
#: pydantic's schema output, so the comparison has no keyword to compare; ``format``
#: is not a step keyword, so ``steps()`` returns ``[]``; and
#: ``hypothesis_jsonschema``'s ``uri`` strategy drew ``https`` in 200 of 200
#: derandomized examples. That instrument gap is ``salesagent-j3k2l.10``'s, not this
#: module's.
#:
#: **``HttpUrl``'s two ceilings are accepted deliberately and named at D5**: it still
#: refuses ``urn:`` and ``file:``, so 227 of 300 positions stay narrower than their
#: document, and it renders ``maxLength: 2083`` and ``minLength: 1`` that no document
#: states -- which ``harness.compare_schema`` admits with one hand-written row per
#: fact, each naming itself.
#:
#: What follows is the reasoning for the type being ours rather than pydantic's at
#: the https branch, which the amendment did not change.  D5 admits
#: a STANDARD type only when it states the document's own facts AND accepts the
#: document's own set, and no pydantic URL type passes: ``AnyUrl`` and
#: ``AnyHttpUrl`` both render a ``minLength: 1`` no ``format: uri`` document
#: states, ``HttpUrl`` adds a ``maxLength: 2083`` as well, and all three admit
#: ``http://``.  So the type is one we emit --
#: ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]``, declared once
#: in ``codegen.constraints`` -- and the ``minLength: 1`` it renders is admitted
#: by a comparison row of its own kind (``harness.compare_schema``) rather than
#: hidden with a ``WithJsonSchema``, which would make the model's rendered schema
#: a claim nobody graded.
#:
#: The document's own ``pattern`` stays with the SCHEMA half: the bundle states
#: eight distinct patterns across 73 of its 300 ``uri`` uses and
#: ``UrlConstraints`` expresses only the first (``^https://``, at 47 sites), so
#: letting the field type vary by how strict a schema author happened to be is
#: what this avoids.  ``strict_validate`` applies the document before the
#: constructor runs, so nothing widens.
#:
#: Each value is ``(node) -> dotted path``.  ``date-time`` and ``date`` ignore the
#: node; ``uri`` is ``constraints.url_type``, which reads the document's own
#: ``pattern``.
FORMAT_TYPES: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "date-time": lambda node: "pydantic.AwareDatetime",
    "date": lambda node: "datetime.date",
    "uri": constraints_module.url_type,
}

#: The formats whose selected type is a URL type, which is what the one refusal
#: below is gated on.  DERIVED by asking each chooser rather than listed: a format
#: whose chooser answers inside the alias module's namespace is a URL format, and a
#: second list to keep in step would be a second place for this to drift.
URL_FORMATS = frozenset(
    fmt
    for fmt, choose in FORMAT_TYPES.items()
    if choose({}).startswith(f"{constraints_module.MODULE}.")
)



def _named_alias(
    path: str,
    kind: str,
    constraints: Mapping[str, Any],
    mod: compiler.Module,
    fmt: str | None = None,
) -> ir.TypeRef:
    """One resolved shape's :class:`ir.TypeRef`, with the alias recorded.

    The record and the type go together or they do not go: an alias referenced and not
    recorded is an ``ImportError`` in the written tree, and one recorded and not
    referenced is a line in a public module nothing reads.  Shared by the two callers
    that resolve a shape -- the scalar tail of :func:`decide_type` and
    :func:`name_the_constraint` -- so there is one place that pairs them.

    Only an alias in ``adcp.types.constraints`` is recorded: rung 2 resolves to a
    pydantic name, which that module does not declare and ``Type``'s dotted path
    imports directly.

    A CONTAINER alias is generic, so its arguments come with it
    (``NonEmptyList[MediaBuyStatus]``): ``of`` carries the decided types and
    ``ir.TypeRef``'s ``alias`` container writes the subscript.
    """
    if path.startswith(f"{constraints_module.MODULE}."):
        constraints_module.record(mod.aliases, path.rsplit(".", 1)[1], kind, constraints, format=fmt)
    return ir.TypeRef(path)


def name_the_constraint(decided: Decided, mod: compiler.Module) -> ir.TypeRef | None:
    """Section 2's NAMED carrier for a decided node whose position has no field.

    ``compiler.carried`` asks this at the three positions that cannot hold a fact on a
    field of their own -- an array's ELEM, a mapping's MAPV and a union BRANCH -- and
    refuses when it answers ``None``.  It is HERE, and ``compiler.carried`` defers the
    import of it to call time, because the names are ``codegen.constraints``'s and
    that module imports ``compiler``: a module-level import from ``compiler`` would
    close that cycle.  It used to be carried on :class:`compiler.Module` as a callable
    for a second reason as well -- ``codegen.emit`` was unnameable while ``runpy``
    bound it twice -- and ``codegen/__main__.py`` retired that half.

    **It does not re-read the node, and that is deliberate.**  Everything it needs is
    on the :class:`Decided` the walk already produced -- the scalar's own type word is
    recoverable from :data:`SCALAR`, a container names itself in ``Type.container`` --
    so there is no second reading of a node's constraints to disagree with
    :func:`decide_type`'s.

    Two shapes reach it, and they are the two that can arrive with a fact still on
    them:

    * a bare SCALAR carrying a ``format`` no type was selected for.  Constraints
      alone never arrive here, because :func:`decide_type` has already resolved a
      spellable scalar shape to an alias -- what arrives with constraints on it is a
      shape the alias module declined, and the answer is the same ``None``.
    * a CONTAINER carrying its own bound: ``minItems``/``maxItems`` on a list,
      ``minProperties``/``maxProperties`` on a mapping.  The alias is GENERIC and the
      container's own contents are its arguments, which is what lets it be named at
      all (``constraints.CONTAINER``).
    """
    kind = _CONTAINER_WORD.get(decided.type.container) or _SCALAR_WORD.get(decided.type.path)
    if kind is None:
        return None
    path = constraints_module.resolve(kind, decided.constraints, format=decided.format)
    if path is None:
        return None
    inner = _named_alias(path, kind, decided.constraints, mod, fmt=decided.format)
    if kind not in constraints_module.CONTAINER:
        return inner
    args = decided.type.of if decided.type.key is None else (decided.type.key, *decided.type.of)
    return ir.TypeRef(path=inner.path, container="alias", of=args)


#: The document's own type word for each container ``Type.container`` names, and for
#: each scalar path :data:`SCALAR` maps to.  Both are inversions and both are written
#: here rather than at the call site, so the two spellings of a type have ONE mapping
#: between them (``constraints.SCALAR_PATH`` is the same arrangement one module over).
#: ``union`` is absent: a union is not a node's own type word, so a union carrying a
#: constraint has no shape for this module to name and refuses.
_CONTAINER_WORD = {"list": "array", "dict": "object"}
_SCALAR_WORD = {path: word for word, path in SCALAR.items()}




# --------------------------------------------------------------------------- #
# the three rows
# --------------------------------------------------------------------------- #
def lower(node: nodes.Scalar, mod: Module) -> Decided | Refusal:
    """One scalar type word: the constraint facts on the TYPE, and the format.

    §2: **constraints bind to the type, not the field.**  A constrained scalar is
    resolved to a NAME -- a standard pydantic type where one says exactly this, an alias
    in ``adcp.types.constraints`` otherwise -- so the same shape in two documents is the
    same symbol with no census over the run, and a bound reached through a list, a mapping
    value or a union branch has somewhere to live.

    ``node.facts`` is the classification ``ir.FACTS`` was: a key whose cell LOWERS at this
    node's position, that holds no subschema, and that this node's own TYPE WORD can carry
    (``schema.parse.ARM``).  The parser states it once, from the table, at the position --
    which is what §11 asks for and what no column of §3 could answer on its own.
    """
    word = node.word
    if word not in SCALAR:
        return Refusal("type", node.pointer, f"unknown type {word!r}", kind=Kind.VERDICT)
    # ``rules.ON_A_VALUE`` is the step-7 keyword that can land on a node with no object to
    # carry a rule tuple: a ``not`` over a ``const`` or an ``enum`` is an excluded VALUE.
    # **It is ENFORCED now and no longer only carried**, which is §5's ``not`` row -- "Over
    # a ``const`` or ``enum`` → a ``NotValue`` after-validator on the value's own annotated
    # type" -- and §2's "where no class sits above the value": there is no class-level kind
    # for a statement about a VALUE, so this is the only half of §2 the shape can take, at
    # every position.  :class:`adcp.types._runtime.ForbiddenGroups` is the keyword's other
    # shape and reads ``not`` over ``required``.
    #
    # Nothing is RENDERED for it: ``not``'s cell is ``rendered=False``, so §8 compares no
    # fact here and the validator narrows the CONSTRUCTOR alone, which is the direction D4
    # permits.  ``strict_validate`` enforced it from the document all along.
    from codegen.lower import rules as lower_rules

    refused = check_keywords(
        node, {"type", "format", *node.facts, *lower_rules.ON_A_VALUE}, mod=mod
    )
    if refused is not None:
        return refused
    bound = lower_rules.on_a_value(node.rules)
    constraints = dict(node.facts)
    fmt = node.format
    # A format SELECTS a type where one is named for it and the document's own draft can
    # decide it (D5, and the comment above FORMAT_TYPES).  The type then states the format
    # in its own rendered schema, so ``format`` is left unset here and the compiler adds no
    # annotation -- which is what keeps the fact in exactly one place.  Where no type is
    # selected the format rides as an annotation on the node's own scalar type, and the
    # schema comparison grades it there.
    # **A ``uri`` beside another string constraint KEEPS BOTH HALVES, and the row's own
    # fallback is what keeps them** (§14 step 9, and §5's group (a)): "The ``format`` row
    # refuses a ``uri`` beside a string constraint because a URL type carries none.  The
    # row's own fallback already answers it: the type is the constrained ``str`` and the
    # ``format`` rides as ``json_schema_extra={"format": "uri"}``.  Both facts are kept
    # and neither half narrows; what is given up is the URL type's parsing, which is not
    # an acceptance fact."
    #
    # So the URL type is not SELECTED here and the two lines below -- the row's second
    # and third choices, which every other unselected format already takes -- answer: a
    # named alias in ``adcp.types.constraints`` for the bound, with ``format`` set, which
    # ``render._field`` puts in ``json_schema_extra`` where §8 grades it.  The refusal
    # this replaced said the keyword "would go missing or differ ungraded", and that was
    # true of the URL type it was about: pydantic refuses to apply a string constraint to
    # one, so the bound had nowhere to go.  It has somewhere to go on a ``str``.
    #
    # ``pattern`` is NOT in this set and the URL type still wins over it, which is §5's
    # ``pattern`` row: "On ``format: uri`` -> selects the type instead, and the pattern
    # stays with the schema half."  That is a different trade from this one -- there the
    # document's two facts are a type and a regex and the row keeps the type; here they
    # are a bound and a format and the fallback keeps both.
    if (
        fmt is not None
        and fmt in mod.asserted
        and fmt in FORMAT_TYPES
        and (fmt not in URL_FORMATS or selects_a_url_type(fmt, constraints))
    ):
        selected = FORMAT_TYPES[fmt](node.facts)
        if fmt in URL_FORMATS:
            return Decided(ir.TypeRef(selected, validators=bound))
        return Decided(ir.TypeRef(selected, validators=bound), constraints)
    path = constraints_module.resolve(word, constraints)
    if path is not None:
        # **The rule goes on THIS SITE's type and never on the shared alias.**  An alias
        # in ``adcp.types.constraints`` names a CONSTRAINT and is reached by every node
        # stating that constraint, so a validator written into its declaration would
        # narrow every other site -- which is the one direction D4 does not permit.  The
        # alias is the inner type and the ``Annotated`` around it is this node's own.
        return Decided(
            replace(_named_alias(path, word, constraints, mod), validators=bound), format=fmt
        )
    return Decided(ir.TypeRef(SCALAR[word], validators=bound), constraints, format=fmt)


def selects_a_url_type(fmt: str | None, constraints: Mapping[str, Any]) -> bool:
    """Does a ``uri`` format select a URL TYPE here, or take the row's own fallback?

    §5's ``format`` row names a URL type for ``uri``; §5's group (a) says what happens
    where the node states another string constraint beside it: "the type is the
    constrained ``str`` and the ``format`` rides as
    ``json_schema_extra={"format": "uri"}``.  Both facts are kept and neither half
    narrows; what is given up is the URL type's parsing, which is not an acceptance
    fact."  pydantic refuses to apply a string constraint to a URL type at all, so the
    two readings are exclusive and this is the one function that says which fires.

    ``pattern`` is NOT a constraint for this question, and that is §5's ``pattern`` row
    rather than an exception here: "On ``format: uri`` → selects the type instead, and
    the pattern stays with the schema half."  There the document's two facts are a type
    and a regex and the row keeps the type; here they are a bound and a format and the
    fallback keeps both.

    **Declared at module scope because a CHECK asks it too.**  ``tests/test_emit.py``'s
    format check derives the type a format selects from :data:`FORMAT_TYPES` and asserts
    the module imports it, so it needs the same answer to "is a type selected here" --
    and a second reading of that is how a check comes to grade a document against a
    compiler nobody runs.  One function, two readers.
    """
    return (
        fmt is not None
        and fmt in URL_FORMATS
        and not sorted(set(constraints) - {"pattern"})
    )


def null(node: nodes.Null, mod: Module) -> Decided | Refusal:
    """``type: null``: nothing, which is ``None``."""
    refused = check_keywords(node, {"type"}, mod=mod)
    if refused is not None:
        return refused
    return Decided(ir.TypeRef("None"))


def typeless(node: nodes.Typeless, mod: Module) -> Decided | Refusal:
    """No type and no kind keyword: a ``not`` over a value, or nothing.

    **At ROOT the answer is §4's third root shape, and both of the refusals that stood
    here are gone** (§14 step 9).  §4's table's last row is "a root stating no schema
    keyword at all -> a permissive root model", and §5's group (a) gives a root stating
    only ``if``/``then`` the same shape with the conditional as a rule.  So one arm
    answers both, which is what the two shapes always were: a root with no kind keyword,
    once with a rule to carry and once without.
    """
    from codegen import bundle
    from codegen.lower import rules as lower_rules

    if node.position is Position.ROOT:
        # **§4: "a root stating no schema keyword at all -> a permissive root model",
        # and it is FAITHFUL rather than wide.**  §4's own reasoning: "Read by its own
        # declared draft it is the empty schema: draft-07 ignores an unknown key, so the
        # document admits every instance, and a permissive root model is faithful to it
        # rather than wide."  Measured on ``core/asset-group-vocabulary.json``, which
        # declares draft-07 and whose keys are not schema keywords:
        # ``Draft7Validator`` accepts ``42``, ``"x"``, ``null``, an object and an array,
        # so ``root: Any`` is exactly as wide as the document.  §5(b)'s row for this was
        # MOVED to group (a) on 2026-10-26 for that reason, and it therefore carries NO
        # approximation -- "a permissive root model over a document that constrains
        # nothing DROPS nothing, so there is no fact to declare", and §8's
        # *over-declared* outcome would report one.
        #
        # **And a root stating only ``if``/``then`` is the same shape with a RULE.**
        # §5's group (a): "The conditional is a rule, and §2 hangs a rule with no class
        # above it on the value's own type: the root is a permissive root model carrying
        # ``ConditionalRequired``.  The document states a conditional and nothing else,
        # and so does the model."  The conditional is read by the same
        # ``lower.rules.lower`` every class's is, off the rule sources the parser
        # classified from the table -- so there is no second reading of what an ``if``
        # compiles to, and the root model's tuple carries it exactly as a class's would.
        #
        # The upstream issue a registry document earns -- the schema should say more
        # than it does -- stands and is the issue list's, not a declaration's (§5(b)).
        stated = compiler.rules_at(node, position=Position.ROOT)
        refused = check_keywords(node, {*stated.screen, *lower_rules.ON_A_VALUE}, mod=mod)
        if refused is not None:
            return refused
        return compiler.declare_root_model(
            mod,
            node.pointer,
            node,
            # §4's "permissive": the empty schema admits every instance, and ``Any`` is
            # that set -- the same reading §4's typeless row gives a typeless node at
            # every other position, which the last line of this function returns.
            ir.TypeRef("typing.Any"),
            rules=stated.rules,
        )
    # ``rules.ON_A_VALUE`` for :func:`lower`'s reason, which does not depend on the type
    # word being present: a ``not`` is a statement about which VALUES the node admits, so
    # D4 leaves it to the schema half, and a node with no ``type`` has no less of a value
    # than a node with one.
    # **The refusal that stood here is DELETED, and it was dead code.**  It read
    # ``set(node) & set(ir.FACTS)`` and answered "a typeless node carrying a constraint
    # has nothing to apply it to", as a VERDICT -- but every one of those eleven keywords
    # has a cell that LOWERS at all eight positions the walk decides a node at, so the
    # screen above refuses it first, by name, as the DEFERRAL ``kind_for`` reads off the
    # cell.  The one position whose cells carry nothing for seven of them is RULE, and a
    # node at RULE is never handed to the dispatch (§4).  Measured over the table at every
    # position, so the deletion moves no document and loses no refusal.
    refused = check_keywords(node, {*lower_rules.ON_A_VALUE}, mod=mod)
    if refused is not None:
        return refused
    # §4's typeless row, with §5's ``not`` row on it where the document states one: a
    # typeless node is ``Any``, and ``Annotated[Any, AfterValidator(NotValue(…)))]`` is
    # ``Any`` minus the values the document excludes, which is the document's own reading
    # -- ``{"not": {"const": v}}`` admits every instance but ``v``.
    return Decided(ir.TypeRef("typing.Any", validators=lower_rules.on_a_value(node.rules)))
