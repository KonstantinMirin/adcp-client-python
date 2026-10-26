"""The keyword x position declaration: one table, and every reader derives from it.

``docs/plan/rebuild-plan.md`` sections 5, 6 and 7 are a table of keyword x position.
This module carries that table ONCE, as data.  ``docs/plan/architecture.md`` section 3
names the four readers that derive from it and the rule that nothing else under
``codegen/`` names a keyword in a set literal:

* **admission** -- the keyword screen (``compiler.check_keywords`` today,
  ``schema/parse.py`` after section 14 step 5) looks every key up at the node's
  POSITION: ``NOTHING``, ``ANNOTATION`` and ``NAME`` are admitted and carried
  nowhere by the screen; ``REFUSE`` refuses the document as a VERDICT; a key with no
  row refuses the document as a VERDICT naming a keyword the bundle did not use
  before; a ``FIELD`` effect is a fact the ENCLOSING field carries, so the node's own
  screen admits it too; and a ``TYPE`` or ``RULE`` effect is a fact the node's own kind
  consumes, so a handler with no code for it yet is a DEFERRAL.
* **descent** -- :attr:`Cell.descends` is the position the subschema(s) a structural
  keyword holds occupy.  Its readers are section 14 step 5's (``schema/parse.py``,
  ``bundle.edges``, ``verify/record.py``); this row declares the column and builds
  none of them.
* **lowering** -- a handler asks which of the keywords on its node are TYPE facts,
  which are RULE sources, which are annotations it carries.  Section 14 step 8's
  reader; this row declares the column.
* **grading** -- the comparison's compared set is
  ``{k for k in TABLE if cell(k, p).rendered}`` (:func:`rendered_at`).

**Where a refusal's KIND comes from.**  Section 3 of the architecture document: the
kind is derived from the cell and never chosen at a raise site.  A ``REFUSE`` cell,
or a document contradicting itself, is a VERDICT; a cell with a lowering effect whose
handler has no code for the shape yet is a DEFERRAL.  ``compiler.kind_for`` is that
derivation and it is the only place the two are told apart.

**What ``rendered`` asks.**  Does a faithful model state this keyword as a FACT in
``model_json_schema()`` -- a value the comparison can compare for equality?  Section 8
of the semantics document gives a keyword four answers, and they are alternatives: the
model *renders it as a fact*, *descends it as structure*, *enforces it as a rule*, or
*carries nothing*.  So:

* a keyword the model states as STRUCTURE -- ``properties``, ``items``,
  ``propertyNames``, ``patternProperties``, ``$ref``, the combinators, the
  conditionals -- has :attr:`Cell.descends` set and ``rendered=False``.  It is graded
  by DESCENDING it, which is the descent column's job and not the rendered column's;
  a comparison that also compared it as a value would report a spelling as a
  difference and leave the facts inside it ungraded.
* a keyword the model enforces as a RULE renders nothing in ``model_json_schema()``,
  so ``rendered=False`` -- section 8: "a keyword the declaration compiles to a rule
  renders nothing in the model's schema, so the comparison grades it against the
  class's rule tuple".  That rule-tuple reader is section 8's and is not built here,
  so ``minProperties``/``maxProperties``/``dependencies`` are declared ``RULE`` and
  ungraded for now.  ``uniqueItems`` is the one exception and the document states it:
  section 5 writes a ``json_schema_extra={"uniqueItems": true}`` beside the rule
  "so it is graded", so its cell is ``RULE`` and ``rendered=True``.

**``compiles`` is why generation is possible at all.**  The grid's prose column is
English and no triple of ``effect``, ``rendered`` and ``descends`` writes it, so the
sentence IS the cell's and the grid is its rendering (architecture section 3).  The
generator is a READER of this table and lives in ``tests/test_keywords.py``: section 11
gives this layer positions, keywords, cells and descent and denies it text, and
section 10's rule is that no module of the compiler is ever bound as ``__main__``, so
there is no ``python -m codegen.keywords``.

**How a row renders to a grid line** (architecture section 3, and
``tests/test_keywords.py`` is the renderer): the default cell's ``compiles``, followed
by one clause per position override in :class:`Position` declaration order; overrides
whose ``compiles`` is identical are ONE clause and their positions are joined with
``" / "``.  A clause is the joined position names followed by the cell's ``compiles``,
which therefore carries its own leading separator (``" -> ..."``, ``": under ..."``,
``" beside a union -> ..."``).  An override whose ``compiles`` is EMPTY renders no
clause: it records a cell the default sentence already covers in prose, which is what
a co-occurrence that is not a position needs -- the table is keyed by position and a
co-occurrence is not one, so it belongs to the sentence of the cell it qualifies.

**Which grid a row renders into is derived, not listed twice.**  Section 3: section 6
is the rows that compile to no type, no rule and no base, and section 7 is the REFUSE
rows, "so each section is a projection and not a second list".  :func:`grid_of` is
that projection; :attr:`Row.grid` names which of section 5's seven sub-tables a
section 5 row belongs to, which is a taxonomy of keyword family and is derivable from
nothing else.

**The ``x-`` namespace rule** (semantics section 6): a key with the prefix is
admitted, and every such key the bundle carries is also a row -- so a prefixed key
with NO row is admitted and REPORTED (:func:`unlisted_extension`), read once rather
than assumed to be metadata.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import NamedTuple


class Position(StrEnum):
    """The positions section 3 of the semantics document names, in its own order.

    The order is load-bearing twice: a grid line's clauses are written in it, and
    :func:`rendered_at` and the admission screen are asked at exactly one of them.
    """

    ROOT = "ROOT"
    PROP = "PROP"
    ELEM = "ELEM"
    MAPV = "MAPV"
    KEY = "KEY"
    BRANCH = "BRANCH"
    CONJ = "CONJ"
    RULE = "RULE"
    DEF = "DEF"


class Effect(StrEnum):
    """What a keyword compiles TO at a position, as a kind rather than as prose.

    ``TYPE``, ``FIELD`` and ``RULE`` are the three that COMPILE to something
    (:data:`COMPILES`), which is what puts a row in section 5 rather than section 6;
    ``TYPE`` and ``RULE`` are the two the NODE'S OWN handler writes (:data:`LOWERED`).
    ``NAME``, ``ANNOTATION`` and ``NOTHING`` are admitted and cost a handler nothing;
    ``REFUSE`` is the document's own obstruction.
    """

    #: The node's own type, or the class it becomes.  Written by the handler for the
    #: node's kind.
    TYPE = "TYPE"
    #: A fact the ENCLOSING FIELD carries.  The node's own handler writes nothing for
    #: it and the enclosing class's field builder does -- ``default`` at PROP is the
    #: one row the bundle reaches it with -- so the screen at the node admits it.
    FIELD = "FIELD"
    #: A rule on the nearest class, written by the rule lowering.
    RULE = "RULE"
    #: A symbol.  ``title`` at ROOT and at BRANCH, and nothing else.
    NAME = "NAME"
    #: A fact a lowering CARRIES rather than compiles: a description, a deprecation.
    ANNOTATION = "ANNOTATION"
    #: Nothing at all.
    NOTHING = "NOTHING"
    #: The document is refused on this keyword here.
    REFUSE = "REFUSE"


#: The effects that COMPILE TO SOMETHING -- a type, a field or a rule.  Section 6's
#: preamble is the complement of this ("none of these can constrain an instance, so
#: none compiles to a type, a rule or a base"), so :func:`grid_of` reads it.
COMPILES = frozenset({Effect.TYPE, Effect.FIELD, Effect.RULE})

#: The effects the NODE'S OWN handler has to write code for.  ``FIELD`` is not one:
#: the enclosing field carries it, so screening the node for it would refuse a key the
#: parent has already consumed.  A key whose cell is one of these and whose handler
#: claims nothing is a DEFERRAL, never a verdict (semantics section 9); a key whose
#: cell is any other effect is admitted by the screen.
LOWERED = frozenset({Effect.TYPE, Effect.RULE})


class Rung(StrEnum):
    """Section 2's LADDER, lowest first; ``TOP`` always terminates.

    ``docs/plan/rebuild-plan.md`` section 2, "Direction: every approximation of
    acceptance is a widening": a fact the annotation cannot carry is **dropped**, never
    substituted, and the handler takes the lowest rung of this one ladder it can render.
    "``Any`` admits everything, so the ladder always has a rung left and no node can run
    out of renderings."

    The order of the members is the ladder's own order and it is load-bearing: a rung is
    compared to another rung to say which is lower, and section 2's monotonicity is the
    claim that a widening only ever moves up it.
    """

    #: Drop the one keyword, keep the type.  ``uniqueItems`` where no class and no named
    #: type hold the rule -> ``list[X]``.
    KEYWORD = "KEYWORD"
    #: Drop a type selection the constraints contradict, keep the constraints.
    #: ``format: uri`` beside ``maxLength`` -> the constrained ``str``, the format riding
    #: as ``json_schema_extra``.
    TYPE = "TYPE"
    #: Replace a shape with the union of the shapes it holds.  A list-valued ``items`` ->
    #: ``list[A | B | ...]``, dropping position and arity.
    JOIN = "JOIN"
    #: Replace the node with its bare container: ``list[Any]``, ``dict[str, Any]``.
    CONTAINER = "CONTAINER"
    #: ``Any``.
    TOP = "TOP"


#: The rungs, lowest first, as a tuple -- so "lower than" is an index comparison and not
#: a reading of the enum's declaration order by a caller.  Section 2's ladder is "finite,
#: monotone and terminates", and this is the order those three words are about.
LADDER = (Rung.KEYWORD, Rung.TYPE, Rung.JOIN, Rung.CONTAINER, Rung.TOP)


class Cell(NamedTuple):
    """One keyword's answer at one position."""

    #: What it compiles to here.
    effect: Effect
    #: Does a faithful model state this keyword as a fact in ``model_json_schema()``.
    rendered: bool
    #: The position of the subschema(s) this keyword holds, where it holds any.
    descends: Position | None
    #: The sentence the grid states for this keyword here; see the module docstring
    #: for the join rule and for what an empty one means.
    compiles: str
    #: **Which rung of section 2's ladder a keyword the handler cannot render here drops
    #: to** (``docs/plan/architecture.md`` section 3).  ``None`` where the keyword states
    #: no fact about an instance -- ``$comment``, ``title``, ``errorMessage``, the
    #: registry data keys -- "because there is nothing to drop and a rung would be a
    #: decision about a non-decision".
    #:
    #: **A FIELD and not derived**, and section 3 gives the test of that: "``effect``,
    #: ``rendered`` and ``descends`` do not determine it.  ``uniqueItems`` is RULE,
    #: rendered, non-descending and drops its keyword (KEYWORD); a list-valued ``items``
    #: is TYPE, rendered, descends to ELEM and drops to the union of its members (JOIN);
    #: an unrowed key has no row at all and drops the node's whole type (TOP).  Cells
    #: whose other three fields agree take different rungs."
    #:
    #: Its NONE-ness is the one half the effect does decide, and :func:`states_a_fact` is
    #: that reading: a cell that compiles to a type, a field or a rule has a fact to drop
    #: and carries a rung; one that compiles to a name, an annotation or nothing has none.
    #: ``tests/test_keywords.py`` asserts the biconditional over every cell, so a row
    #: added without a rung is a failing test rather than a silent ``None`` that
    #: :func:`codegen.lower.approximate.approximate` would turn into a ``BuildFailure``
    #: at the first document to need it.
    widens_to: Rung | None = None


