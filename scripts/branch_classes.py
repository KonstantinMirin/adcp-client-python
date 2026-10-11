"""One class per arm, for a flat root whose arms partition.

``scripts/schema_constraints.py`` reads a root's constraint content into
``Arm`` records and proves whether the arms partition the document space.
Where they do, the arms are not a rule over one class -- they are distinct
types, and the generator's flattening is what turned them into a rule. This
module renders that.

The arms are ONE type with different requiredness, not several types, and the
emission says so: a shared base per split root -- ``<Root>Shape`` -- carries the
root's own properties, each arm subclasses it and restates only what it changes, and the
root's public name becomes a union over the arms.

Measured over the eleven roots this splits, counting the properties the base
declares against the names any arm constrains at all (requires, forbids, or
pins): 31/5 on ``create-media-buy-request``, 21/8 on
``list-account-changes-response``, 17/2 on ``creative-asset``, down to 2/2 on
``webhook-challenge-response``. No root's base is empty, and no arm constrains
more than 7 of its root's properties -- the arms differ in which fields they
require and which they forbid, not in what the fields are. So none of these
roots is a union of unrelated classes, and a union of unrelated classes would
also have no base to subclass, which is what the two generated classes that
subclass a split root need.

What that makes unconstructible, and why it is a different claim from a check:

* A field an arm forbids is typed ``None`` on that arm, so
  ``CreateMediaBuyRequestCommittedProposalExecution(packages=[...])`` is a type
  error before anything runs. It is declared rather than omitted because the
  base declares it: omitting it on the subclass would inherit the base's
  permissive annotation.
* An arm's required field is required on that arm's class, so omitting it is a
  missing argument rather than a validator's refusal.

What stays a check, named rather than implied: everything in an arm's condition
that is not requiredness or absence -- a const one level down, an overlay on an
array's items, a value bound. Those are compiled onto the arm's own class by
``scripts/compile_conditions.py``, so the refusal still arrives from the class
the caller named, but it arrives at validation rather than at type-check time.

Nothing here invents an identifier. Arm names come from
``scripts/union_arm_names.py``'s rungs over the same ``Arm`` records, and the
shared base is the root's name plus ``Shape``.

The base is PUBLIC, and its visibility FOLLOWS its root's: a shape is exported
exactly when some public name resolves to the union over its arms, which is
five of the eleven today. ``adcp.types`` never exported the other six roots, so
a consumer cannot name those roots either. ``tests/test_branch_classes.py``
asserts that as a set equality in both directions, which is how two errors in a
hand-picked export list were found.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

try:
    from compile_conditions import (
        ROOT_CONSTRAINT_VALIDATOR,
        compile_condition,
        schema_keyword_raise,
    )
    from schema_constraints import (
        AllOf,
        AnyOf,
        Cond,
        Not,
        PropSatisfies,
        Restated,
        RootConstraints,
        Supplied,
        Undeclarable,
        ValueConst,
        ValueType,
        arm_conditions,
    )
    from union_arm_names import branch_class_names
except ModuleNotFoundError:  # Imported as ``scripts.branch_classes`` in tests.
    from scripts.compile_conditions import (  # type: ignore[assignment]
        ROOT_CONSTRAINT_VALIDATOR,
        compile_condition,
        schema_keyword_raise,
    )
    from scripts.schema_constraints import (  # type: ignore[assignment]
        AllOf,
        AnyOf,
        Cond,
        Not,
        PropSatisfies,
        Restated,
        RootConstraints,
        Supplied,
        Undeclarable,
        ValueConst,
        ValueType,
        arm_conditions,
    )
    from scripts.union_arm_names import branch_class_names  # type: ignore[assignment]

__all__ = [
    "BranchPlan",
    "plan_branches",
    "render_absence_hook",
    "repoint_subclasses_of",
    "split_into_branch_classes",
]


@dataclass(frozen=True)
class BranchPlan:
    """What one arm becomes: a field set, a requiredness, and what is left over."""

    name: str
    title: str | None
    pointer: str
    absent: frozenset[str]
    """Names this arm forbids whose position the schema does NOT permit null at."""

    absent_nullable: frozenset[str]
    """Names it forbids at a position where a null survives to the document."""

    required: frozenset[str]
    literals: dict[str, Any]
    residual: Cond


def _conjunction(operands: list[Cond]) -> Cond:
    """The conjunction of what is left, without a one-element ``AllOf``."""
    if not operands:
        return Restated("arm")
    return operands[0] if len(operands) == 1 else AllOf(tuple(operands))


def _conjuncts(condition: Cond) -> list[Cond]:
    """Flatten a conjunction so each leaf can be read on its own."""
    if isinstance(condition, AllOf):
        return [leaf for operand in condition.operands for leaf in _conjuncts(operand)]
    return [condition]


def _absent_names(leaf: Cond) -> tuple[Supplied, ...] | None:
    """The names a leaf forbids, or ``None`` when it forbids nothing.

    Two spellings, both in the bundle: ``not: {required: [x]}`` for one name and
    ``not: {anyOf: [{required: [x]}, ...]}`` for several. Both say the document
    may not carry the name, which on a class is a field typed ``None``.

    The ``Supplied`` records come back rather than bare names, because each
    carries whether the schema permits null at that position -- and that decides
    what "carry" means. Where null is forbidden the client drops a null-valued
    key, so only a non-null value is carried; where it is permitted, presence is.
    """
    if not isinstance(leaf, Not):
        return None
    inner = leaf.operand
    if isinstance(inner, Supplied):
        return (inner,)
    if isinstance(inner, AnyOf) and all(
        isinstance(operand, Supplied) for operand in inner.operands
    ):
        return tuple(inner.operands)  # type: ignore[arg-type]
    if isinstance(inner, AllOf) and all(
        isinstance(operand, Supplied) for operand in inner.operands
    ):
        # ``not: {required: [a, b]}`` bans the PAIR, not either name. It becomes
        # an absence only where the arm already requires one of them, which the
        # caller resolves; here it is left to the residual check.
        return None
    return None


def _lifted_literal(leaf: Cond, fields: frozenset[str]) -> tuple[str, Any, Cond] | None:
    """A field pinned to one value by this leaf, and what the leaf has left.

    ``{"properties": {"status": {"type": "string", "const": "completed"}}}``
    pins ``status``; the sibling ``type`` is the field's own annotation and
    needs no check, but it is only dropped where the ``const`` it accompanies
    becomes a ``Literal`` -- which is what makes dropping it sound.
    """
    if not isinstance(leaf, PropSatisfies) or leaf.name not in fields:
        return None
    operands = leaf.operand.operands if isinstance(leaf.operand, AllOf) else (leaf.operand,)
    pinned = [operand for operand in operands if isinstance(operand, ValueConst)]
    if len(pinned) != 1:
        return None
    value = pinned[0].value
    rest = [
        operand
        for operand in operands
        if not isinstance(operand, ValueConst)
        and not (isinstance(operand, ValueType) and _value_has_type(value, operand.types))
    ]
    remainder: Cond = Restated("literal")
    if rest:
        inner: Cond = rest[0] if len(rest) == 1 else AllOf(tuple(rest))
        remainder = PropSatisfies(leaf.name, inner)
    return leaf.name, value, remainder


#: JSON type names, and whether a Python value answers to each. Only consulted
#: to decide whether a sibling ``type`` is implied by the ``const`` beside it,
#: so it is checked rather than assumed: a ``Literal['completed']`` annotation
#: carries ``type: string`` and nothing else does.
_JSON_TYPE_OF: dict[type, tuple[str, ...]] = {
    bool: ("boolean",),
    int: ("integer", "number"),
    float: ("number",),
    str: ("string",),
    list: ("array",),
    dict: ("object",),
    type(None): ("null",),
}


def _value_has_type(value: Any, names: tuple[str, ...]) -> bool:
    """Whether ``value`` satisfies every one of the named JSON types."""
    answered = _JSON_TYPE_OF.get(type(value), ())
    return bool(names) and all(name in answered for name in names)


def plan_branches(
    constraints: RootConstraints, parent: str, schema_file: str, fields: frozenset[str]
) -> tuple[BranchPlan, ...]:
    """What each arm becomes, from the records and nothing else.

    ``fields`` are the attribute names the flat class declares, so a predicate
    naming a key no field holds stays in the residual check rather than being
    read as a field to drop.
    """
    names = branch_class_names(parent, constraints.arms, schema_file)
    plans: list[BranchPlan] = []
    for arm, name, condition in zip(
        constraints.arms, names, arm_conditions(constraints), strict=True
    ):
        absent: set[str] = set()
        absent_nullable: set[str] = set()
        required: set[str] = set(arm.required)
        literals: dict[str, Any] = {}
        residual: list[Cond] = []
        for leaf in _conjuncts(condition):
            banned = _absent_names(leaf)
            if banned is not None and {node.name for node in banned} <= fields:
                for node in banned:
                    (absent_nullable if node.nullable else absent).add(node.name)
                continue
            if isinstance(leaf, Supplied) and leaf.name in fields:
                required.add(leaf.name)
                continue
            if isinstance(leaf, Undeclarable):
                # False of every instance, so an arm carrying it positively is
                # dead and the emitter must not pretend otherwise.
                residual.append(leaf)
                continue
            lifted = _lifted_literal(leaf, fields)
            if lifted is not None:
                field_name, value, remainder = lifted
                literals[field_name] = value
                if not isinstance(remainder, Restated):
                    residual.append(remainder)
                continue
            residual.append(leaf)
        plans.append(
            BranchPlan(
                name=name,
                title=arm.title,
                pointer=arm.pointer,
                absent=frozenset(absent - required),
                absent_nullable=frozenset(absent_nullable - required),
                required=frozenset(required),
                literals=literals,
                residual=_conjunction(residual),
            )
        )
    return tuple(plans)


# --------------------------------------------------------------------------- #
# Rendering: the flat class's statements, per arm
# --------------------------------------------------------------------------- #


def _strip_none(annotation: ast.expr) -> ast.expr:
    """``X | None`` -> ``X``, inside an ``Annotated`` too. Required means no null.

    A required field whose schema also permits ``null`` keeps it: the union is
    only stripped where ``None`` is the optionality the generator added for a
    field the root did not require.
    """
    if isinstance(annotation, ast.Subscript) and _name_of(annotation.value) == "Annotated":
        if isinstance(annotation.slice, ast.Tuple) and annotation.slice.elts:
            elements = list(annotation.slice.elts)
            elements[0] = _strip_none(elements[0])
            return ast.Subscript(
                value=annotation.value,
                slice=ast.Tuple(elts=elements, ctx=ast.Load()),
                ctx=annotation.ctx,
            )
        return annotation
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        if _is_none(annotation.right):
            return _strip_none(annotation.left)
        if _is_none(annotation.left):
            return _strip_none(annotation.right)
        return ast.BinOp(
            left=_strip_none(annotation.left),
            op=annotation.op,
            right=_strip_none(annotation.right),
        )
    return annotation


def _literal_annotation(annotation: ast.expr, value: Any) -> ast.expr:
    """Replace the type half of an annotation with ``Literal[value]``."""
    literal = ast.Subscript(
        value=ast.Name(id="Literal", ctx=ast.Load()),
        slice=ast.Constant(value=value),
        ctx=ast.Load(),
    )
    if isinstance(annotation, ast.Subscript) and _name_of(annotation.value) == "Annotated":
        if isinstance(annotation.slice, ast.Tuple) and annotation.slice.elts:
            elements = list(annotation.slice.elts)
            elements[0] = literal
            return ast.Subscript(
                value=annotation.value,
                slice=ast.Tuple(elts=elements, ctx=ast.Load()),
                ctx=annotation.ctx,
            )
    return literal


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _name_of(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _field_name(statement: ast.AnnAssign) -> str | None:
    return statement.target.id if isinstance(statement.target, ast.Name) else None


def _statement_source(statement: ast.stmt, source: str) -> str:
    """One statement exactly as written, decorators and comments included.

    ``ast.get_source_segment`` starts a decorated function at its ``def``, so
    copying a validator through it silently drops the ``@model_validator`` that
    makes it run -- a validator that still reads as one and enforces nothing.
    The span is taken from the first decorator instead.
    """
    lines = source.splitlines()
    decorators = getattr(statement, "decorator_list", [])
    start = min([node.lineno for node in decorators] + [statement.lineno]) - 1
    end = statement.end_lineno or start + 1
    block = lines[start:end]
    indent = min(
        (len(line) - len(line.lstrip()) for line in block if line.strip()),
        default=0,
    )
    return "\n".join(line[indent:] if line.strip() else "" for line in block)


def _base_name(flat_class: str) -> str:
    """The base takes the ROOT'S PLAIN NAME, so it needs no suffix at all.

    The base is what a consumer constructs, parses through and tests with
    ``isinstance``, because it carries the branches' core schema -- so the
    root's own name belongs on it. Only the union needs a name of its own,
    and :func:`_branches_name` gives it one.

    An earlier spelling suffixed the base and bound the root's name to the
    union. That made the public name uncallable, which broke two tests the repo
    already merged to assert what a consumer does, and required editing every
    call site to say the same thing in more words.
    """
    return flat_class


def _branches_name(flat_class: str) -> str:
    """The union over the branches: the root's name plus ``Branches``.

    Exported beside the base, because the two say different things. A consumer
    annotating the base says "a request of this kind"; one annotating the union
    says "exactly one of these", which is what makes a type checker force
    exhaustive narrowing.
    """
    return f"{flat_class}Branches"


def _render_branch_models(branch_names: Sequence[str], combinator: str) -> list[str]:
    """Declare the branches, which is how the shared hook finds them.

    ``BranchDispatchMixin`` carries the one implementation, and the base is the
    class that DECLARES this method -- so declaring it is what makes a class the
    base, and a branch or a refinement elsewhere inherits it and keeps its own
    shape. Nothing has to be registered, so nothing can be forgotten: a new
    split root works by emitting this method.

    This replaced a hook emitted per root, which was eleven copies of one
    function. Two bugs were found in that function while it was still one copy.

    """
    listed = ",\n            ".join(branch_names)
    return [
        "",
        "    @classmethod",
        "    def _branch_models(cls) -> tuple[type, ...]:",
        "        # The branches subclass this class, so they are not defined while",
        "        # this body is compiled. The hook resolves them on first use, after",
        "        # the model_rebuild below.",
        "        return (",
        f"            {listed},",
        "        )",
        "",
        "    @classmethod",
        "    def _branch_combinator(cls) -> str:",
        "        # The keyword a refusal names, from the root's own schema. The",
        "        # union the hook builds carries the wrapper that supplies it.",
        f"        return {combinator!r}",
    ]


def _render_base(
    flat: ast.ClassDef,
    flat_class: str,
    schema_file: str,
    source: str,
    branch_names: Sequence[str],
    combinator: str,
) -> str:
    """The root's own shape: every property and everything other passes added.

    This is what makes the branches one type rather than several. Measured over
    the eleven partitioning roots: every one has properties shared by all of its
    branches (29 on ``create-media-buy-request``, 17 on ``creative-asset``, 2 on
    the smallest), and eight of the eleven have branches that constrain NO
    property at all -- they differ only in which fields they require and which
    they forbid. So the faithful rendering is one base and a subclass per arm;
    a union of unrelated classes would say the branches are different types,
    which the schema does not say anywhere in this population.

    The body is copied verbatim, so every earlier pass's field metadata,
    validator and config lands on the base and is inherited once rather than
    repeated per arm.
    """
    # The mixin is listed FIRST so its __get_pydantic_core_schema__ wins over
    # BaseModel's. model_config merges right-to-left with the right-most base
    # winning, so prepending it does not disturb the config the generated bases
    # resolve -- which is the same ordering fact the canonical layer depends on.
    bases = ", ".join(["BranchDispatchMixin", *(ast.unparse(base) for base in flat.bases)])
    members = "\n".join(f"    ``{name}``" for name in branch_names)
    lines = [
        f"class {_base_name(flat_class)}({bases}):",
        f'    """What every arm of {schema_file} shares.',
        "",
        "    The root's own properties and requiredness. Each arm subclasses this",
        "    and states only what it changes, so the arms are one type with",
        "    different requiredness rather than unrelated classes:",
        "",
        members,
        "",
        "    This class carries the branches' CORE SCHEMA, so parsing it -- by",
        "    name, nested in another model, or through a TypeAdapter -- returns",
        "    the branch the document satisfies, and refuses a document that",
        "    satisfies none or two of them.",
        "",
        f"    {_branches_name(flat_class)} is the union over those branches, for a",
        "    caller that wants a type checker to force exhaustive narrowing.",
        '    """',
        "",
    ]
    body = 0
    for statement in flat.body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue  # the flat class's own docstring, replaced above
        if isinstance(statement, ast.FunctionDef) and statement.name == ROOT_CONSTRAINT_VALIDATOR:
            # A compiled check over the WHOLE combinator, left by an earlier run
            # of the constraint pass. On the base it would re-ask of every arm
            # what the arm's own shape answers, and its return annotation would
            # name the union. Each arm's residual check is emitted below instead.
            continue
        lines.extend(
            f"    {line}" if line.strip() else ""
            for line in _statement_source(statement, source).splitlines()
        )
        body += 1
    if not body:
        lines.append("    pass")
    lines.extend(_render_branch_models(branch_names, combinator))
    return "\n".join(lines)


