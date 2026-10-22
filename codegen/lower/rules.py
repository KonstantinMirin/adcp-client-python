"""D6's six keyword families: what a document says about an instance AS A WHOLE.

``oneOf``/``anyOf`` over ``required``; ``if``/``then``/``else``; ``dependencies``;
``min``/``maxProperties``; ``uniqueItems``; ``not``.  None of them has a field to live
on, so none can be a ``Field`` kwarg.  Each becomes either a frozen-dataclass
constructor in the one class-level ``_adcp_rules`` tuple that
``adcp.types._runtime.RuleBound`` reads, or -- when it is a statement about a VALUE
rather than about which keys are present -- nothing on the class at all.

**Nothing here refuses a document.**  That is D4, and it is the one judgement this
module makes, so it is stated once rather than per keyword.  The accepted set of every
emitted class is ``strict_validate``, which validates the payload against the
document's own schema and therefore refuses every one of these keywords already,
expressible as a rule or not.  A rule is NOT what makes the model as narrow as its
document; it is what makes the ``model_validate`` CONSTRUCTOR as narrow, on the subset
of statements that are about key presence.  Refusing a document for the rest would cost
the whole ``if`` population for constraints the accepted set enforces, and would buy no
narrowing anywhere.

What that trades away, named here so it is not discovered later:
``core/canvas-constraint.json``'s ``if unit == "percent" then x.maximum = 100`` gets no
rule, so ``CanvasConstraint.model_validate({"unit": "percent", "x": 101})`` builds while
``CanvasConstraint.strict_validate`` of the same payload refuses on ``maximum``.  That
pair is a committed test, so the ceiling is measured rather than claimed.

``uniqueItems`` is read and carried nowhere, for a different reason: it constrains the
MEMBERS of an array, the array lowering is step 6's row and another module's file, and a
rule no emitted class can carry is dead code no instrument can grade.  It is in
:data:`KEYWORDS` so that it does not block the lowering that will reach it, and its
instrument -- a ``harness.steps()`` step, which had never existed -- is in this step.

**The step-5 boundary, and why it is a predicate and not a precedence rule.**  A
``oneOf``/``anyOf`` whose branches are SHAPES is a union root: a base, one subclass per
branch, step 5's row.  A ``oneOf``/``anyOf`` whose every branch is ``required``-only has
no shape to subclass -- the branches declare no property at all -- so it is a class plus
a rule, which is this row.  :func:`presence_only` is that test, and
``bundle.states_an_object_rule`` is the selector built on it, so the two rows cannot
both claim one document and the unordered dispatch table has no precedence question to
answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from codegen import compiler

RUNTIME_MODULE = "adcp.types._runtime"

#: Keywords that ANNOTATE a node without constraining an instance.
#:
#: ``codegen.compiler``'s, not a second copy: D13 puts the machinery a lowering is
#: handed there, and every reader of this set can import it -- the walk
#: (``emit.decide_type``), the keyword screen (``compiler.check_keywords``), every
#: reduction below, and ``bundle.states_an_object_rule`` through
#: :func:`presence_only`.  The lane homed it HERE on the reasoning that this package
#: was the only one all three could import without a cycle, which was true of the
#: seam it was written against and is not true of D13's: ``compiler`` sits below both
#: this package and ``bundle``.  Two copies of the set would be one place for a
#: selector to claim a document its lowering cannot read.
ANNOTATIONS = compiler.ANNOTATIONS

#: Everything this module reads off an OBJECT node.  ``emit`` adds it to the handled set
#: of an object node, which is what stops a document being refused for one of them.
KEYWORDS = frozenset(
    {
        "oneOf",
        "anyOf",
        "if",
        "then",
        "else",
        "dependencies",
        "minProperties",
        "maxProperties",
        "uniqueItems",
        "not",
    }
)

#: Of those, the ones that can appear on a node with no object to carry a rule -- a
#: scalar, where a rule tuple has nowhere to live.  Measured over the 1,054 portable
#: documents: ``not`` and nothing else, and every one of those is
#: ``not: {"const": <value>}`` or ``not: {"enum": [...]}`` -- an excluded VALUE, and so
#: the schema's statement by the same reasoning as the rest of this module.
#: ``minProperties`` and ``uniqueItems`` say nothing about a scalar and do not appear on
#: one; a conditional and a combinator would, and do not.
ON_A_VALUE = frozenset({"not"})

#: The three keywords a conditional is spelled with, in the order a document writes
#: them, so the properties collected out of them are in document order too.
_CONDITIONAL = ("if", "then", "else")

#: The two combinators, and the order a rule tuple lists them in.
_COMBINATORS = ("oneOf", "anyOf")


@dataclass
class Lowered:
    """What one object node's rules come to.

    ``rules`` is the SOURCE of each constructor, in document order, which is what makes
    the emitted tuple a function of the document rather than of a dict's iteration
    (P7).  ``properties`` holds the declarations of properties the node mentions ONLY
    inside a conditional -- the field has to exist for the instance to carry the value
    the conditional talks about.  ``imports`` is ``(module, name)``, the shape
    ``emit.Module.imports`` holds.
    """

    rules: list[str] = field(default_factory=list)
    properties: dict[str, dict] = field(default_factory=dict)
    imports: set[tuple[str, str]] = field(default_factory=set)


def lower(node: dict) -> Lowered:
    """Every rule one object node states, and the properties only its conditionals name."""
    out = Lowered()
    _depends(node, out)
    _count(node, out)
    _negated(node, out)
    _combinator(node, out)
    _conditional(node, out)
    for name, declaration in conditional_properties(node).items():
        if name not in (node.get("properties") or {}):
            out.properties[name] = declaration
    if out.rules:
        out.imports.add((RUNTIME_MODULE, "Rule"))
        out.imports.add(("typing", "ClassVar"))
    return out


def block(rules: list[str]) -> str:
    """The class-body line that binds the tuple, or nothing when there is no rule.

    The FIRST line carries no indentation and the continuation lines carry their own:
    this goes through the compiler's ``class_body_lines`` channel, whose template
    indents the first line of an entry and passes the rest through verbatim (measured,
    and the reason the shape is asymmetric rather than tidy).
    """
    if not rules:
        return ""
    body = "".join(f"        {r},\n" for r in rules)
    return f"_adcp_rules: ClassVar[tuple[Rule, ...]] = (\n{body}    )"


# --------------------------------------------------------------------------- #
# the step-5 boundary, which is also the selector's per-node test
# --------------------------------------------------------------------------- #
def presence_only(node: dict) -> bool:
    """Is every combinator at ``node`` a statement about key PRESENCE?

    The one question that decides between step 5's row and this one, asked per node
    because a document can carry a combinator anywhere.  A ``oneOf``/``anyOf`` of
    ``required``-only branches is a rule; a ``oneOf``/``anyOf`` of shapes is a union
    root.  Both predicates are read off the same branches, so no document satisfies
    both and the unordered table has nothing to arbitrate.

    ``if``/``then``/``else``, ``not``, ``dependencies``, ``min``/``maxProperties`` and
    ``uniqueItems`` are not asked about: no other D2 row claims a document for one of
    them, so there is no boundary to police, and D4 is what makes an unreadable one
    safe to carry rather than refuse.
    """
    for keyword in _COMBINATORS:
        branches = node.get(keyword)
        if branches is None:
            continue
        if not isinstance(branches, list) or not branches:
            return False
        if not all(_required_only(b) for b in branches):
            return False
    return True


def _required_only(branch: Any) -> bool:
    """A branch that says nothing but which keys are present."""
    if not isinstance(branch, dict):
        return False
    return _keys(branch) == {"required"} and isinstance(branch["required"], list)


# --------------------------------------------------------------------------- #
# one reduction per keyword family
# --------------------------------------------------------------------------- #
def _depends(node: dict, out: Lowered) -> None:
    """draft-07 ``dependencies``, the list-of-names form.

    Sorted by trigger: the keyword's value is a JSON object, so document order is dict
    order, and P7 wants the emitted tuple to be a function of the document's CONTENT.
    """
    dependencies = node.get("dependencies")
    if not isinstance(dependencies, dict):
        return
    for trigger in sorted(dependencies):
        requires = dependencies[trigger]
        if not isinstance(requires, list) or not all(isinstance(r, str) for r in requires):
            continue  # the schema-valued form: a conditional, and the schema's own
        names = tuple(r for r in requires if r != trigger)
        if names:
            out.rules.append(f"Dependencies({trigger!r}, {names!r})")
            out.imports.add((RUNTIME_MODULE, "Dependencies"))


def _count(node: dict, out: Lowered) -> None:
    lo, hi = (_whole(node.get(k)) for k in ("minProperties", "maxProperties"))
    if lo is None and hi is None:
        return
    out.rules.append(f"PropertyCount(minimum={lo!r}, maximum={hi!r})")
    out.imports.add((RUNTIME_MODULE, "PropertyCount"))


def _negated(node: dict, out: Lowered) -> None:
    groups = _required_groups(node.get("not"))
    if not groups:
        return
    out.rules.append(f"ForbiddenGroups({tuple(groups)!r})")
    out.imports.add((RUNTIME_MODULE, "ForbiddenGroups"))


def _combinator(node: dict, out: Lowered) -> None:
    """``oneOf`` / ``anyOf`` over ``required``: which groups of keys may be present.

    Only the all-``required``-only form, which is :func:`presence_only`'s test and the
    step-5 boundary.  A combinator of shapes is a union root and this writes nothing for
    it -- the document is step 5's and the selector does not claim it.
    """
    for keyword in _COMBINATORS:
        branches = node.get(keyword)
        if not isinstance(branches, list) or not branches:
            continue
        if not all(_required_only(b) for b in branches):
            continue
        groups = tuple(
            tuple(n for n in b["required"] if isinstance(n, str))
            for b in branches
            if isinstance(b, dict)
        )
        if not any(groups):
            continue
        out.rules.append(f"RequiredGroups({groups!r}, {keyword!r})")
        out.imports.add((RUNTIME_MODULE, "RequiredGroups"))


def _conditional(node: dict, out: Lowered) -> None:
    when = _clauses(node.get("if"))
    if when is None:
        return
    spelled = "(" + "".join(f"Match({c!r}, {p!r}, {a!r})," for c, p, a in when) + ")"
    for keyword, kind in (("then", "ConditionalRequired"), ("else", "NegatedConditional")):
        branch = _branch(node.get(keyword))
        if branch is None or not any(branch):
            continue
        require, forbid = branch
        out.rules.append(f"{kind}({spelled}, require={require!r}, forbid={forbid!r})")
        out.imports.add((RUNTIME_MODULE, kind))
        out.imports.add((RUNTIME_MODULE, "Match"))


def conditional_properties(node: dict) -> dict[str, dict]:
    """Every property declared inside this node's conditionals, in document order.

    A property the node declares only under ``then`` or ``else`` still arrives on the
    wire, so the class needs an optional field to carry it, and the declaration there is
    what types it.  ``if`` is walked too, because a key an ``if`` tests on is a key the
    instance may carry.

    Declared twice and DIFFERENTLY -- two branches narrowing the same key -- the key
    gets the annotations only, which lowers to ``Any``: picking one branch's type would
    make the field refuse an instance the other branch admits, which is a failure of the
    accepts check for a model that must be at least as wide as its document.
    """
    found: dict[str, list[dict]] = {}

    def walk(sub: Any) -> None:
        if not isinstance(sub, dict):
            return
        for name, declaration in (sub.get("properties") or {}).items():
            if isinstance(declaration, dict):
                found.setdefault(name, []).append(declaration)
        for keyword in _CONDITIONAL:
            walk(sub.get(keyword))

    for keyword in _CONDITIONAL:
        walk(node.get(keyword))
    return {
        name: (
            declarations[0]
            if all(d == declarations[0] for d in declarations)
            else {k: v for k, v in declarations[0].items() if k in ANNOTATIONS}
        )
        for name, declarations in found.items()
    }


# --------------------------------------------------------------------------- #
# the readings, each of which answers None for "not about presence"
# --------------------------------------------------------------------------- #
def _whole(value: Any) -> int | None:
    """``value`` if it is a JSON integer, which ``True`` is not."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _keys(sub: dict) -> set[str]:
    """The keys of ``sub`` that SAY something about an instance."""
    return {k for k in sub if k not in ANNOTATIONS and not k.startswith("x-")}