class Row(NamedTuple):
    """One keyword: a default cell, and an override per position that differs."""

    default: Cell
    #: The positions whose answer differs from :attr:`default`.
    at: Mapping[Position, Cell] = {}
    #: Which of section 5's seven sub-grids this row's line belongs to.  Empty for a
    #: section 6 or section 7 row, whose grid :func:`grid_of` derives.
    grid: str = ""
    #: The grid line's keyword column where it is not the row's own name -- the two
    #: lines whose column is prose rather than a list of keywords.  Every row of one
    #: group carries the same label.
    label: str | None = None


# --------------------------------------------------------------------------- #
# the grids section 5 is written in, and the two section 3 derives
# --------------------------------------------------------------------------- #
#: Section 5's seven sub-tables, in the document's order.  A keyword FAMILY, which is
#: derivable from no other column, so it is declared.
STRUCTURE, VALUES, STRINGS = "structure", "values", "strings"
NUMBERS, ARRAYS, OBJECTS, COMBINATORS = "numbers", "arrays", "objects", "combinators"
SECTION_5 = (STRUCTURE, VALUES, STRINGS, NUMBERS, ARRAYS, OBJECTS, COMBINATORS)
#: Section 6 and section 7, which are projections of the cells and not declared.
ADMITTED, REFUSED = "admitted", "refused"
GRIDS = (*SECTION_5, ADMITTED, REFUSED)

#: The one prefix that admits a keyword by SHAPE rather than by name, and the one
#: exception the semantics document's by-name principle has.
NAMESPACE = "x-"

#: The grid line that stands for the whole vendor namespace, and the sentence every
#: row of it carries.  One line for 29 rows, because section 6 writes one.
_X_LABEL = "the `x-` namespace"
_X_COMPILES = "Nothing, and **still listed by name** — see below."

#: Section 7's second line: the keyword column is prose and the names are in the why
#: column, so the label is the line's and the sentence is every row's.
_REGISTRY_LABEL = "`version`, `lastUpdated`, `vocabulary`, and the registry payload keys"
_REGISTRY_COMPILES = (
    "Nothing. A registry's own instance data sitting at a schema root: `_generated`, "
    "`_generatedAt`, `adcp_version`, `architecture`, `asset_types`, `baseUrl`, "
    "`extensions`, `governance`, `last_updated`, `mappings`, `prerelease`, "
    "`protocol_layers`, `published_version`, `stability`, `usage_notes`, "
    "`versioning`. None of them constrains an instance, and draft-07 says the same "
    "thing by ignoring an unknown key, so an annotation that omits one omits no fact "
    "and admitting it by name says only what is true of instance data. A root stating "
    "only these keys is the empty schema and emits as a permissive root model; a "
    "document stating them BESIDE a real schema emits normally, with the data keys "
    "compiling to nothing."
)


def _nothing(compiles: str = " → nothing.") -> Cell:
    """A cell that compiles to nothing and is carried nowhere."""
    return Cell(Effect.NOTHING, False, None, compiles)


def _group(positions: tuple[Position, ...], cell: Cell) -> dict[Position, Cell]:
    """One cell at several positions, which the grid renders as one clause."""
    return dict.fromkeys(positions, cell)


