"""D5's third rung: the aliases that belong to no document, and their one module.

``docs/plan/rebuild-plan.md`` D5 says a constrained type is **named once and
referenced**, and gives the resolution order the walk follows for every
constrained scalar it meets:

1. **a type the bundle itself names** -- a titled root carrying those
   constraints, reached ``by $ref as an import``.  That already works and needs
   nothing here: ``emit.decide_type``'s ``$ref`` arm binds the target's module
   and names its symbol, and nothing of the target's own schema is copied (P2).
   An INLINE declaration is not that case and must not be turned into one.
   Measured over the bundle: 229 titled scalar roots, and rewriting an inline
   site into an import of a content-equal one would invent a reference the
   citing document does not state AND would put the target root's own
   ``description`` into the citing field's rendered schema, which is a fact the
   citing document does not state -- so the symmetric comparison would report it
   as added.  Rung 1 is reached through a ``$ref`` or not at all.
2. **a type pydantic names**, and only where it states the document's own facts
   AND accepts the document's own set.  :func:`standard` is that rule, with both
   measurements in its docstring.
3. **otherwise an alias we emit**, named by :func:`symbol` and declared in
   ``adcp.types.constraints``.

**An alias has no document, so it has no domain.**  Every other type this
pipeline emits is reachable at ``adcp.types.<domain>.<Name>`` where the domain is
the document's own path (D1).  A type derived from a constraint belongs to no
document, so inventing a domain for it would be naming it after a concept, which
D5 forbids.  One module holds them all, it is PUBLIC (a consumer annotating
application code imports from it), and it is named for what it holds rather than
for ``Annotated``, which is only the mechanism.

**An alias names a constraint, never a concept.**  :func:`symbol` derives the
name from the constraint and from nothing else -- never from a property key,
never from a domain word -- because two fields sharing a bound are not thereby
the same idea.  A ``pattern`` is the one keyword with no readable spelling, so it
contributes a DIGEST of itself: mechanical, stable, a function of the constraint
alone, and manifestly not a concept.  :func:`record` makes a digest collision a
build failure rather than two constraints quietly sharing a symbol.

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

**A constrained CONTAINER is not here, and the reason is the naming rule rather
than an omission.**  A bound on a list is a bound on the FIELD holding it
(``codegen.lower.containers``, and ``compiler.Type`` carries no constraints for a
container at all), so ``Annotated[list[str], Field(min_length=1)]`` is already
D5's correct form.  Naming it would need the ELEMENT type in the symbol --
``list[RightUse]`` and ``list[str]`` are different types -- and an element type is
a domain word, which D5's naming rule forbids.  Measured on the tree this lands
on: 21 such shapes over 30 sites, 2 of them repeating (``list[str]`` at 8 sites
and ``list[RightUse]`` at 3), all of them already field-bound.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from codegen import compiler
from codegen.compiler import Rendered

#: The module an emitted alias is reachable at, and the only path to one: there is
#: no flat root and no second spelling.  PUBLIC, unlike ``adcp.types._schemas``,
#: so an emitted module names it absolutely rather than by the depth-dependent
#: relative spelling ``emit.relative_module`` derives for a sibling (P8's reason
#: for a relative import is that ``_schemas`` is private, and this is not).
MODULE = "adcp.types.constraints"

#: The one type that is a DECISION rather than a derivation, so it is declared
#: whatever the run met.  D5: a ``format: uri`` field is ``AdCPUrl``, defined once
#: as ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]`` -- named for
#: provenance rather than after a standard, because pydantic exports 22 URL types
#: and none is https-only, so ``HttpsUrl`` would read as an upstream export a
#: reader cannot find.
URL = "AdCPUrl"
URL_LINE = f'{URL} = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]'
URL_IMPORTS = {("typing", "Annotated"), ("pydantic", "AnyUrl"), ("pydantic", "UrlConstraints")}

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

#: The word a scalar ``type`` contributes, in the document's own vocabulary.
#: ``boolean`` is absent: a boolean carries no constraint keyword, so no shape
#: reaches this module for one.
BASE = {"string": "Str", "integer": "Int", "number": "Float"}


def standard(kind: str, constraints: Mapping[str, Any]) -> str | None:
    """D5's rung 2: the pydantic type for this shape, where one QUALIFIES.

    **Both halves are required: the type must state the document's own facts and
    accept the document's own set.**  That is a rule and not a list of blessed
    names, and the schema comparison enforces the first half on every pair, so a
    type admitted here cannot quietly state something else.  Re-measured on
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