def _required_groups(sub: Any) -> list[tuple[str, ...]] | None:
    """``sub`` as a set of key groups, or ``None`` if it says anything else.

    A group is a set of names whose simultaneous presence satisfies ``sub``, so an
    enclosing ``not`` forbids it.  ``anyOf`` of branches is the union of their groups
    (any branch satisfied satisfies ``sub``); ``allOf`` of single-group branches is one
    group, the union of their names.  ``oneOf`` is deliberately absent: its negation is
    "not exactly one", which no list of forbidden groups expresses.
    """
    if not isinstance(sub, dict):
        return None
    keys = _keys(sub)
    if keys == {"required"} and isinstance(sub["required"], list):
        names = tuple(n for n in sub["required"] if isinstance(n, str))
        return [names] if names else None
    if keys == {"anyOf"} and isinstance(sub["anyOf"], list):
        out: list[tuple[str, ...]] = []
        for branch in sub["anyOf"]:
            groups = _required_groups(branch)
            if groups is None:
                return None
            out.extend(groups)
        return out or None
    if keys == {"allOf"} and isinstance(sub["allOf"], list):
        merged: list[str] = []
        for branch in sub["allOf"]:
            groups = _required_groups(branch)
            if groups is None or len(groups) != 1:
                return None
            merged.extend(groups[0])
        return [tuple(merged)] if merged else None
    return None