# --------------------------------------------------------------------------- #
# section 5: how each keyword compiles
# --------------------------------------------------------------------------- #
_STRUCTURE: dict[str, Row] = {
    "type": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "A scalar word → `str` / `int` / `float` / `bool`, unless a constrained "
            "type or `format` selects one. `object` with `properties` → a class; "
            "without → `dict[K, V]`. `array` → `list[X]`. `null` → `None`. A LIST of "
            "words → `A \\| B`, each sibling keyword going to the one type word that "
            "can carry it. Absent → `Any`; absent beside `properties` → an object, "
            "where an enclosing node applies `type: object` to the same instance, and "
            "refused otherwise.",
        ),
        grid=STRUCTURE,
    ),
    "properties": Row(
        Cell(Effect.TYPE, False, Position.PROP, "A class with one field per key."),
        {
            Position.ROOT: Cell(
                Effect.TYPE,
                False,
                Position.PROP,
                " beside a union → fields on the base, inherited by every branch.",
            ),
            **_group(
                (Position.PROP, Position.ELEM, Position.MAPV, Position.DEF),
                Cell(Effect.TYPE, False, Position.PROP, " → a nested class."),
            ),
            Position.BRANCH: Cell(
                Effect.TYPE, False, Position.PROP, " → the branch class."
            ),
            Position.CONJ: Cell(
                Effect.TYPE,
                False,
                Position.PROP,
                " → fields of the composed class. A property two conjuncts declare is "
                "one field: its constraints intersect by §2, and two object "
                "declarations compose as an `allOf` of the two at that property; an "
                "empty intersection — two type words, disjoint enums — refuses, "
                "because the document admits nothing there. A `default` or a "
                "`description` is not a constraint, and the document's own statement "
                "wins over a base's.",
            ),
            Position.RULE: Cell(
                Effect.RULE,
                False,
                Position.PROP,
                ": under `if` → the values a `Match` clause tests, read only where "
                "`const` or `enum`; under `then` / `else` / `not` → nothing.",
            ),
        },
        grid=STRUCTURE,
    ),
    "required": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "The named fields are required: no `\\| None`, no default. Naming a "
            "property no node declares → refused, a presence rule with no field. "
            "`required: []` → nothing.",
        ),
        {
            Position.ROOT: Cell(
                Effect.TYPE,
                True,
                None,
                " beside a union → required on the base's fields, and the names "
                "recorded in `_ROOT_REQUIRED`, so a refusal can separate a field the "
                "root requires from one that selects a branch.",
            ),
            Position.BRANCH: Cell(
                Effect.TYPE,
                True,
                None,
                " → the branch class's requiredness, and the third of the "
                "branch-naming choices.",
            ),
            Position.CONJ: Cell(
                Effect.TYPE,
                True,
                None,
                " → unioned into the composed class's `required`; a `required`-only "
                "conjunct → the overlay.",
            ),
            Position.RULE: Cell(
                Effect.RULE,
                False,
                None,
                " → a presence rule: `RequiredGroups`, `ForbiddenGroups` under `not`, "
                "the keys a `Match` clause tests under `if`, `ConditionalRequired` / "
                "`NegatedConditional` under `then` / `else`.",
            ),
        },
        grid=STRUCTURE,
    ),
    "definitions": Row(
        Cell(
            Effect.NOTHING,
            False,
            Position.DEF,
            "Nothing by itself: a bag of named subschemas. Each entry is declared on "
            "demand when a `$ref` names it, as the node's own kind, under "
            "`<Root><Key>`.",
        ),
        grid=STRUCTURE,
    ),
    "$defs": Row(
        Cell(
            Effect.NOTHING,
            False,
            Position.DEF,
            "Nothing by itself: a bag of named subschemas. Each entry is declared on "
            "demand when a `$ref` names it, as the node's own kind, under "
            "`<Root><Key>`.",
        ),
        grid=STRUCTURE,
    ),
    "$ref": Row(
        Cell(
            Effect.TYPE,
            False,
            None,
            "Another document's root → an IMPORT of that module's symbol; nothing of "
            "the target is copied into the module, and in the document of record (§3) "
            "the target is inlined unchanged. A fragment of another document → an "
            "import of a symbol the target declares. Local `#/…` → the entry decided "
            "on demand in this module; a cycle refuses. An annotation sibling → the "
            "sibling's description wins. A CONSTRAINING sibling → nothing, and "
            "REPORTED: draft-07 ignores every sibling of `$ref`, so the keyword "
            "constrains no instance and the document's accepted set is the target's "
            "alone. The record keeps the key, because §3 drops none; the "
            "declaration's cell says it compiles to nothing at this co-occurrence, so "
            "§8 does not grade it; and the report names it, because a key that reads "
            "as a constraint and is inert is worth reading once. Refusing it instead "
            "would refuse a document whose accepted set its own draft decides, and "
            "letting the referring value win would make the record state an "
            "acceptance fact the bundle does not — §9's last rule.",
        ),
        {
            Position.KEY: Cell(Effect.TYPE, False, None, " → the key type."),
            Position.BRANCH: Cell(
                Effect.TYPE,
                False,
                None,
                " of a root union → a class with two bases; of a nested union → a "
                "member type.",
            ),
            Position.CONJ: Cell(
                Effect.TYPE,
                False,
                None,
                " → a BASE where the target is a class declaring fields. Where it is "
                "not — a scalar, an enum, a container, or a union root, whose instance "
                "is one of its branches — it is not a class a model can extend: the "
                "target is this node's own TYPE, and the other conjuncts and the "
                "`allOf`'s siblings constrain it, which is §2's intersection at a node "
                "that declares no fields of its own.",
            ),
        },
        grid=STRUCTURE,
    ),
}

_VALUES: dict[str, Row] = {
    "const": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "`Literal[value]`; the type word is not restated, since Pydantic renders "
            "it. A `str`, `bool` or `int` value; an object, array, `null` or float "
            "refuses. On a branch's property → also the second of the branch-naming "
            "choices. AT a branch node, pinning the whole branch → the branch is a "
            "scalar: a `Literal` member of the union. Where EVERY branch of a root "
            "union is a scalar there are no branch classes to declare, so the root "
            "emits as an alias over the union of their types — `Literal['asap'] | "
            "AwareDatetime` — and not as a base with branches. A root union with a "
            "scalar branch beside a class branch → refused by name: the root symbol "
            "is a class or an alias, no shape in §4 carries both, and the first "
            "document to state one decides it rather than taking a rendering nothing "
            "has exercised.",
        ),
        {
            Position.RULE: Cell(
                Effect.RULE,
                False,
                None,
                ": under `if` → a `Match` clause's value; under `then` / `else` / "
                "`not` → nothing.",
            )
        },
        grid=VALUES,
    ),
    "enum": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "A named node → `StrEnum` / `IntEnum`, base read off the members; "
            "`enumDescriptions` → member docstrings. An untitled BRANCH of a root "
            "union → a `Literal` of the members. Mixed member types, an empty list, "
            "or a duplicate member → refused. Two members whose spellings yield one "
            "Python name → refused, naming both: a silent collision would drop a "
            "member the document admits.",
        ),
        {
            Position.ROOT: Cell(
                Effect.TYPE,
                True,
                None,
                " → the enum with a module-level `strict_validate`.",
            ),
            Position.PROP: Cell(Effect.TYPE, True, None, " → a nested enum."),
            # **FAITHFUL, and §5's group (a) is the sentence** (§14 step 9): "`propertyNames`
            # with an `enum`, and `enum` at KEY.  Both rows refuse 'by name with the key
            # set'.  A `Literal` of the members is the key type, and Pydantic renders
            # `dict[Literal[…], V]` back as `propertyNames: {enum: […]}` -- the document's
            # own keyword, rendered and gradable.  Faithful, not wide.  Where the key node
            # is named, the `StrEnum` is the key type and renders the same way."
            #
            # ``rendered`` is True for exactly that reason: the fact reaches
            # ``model_json_schema()`` under the document's own keyword, so §8 compares it
            # rather than having to excuse it.
            Position.KEY: Cell(
                Effect.TYPE,
                True,
                None,
                " → a `Literal` of the members as the mapping's KEY type, which "
                "pydantic renders back as `propertyNames: {enum: […]}` — the document's "
                "own keyword, rendered and gradable; where the key node carries a "
                "`title` the `StrEnum` is the key type and renders the same way.",
            ),
            Position.RULE: Cell(
                Effect.RULE,
                False,
                None,
                ": under `if` → `Match` values; else nothing.",
            ),
        },
        grid=VALUES,
    ),
    "default": Row(
        Cell(
            Effect.ANNOTATION,
            True,
            None,
            "On a REQUIRED property → dropped and reported, because no rendering "
            "makes a field both required and defaulted. On a node that becomes an "
            "alias → no slot.",
        ),
        {
            Position.PROP: Cell(
                Effect.FIELD,
                True,
                None,
                " → the field's default; `None` is a default, absence is not.",
            ),
        },
        grid=VALUES,
    ),
}

