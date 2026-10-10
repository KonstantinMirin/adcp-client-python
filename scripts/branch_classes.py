"""One class per arm, for a flat root whose arms partition.

``scripts/schema_constraints.py`` reads a root's constraint content into
``Arm`` records and proves whether the arms partition the document space.
Where they do, the arms are not a rule over one class -- they are distinct
types, and the generator's flattening is what turned them into a rule. This
module renders that: each arm becomes a class carrying the fields that arm
permits, requiring the fields that arm requires, and NOT DECLARING the fields
that arm forbids; the root's public name becomes a union over them.

What that makes unconstructible, and why it is a different claim from a check:

* A request combining fields from two arms has no class that carries both
  names. ``CreateMediaBuyRequestCommittedProposalExecution(packages=...)`` is
  an unknown keyword argument -- a type error, before anything runs.
* An arm's required field is required on that arm's class, so omitting it is a
  missing argument rather than a validator's refusal.

What stays a check, named rather than implied: everything in an arm's condition
that is not requiredness or absence -- a const one level down, an overlay on an
array's items, a value bound. Those are compiled onto the arm's own class by
``scripts/compile_conditions.py``, so the refusal still arrives from the class
the caller named, but it arrives at validation rather than at type-check time.

Nothing here invents an identifier. Class names come from
``scripts/union_arm_names.py``'s rungs over the same ``Arm`` records, and the
module-internal spellings are the parent name with a leading underscore.
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

try:
    from compile_conditions import ROOT_CONSTRAINT_VALIDATOR, compile_condition
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
    "split_into_branch_classes",
]


@dataclass(frozen=True)
class BranchPlan:
    """What one arm becomes: a field set, a requiredness, and what is left over."""

    name: str
    title: str | None
    pointer: str
    absent: frozenset[str]
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


def _absent_names(leaf: Cond) -> frozenset[str] | None:
    """The names a leaf forbids, or ``None`` when it forbids nothing.

    Two spellings, both in the bundle: ``not: {required: [x]}`` for one name and
    ``not: {anyOf: [{required: [x]}, ...]}`` for several. Both say the document
    may not carry the name, which on a class is the absence of the field.
    """
    if not isinstance(leaf, Not):
        return None
    inner = leaf.operand
    if isinstance(inner, Supplied):
        return frozenset({inner.name})
    if isinstance(inner, AnyOf) and all(
        isinstance(operand, Supplied) for operand in inner.operands
    ):
        return frozenset(operand.name for operand in inner.operands)  # type: ignore[union-attr]
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
        required: set[str] = set(arm.required)
        literals: dict[str, Any] = {}
        residual: list[Cond] = []
        for leaf in _conjuncts(condition):
            banned = _absent_names(leaf)
            if banned is not None and banned <= fields:
                absent |= set(banned)
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


def _render_class(
    plan: BranchPlan,
    flat: ast.ClassDef,
    schema_file: str,
    source: str,
) -> str:
    """One arm's class: the flat class's statements, minus what the arm forbids."""
    bases = ", ".join(ast.unparse(base) for base in flat.bases)
    heading = plan.title or f"The {plan.pointer} arm"
    lines = [
        f"class {plan.name}({bases}):",
        f'    """{heading}.',
        "",
        f"    One arm of {schema_file}, which states {plan.pointer} as a shape",
        "    rather than as a rule: the fields this arm forbids are not declared",
        "    here, and the fields it requires carry no default.",
        '    """',
        "",
    ]
    body = 0
    for statement in flat.body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue  # the flat class's own docstring
        if isinstance(statement, ast.FunctionDef) and statement.name == ROOT_CONSTRAINT_VALIDATOR:
            # A compiled check over the WHOLE combinator, left on the flat class
            # by an earlier run of the constraint pass. Copying it onto every arm
            # would re-ask what the arm's own shape answers, and would answer it
            # with a union-typed return annotation. This arm's own residual check
            # is appended below instead.
            continue
        if isinstance(statement, ast.AnnAssign):
            name = _field_name(statement)
            if name is not None and name in plan.absent:
                continue
            rendered = _render_field(statement, plan)
        else:
            rendered = _statement_source(statement, source)
        lines.extend(f"    {line}" if line.strip() else "" for line in rendered.splitlines())
        body += 1
    if not body:
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
    if not plan.absent:
        return ""
    names = ", ".join(repr(name) for name in sorted(plan.absent))
    return "\n".join(
        [
            "",
            f"    _ABSENT: ClassVar[frozenset[str]] = frozenset({{{names}}})",
            "",
            "    @model_validator(mode='before')",
            "    @classmethod",
            "    def _refuse_keys_this_shape_forbids(cls, data: Any) -> Any:",
            "        # The fields this arm forbids are not declared above, which is what",
            "        # makes the combination unspellable. A raw document still needs this:",
            "        # extra='allow' would file the key under extras and accept.",
            "        return _c.absent(data, sorted(cls._ABSENT))",
        ]
    )


def _render_validator(plan: BranchPlan, schema_file: str) -> str:
    """The arm's residual check, or the empty string when nothing is left."""
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
            "            raise ValueError(",
            f"                {refusal!r}",
            "            )",
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
        _render_class(plan, flat, schema_file, source)
        + render_absence_hook(plan)
        + _render_validator(plan, schema_file)
        for plan in plans
    ]
    union = " | ".join(plan.name for plan in plans)
    blocks.append(
        "\n".join(
            [
                f"#: {schema_file}'s arms, proven pairwise disjoint, so a parsed document",
                "#: comes back as exactly one of them. The alias is the contract; a member",
                "#: is what a caller names to CONSTRUCT one.",
                f"{flat_class}: TypeAlias = {union}",
                "",
                "#: Parsing is what a union needs an adapter for. Built once, at import.",
                f"{flat_class}Adapter: TypeAdapter[{flat_class}] = TypeAdapter({flat_class})",
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