def _render_branch(plan: BranchPlan, flat: ast.ClassDef, flat_class: str, schema_file: str) -> str:
    """One arm: only what it changes about the base.

    A required field is redeclared without its default, a pinned field as the
    ``Literal`` the arm pins it to, and a forbidden field as ``None`` -- which
    is what makes passing it a type error rather than a validator's refusal.
    Everything else is inherited, so the arm's class says exactly what the arm
    says and nothing more.
    """
    declared = {
        name: statement
        for statement in flat.body
        if isinstance(statement, ast.AnnAssign)
        for name in (_field_name(statement),)
        if name is not None
    }
    heading = plan.title or f"The {plan.pointer} arm"
    lines = [
        f"class {plan.name}({_base_name(flat_class)}):",
        f'    """{heading}.',
        "",
        f"    One arm of {schema_file}, stated as a shape: {plan.pointer} requires",
        "    what it declares below without a default, and types what it forbids",
        "    as ``None``.",
        '    """',
        "",
    ]
    changed = 0
    for name in sorted(plan.absent | plan.absent_nullable):
        statement = declared.get(name)
        if statement is None:
            continue
        lines.append(f"    {name}: None = None")
        changed += 1
    for name in sorted(plan.required | set(plan.literals)):
        statement = declared.get(name)
        if statement is None:
            continue
        rendered = _render_field(statement, plan)
        lines.extend(f"    {line}" if line.strip() else "" for line in rendered.splitlines())
        changed += 1
    if not changed:
        lines.append("    pass")
    return "\n".join(lines)