_STRINGS: dict[str, Row] = {
    "pattern": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "`pattern` on the type, as a named alias. On `format: uri` → selects the "
            "type instead, and the pattern stays with the schema half. The regex "
            "engine is derived per class, because a pattern using look-around needs "
            "Python's engine rather than Rust's.",
        ),
        {
            Position.ROOT: Cell(Effect.TYPE, True, None, " → the root alias over it."),
            **_group(
                (Position.ELEM, Position.BRANCH),
                Cell(
                    Effect.TYPE,
                    True,
                    None,
                    " → the alias as the element or member type.",
                ),
            ),
            Position.KEY: Cell(Effect.TYPE, True, None, " → an annotated `str` key."),
            Position.RULE: _nothing(),
        },
        grid=STRINGS,
    ),
    "format": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "Selects a TYPE where the document's draft asserts the format and a type "
            "is named: `date-time` → `AwareDatetime`, `date` → `datetime.date`, `uri` "
            "→ a URL type chosen by `pattern`. Otherwise rides as "
            '`json_schema_extra={"format": …}` on the field. A `uri` beside another '
            "string constraint → refused: a URL type carries none.",
        ),
        {
            **_group(
                (Position.ELEM, Position.MAPV),
                Cell(
                    Effect.TYPE,
                    True,
                    None,
                    " with no type selected → a named alias carries it.",
                ),
            ),
            Position.BRANCH: Cell(
                Effect.TYPE, True, None, " → the selected type as the member."
            ),
        },
        grid=STRINGS,
    ),
    "minLength": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "`min_length` / `max_length` on the type, as a named alias. On a URL type "
            "→ refused, not representable.",
        ),
        {
            Position.ROOT: Cell(Effect.TYPE, True, None, " → the root alias."),
            **_group(
                (Position.ELEM, Position.MAPV),
                Cell(Effect.TYPE, True, None, " → the alias inside the container."),
            ),
            Position.KEY: Cell(
                Effect.TYPE,
                True,
                None,
                " → the key type, which Pydantic renders back as "
                "`propertyNames.minLength`.",
            ),
            Position.RULE: _nothing(),
        },
        grid=STRINGS,
    ),
    "maxLength": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "`min_length` / `max_length` on the type, as a named alias. On a URL type "
            "→ refused, not representable.",
        ),
        {
            Position.ROOT: Cell(Effect.TYPE, True, None, " → the root alias."),
            **_group(
                (Position.ELEM, Position.MAPV),
                Cell(Effect.TYPE, True, None, " → the alias inside the container."),
            ),
            Position.KEY: Cell(
                Effect.TYPE,
                True,
                None,
                " → the key type, which Pydantic renders back as "
                "`propertyNames.minLength`.",
            ),
            Position.RULE: _nothing(),
        },
        grid=STRINGS,
    ),
}

_BOUND_COMPILES = (
    "`ge` / `le` on the type: a standard Pydantic type where one says exactly this, a "
    "named alias otherwise."
)
_BOUND_AT = {
    **_group(
        (Position.ELEM, Position.MAPV),
        Cell(Effect.TYPE, True, None, " → the alias inside the container."),
    ),
    Position.BRANCH: Cell(Effect.TYPE, True, None, " → the alias as the member type."),
    Position.RULE: _nothing(),
}
_EXCLUSIVE_COMPILES = (
    "`gt` / `lt` on the type, **never `ge` / `le`**. The bundle distinguishes "
    "`minimum: 0` from `exclusiveMinimum: 0`, and the two differ on exactly one "
    "instance, so rendering either as the other makes a field accept a zero its "
    "document refuses or refuse a zero its document accepts."
)

_NUMBERS: dict[str, Row] = {
    "minimum": Row(
        Cell(Effect.TYPE, True, None, _BOUND_COMPILES), _BOUND_AT, grid=NUMBERS
    ),
    "maximum": Row(
        Cell(Effect.TYPE, True, None, _BOUND_COMPILES), _BOUND_AT, grid=NUMBERS
    ),
    "exclusiveMinimum": Row(
        Cell(Effect.TYPE, True, None, _EXCLUSIVE_COMPILES), grid=NUMBERS
    ),
    "exclusiveMaximum": Row(
        Cell(Effect.TYPE, True, None, _EXCLUSIVE_COMPILES), grid=NUMBERS
    ),
    "multipleOf": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "Unused by the bundle. The first document to carry one refuses by name, "
            "rather than taking a rendering nothing has exercised.",
        ),
        grid=NUMBERS,
    ),
}

_ITEM_BOUND_COMPILES = (
    "`min_length` / `max_length` on the annotation of the **array's own type**, at "
    "every position. `minItems: 0` states nothing. `constraints` declares it once, "
    "generically, as `type NonEmptyList[T] = Annotated[list[T], "
    "Field(min_length=1)]`."
)
_ITEM_BOUND_AT = {
    Position.PROP: Cell(Effect.TYPE, True, None, " → on the field."),
    **_group(
        (Position.ELEM, Position.MAPV, Position.DEF),
        Cell(
            Effect.TYPE,
            True,
            None,
            " → the container's type must be named to carry it.",
        ),
    ),
    Position.BRANCH: Cell(
        Effect.TYPE,
        True,
        None,
        " → on the branch's own type, never on the field holding the union.",
    ),
    Position.RULE: _nothing(),
}

_ARRAYS: dict[str, Row] = {
    "items": Row(
        Cell(
            Effect.TYPE,
            False,
            Position.ELEM,
            "`list[X]`, X decided by the same walk and named where it needs a symbol. "
            "A list-valued `items` → refused: that is tuple validation.",
        ),
        {
            Position.ROOT: Cell(
                Effect.TYPE, False, Position.ELEM, " array → `RootModel[list[X]]`."
            ),
            Position.RULE: Cell(
                Effect.NOTHING, False, Position.ELEM, " → nothing."
            ),
        },
        grid=ARRAYS,
    ),
    "minItems": Row(
        Cell(Effect.TYPE, True, None, _ITEM_BOUND_COMPILES), _ITEM_BOUND_AT, grid=ARRAYS
    ),
    "maxItems": Row(
        Cell(Effect.TYPE, True, None, _ITEM_BOUND_COMPILES), _ITEM_BOUND_AT, grid=ARRAYS
    ),
    "uniqueItems": Row(
        Cell(
            Effect.RULE,
            True,
            None,
            "A `UniqueItems` rule on the class holding the array, plus "
            '`json_schema_extra={"uniqueItems": true}` on the field so it is graded, '
            "and the keyword is stripped off the array's own declaration. Where no "
            "class sits above the array → a `Distinct` after-validator on its own "
            "annotated type, beside the same `json_schema_extra`.",
        ),
        grid=ARRAYS,
    ),
    #: ``TYPE`` and not ``RULE``, and the distinction is D6's six families: a
    #: ``contains`` at a field position is an ``AtLeastOne`` after-validator on the
    #: ARRAY'S OWN annotated type (§7 of the architecture document puts those on
    #: ``TypeRef.validators``), where a RULE cell is one ``lower/rules.py`` writes into
    #: a class's rule tuple.  Declared ``RULE`` it joined ``rule_sources`` and a
    #: composing root carrying a ``contains`` was ADMITTED -- measured on the probe in
    #: ``tests/test_emit_product.py``, which reported the document on the conjunct's
    #: ``$ref`` instead of on the keyword that is the reason.
    "contains": Row(
        Cell(
            Effect.TYPE,
            False,
            Position.ELEM,
            "An existential quantifier — `items` constrains every element, `contains` "
            "says at least one matches — and the model states the **predicate**, not "
            "a transcription of the subschema. A field position → an `AtLeastOne` "
            "after-validator on the array's own annotated type: "
            "`AtLeastOne(**{property: const})` where the subschema requires "
            "properties pinned to a const, `AtLeastOne(value)` where it is a bare "
            "`const` or a one-member `enum`. Any other predicate at a field position "
            "— a bound, a pattern, a nested `contains`, a `$ref` — → refused by name: "
            "a transcription of the subschema is the thing this row declines to emit, "
            "and the first document to state such a predicate decides its rendering.",
        ),
        {
            Position.RULE: Cell(
                Effect.RULE,
                False,
                Position.ELEM,
                " position → a `Match` MEMBERSHIP clause, `value in field`, and no "
                "validator.",
            )
        },
        grid=ARRAYS,
    ),
}