def _clauses(sub: Any) -> list[tuple[str, bool, tuple[Any, ...] | None]] | None:
    """An ``if`` as ``(key, present, allowed values)`` clauses, or ``None``.

    Every clause must be about a key the ``if`` also REQUIRES.  A ``properties`` entry
    for a key the ``if`` does not require is satisfied by the key being ABSENT as well
    as by its value matching, and a clause cannot say "absent or one of these" -- so
    such an ``if`` reduces to nothing rather than to something stronger than the
    document.
    """
    if not isinstance(sub, dict):
        return None
    keys = _keys(sub)
    if sub.get("type") not in (None, "object"):
        return None
    if not keys <= {"required", "properties", "type"} or not isinstance(sub.get("required"), list):
        return None
    required = [n for n in sub["required"] if isinstance(n, str)]
    properties = sub.get("properties") or {}
    if not isinstance(properties, dict) or not set(properties) <= set(required):
        return None
    out = []
    for name in required:
        declaration = properties.get(name)
        allowed = None
        if isinstance(declaration, dict):
            allowed = _values(declaration)
            if allowed is None:
                return None
        out.append((name, True, allowed))
    return out or None


def _values(sub: dict) -> tuple[Any, ...] | None:
    """The values a property declaration admits, as a tuple, or ``None``.

    ``()`` is not a possible answer and ``None`` means "more than a listed set", which
    is why this cannot return an empty tuple for an unreadable declaration.  A bare
    ``{"type": ...}`` admits every value of that type, so it is ``None`` too: a clause
    testing it would hold for exactly the values the document's ``if`` holds for, which
    is the same statement, but there is nothing to list.
    """
    keys = _keys(sub)
    if "const" in keys and keys <= {"const", "type"}:
        return (sub["const"],)
    if "enum" in keys and keys <= {"enum", "type"} and isinstance(sub["enum"], list):
        return tuple(sub["enum"]) or None
    return None


def _branch(sub: Any) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """A ``then``/``else`` as ``(must be present, must be absent)``, or ``None``.

    A ``properties`` in the branch is ignored rather than refused: it narrows a VALUE,
    which is the schema's statement and not a rule's (see the module docstring), and its
    declarations are collected separately by :func:`conditional_properties`.  A ``not``
    is read only when it forbids ONE name -- ``not: {"required": [a, b]}`` forbids the
    PAIR, and a list of individually-absent keys would be stronger than the document.
    """
    if not isinstance(sub, dict):
        return None
    require = tuple(n for n in (sub.get("required") or []) if isinstance(n, str))
    forbid: tuple[str, ...] = ()
    groups = _required_groups(sub.get("not"))
    if groups and all(len(g) == 1 for g in groups):
        forbid = tuple(g[0] for g in groups)
    return require, forbid