def _digest(pattern: str) -> str:
    """The word a ``pattern`` contributes: eight hex digits of its SHA-256.

    A regular expression has no readable name that is not a concept -- calling
    ``^[A-Z]{3}$`` ``CurrencyCode`` names the idea three of its sites happen to
    share and would be a lie at the fourth.  A digest is derived from the
    constraint, is stable across runs and bundles, and cannot be mistaken for a
    domain word.  Eight hex digits over the bundle's distinct patterns is ample;
    :func:`record` turns a collision into a build failure rather than two
    constraints sharing a symbol.
    """
    return hashlib.sha256(pattern.encode()).hexdigest()[:8].upper()


def symbol(kind: str, constraints: Mapping[str, Any]) -> str | None:
    """D5's rung 3: the alias name for this shape, derived from the constraint.

    ``None`` where the shape has no spelling here -- an unknown ``type``, no
    constraint at all, or a keyword :data:`SPELLING` does not name -- and the
    caller then leaves the site inline, which is what it did before this module
    existed.  Returning a name for a keyword this module cannot spell would be
    the one failure mode that matters: an alias whose annotation drops a fact.
    """
    base = BASE.get(kind)
    if base is None or not constraints:
        return None
    if set(constraints) - {kw for kw, _ in SPELLING}:
        return None
    parts = [
        word + (_digest(constraints[kw]) if kw == "pattern" else _number(constraints[kw]))
        for kw, word in SPELLING
        if kw in constraints
    ]
    name = base + "".join(parts)
    return name if name.isidentifier() else None


def resolve(kind: str, constraints: Mapping[str, Any]) -> str | None:
    """The dotted path this shape's named type is reachable at, or ``None``.

    Rung 2 before rung 3, which is D5's own order, and rung 1 is not here: it is
    reached through a ``$ref`` in ``emit.decide_type`` and never by matching an
    inline declaration against another document's content (see the module
    docstring).
    """
    if not constraints:
        return None
    found = standard(kind, constraints)
    if found is not None:
        return found
    name = symbol(kind, constraints)
    return None if name is None else f"{MODULE}.{name}"


class AliasCollision(Exception):
    """Two distinct constraints derive one alias name.

    A BUILD FAILURE and not a ``Refusal``, on ``emit.AmbiguousRoot``'s reasoning:
    a refusal is the designed outcome of a keyword this emitter does not lower,
    and this is the emitter disagreeing with itself about what a name MEANS.
    Recording it as a refusal would file it against a document, where it would
    read as the bundle's fault, and the build would pass.
    """