_OBJECTS: dict[str, Row] = {
    "additionalProperties": Row(
        Cell(
            Effect.TYPE,
            True,
            Position.MAPV,
            "The empty schema `{}` IS `true` and is read as `true` everywhere below, "
            "never as a typed value schema. On a class: `false` → `forbid`; `true` → "
            "`allow`; typed → `allow` with a typed `__pydantic_extra__`; absent → "
            "`ignore`. On a mapping (no `properties`) → the VALUE type; `true` or "
            "`{}` → `Any`; `false` → refused, it admits only the empty object. Beside "
            "`patternProperties` → refused, two value schemas. `false` on an `allOf` "
            "overlay would reject the fields its sibling conjunct contributes, which "
            "is why `true` is the only value an overlay can carry.",
        ),
        {
            Position.ROOT: Cell(
                Effect.TYPE,
                True,
                Position.MAPV,
                " beside a union → the same, on the base, inherited by every branch; "
                "a branch stating its own composes with it by the CONJ rule below.",
            ),
            Position.CONJ: Cell(
                Effect.TYPE,
                True,
                Position.MAPV,
                " → `true` is the identity and contributes nothing, `false` on any "
                "conjunct closes the composed object, and two typed ones intersect "
                "their value schemas; a typed conjunct beside a `true` one is a "
                "widening and refuses.",
            ),
        },
        grid=OBJECTS,
    ),
    "patternProperties": Row(
        Cell(
            Effect.TYPE,
            False,
            Position.MAPV,
            "A mapping whose KEY carries the pattern: `dict[Annotated[str, "
            "StringConstraints(pattern=…)], V]`, which Pydantic renders back as "
            "`patternProperties` — the document's own keyword. More than one pattern "
            "→ refused: that is a value schema per key shape. Beside a non-`false` "
            "`additionalProperties` → refused.",
        ),
        grid=OBJECTS,
    ),
    "propertyNames": Row(
        Cell(
            Effect.TYPE,
            False,
            Position.KEY,
            "The mapping's KEY type: a `$ref` → that type; `minLength` / `maxLength` "
            "→ a length-bounded `str`; `pattern` → an annotated `str`; `enum` → a "
            "`Literal` of the members, which pydantic renders back as this very "
            "keyword; `anyOf` → a union of key types. Beside "
            "`patternProperties` → the key type carries both, by §2's intersection: "
            "each states a constraint on the same key. On a CLASS with declared "
            "`properties` → checked against the declared names when the class is "
            "emitted and carried nowhere, because those names are fixed and known; a "
            "declared name the constraint refuses is a contradiction in the document "
            "and refuses by name. Where that class also admits extras, a key beyond "
            "the declared names is checked by the schema half alone, and the model is "
            "looser than its document there, which §2 permits.",
        ),
        {
            Position.RULE: Cell(
                Effect.NOTHING,
                False,
                Position.KEY,
                " position → nothing on the model: a rule position constrains which "
                "keys a conditional *tests*, so there is no key type to annotate and "
                "no value to hang a validator on.",
            )
        },
        grid=OBJECTS,
    ),
    "minProperties": Row(
        Cell(
            Effect.RULE,
            False,
            None,
            "On a class → a `PropertyCount` rule. `minProperties` is written only "
            "where `additionalProperties` is stated, because a dropped key would make "
            "the rule refuse what the document accepts; `maxProperties` needs no such "
            "gate, since a dropped key only lowers the count. On a mapping → "
            "`Field(min_length / max_length)` on the dict's type, because a "
            "`PropertyCount` rule counts declared fields and a dict has none.",
        ),
        grid=OBJECTS,
    ),
    "maxProperties": Row(
        Cell(
            Effect.RULE,
            False,
            None,
            "On a class → a `PropertyCount` rule. `minProperties` is written only "
            "where `additionalProperties` is stated, because a dropped key would make "
            "the rule refuse what the document accepts; `maxProperties` needs no such "
            "gate, since a dropped key only lowers the count. On a mapping → "
            "`Field(min_length / max_length)` on the dict's type, because a "
            "`PropertyCount` rule counts declared fields and a dict has none.",
        ),
        grid=OBJECTS,
    ),
    "dependencies": Row(
        Cell(
            Effect.RULE,
            False,
            None,
            "The list form → a `Dependencies` rule: if A is present, B is required. "
            "The schema form refuses by name on the first occurrence, rather than "
            "being skipped.",
        ),
        grid=OBJECTS,
    ),
}

_COMBINATORS: dict[str, Row] = {
    "allOf": Row(
        Cell(Effect.TYPE, False, Position.CONJ, ""),
        {
            Position.ROOT: Cell(
                Effect.TYPE,
                False,
                Position.CONJ,
                " with no union beside → `$ref` conjuncts are BASES, inline conjuncts "
                "are fields and rules of this class; beside a union → the same, onto "
                "the base: `$ref` conjuncts are the base's bases and inline conjuncts "
                "are its fields and rules, and every branch inherits them.",
            ),
            **_group(
                (Position.PROP, Position.ELEM, Position.DEF),
                Cell(
                    Effect.TYPE,
                    False,
                    Position.CONJ,
                    " → the same reader at the node's own pointer.",
                ),
            ),
            Position.BRANCH: Cell(
                Effect.TYPE,
                False,
                Position.CONJ,
                " → the branch class composes, with the union base first.",
            ),
            Position.CONJ: Cell(
                Effect.TYPE,
                False,
                Position.CONJ,
                " → the same rule applied to the conjunct's own conjuncts.",
            ),
            Position.RULE: Cell(
                Effect.RULE,
                False,
                Position.CONJ,
                ": under `not` → single-group conjuncts merge into one group; else "
                "nothing.",
            ),
        },
        grid=COMBINATORS,
    ),
    "oneOf": Row(
        Cell(
            Effect.TYPE,
            False,
            Position.BRANCH,
            "Presence-only, every branch `required`-only → a `RequiredGroups` rule "
            "naming the combinator. Shapes at ROOT → the base plus one class per "
            "branch. Shapes nested → one type `A \\| B`; a sibling beside it refuses. "
            "For `oneOf`, `A \\| B` admits an instance satisfying two branches and the "
            "schema half enforces exclusivity. A union whose branches declare the same "
            "properties with the same `required`, and differ only in the `const` or "
            "`enum` each pins on some of them → one class: each such field admits the "
            "union of the branches' values, and one rule whose clauses are the "
            "branches themselves — one clause per branch pinning that branch's values, "
            "satisfied when the instance matches at least one clause. A branch that "
            "differs in a type, a bound, a format, a nested shape or its `required` is "
            "a branch of shapes and takes the base-plus-branches answer. For `oneOf` "
            "the schema half enforces exclusivity, as it does for `A \\| B`.",
        ),
        {
            Position.KEY: Cell(
                Effect.TYPE, False, Position.BRANCH, " → a union of key types."
            ),
            Position.CONJ: Cell(
                Effect.TYPE,
                False,
                Position.BRANCH,
                " → one class per branch over the composed bases.",
            ),
            Position.RULE: Cell(
                Effect.RULE,
                False,
                Position.BRANCH,
                ": under `not` → the union of the branches' groups; else nothing.",
            ),
        },
        grid=COMBINATORS,
    ),
    "if": Row(
        Cell(
            Effect.RULE,
            False,
            Position.RULE,
            "A `Match` clause list where it states `required` plus `properties` with "
            "`const` or `enum` values; otherwise nothing, and the schema half answers. "
            "With `then` / `else` → a rule on the nearest class.",
        ),
        grid=COMBINATORS,
    ),
    "then": Row(
        Cell(
            Effect.RULE,
            False,
            Position.RULE,
            "`ConditionalRequired` / `NegatedConditional` from its `required` and a "
            "single-name `not`. Its `properties` → nothing on the model; the schema "
            "half narrows the value.",
        ),
        grid=COMBINATORS,
    ),
    "not": Row(
        Cell(
            Effect.RULE,
            False,
            Position.RULE,
            "`not: {required: …}`, and `anyOf` / `allOf` of those → a "
            "`ForbiddenGroups` rule. Over a `const` or `enum` → a `NotValue` "
            "after-validator on the value's own annotated type. Any other shape → "
            "nothing on the model; the schema half answers and the ceiling is named. "
            "`not: {}` admits nothing, which the typeless `Any` carries.",
        ),
        grid=COMBINATORS,
    ),
}
# ``anyOf`` is ``oneOf``'s row and ``else`` is ``then``'s: section 5 writes one line
# for each pair, which is the grid's own way of saying the two cells are equal.
_COMBINATORS["anyOf"] = _COMBINATORS["oneOf"]
_COMBINATORS["else"] = _COMBINATORS["then"]


# --------------------------------------------------------------------------- #
# section 6: keywords we admit and do not compile
# --------------------------------------------------------------------------- #
_ENUM_DESCRIPTIONS = Row(
    Cell(
        Effect.ANNOTATION,
        False,
        None,
        "Member docstrings on the enumeration, keyed by the member's value. Two "
        "spellings of one keyword; both are read.",
    )
)