def _render_field(statement: ast.AnnAssign, plan: BranchPlan) -> str:
    """One field statement, re-annotated for this arm."""
    name = _field_name(statement)
    annotation = statement.annotation
    value = statement.value
    if name is not None and name in plan.literals:
        annotation = _literal_annotation(annotation, plan.literals[name])
        value = None
    if name is not None and name in plan.required:
        annotation = _strip_none(annotation)
        value = None
    rebuilt = ast.AnnAssign(target=statement.target, annotation=annotation, value=value, simple=1)
    return ast.unparse(ast.fix_missing_locations(rebuilt))


def render_absence_hook(plan: BranchPlan) -> str:
    """The arm's forbidden keys, refused on the document as sent.

    Absence is a type at CONSTRUCTION -- the field is not on the class, so the
    keyword argument does not exist -- and it is this hook at WIRE VALIDATION,
    because a model configured ``extra='allow'`` would otherwise file the key
    under extras and accept a document its schema refuses. The design names
    this as the one place the type system alone cannot carry an arm's content:
    the type system does not see raw documents.
    """
    if not (plan.absent or plan.absent_nullable):
        return ""
    names = ", ".join(repr(name) for name in sorted(plan.absent))
    nullable = ", ".join(repr(name) for name in sorted(plan.absent_nullable))
    return "\n".join(
        [
            "",
            f"    _ABSENT: ClassVar[frozenset[str]] = frozenset({{{names}}})",
            f"    _ABSENT_NULLABLE: ClassVar[frozenset[str]] = frozenset({{{nullable}}})",
            "",
            "    @model_validator(mode='before')",
            "    @classmethod",
            "    def _refuse_keys_this_shape_forbids(cls, data: Any) -> Any:",
            "        # The fields this arm forbids are typed None above, which is what",
            "        # makes the combination a type error. A raw document still needs",
            "        # this: extra='allow' files an undeclared key under extras and",
            "        # accepts, and a declared one would arrive as a None the arm does",
            "        # not forbid at a nullable position.",
            "        return _c.absent(",
            "            data, sorted(cls._ABSENT), sorted(cls._ABSENT_NULLABLE)",
            "        )",
        ]
    )