def record(
    into: dict[str, tuple[str, dict[str, Any]]],
    name: str,
    kind: str,
    constraints: Mapping[str, Any],
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
    shape = (kind, dict(constraints))
    found = into.get(name)
    if found is not None and found != shape:
        raise AliasCollision(
            f"{name!r} is derived by two distinct constraints, {found} and {shape}, so one "
            "alias would annotate two fields and state a constraint one document does not"
        )
    into[name] = shape


def declare(shapes: Mapping[str, tuple[str, Mapping[str, Any]]]) -> str:
    """The text of ``adcp/types/constraints.py``, for the shapes a run met.

    :data:`URL` is declared whatever the run met, because it is a DECISION rather
    than a derivation -- D5 names it, ``emit.FORMAT_TYPES`` points every
    ``format: uri`` field at it, and a consumer who wants to parse a URL of their
    own imports it from here.  The derived aliases are exactly the shapes the run
    resolved, sorted, so the module is a function of the run and holds no alias
    nothing names.

    **The ANNOTATION is the compiler's**, read off the same ``DataModelField`` a
    class property gets (``compiler.render_alias``), so a ``minLength`` on an
    alias here and a ``minLength`` on a property there cannot come to be spelled
    two different ways.  What is this function's is the module around them.
    ``render_alias`` also reports the ``SchemaRef`` import a ROOT alias module
    needs; these aliases carry no schema reference -- an alias has no document --
    so that one import is dropped here by name.
    """
    imports: set[tuple[str, str]] = set(URL_IMPORTS)
    lines: list[str] = [URL_LINE]
    for name in sorted(shapes):
        kind, cons = shapes[name]
        rendered: Rendered = compiler.render_alias(name, compiler.Type(SCALAR_PATH[kind]), cons)
        lines.append(rendered.text)
        imports |= {i for i in rendered.imports if i != ("adcp.types._base", "SchemaRef")}
    by_module: dict[str, set[str]] = {}
    for module, item in imports:
        by_module.setdefault(module, set()).add(item)
    # The emitted modules' own layout (``emit.render``): stdlib, then the library,
    # one blank line between the groups.  Spelled here rather than shared, because
    # ``emit.render`` writes a MODULE OF CLASSES and takes a ``compiler.Module``
    # this file has none of -- and two of its four ranks (``_base``, a sibling
    # schema module) cannot occur here at all: an alias imports nothing but the
    # annotation machinery.
    groups = [
        [f"from {m} import {', '.join(sorted(by_module[m]))}" for m in sorted(by_module) if keep(m)]
        for keep in (lambda m: m != "pydantic", lambda m: m == "pydantic")
    ]
    head: list[str] = []
    for group in groups:
        if group:
            head += ["", *group]
    return "\n".join(
        [HEADER, DOCSTRING, "", "from __future__ import annotations", *head, "", "", *lines, ""]
    )


#: The same first line every emitted module carries, less the document name: this
#: module is the one output that belongs to no document.
HEADER = "# Generated by codegen.emit. Do not edit."


#: ``compiler.SCALAR`` keyed by the document's own word, which is what this module
#: is handed.  Named here rather than inverted at the call site so the two
#: spellings of a scalar type have one mapping between them.
SCALAR_PATH = {"string": "str", "integer": "int", "number": "float"}

DOCSTRING = '''"""Constrained types, each named for the constraint it carries.

GENERATED by ``codegen.emit``; see ``codegen/constraints.py``.  Edit neither --
the tree is ``f(bundle, emitter, pinned compiler)`` and a hand edit here is a
fact no input states (P10).

Every other type this SDK emits is reachable at ``adcp.types.<domain>.<Name>``,
where the domain is the schema document's own path.  A type derived from a
CONSTRAINT belongs to no document, so it has no domain and lives here instead.
Its name is derived from the constraint and from nothing else -- never from a
property key and never from a domain word, because two fields sharing a bound
are not thereby the same idea.  A ``pattern`` has no readable name that is not a
concept, so it contributes eight hex digits of its own SHA-256.  Two distinct
constraints deriving one name is a build failure rather than a shared alias.

``AdCPUrl`` is the one name here that is a decision rather than a derivation:
every ``format: uri`` field in this SDK is annotated with it.  A consumer who
wants to parse a URL of their own can import it, and the document's own
``pattern`` -- the bundle states eight distinct ones across 73 of its 300 ``uri``
uses, and ``UrlConstraints`` expresses only the first -- stays with the schema
half, which ``strict_validate`` applies before the constructor ever runs.
"""'''