_ADMITTED: dict[str, Row] = {
    "$schema": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing on the class, but it selects the **validator** the schema half "
            "runs, and through it the format checkers a type may be selected for. The "
            "one annotation that decides a behaviour, and it decides it on the schema "
            "half.",
        )
    ),
    "title": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nested → nothing: a nested node is named by its property or entry key. "
            "Its presence selects `StrEnum` over `Literal` for an enum node. Never "
            "rendered.",
        ),
        {
            Position.ROOT: Cell(Effect.NAME, False, None, " → the symbol."),
            Position.BRANCH: Cell(
                Effect.NAME, False, None, " → the branch class's name."
            ),
        },
    ),
    "description": Row(
        Cell(
            Effect.ANNOTATION,
            True,
            None,
            "A `$ref` sibling's description wins over the target's; a composed base's "
            "loses to the document's own.",
        ),
        {
            Position.ROOT: Cell(
                Effect.ANNOTATION,
                True,
                None,
                " class → the docstring; ROOT alias → `Field(description=…)`; ROOT "
                "enum → the enum's docstring.",
            ),
            Position.PROP: Cell(
                Effect.ANNOTATION, True, None, " → `Field(description=…)`."
            ),
            **_group(
                (Position.ELEM, Position.MAPV),
                Cell(Effect.ANNOTATION, True, None, " → the named alias carries it."),
            ),
            Position.BRANCH: Cell(
                Effect.ANNOTATION,
                True,
                None,
                " that is a class → its docstring; a non-object branch of a nested "
                "union → its own annotated type.",
            ),
            **_group((Position.CONJ, Position.RULE), _nothing()),
        },
    ),
    "examples": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing on the model. The accepts check replays every one, at every "
            "position: a ROOT example constructs the class, and an example at a "
            "nested node is validated against that node's own annotated type. A "
            "payload the document refuses is a spec defect, reported by document and "
            "pointer; one the document accepts and the class refuses is ours.",
        )
    ),
    "$comment": Row(
        Cell(Effect.NOTHING, False, None, "Nothing. A note to a reader.")
    ),
    "readOnly": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing. Pydantic can render them, but the SDK has one model per document "
            "and no read/write split for them to state.",
        )
    ),
    "writeOnly": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing. Pydantic can render them, but the SDK has one model per document "
            "and no read/write split for them to state.",
        )
    ),
    #: **``rendered`` is FALSE here and §6's row says "Rendered, so graded" -- a
    #: DEVIATION, measured, and reported on the row rather than resolved by this one.**
    #:
    #: The emitter writes nothing for ``deprecated``: no ``Field(deprecated=True)``, no
    #: ``json_schema_extra`` on a class.  Measured by setting this cell to ``True`` and
    #: grading the committed tree: 117 pairs over 105 documents report the keyword
    #: ``missing`` -- 115 at a property of a root class, 25 at a property of a nested
    #: one, 11 at a class root, 2 inside an array element -- and NOTHING ELSE moves.
    #: The report is correct: the model does not state a fact its document states.
    #:
    #: It is not resolved here because the emitter half is a handler edit and §14 gives
    #: no step that carries it: step 8's list of unwritten cells names root siblings on
    #: a union base, a scalar target as a composing node's type, the type-bound
    #: validators for ``uniqueItems``/``contains``/``not``, a one-class union, and the
    #: manifest dispatch source -- and not this.  So the choice at this row is between
    #: a declaration that states what §6 states and 117 red pairs with no row to clear
    #: them, or this line.  Flipping it is the whole of the change once a row owns the
    #: emitter half, and the measurement above is what that row inherits.
    "deprecated": Row(
        Cell(Effect.NOTHING, False, None, "A `false` → nothing. Rendered, so graded."),
        {
            **_group(
                (Position.ROOT, Position.BRANCH),
                Cell(
                    Effect.ANNOTATION,
                    False,
                    None,
                    " → the class's `json_schema_extra`.",
                ),
            ),
            Position.PROP: Cell(
                Effect.ANNOTATION, False, None, " → `Field(deprecated=True)`."
            ),
        },
    ),
    "enumDescriptions": _ENUM_DESCRIPTIONS,
    "x-enum-descriptions": _ENUM_DESCRIPTIONS,
    "enumMetadata": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing: recovery and action metadata for a reader. The `enum` beside it "
            "has already closed the value set.",
        )
    ),
    "notes": Row(
        Cell(Effect.NOTHING, False, None, "Nothing: English sentences for a reader.")
    ),
    "discriminator": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing on the class. It names a branch where that branch pins more than "
            "one `const`, and separately it **confirms** a dispatch key the branches "
            "already state — it does not establish one. A union whose branches pin a "
            "distinct const dispatches on that property whether or not the keyword is "
            "present, and a declared keyword the branches do not confirm is not a "
            "dispatch source.",
        )
    ),
}

#: Every `x-` key the bundle carries, less `x-enum-descriptions`, which section 6
#: lists on its own line because it CARRIES something.  The namespace rule admits a
#: prefixed key by shape; the names are kept as well because the prefix rule dropped
#: `x-enum-descriptions` silently once, and because a prefixed key with no row here is
#: admitted and REPORTED rather than assumed to be metadata.
_EXTENSIONS = (
    "x-accessibility",
    "x-added-in",
    "x-adcp-file-size-units",
    "x-adcp-hoist",
    "x-adcp-model-context-inline",
    "x-adcp-open-payload",
    "x-adcp-schema-uri",
    "x-adcp-sdk-local",
    "x-adcp-validation",
    "x-canonical-policy-required-params-not-enforced",
    "x-canonicalization",
    "x-compatibility-projection-only",
    "x-deprecated-enum-values",
    "x-deprecated-enum-values-doc",
    "x-deprecated-in",
    "x-entity",
    "x-entity-definitions",
    "x-extensible",
    "x-governed-commitment",
    "x-idempotency-key-required",
    "x-legacy-fallback",
    "x-mutates-state",
    "x-operation-family",
    "x-pattern",
    "x-removed-in",
    "x-status",
    "x-superseded-by",
    "x-task-result-schema-overrides",
    "x-tool-summary",
)
for _name in _EXTENSIONS:
    _ADMITTED[_name] = Row(
        Cell(Effect.NOTHING, False, None, _X_COMPILES), label=_X_LABEL
    )


# --------------------------------------------------------------------------- #
# section 7: keywords we refuse
# --------------------------------------------------------------------------- #
#: A registry's own instance data at a schema root.  Section 7 names them on one line
#: and the names are in its why column, so every row carries that line's label.
_REGISTRY_KEYS = (
    "version",
    "lastUpdated",
    "vocabulary",
    "_generated",
    "_generatedAt",
    "adcp_version",
    "architecture",
    "asset_types",
    "baseUrl",
    "extensions",
    "governance",
    "last_updated",
    "mappings",
    "prerelease",
    "protocol_layers",
    "published_version",
    "stability",
    "usage_notes",
    "versioning",
)

_REFUSED: dict[str, Row] = {
    "errorMessage": Row(
        Cell(
            Effect.REFUSE,
            False,
            None,
            "An `ajv-errors` extension customising a validator's message. It has no "
            "Pydantic rendering, and a conjunct carrying one contributes nothing, so "
            "the drop is reported rather than silent.",
        )
    )
}
# **The registry data keys are NOTHING at every position** (section 6 of the semantics
# document, and section 3 of the architecture document: "`errorMessage` and the registry
# data keys move into section 6's projection, where they always belonged: each is NOTHING
# at every position").  Section 7 says why the REFUSE cell was never a statement about the
# document's accepted set: "the first half was answering a question nobody asked --
# admitting a key by name says it carries no acceptance meaning, which for instance data is
# simply true, and draft-07 says the same thing by ignoring it. The second half was real --
# the refusal was a SIGNAL about the document, not a statement about its accepted set --
# and a refusal is the wrong instrument for a signal, because it costs the document its
# type to carry it."
#
# The signal survives where section 7 puts it: a root stating only these keys emits as a
# permissive root model (section 4's last table row), which is a document whose whole type
# is `Any` -- as visible in the emitted module as a refusal was in the report -- and the
# upstream request, that the registry either drop its `$schema` or declare a schema, is the
# issue list's and not a declaration's (section 5(b), corrected 2026-10-26).
#
# They stay in `_REFUSED` as the dict this file builds the table from and leave section 7's
# PROJECTION, because `grid_of` reads the EFFECT and not the dict: a row NOTHING at every
# position projects into section 6.
for _name in _REGISTRY_KEYS:
    _REFUSED[_name] = Row(
        Cell(Effect.NOTHING, False, None, _REGISTRY_COMPILES), label=_REGISTRY_LABEL
    )