def _render_validator(plan: BranchPlan, schema_file: str, combinator: str) -> str:
    """The arm's residual check, or the empty string when nothing is left.

    The refusal names the root combinator, because that is the keyword a
    consumer puts in ``error.issues[].keyword`` -- the arm's residual is part of
    what the root's ``anyOf``/``oneOf`` states. A bare ``ValueError`` arrives as
    ``value_error``, names no keyword, and ``core/error.json`` requires one; a
    seller reported exactly that reaching the wire for ``core/creative-asset``,
    which is one of the roots this emitter splits.
    """
    predicate = compile_condition(plan.residual)
    if predicate == "True":
        return ""
    refusal = (
        f"{plan.name} violates what {schema_file} states for its {plan.pointer} arm "
        f"beyond the fields it requires and forbids"
    )
    return "\n".join(
        [
            "",
            "    @model_validator(mode='after')",
            f"    def {ROOT_CONSTRAINT_VALIDATOR}(self) -> {plan.name}:",
            f"        # Compiled from {schema_file} {plan.pointer}: what this arm states",
            "        # that its field set cannot carry -- a value one level down, an",
            "        # overlay on an array's items, a bound. Requiredness and absence",
            "        # are the class's own shape and are not re-checked here.",
            "        if not (",
            f"            {predicate}",
            "        ):",
            schema_keyword_raise(combinator, refusal, indent=" " * 12),
            "        return self",
        ]
    )