# --------------------------------------------------------------------------- #
# the rung each keyword drops to, and the pass that puts it in the cell
# --------------------------------------------------------------------------- #
def states_a_fact(effect: Effect) -> bool:
    """Does a cell with this effect have a FACT a widening could drop.

    ``docs/plan/architecture.md`` section 3: ``widens_to`` "is ``None`` for a keyword
    that states no fact about an instance -- ``$comment``, ``title``, ``errorMessage``,
    the registry data keys -- because there is nothing to drop and a rung would be a
    decision about a non-decision."

    That is exactly :data:`COMPILES`: section 6's preamble is this predicate's
    complement ("none of these can constrain an instance, so none compiles to a type, a
    rule or a base"), and a ``NAME`` is a symbol, an ``ANNOTATION`` is a description or
    a deprecation, and a ``REFUSE`` cell refuses the document instead of widening it.
    So the NONE-ness of ``widens_to`` is decided by the effect and its VALUE is not,
    which is the division section 3 draws when it says the field is needed because
    "cells whose other three fields agree take different rungs".
    """
    return effect in COMPILES


#: **The rung each keyword drops to, one entry per keyword that states a fact anywhere**
#: (``docs/plan/architecture.md`` section 3, "Where the RUNG of a widening comes from").
#: Written per KEYWORD because section 2 says so -- "which rung a keyword takes is the
#: keyword's decision and lives in its cell (section 5), never at the site that widens"
#: -- and a keyword's reach is the same fact at every position except where
#: :data:`_RUNG_AT` names one.
#:
#: **Four entries are section 5's own words and the rest are one stated rule.**  Section
#: 5's "(b) Rows whose answer is a declared widening" names a rung for four cells, and
#: each is here with that rung:
#:
#: * ``uniqueItems`` and ``contains`` -- "Rung KEYWORD: the array is ``list[X]`` and the
#:   duplicate or existential check is the schema half's alone";
#: * ``items`` -- "A list-valued ``items``.  Rung JOIN: ``list[A \\| B \\| ...]`` over the
#:   positional schemas, dropping position and arity";
#: * ``allOf`` -- "An ``allOf`` restatement that neither matches nor narrows.  Rung
#:   KEYWORD: the field takes the base's declaration and the restatement's extra facts
#:   are dropped."
#:
#: The rest take the rung that follows from WHAT THE KEYWORD CONSTRAINS, which is the
#: only thing a rung can be a function of -- section 2's ladder is ordered by how much
#: of a node a drop costs:
#:
#: * a keyword that SELECTS the type word drops that selection and keeps the
#:   constraints, which is the ladder's own second rung and its own example
#:   (``format: uri`` beside ``maxLength``): ``type``, ``format`` -> ``TYPE``;
#: * a keyword holding ALTERNATIVE subschemas is replaced by the union of the shapes it
#:   holds, the ladder's third rung: ``oneOf``, ``anyOf``, ``items`` -> ``JOIN``;
#: * a keyword declaring the node's CONTAINER leaves the bare container, the ladder's
#:   fourth rung (``dict[str, Any]``): ``properties``, ``additionalProperties``,
#:   ``patternProperties``, ``propertyNames`` -> ``CONTAINER``;
#: * a keyword whose reach is ANOTHER DOCUMENT's is unknown here, and section 6 of the
#:   architecture document says what that costs -- a fragment the target declared no
#:   symbol at widens "to the target's own root symbol where the fragment is reachable
#:   under it and to TOP otherwise" -- so ``$ref`` -> ``TOP``, which is the rung that is
#:   safe without knowing;
#: * everything else is ONE CONSTRAINT among others on a type that survives the drop,
#:   which is the ladder's first rung: every bound, every pattern, every pinned value,
#:   every rule.
#:
#: **A fact-stating cell whose keyword is not here is a ``BuildFailure`` at import**
#: (:func:`_with_rungs`), so a row added later cannot reach a handler with a ``None``
#: rung and be told at that handler that it has no rung -- which is where
#: ``approximate`` would report a decision nobody made as a compiler defect.
_RUNG: Mapping[str, Rung] = {
    # structure
    "type": Rung.TYPE,
    "properties": Rung.CONTAINER,
    "required": Rung.KEYWORD,
    "$ref": Rung.TOP,
    # values
    "const": Rung.KEYWORD,
    "enum": Rung.KEYWORD,
    "default": Rung.KEYWORD,
    # strings
    "pattern": Rung.KEYWORD,
    "format": Rung.TYPE,
    "minLength": Rung.KEYWORD,
    "maxLength": Rung.KEYWORD,
    # numbers
    "minimum": Rung.KEYWORD,
    "maximum": Rung.KEYWORD,
    "exclusiveMinimum": Rung.KEYWORD,
    "exclusiveMaximum": Rung.KEYWORD,
    "multipleOf": Rung.KEYWORD,
    # arrays
    "items": Rung.JOIN,
    "minItems": Rung.KEYWORD,
    "maxItems": Rung.KEYWORD,
    "uniqueItems": Rung.KEYWORD,
    "contains": Rung.KEYWORD,
    # objects
    "additionalProperties": Rung.CONTAINER,
    "patternProperties": Rung.CONTAINER,
    "propertyNames": Rung.CONTAINER,
    "minProperties": Rung.KEYWORD,
    "maxProperties": Rung.KEYWORD,
    "dependencies": Rung.KEYWORD,
    # combinators and conditionals
    "allOf": Rung.KEYWORD,
    "oneOf": Rung.JOIN,
    "anyOf": Rung.JOIN,
    "if": Rung.KEYWORD,
    "then": Rung.KEYWORD,
    "else": Rung.KEYWORD,
    "not": Rung.KEYWORD,
}

#: The positions whose rung differs from the keyword's own, with the sentence that
#: decides each.  Section 5's "(b)" has one such row: "**An empty intersection** -- two
#: disjoint type words, two disjoint enums.  The node admits nothing, which is a
#: contradiction in the document.  Rung TOP, and this is the answer the ``not`` row
#: already gives for ``not: {}``."
#:
#: A conjunct is at CONJ, so the cell that row names is ``type`` and ``enum`` THERE, and
#: it differs from those keywords' own rungs (``TYPE`` and ``KEYWORD``) -- which is the
#: test section 3 sets for a position override existing at all.
#:
#: Where the row has no override CELL at that position, :func:`_with_rungs` synthesises
#: one from the default with an EMPTY ``compiles``, which is the module docstring's own
#: rule for a cell that differs in nothing a grid line states: "An override whose
#: ``compiles`` is EMPTY renders no clause: it records a cell the default sentence
#: already covers in prose."  So the generated grids do not move for a rung.
_RUNG_AT: Mapping[tuple[str, Position], Rung] = {
    ("type", Position.CONJ): Rung.TOP,
    ("enum", Position.CONJ): Rung.TOP,
}


def _with_rungs(table: dict[str, Row]) -> dict[str, Row]:
    """Every cell of ``table``, with :attr:`Cell.widens_to` filled from the declaration.

    One pass and not 107 positional arguments, for the reason the rung is declared per
    keyword rather than per cell: a reader auditing "which rung does this keyword drop
    to" reads one mapping with the rule beside it, where 107 trailing arguments can only
    be audited by reading all of them.  The CELL is what carries the answer afterwards --
    section 3's "``widens_to`` enters the cell" -- and
    :func:`codegen.lower.approximate.approximate` reads it there and nowhere else.

    Raises :class:`codegen.refusal.BuildFailure`'s own condition as a ``ValueError``
    here, because this module imports nothing of this package (section 11: the
    declaration layer is a leaf) and a malformed table is a defect in the compiler that
    must stop the import rather than reach a handler.
    """
    out: dict[str, Row] = {}
    for keyword, row in table.items():
        rung = _RUNG.get(keyword)
        compiling = any(states_a_fact(c.effect) for c in (row.default, *row.at.values()))
        if rung is None and compiling:
            raise ValueError(
                f"{keyword!r} has a cell that compiles to a type, a field or a rule and "
                "no entry in _RUNG: section 3 of the architecture document makes the "
                "rung the keyword's own decision, so a keyword with a fact to drop has "
                "to say which rung dropping it takes"
            )
        if rung is not None and not compiling:
            raise ValueError(
                f"{keyword!r} has an entry in _RUNG and no cell that compiles to "
                "anything: a rung for a keyword with nothing to drop is a decision "
                "about a non-decision (section 3), so the entry has to go"
            )
        at_cells = {
            position: _filled(cell, _RUNG_AT.get((keyword, position), rung))
            for position, cell in row.at.items()
        }
        for (kw, position), override in _RUNG_AT.items():
            if kw != keyword or position in at_cells:
                continue
            if not states_a_fact(row.default.effect):
                raise ValueError(
                    f"_RUNG_AT names ({kw!r}, {position}) and the cell there compiles to "
                    "nothing, so there is no fact for a rung to be about"
                )
            # The module docstring's own rule for a cell that differs in nothing a grid
            # line states: an EMPTY ``compiles`` renders no clause.
            at_cells[position] = row.default._replace(widens_to=override, compiles="")
        out[keyword] = row._replace(default=_filled(row.default, rung), at=at_cells)
    return out


def _filled(cell: Cell, rung: Rung | None) -> Cell:
    """``cell`` with its rung, or unchanged where it states no fact to drop."""
    return cell._replace(widens_to=rung) if states_a_fact(cell.effect) else cell


#: **The table.**  Insertion order is the document's own grid order, because a grid
#: line's position in its sub-table is read off it.
TABLE: Mapping[str, Row] = _with_rungs(
    {
        **_STRUCTURE,
        **_VALUES,
        **_STRINGS,
        **_NUMBERS,
        **_ARRAYS,
        **_OBJECTS,
        **_COMBINATORS,
        **_ADMITTED,
        **_REFUSED,
    }
)


# --------------------------------------------------------------------------- #
# the readings
# --------------------------------------------------------------------------- #
def cell(keyword: str, position: Position) -> Cell | None:
    """This keyword's answer at this position, or ``None`` where it has no row.

    ``None`` is the answer that refuses the document BY NAME: a keyword in none of
    sections 5, 6 and 7 is one the bundle does not use, and the first document to
    carry one is loud rather than ignored.  A caller distinguishes it from every
    other answer, which is why it is ``None`` and not a REFUSE cell -- the two have
    different reasons and a reader should not have to tell them apart by prose.
    """
    row = TABLE.get(keyword)
    if row is None:
        return None
    return row.at.get(position, row.default)


def rendered_at(position: Position) -> frozenset[str]:
    """The comparison's compared set: every keyword a faithful model RENDERS here.

    Section 8 of the semantics document: "the comparison's keyword set equals the set
    the declaration renders.  A keyword the declaration renders and the comparison
    does not carry is a defect in the comparison.  Nothing else in this section means
    anything until that holds, because every other check inherits its reach."
    """
    return frozenset(k for k in TABLE if (c := cell(k, position)) is not None and c.rendered)


def descends_at(position: Position) -> Mapping[str, Position]:
    """The structural keywords at this position and the position each one's
    subschema(s) occupy -- the ONE descent table, where today there are three.

    Declared here; its readers are section 14 step 5's and are not built by this row.
    """
    out: dict[str, Position] = {}
    for keyword in TABLE:
        answer = cell(keyword, position)
        if answer is not None and answer.descends is not None:
            out[keyword] = answer.descends
    return out


def lowers(answer: Cell) -> bool:
    """Does the NODE'S OWN handler have to write something for this cell."""
    return answer.effect in LOWERED


def rule_sources(position: Position) -> frozenset[str]:
    """The keywords whose cell at ``position`` compiles to a RULE.

    Here rather than in ``compiler.py`` because ``codegen/schema/parse.py`` classifies a
    node's rule sources (§4) and the decision layer screens and lowers them, so both read
    one declaration -- which is §11's layering: this is the declaration layer, and a
    predicate over a cell is a reader of the table and not a second copy of it.
    """
    return frozenset(
        k for k in TABLE if (c := cell(k, position)) is not None and c.effect is Effect.RULE
    )


def combinators(position: Position) -> frozenset[str]:
    """``oneOf`` and ``anyOf``, read off the DESCENT column rather than named.

    They are the keywords whose subschemas occupy a BRANCH, which is what a combinator
    IS -- so the pair is a reading of the declaration and not a literal.
    """
    return frozenset(
        k for k in TABLE if (c := cell(k, position)) is not None and c.descends is Position.BRANCH
    )


def declares(keyword: str, position: Position) -> bool:
    """Does this key STATE something about an instance at this position?

    The question the parser's classification asks of a branch (``parse._required_only``)
    and of a node's annotations, and the one the screen asks in the other direction.  A
    key that annotates without constraining is not a declaration; a key with no row is,
    because a keyword the bundle did not use before could constrain anything.
    """
    answer = cell(keyword, position)
    if answer is None:
        return not admitted_by_prefix(keyword)
    return lowers(answer) or answer.effect is Effect.REFUSE


def admitted_by_prefix(keyword: str) -> bool:
    """The one admission by SHAPE: a vendor extension cannot be a schema keyword."""
    return keyword.startswith(NAMESPACE)


def unlisted_extension(keyword: str) -> bool:
    """A key in the namespace with no row: admitted, and REPORTED.

    Section 6: "a key in the namespace but not on the list is admitted and reported,
    so it gets read once rather than assumed to be metadata."  The prefix rule is
    leaky -- it dropped ``x-enum-descriptions``, which carries member docstrings,
    silently -- which is why the names are kept as well.
    """
    return admitted_by_prefix(keyword) and keyword not in TABLE


def grid_of(keyword: str) -> str:
    """Which grid this row's line renders into, as a PROJECTION of its cells.

    Section 3 of the architecture document: section 6 is the rows that compile to no
    type, no rule and no base -- which is section 6's own preamble, "none of these can
    constrain an instance, so none compiles to a type, a rule or a base" -- and
    section 7 is the REFUSE rows.  So each is a projection and not a second list, and
    only section 5's seven sub-tables are declared (:attr:`Row.grid`), the family of a
    keyword being derivable from no other column.

    **A row that carries nothing but HOLDS a subschema is section 5's**, and
    ``definitions`` is why the descent column is read here: it compiles to nothing at
    every position and section 5 states it anyway, because what it holds reaches an
    instance through a ``$ref``.  Section 6's preamble is about what a keyword
    compiles to; a keyword holding a subschema is structure whatever it compiles to.
    """
    row = TABLE[keyword]
    cells = (row.default, *row.at.values())
    if all(c.effect is Effect.REFUSE for c in cells):
        return REFUSED
    if any(c.effect in COMPILES or c.effect is Effect.REFUSE for c in cells):
        return row.grid
    if any(c.descends is not None for c in cells):
        return row.grid
    return ADMITTED


#: Which SECTION of the semantics document each grid is, so a cell's address names the
#: section a reader goes to.  Section 5's seven sub-tables are all section 5; section 6
#: is the admitted projection and section 7 the refused one (:func:`grid_of`).
_SECTION: Mapping[str, int] = {**dict.fromkeys(SECTION_5, 5), ADMITTED: 6, REFUSED: 7}

#: The one place the semantics document is named from this package, so a renamed
#: document moves in one line.  An address is read by a human, which is what makes the
#: file name part of it.
DOCUMENT = "docs/plan/rebuild-plan.md"


def address(keyword: str) -> str:
    """**The cell's own address**: where the row that decided this keyword is written.

    ``docs/plan/architecture.md`` section 3, on why the OURS attribution of a widening is
    derived and not stored: "the attribution of a widening the design decided is 'the row
    that decided it', and the cell IS that row: the generator already knows a cell's
    section and keyword, because it writes the grid from them.  A field holding it would
    be a second copy of the cell's own address."

    So this is that derivation, and it is the whole of the ``Ours`` attribution -- section
    2 of the semantics document: "The attribution is therefore the **cell's own address**
    and is derived, not stored: a reader goes from a widened field to the row that decided
    it, and that row says why."

    A keyword with NO ROW has no address, and section 5's own answer for it is the one
    thing that can be said -- it is in none of sections 5, 6 and 7 -- so that is what it
    reads, with the keyword named.  Rung TOP and this address are the pair the semantics
    document's section 7 gives the first document to carry a new keyword.
    """
    if keyword not in TABLE:
        return f"{DOCUMENT} §7 (no row): {keyword}"
    grid = grid_of(keyword)
    return f"{DOCUMENT} §{_SECTION[grid]} {grid}/{keyword}"