def split_into_branch_classes(
    source: str,
    flat_class: str,
    constraints: RootConstraints,
    schema_file: str,
    fields: frozenset[str],
) -> str | None:
    """Rewrite a module's flat root class into one class per arm plus a union.

    ``None`` when the module does not hold the flat class as a plain class
    statement, which is the one shape this rewrite understands.
    """
    tree = ast.parse(source)
    flat = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == flat_class),
        None,
    )
    if flat is None:
        return None

    plans = plan_branches(constraints, flat_class, schema_file, fields)
    blocks = [
        _render_base(
            flat,
            flat_class,
            schema_file,
            source,
            [plan.name for plan in plans],
            constraints.combinator or "anyOf",
        )
    ]
    blocks.extend(
        _render_branch(plan, flat, flat_class, schema_file)
        + render_absence_hook(plan)
        + _render_validator(plan, schema_file, constraints.combinator or "anyOf")
        for plan in plans
    )
    union = " | ".join(plan.name for plan in plans)
    combinator = constraints.combinator or "anyOf"
    branches = _branches_name(flat_class)
    blocks.append(
        "\n".join(
            [
                f"#: {schema_file}'s branches, proven pairwise disjoint, so a parsed",
                "#: document comes back as exactly one of them. Annotate this to make a",
                f"#: type checker force exhaustive narrowing; annotate {flat_class} to",
                '#: say "a request of this kind" and get the same strictness at runtime.',
                "#:",
                "#: The wrapper names the root combinator on a refusal. A document that",
                "#: satisfies no branch fails each branch at field validation, so pydantic",
                "#: reports 'missing' and nothing names the keyword core/error.json",
                "#: requires in issues[].keyword.",
                f"{branches}: TypeAlias = Annotated[",
                f"    {union},",
                "    WrapValidator(",
                f"        _c.name_the_combinator({combinator!r}, {flat_class}._branch_models())",
                "    ),",
                "]",
                "",
                "#: Parsing a union is what a TypeAdapter is for. Built once, at import.",
                f"{branches}Adapter: TypeAdapter[{branches}] = TypeAdapter({branches})",
                "",
                f"# {flat_class} is declared above its branches, so _branch_models",
                "# cannot resolve them while the class body is compiled. The rebuild is",
                "# what installs the branches' schema -- a class's core schema is built",
                "# at class creation, so the hook's earlier return is already cached.",
                "#",
                "# This is not a surviving patch. What this series deletes is a model",
                "# patched from a FOREIGN module: a field installed that the class never",
                "# declared, with a forced rebuild to make the patch take. A rebuild in",
                "# the declaring module, resolving a forward reference the class cannot",
                "# name at declaration time, is what model_rebuild is for.",
                f"{flat_class}.model_rebuild(force=True)",
            ]
        )
    )

    lines = source.splitlines(keepends=True)
    start = min([decorator.lineno for decorator in flat.decorator_list] + [flat.lineno]) - 1
    end = flat.end_lineno or len(lines)
    replaced = "\n\n\n".join(blocks) + "\n"
    return "".join(lines[:start]) + replaced + "".join(lines[end:])


def arm_names(constraints: RootConstraints, parent: str, schema_file: str) -> Sequence[str]:
    """The class names this module would emit, without rendering anything."""
    return branch_class_names(parent, constraints.arms, schema_file)


def repoint_subclasses_of(source: str, flat_class: str) -> str | None:
    """Repoint a class that subclasses a split root onto the root's shared base.

    A union is not a base, so a generated subclass of a root the emitter splits
    has to name the base instead. There are two in the pinned bundle --
    ``Creative(CreativeAsset)`` and ``CreativeRepresentation(CreativeManifest)``
    -- and nothing subclasses either of those in turn, so this does not recurse.

    ``None`` when the module names the class in no base list, which is every
    module but the one or two that do.

    The subclass is NOT a member of the union afterwards, and that is the honest
    reading: it is a different shape, with its own fields, and a consumer
    annotating the union never meant to accept it. What it does get is the
    fields every arm shares, which is what it was reaching for by subclassing
    the flat class.
    """
    base = _base_name(flat_class)
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    edits: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for reference in node.bases:
            target = reference.value if isinstance(reference, ast.Subscript) else reference
            named = target.id if isinstance(target, ast.Name) else getattr(target, "attr", None)
            if named != flat_class:
                continue
            spelling = ast.unparse(target)
            edits.append((node.lineno - 1, spelling, spelling.replace(flat_class, base)))
    if not edits:
        return None
    for index, old, new in edits:
        lines[index] = lines[index].replace(f"({old})", f"({new})").replace(f"({old},", f"({new},")
    rewritten = "".join(lines)
    return _repoint_import(rewritten, flat_class, base)


def _repoint_import(source: str, flat_class: str, base: str) -> str:
    """Make the base importable wherever the flat class was imported by name.

    The import is ADDED rather than replaced: the module may still reference the
    union as a field annotation, which stays valid.
    """

    if re.search(rf"^class {re.escape(flat_class)}\b", source, re.MULTILINE):
        # Declared in this very module, so the base is declared here too.
        return source
    pattern = re.compile(
        rf"^(from [^\n]*? import )([^\n(]*\b{re.escape(flat_class)}\b[^\n]*)$", re.MULTILINE
    )
    match = pattern.search(source)
    if match is None:
        # The class was rewritten to name a base that nothing imports, which is
        # a module that fails at import. Raised rather than returned, like the
        # pipeline's other import helpers: the generated shape changed in a way
        # this rewrite no longer matches -- a parenthesized import block, say --
        # and that is a regeneration failure, not something to leave quiet.
        raise RuntimeError(f"no single-line 'import {flat_class}' statement to extend with {base}")
    names = [name.strip() for name in match.group(2).split(",") if name.strip()]
    if base in names:
        return source
    statement = match.group(1) + ", ".join(sorted({*names, base}))
    return source[: match.start()] + statement + source[match.end() :]
