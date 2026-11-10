"""The keyword x position declaration: one table, and every reader derives from it.

``docs/plan/rebuild-plan.md`` sections 5, 6 and 7 are a table of keyword x position.
This module carries that table ONCE, as data.  ``docs/plan/architecture.md`` section 3
names the four readers that derive from it and the rule that nothing else under
``codegen/`` names a keyword in a set literal:

* **admission** -- the keyword screen (``compiler.check_keywords`` today,
  ``schema/parse.py`` after section 14 step 5) looks every key up at the node's
  POSITION: ``NOTHING``, ``ANNOTATION`` and ``NAME`` are admitted and carried
  nowhere by the screen; a key with NO ROW refuses the document as a VERDICT naming a
  keyword the bundle did not use before, and is the ONLY answer that refuses it;
  a ``FIELD`` effect is a fact the ENCLOSING field carries, so the node's own
  screen admits it too; and a ``TYPE`` or ``RULE`` effect is a fact the node's own kind
  consumes, so a handler with no code for it yet is a DEFERRAL.
* **descent** -- :attr:`Cell.descends` is the position the subschema(s) a structural
  keyword holds occupy.  Its readers are section 14 step 5's (``schema/parse.py``,
  ``bundle.edges``, ``verify/record.py``); this row declares the column and builds
  none of them.
* **lowering** -- a handler asks which of the keywords on its node are TYPE facts,
  which are RULE sources, which are annotations it carries.  Section 14 step 8's
  reader; this row declares the column.
* **the document-side fold** -- the facts a fold carries from a conjunct into the node
  it composes, and from a union's branches into their agreement, are
  ``{k for k in TABLE if cell(k, p).rendered}`` (:func:`rendered_at`).
  ``harness.FOLDED_FACTS`` is that set at ROOT, which is where every fold is entered.

**Where a refusal's KIND comes from.**  Section 3 of the architecture document: the
kind is derived from the cell and never chosen at a raise site.  A key with NO ROW,
or a document contradicting itself, is a VERDICT; a cell with a lowering effect whose
handler has no code for the shape yet is a DEFERRAL.  ``compiler.kind_for`` is that
derivation and it is the only place the two are told apart.

**What ``rendered`` asks.**  Does a faithful model state this keyword as a FACT about a
value -- one self-contained assertion, at one pointer, that a fold can carry from the
node that states it to the node it applies to?  Section 8 of the semantics document
gives a keyword four answers, and they are alternatives: the model *renders it as a
fact*, *descends it as structure*, *enforces it as a rule*, or *carries nothing*.  So:

* a keyword the model states as STRUCTURE -- ``properties``, ``items``,
  ``propertyNames``, ``patternProperties``, ``$ref``, the combinators, the
  conditionals -- has :attr:`Cell.descends` set and ``rendered=False``.  It is read by
  DESCENDING it, which is the descent column's job and not the rendered column's; a
  fold that carried it as a value would copy a whole subtree to the composed pointer
  and bury the facts inside it one level deeper than the walk looks.
* a keyword the model enforces as a RULE renders nothing about the value on its own
  node, so ``rendered=False``: it compiles to a validator the class runs, which is not
  a fact at a pointer and so is not a fact a fold can carry.  ``uniqueItems`` is the
  one exception and the document states it: section 5 writes a
  ``json_schema_extra={"uniqueItems": true}`` beside the rule, so its cell is ``RULE``
  and ``rendered=True``.

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
is the rows that compile to no type, no rule and no base, "so each section is a
projection and not a second list".  :func:`grid_of` is that projection;
:attr:`Row.grid` names which of section 5's seven sub-tables a
section 5 row belongs to, which is a taxonomy of keyword family and is derivable from
nothing else.  **Section 7's projection is EMPTY**, because no keyword's presence
refuses a document and there is no ``Effect.REFUSE`` for a cell to say it with; the
region is still generated, and its emptiness is what makes section 7's title a fact the
document holds rather than a claim its prose makes.

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
    ``NAME``, ``ANNOTATION`` and ``NOTHING`` are admitted and cost a handler nothing.

    **There is no ``REFUSE``, and its absence is the point** (section 14 step 8, retired
    2026-10-30).  Section 7 of the semantics document is empty and its grid is the empty
    projection: no keyword's presence refuses a document, so there is no effect for a
    cell to say it with, and "refuse a document on a keyword" is a name error here rather
    than a path the compiler can silently take.  The member survived step 8 because 1 of
    141 primary refusals sat on a ``REFUSE`` cell and retiring it early would have
    crashed 140 documents; ``refused`` is 0 now and the last cell to say it --
    ``errorMessage`` -- is NOTHING with :attr:`Cell.reported` set.
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
    #: **Is the drop REPORTED wherever the document states this keyword.**
    #: ``docs/plan/rebuild-plan.md`` section 7, on ``errorMessage`` joining section 6:
    #: "it customises a validator's message and constrains no instance, so an annotation
    #: that omits it omits no fact.  The drop is reported, as it was" -- and, beside it,
    #: "**the drop is reported at every position the keyword occupies, and not only where
    #: a conjunct encloses it**".
    #:
    #: A FIELD and not derived from :attr:`effect`, and the test section 3 sets for that
    #: is met: ``$comment`` and the registry data keys are NOTHING at every position and
    #: are reported NOWHERE, because a note about them tells a reader nothing they could
    #: have believed otherwise -- a comment is manifestly a note and a registry's own
    #: data is manifestly data.  ``errorMessage`` is NOTHING too and sits BESIDE a
    #: constraint, on a ``not`` or on a ``then``, so a reader who is not told has no way
    #: to see that the class carries nothing for it.  Cells whose other fields agree
    #: take different answers, which is what makes this the cell's own decision.
    #:
    #: It is a REPORT and not an approximation: a cell that states no fact has nothing to
    #: widen (:func:`states_a_fact`), so this never co-occurs with a rung.  The two
    #: channels section 10 forbids summing stay two (``Module.carries_nothing`` against
    #: ``Module.approximations``).
    reported: bool = False
    #: **Does this keyword's subschema OWN the child instance location it descends to**:
    #: does it state something about EVERY instance at that location, and about exactly
    #: that one?  A QUALIFIER OF :attr:`descends` and never true without it
    #: (:func:`_with_ownership` raises otherwise).
    #:
    #: ``properties`` owns one named key, a single-schema ``items`` owns every element,
    #: and ``additionalProperties`` owns the keys no other keyword names.  A keyword that
    #: descends to the same position WITHOUT owning it speaks about SOME instance there or
    #: about SEVERAL locations at once -- ``contains`` about one element of the array,
    #: ``patternProperties`` about every key one pattern matches -- so no single value can
    #: answer for it, and a reader that replaced it would be answering a question the
    #: document asked of something else.  ``propertyNames`` descends to a KEY, which is a
    #: location of a different kind and not a value a child holds.
    #:
    #: **A FIELD, and section 3's test of that is met on the DESCENT column's own triple**
    #: -- the triple that section 3 states the test over for :attr:`widens_to`:
    #: ``items`` and ``contains`` are both ``TYPE``, both unrendered, and both descend to
    #: ``ELEM``, and one owns the element location while the other states an existential
    #: about it.  So no reading of ``effect``, ``rendered`` and ``descends`` separates
    #: them.  Neither does :attr:`widens_to` stand in for it: a rung says what DROPPING
    #: the keyword costs, which is a different question, and the three places it happens
    #: to disagree (``items`` JOIN against ``contains`` KEYWORD, ``additionalProperties``
    #: rendered against ``patternProperties`` not, ``properties`` at PROP against
    #: ``propertyNames`` at KEY) are three unrelated coincidences and not one predicate --
    #: a disjunction over them would read a pydantic round-trip fact as an ownership fact
    #: and would answer the first new keyword silently and wrongly.
    #:
    #: Its reader is :func:`owns_a_location`, and the frontier walk's
    #: ``harness._OWNS`` is that set.
    owns: bool = False


class Row(NamedTuple):
    """One keyword: a default cell, and an override per position that differs."""

    default: Cell
    #: The positions whose answer differs from :attr:`default`.
    at: Mapping[Position, Cell] = {}
    #: Which of section 5's seven sub-grids this row's line belongs to.  Empty for a
    #: section 6 row, whose grid :func:`grid_of` derives.
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
#: :data:`REFUSED` is the EMPTY projection -- no cell can be in it -- and survives as the
#: NAME of section 7's generated region, which :data:`GRIDS` is zipped against.
ADMITTED, REFUSED = "admitted", "refused"
GRIDS = (*SECTION_5, ADMITTED, REFUSED)

#: The one prefix that admits a keyword by SHAPE rather than by name, and the one
#: exception the semantics document's by-name principle has.
NAMESPACE = "x-"

#: The grid line that stands for the whole vendor namespace, and the sentence every
#: row of it carries.  One line for 30 rows, because section 6 writes one.  (29 until
#: bundle 3.3 added ``x-adcp-owned``; the three ``x-max-*-4.0`` keys it also added are
#: NOT on this line and :data:`_FUTURE_BOUNDS` says why.)
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
            "refused otherwise. An enclosing `oneOf` APPLIES a type word it does not "
            "state, where TWO OR MORE of its branches admit that type vacuously: "
            "`oneOf` admits an instance satisfying exactly one branch, so an instance "
            "two branches both admit is refused by the combinator, and the type is "
            "excluded by the document itself. This is EXACT and not a widening — it "
            "reads a constraint the document imposes rather than relaxing one — so it "
            "owes no declaration and no rung. It holds at `oneOf` ALONE: at `anyOf` an "
            "instance one branch admits is admitted, so the same derivation there would "
            "state a constraint the document does not "
            "(`adcp-client-python-10l.69`, decided 2026-10-29).",
        ),
        grid=STRUCTURE,
    ),
    "properties": Row(
        Cell(
            Effect.TYPE,
            False,
            Position.PROP,
            "A class with one field per key. An entry whose subschema ADMITS "
            "NOTHING — `false`, or `{\"not\": {}}`, which draft-07 makes the same "
            "schema — is NOT a field: draft-07 validates a `properties` entry only "
            "where the key is PRESENT and that entry then always fails, so the "
            "document's statement is that the key MAY NOT APPEAR and it says nothing "
            "at all about a value. The accepted set is the accepted set of "
            "`not: {required: [key]}`, which the `not` row already compiles to a "
            "`ForbiddenGroups` rule, so the key joins that rule on the nearest "
            "enclosing class and no field is declared. EXACT, not wide: nothing is "
            "dropped reaching it and no declaration is owed. `extra` is NOT the "
            "carrier — all three sites of the bundle state `additionalProperties: "
            "true` beside the forbidden key, so closing the class would refuse the "
            "other extras the document admits. Where `required` ALSO names the key "
            "the document admits nothing, and so does the class without an arm of its "
            "own: the `required` row's undeclared-name field refuses a payload "
            "omitting the key and this rule refuses one carrying it.",
        ),
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
            "property NO declaration declares → a required field of type `Any`, and "
            "it is EXACT rather than wide: `required: ['x']` with no entry for `x` "
            "admits an object carrying `x` with any value, which is what the `type` "
            "row already gives an absent type word, so nothing is dropped and no "
            "declaration is owed. The model-only `properties` entry it renders is "
            "the empty schema, which states nothing the document does not. "
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
            "declaration's cell says it compiles to nothing at this co-occurrence; and "
            "the report names it, because a key that reads as a constraint and is "
            "inert is worth reading once. Refusing it instead "
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
                "not — a scalar, an enum, a container, or a union root — it is not a "
                "class a model can extend: the "
                "target is this node's own TYPE, and the other conjuncts and the "
                "`allOf`'s siblings constrain it, which is §2's intersection at a node "
                "that declares no fields of its own. A UNION root beside a node that "
                "DOES declare fields distributes: conjunction distributes over "
                "disjunction, so `(A | B) and C` is `(A and C) | (B and C)`, and the "
                "node is a union whose branches each take one of the target's branches "
                "as a base and add the node's own fields. Each branch of a union root "
                "is a class declaring fields, so this is the CONJ rule above applied "
                "once per branch and not a second answer. A property the node and the "
                "target's branch BOTH declare is one field taking §2's intersection, "
                "exactly as the `properties` row at CONJ states it for two conjuncts — "
                "the node's declaration does not shadow the branch's, and two `const`s "
                "intersect to the pin where they agree and to nothing where they "
                "differ. A distributed branch whose intersection is EMPTY is DROPPED, "
                "and the node refuses only where every branch is: "
                "`(A \\| B \\| C) and D` with `A and D` empty is exactly "
                "`(B and D) \\| (C and D)`, so the accepted set is unchanged and "
                "nothing is approximated. The emptiness must be PROVED from the pins "
                "the two sides state — disjoint `const`s, disjoint `enum`s, disjoint "
                "type words — which is the same test the empty-intersection row names; "
                "an intersection this compiler cannot compute is the restatement row "
                "and not this one.",
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
            "it. A `format` beside the pin compiles to NOTHING and the pin alone is "
            "rendered, because a fixed value either satisfies the format or the node "
            "admits nothing: the pin is checked against the format, and where it "
            "satisfies it the `Literal` is already strictly tighter than any type the "
            "format would select, while where it does not the node is §5's empty "
            "intersection and refuses upstream. So no fact is dropped, and the cell "
            "declares the `format` as rendering nothing at this co-occurrence "
            "(`adcp-client-python-10l.70`, decided 2026-10-29). "
            "A `str`, `bool` or `int` value; an object, array, `null` or float "
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
            "Python name → a `Literal` of the members and NOT an enum class (decided "
            "2026-10-29). The collision exists only because an enum mints a Python "
            "IDENTIFIER per member; a `Literal` needs none, so both values are carried "
            "exactly as the document spells them and nothing is dropped. This is the "
            "same answer the row already gives an untitled branch of a root union, "
            "reached by a second route. Refusing instead cost **21 of the 95 refusals** "
            "for one node — `formats/canonical/html5.json`'s `clicktag_macro`, whose "
            "`clickTag` and `clickTAG` both spell `CLICKTAG` — including "
            "`core/product.json`. The cost is that one node gives a string-literal "
            "union rather than an enum class, which is a DX difference and not a "
            "correctness one; dropping a member, which the old clause rightly refused "
            "to do, remains forbidden.",
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
            # ``model_json_schema()`` under the document's own keyword, so the model
            # states the document's own fact rather than an approximation of it.
            Position.KEY: Cell(
                Effect.TYPE,
                True,
                None,
                " → a `Literal` of the members as the mapping's KEY type, which "
                "pydantic renders back as `propertyNames: {enum: […]}` — the document's "
                "own keyword, rendered and gradable; where the key node carries a "
                "`title` the `StrEnum` is the key type and renders the same way.",
            ),
            # **§5's "An `enum` conjunct beside a `$ref` to an enum" (decided
            # 2026-10-29).**  The cell and not the grid line: §3 generates the line from
            # here, and this cell carried an EMPTY ``compiles`` synthesised by
            # :data:`_RUNG_AT` for the rung alone -- a cell saying the keyword lowers at
            # CONJ with no handler claiming it, which is the defect this epic has found
            # seven times.
            #
            # ``widens_to`` stays :attr:`Rung.TOP` through :data:`_RUNG_AT`, which is §5's
            # empty-intersection row: two disjoint vocabularies admit nothing and the
            # typeless ``Any`` carries it.
            #
            # The clause renders BETWEEN the KEY one and the RULE one, which is
            # :class:`Position`'s own declaration order and is why the general decision
            # does not read as part of the position-specific override that ends the line.
            Position.CONJ: Cell(
                Effect.TYPE,
                True,
                None,
                " beside a `$ref` whose target is an enumeration → §2's intersection of "
                "the two vocabularies, rendered as a `Literal` over the TARGET's MEMBERS "
                "and not over their raw values. The two dump identically — "
                "`{\"enum\": [the members], \"type\": \"string\"}` — so they state the "
                "same fact either way, and the member form keeps the imported symbol a "
                "caller can name: where two renderings state one fact, DX decides. "
                "A vocabulary the target does not contain is the empty intersection and "
                "refuses, by the same rule that refuses a member the node's own "
                "constraints exclude.",
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

#: **The clause for a node that states a value keyword and no `type`**, shared by the
#: array bounds and the string bounds because it is one sentence about both: the keyword
#: has no annotation to sit on, so it is DROPPED and declared, and the rung is the one
#: this row's own ``widens_to`` already carries.  It belongs in the DEFAULT cell of each
#: row and not at the tail of a position-specific override: a typeless node is reachable
#: at every position the row gives an answer at, and a sentence written into one
#: override's text reads as part of that override's clause.
_TYPELESS_DROPS = (
    " A node stating the bound and **no `type`** is `Any` (§5's `type` row, \"absent → "
    "`Any`\"), which carries no bound: the keyword is dropped at rung KEYWORD — the type "
    "is unchanged, which is what that rung is — and the drop is declared. Selecting the "
    "type the bound implies instead would NARROW, because a typeless node admits an "
    "instance of every type and the bound constrains only one of them."
)

_ITEM_BOUND_COMPILES = (
    "`min_length` / `max_length` on the annotation of the **array's own type**, at "
    "every position. `minItems: 0` states nothing. `constraints` declares it once, "
    "generically, as `type NonEmptyList[T] = Annotated[list[T], "
    "Field(min_length=1)]`." + _TYPELESS_DROPS
)

_STRING_BOUND_COMPILES = (
    "`min_length` / `max_length` on the type, as a named alias. On a URL type → "
    "refused, not representable." + _TYPELESS_DROPS
)


_STRINGS: dict[str, Row] = {
    "pattern": Row(
        Cell(
            Effect.TYPE,
            True,
            None,
            "`pattern` on the type, as a named alias. On `format: uri` → **both**: the "
            "format selects a type only where that type STATES the pattern, which is "
            "`^https://` and `AdCPUrl`'s `allowed_schemes` alone, and the node takes the "
            "constrained `str` with `json_schema_extra={\"format\": \"uri\"}` at every "
            "other pattern. The row read \"selects the type instead, and the pattern "
            "stays with the schema half\" and that was a SILENT widening at 408 "
            "positions in 115 documents: `strict_validate` applied it, the class did "
            "not, and no `__adcp_approximations__` entry said so "
            "(adcp-client-python-bgyd). The regex "
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
            '`json_schema_extra={"format": …}` on the field. **A `uri` beside any '
            "assertion the URL type does not itself state → the constrained `str`, and "
            "the format rides**: a URL type carries no string constraint, so the type "
            "is given up and both of the document's facts are kept. Where a constraint "
            "is there to join it the format joins the NAMED TYPE rather than the field, "
            "because an ELEM, a MAPV and a BRANCH have no field to ride on.",
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
        Cell(Effect.TYPE, True, None, _STRING_BOUND_COMPILES),
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
        Cell(Effect.TYPE, True, None, _STRING_BOUND_COMPILES),
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
            "class encloses the array → a `Distinct` after-validator on its own "
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
            "a transcription of the subschema. Every position → an `AtLeastOne` "
            "after-validator on the array's own annotated type, because no class has "
            "a kind for it: `AtLeastOne(pinned=((property, const), …))` where the "
            "subschema requires properties pinned to a const, `AtLeastOne(values=("
            "value,))` where it is a bare `const` or a one-member `enum`. A property "
            "KEY is not required to be a Python identifier, so the predicate is a "
            "tuple of pairs and not keyword arguments. Any other predicate — a bound, "
            "a pattern, a nested `contains`, a `$ref` — → the keyword is CARRIED and "
            "the schema half answers alone: a transcription of the subschema is the "
            "thing this row declines to emit, and the first document to state such a "
            "predicate decides its rendering.",
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
            "`ignore`. **A class DECLARES the `extra` the document gives it and never "
            "inherits it** (decided 2026-10-29): pydantic merges `model_config` along "
            "the MRO, so a branch composing TWO bases takes whichever value the later "
            "base happens to carry, and `absent → ignore` on that base silently "
            "overrides an `allow` the document states. Measured on "
            "`content-standards/get-content-standards-response.json#/oneOf/0`, where "
            "the union base states `allow` from the root's envelope conjunct and the "
            "composed target's default `ignore` wins the merge, so the model drops keys "
            "the document admits. The "
            "value is read from what the document states at the class's own pointer "
            "after the document-side fold — which is where the root's conjunct arrives — and "
            "written on the class, so MRO order decides nothing a document states. "
            "On a mapping (no `properties`) → the VALUE type; `true` or "
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
                "no value to annotate.",
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
            "naming the combinator. Presence-only where a branch also `not`s a group of "
            "`required` → a `PresenceGroups` rule naming the combinator, whose clauses "
            "are the branches: each clause carries its OWN required group and its own "
            "forbidden groups, because the `not` is per branch — a `ForbiddenGroups` "
            "over the union of them forbids every group unconditionally and refuses a "
            "payload the document admits. Shapes at ROOT → the base plus one class per "
            "branch. Shapes nested, with nothing beside the combinator → one type "
            "`A \\| B`. A sibling a CLASS carries → that same base-plus-branches shape, "
            "at a union in ANY position: the siblings become the base, each branch "
            "becomes a subclass narrowing what it narrows, and the union is over the "
            "subclasses. A sibling no class carries refuses, because it is a "
            "conjunction with every branch and `A \\| B` has no slot for a fact of its "
            "own. "
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
                ": nothing, and the schema half answers. The `not` clause this row "
                "carried — the union of the branches' groups — is WITHDRAWN (§8, "
                "2026-11-03): `not oneOf` admits an instance satisfying ZERO branches "
                "or TWO OR MORE, and a forbidden group over the union refuses an "
                "instance satisfying two, which the document admits. A forbidden-group "
                "list cannot say \"not exactly one\", so such a node DECLARES rather "
                "than lowers.",
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
            "`not: {}` admits nothing, which the typeless `Any` carries — at a node "
            "whose OWN accepted set is the thing being typed. As a `properties` entry "
            "it is not that node: the enclosing object still admits every instance "
            "without the key, and the `properties` row answers it there with the "
            "`ForbiddenGroups` this row already decides for the keyword's other "
            "spelling.",
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

#: The two keys ``extensions/adcp.json``'s root states as the manifest header of the
#: extension it declares; one row object, so the generator writes them one grid line.
_MANIFEST_HEADER = Row(
    Cell(
        Effect.NOTHING,
        False,
        None,
        "Nothing. An extension manifest's own header at a schema root: where a reader "
        "goes for the extension's prose, and the protocol version it became valid at. "
        "Neither says anything about an instance — draft-07 says the same by ignoring "
        "an unknown key — so an annotation that omits them omits no fact. "
        "`extensions/adcp.json` is the one document stating them at a schema position, "
        "and it states a real schema beside them, so it emits normally with the two "
        "compiling to nothing.",
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
    #: **draft-07's own identifier, and the one keyword of the seven 3.3 adds that
    #: COULD have changed a reading.**  It is not a constraint -- draft-07 defines it as
    #: the document's URI and as the BASE every reference in it resolves against -- so
    #: the question is not whether it bounds an instance but whether it REDIRECTS a
    #: reference.  Measured over the 3.3 bundle, it cannot:
    #:
    #: * 1,138 of 1,138 portable documents state it, all of them at ROOT and NONE at any
    #:   other pointer, so there is no nested ``$id`` to re-base a subtree against;
    #: * every one of the bundle's 4,164 non-local references is an ABSOLUTE URI and the
    #:   remaining 450 are local pointers into the referrer, so no reference's resolution
    #:   is a function of a base at all;
    #: * ``bundle.document_for`` matches a reference's longest trailing run of path
    #:   segments against the bundle's own FILE SET and reads no ``$id`` -- which is also
    #:   what makes the 39 documents whose ``$id`` names a path other than their own
    #:   (``core/async-response-refs/...``) resolve by where they are and not by what
    #:   they call themselves.
    #:
    #: So the identifier is read by nothing in either half, and the cell is NOTHING at
    #: every position for the same reason ``$schema``'s is: an annotation that omits it
    #: omits no fact about an instance.
    "$id": Row(
        Cell(
            Effect.NOTHING,
            False,
            None,
            "Nothing. draft-07's URI for the document, and the base a reference in it "
            "would resolve against — so it identifies and does not constrain, and an "
            "annotation that omits it omits no fact. It cannot redirect a reference "
            "here either: the bundle states it at document roots and at no node below "
            "one, every non-local `$ref` is an absolute URI, and the resolver matches "
            "a reference's trailing path segments against the bundle's own file set "
            "rather than against any `$id` — which is why a document whose `$id` names "
            "a path other than its own is still reached at the path it is written at. "
            "Bundle 3.2 states it nowhere and 3.3 states it at every document root, "
            "and that is the whole of the difference it makes.",
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
    #: DEVIATION, and it is declared on the row rather than resolved by this one.**
    #:
    #: The emitter writes nothing for ``deprecated``: no ``Field(deprecated=True)``, no
    #: ``json_schema_extra`` on a class.  Measured over the committed tree, the keyword
    #: is stated by 105 documents at 153 positions -- 115 at a property of a root class,
    #: 25 at a property of a nested one, 11 at a class root, 2 inside an array element
    #: -- and the model states none of them.
    #:
    #: ``False`` is therefore the declaration that matches the emitter, and the column's
    #: one live reader makes the direction matter: ``rendered_at`` is the set the
    #: document-side FOLD carries, so declaring ``True`` for a keyword the emitter never
    #: writes would make the fold carry a fact to a composed pointer that no artifact
    #: states there.
    #:
    #: It is not resolved here because the emitter half is a handler edit and §14 gives
    #: no step that carries it: step 8's list of unwritten cells names root siblings on
    #: a union base, a scalar target as a composing node's type, the type-bound
    #: validators for ``uniqueItems``/``contains``/``not``, a one-class union, and the
    #: manifest dispatch source -- and not this.  Flipping it is the whole of the change
    #: once a row owns the emitter half.
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
    #: **An extension manifest's own metadata, and the registry line's reason one level
    #: in.**  ``extensions/adcp.json`` is a schema AND the manifest of the extension it
    #: declares, so its root states two keys that describe the extension rather than the
    #: ``ext`` payload the schema below them admits.  Measured on the 3.3 bundle: one
    #: document, one occurrence each, both at ROOT and neither anywhere else.
    #: ``extensions/index.json`` states them a second time inside its ``extensions``
    #: value, which is a registry's instance data and a key the walk does not descend
    #: into, so they reach no schema position there.
    #:
    #: ONE row object for the two, which the generator renders as one grid line: they are
    #: one decision about one document's manifest header, and ``readOnly`` / ``writeOnly``
    #: is the shape section 6 already writes it in.  NOT ``_REGISTRY_KEYS``, whose
    #: sentence is about a root that is ONLY instance data and emits as a permissive
    #: model -- this root carries a real schema beside them and emits normally.
    "docs_url": _MANIFEST_HEADER,
    "valid_from": _MANIFEST_HEADER,
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
    "x-adcp-owned",
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
# a future version's bounds, announced early: the `x-max-*-4.0` keys
# --------------------------------------------------------------------------- #
#: **The one group in the namespace whose keys READ as constraints, and they are not
#: constraints of THIS version.**  Bundle 3.3 states three of them -- ``x-max-length-4.0``
#: beside ``type: string`` (80 sites in 18 documents), ``x-max-items-4.0`` beside
#: ``type: array`` (78 in 16), ``x-max-properties-4.0`` beside ``type: object`` (6 in 5),
#: each carrying a number -- and the ``-4.0`` suffix is the whole of what they say: these
#: are the bounds version 4.0 will impose, written into a 3.3 document so an implementer
#: can see them coming.
#:
#: **So the cell is NOTHING, and reading one as a bound would be the one error section 1
#: forbids outright.**  3.3's validator ignores an unknown key, so a string longer than
#: its ``x-max-length-4.0`` is a string the 3.3 document ADMITS; a class carrying that
#: number as a ``max_length`` would refuse a payload its own document accepts, which is a
#: NARROWING -- section 2's "an annotation tighter than its document refuses a payload the
#: protocol accepts", the direction that is never a legitimate approximation.  The three
#: are therefore annotations BY THE VERSION THE BUNDLE IS and not by the keyword's
#: spelling, which is why they are not on the namespace line with the other metadata.
#:
#: **Where they are promoted.**  Against a 4.0 bundle each one becomes the cell its own
#: unprefixed keyword already has -- ``maxLength``, ``maxItems``, ``maxProperties``, in
#: section 5's strings, arrays and objects grids, each ``TYPE``/``RULE`` with that row's
#: own rung -- and the promotion is a row of its own, because it changes what a class
#: admits.  Not ``reported``: the drop is reported nowhere because there is no drop, the
#: keyword constrains nothing at this version, and a note saying the class carries nothing
#: for a bound the document does not impose would read as a loss where there is none.
_FUTURE_BOUNDS = ("x-max-length-4.0", "x-max-items-4.0", "x-max-properties-4.0")
_FUTURE_BOUND_ROW = Row(
    Cell(
        Effect.NOTHING,
        False,
        None,
        "Nothing **at this version**, and the keys are listed apart from the namespace "
        "line because each one reads as a bound. Each sits beside the `type` word it "
        "would bound — `x-max-length-4.0` beside a `string`, `x-max-items-4.0` beside an "
        "`array`, `x-max-properties-4.0` beside an `object` — and names the bound "
        "**version 4.0** will impose, which is what the suffix says. A 3.3 document is "
        "not bounded by it: 3.3's validator ignores the key, so a value exceeding the "
        "number is a value the document ADMITS, and a class carrying it as a constraint "
        "would refuse a payload its own document accepts — the narrowing §1 and §2 "
        "forbid outright. So these annotate **by the version the bundle is**, not by how "
        "they are spelled. Promoting them is a 4.0 row: each becomes the cell its "
        "unprefixed keyword already has — `maxLength`, `maxItems`, `maxProperties` — and "
        "this line is the reason it had not happened yet.",
    ),
)
for _name in _FUTURE_BOUNDS:
    _ADMITTED[_name] = _FUTURE_BOUND_ROW


# --------------------------------------------------------------------------- #
# section 6, continued: the two groups that came from section 7 on 2026-10-26
# --------------------------------------------------------------------------- #
# **Section 7 has no rows and no dict.**  Both of its groups moved to section 6 by the
# owner's directive, "each refused for a reason that was never about the document's
# accepted set", and they are declared HERE because that is the section they render into:
# a dict of its own, kept beside this one and spread after it, would be a second list for
# `grid_of` to disagree with.
#
# `_ADMITTED` and not `_REFUSED` is also where the ORDER comes from.  Insertion order is
# section 6's own grid order (`TABLE`), so these rows come after the `x-` namespace, which
# is where the committed grid already carries the registry line.
#
#: A registry's own instance data at a schema root.  Section 6 names them on one line
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

# **`errorMessage` is NOTHING at every position, and its drop is REPORTED at every
# position.**  Section 7: "it customises a validator's message and constrains no instance,
# so an annotation that omits it omits no fact.  The drop is reported, as it was" -- and
# "**the drop is reported at every position the keyword occupies, and not only where a
# conjunct encloses it**".  ONE cell and no override is what says "every position": the
# position rule is not a second decision to be taken per cell, so the row states the
# answer once (:attr:`Cell.reported`, and ``bundle.reported_drops`` is the channel).
_ADMITTED["errorMessage"] = Row(
    Cell(
        Effect.NOTHING,
        False,
        None,
        "Nothing. An `ajv-errors` extension customising a validator's message, so it "
        "constrains no instance and an annotation that omits it omits no fact. It has "
        "no Pydantic rendering and never needed one. **The drop is reported**, at every "
        "position the document states it at.",
        reported=True,
    )
)

# **The registry data keys are NOTHING at every position** (section 6 of the semantics
# document, and section 3 of the architecture document: "`errorMessage` and the registry
# data keys move into section 6's projection, where they always belonged: each is NOTHING
# at every position").  Section 7 says why the old REFUSE cell was never a statement about
# the document's accepted set: "the first half was answering a question nobody asked --
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
# They are NOT `reported`, and the difference from `errorMessage` above is the cell's own
# decision: a registry's own data at a schema root is manifestly data, so a note saying the
# class carries nothing for it tells a reader nothing they could have believed otherwise.
for _name in _REGISTRY_KEYS:
    _ADMITTED[_name] = Row(
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
    rule or a base"), and a ``NAME`` is a symbol while an ``ANNOTATION`` is a description
    or a deprecation.
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


#: **The keywords whose subschema OWNS the child instance location it descends to**, and
#: the whole of :attr:`Cell.owns` (which states what owning IS and why no other column
#: answers it).  Declared per KEYWORD and folded onto its cells by
#: :func:`_with_ownership`, for the reason :data:`_RUNG` is -- "one pass and not 107
#: positional arguments" -- and because ownership is draft-07's APPLICABILITY and the same
#: fact at every position the keyword descends from: ``properties`` names one key whether
#: the object is a root, a branch or a conjunct.
#:
#: Each of the three is one sentence of draft-07's own applicability:
#:
#: * ``properties`` -- an entry applies to the instance at ITS key and to no other, so
#:   that key is its location and one value answers for it.
#: * ``items`` in its SINGLE-SCHEMA form -- applies to EVERY element, so the elements are
#:   one location and one value answers for all of them.  (A list-valued ``items`` is a
#:   per-INDEX location that ``additionalItems`` also reaches, which is why section 5's
#:   row refuses it and why ownership here is the single-schema reading.)
#: * ``additionalProperties`` in its schema form -- applies to the keys no other keyword
#:   names, which is a location of its own and meets nothing.
#:
#: **The three keywords that descend to the same positions and are NOT here**, because an
#: owner is what a single value can answer for: ``patternProperties`` (one entry reaches
#: several keys), ``contains`` (an existential about one element) and ``propertyNames``
#: (a KEY and not a value a child holds).  A reader that pinned one of them would answer
#: a question the document asked of something else.
_OWNS_ITS_LOCATION = frozenset({"properties", "items", "additionalProperties"})


def _with_ownership(table: dict[str, Row]) -> dict[str, Row]:
    """Every cell of ``table``, with :attr:`Cell.owns` filled from the declaration.

    The CELL carries the answer afterwards, which is what puts the decision in the table
    rather than in a set beside it (section 3), and :func:`owns_a_location` reads it there.

    Two malformed-table conditions, raised as ``ValueError`` for :func:`_with_rungs`'s own
    reason -- this module imports nothing of this package, so a malformed table stops the
    import rather than reaching a reader:

    * a keyword declared an owner with no row, which is an ownership decision about a
      keyword the table does not carry;
    * a keyword declared an owner with a cell that DESCENDS NOWHERE, since ownership
      qualifies the descent column and there is no location to own without it.
    """
    out: dict[str, Row] = {}
    for keyword, row in table.items():
        owns = keyword in _OWNS_ITS_LOCATION
        if owns and all(c.descends is None for c in (row.default, *row.at.values())):
            raise ValueError(
                f"{keyword!r} is declared in _OWNS_ITS_LOCATION and no cell of it "
                "descends: Cell.owns qualifies the descent column, so there is no child "
                "instance location for it to own"
            )
        out[keyword] = row._replace(
            default=row.default._replace(owns=owns and row.default.descends is not None),
            at={
                position: cell._replace(owns=owns and cell.descends is not None)
                for position, cell in row.at.items()
            },
        )
    unrowed = _OWNS_ITS_LOCATION - set(table)
    if unrowed:
        raise ValueError(
            f"_OWNS_ITS_LOCATION names keywords with no row: {sorted(unrowed)} -- a cell "
            "is where an ownership decision lives, so a keyword the table does not carry "
            "cannot be declared an owner"
        )
    return out


#: **The table.**  Insertion order is the document's own grid order, because a grid
#: line's position in its sub-table is read off it.
TABLE: Mapping[str, Row] = _with_rungs(
    _with_ownership({
        **_STRUCTURE,
        **_VALUES,
        **_STRINGS,
        **_NUMBERS,
        **_ARRAYS,
        **_OBJECTS,
        **_COMBINATORS,
        **_ADMITTED,
    })
)

_NUMERIC = frozenset({"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"})

#: Which constraint keywords each ``type`` word can carry.  draft-07 applies a
#: constraint keyword only to an instance OF the type it is defined for and ignores it
#: for every other type, so a ``type`` LIST means "this keyword on this arm".
#:
#: **DECLARED SEMANTICS, which is why it is in this module and not in the walk.**  That
#: sentence is draft-07's, not this compiler's, and it is read by BOTH halves of the
#: pipeline for two operations that are each other's inverse:
#:
#: * the walk CUTS a type list into one arm per word, each holding only what that word
#:   carries (``schema.parse`` builds :attr:`nodes.MultiType.members` from this);
#: * the verifier FOLDS a model's ``anyOf`` of such arms back into the document's type
#:   list plus the per-arm facts (``harness._normalize``).
#:
#: A fold that read a different table from the cut would disagree with it about which
#: arm owns a keyword, and the disagreement would be silent in the direction that
#: matters: a keyword lifted onto the wrong arm states a fact at a type the document
#: says nothing about.  ``docs/plan/architecture.md`` §9 is the rule that puts it here --
#: the verifier may not read the walk, and "sharing DATA is a different matter from
#: sharing a READING: the keyword table is the declared semantics, and both halves must
#: read the same declaration or the grade means nothing."
#:
#: It is NOT :func:`grid_of`, and the difference is not cosmetic: ``properties`` and
#: ``required`` are in the STRUCTURE grid while being object-only keywords, and the
#: OBJECTS grid carries ``minProperties``, ``patternProperties`` and ``dependencies``,
#: which this table deliberately does not -- a node stating one of those beside a type
#: list refuses by name (``lower.containers.multi_type``) rather than being cut onto an
#: arm no row decided.  The grid is which SUB-TABLE a row renders into; this is which
#: INSTANCE TYPE its keyword constrains.
#:
#: A ``description`` is in no arm, deliberately: it is a statement about the instance
#: that every word carries equally, and ``schema.parse`` copies it into every member for
#: that reason.
ARM: Mapping[str, frozenset[str]] = {
    "string": frozenset({"format", "minLength", "maxLength", "pattern"}),
    "integer": _NUMERIC,
    "number": _NUMERIC,
    "boolean": frozenset(),
    "null": frozenset(),
    "array": frozenset({"items", "uniqueItems", "minItems", "maxItems"}),
    "object": frozenset({"properties", "required", "additionalProperties", "propertyNames"}),
}

#: **The ORDERING keywords, as the five RANGES they pin** -- each pair being
#: ``(the keyword that pins the floor, the keyword that pins the ceiling)``.
#:
#: **DECLARED SEMANTICS, and here for :data:`ARM`'s reason exactly** -- that it is read by
#: BOTH halves of the pipeline, for two operations that have to agree:
#:
#: * the WALK asks which of two restatements is NARROWER (``compiler._narrower``: a
#:   narrower floor is a LARGER number and a narrower ceiling a smaller one), and §2's
#:   intersection rule keeps the tighter;
#: * the VERIFIER asks the same question twice -- folding an ``allOf`` conjunct's bound
#:   into the node it composes (``harness._tighter``, §2's "a bound is the tighter one"),
#:   and drawing the value classes a dropped bound distinguishes (``harness.value_classes``,
#:   which needs both ENDS of the range to pin a draw inside it).
#:
#: Three literals held that one fact before ``adcp-client-python-3be.8``, in two modules,
#: and they had already drifted in both directions: the walk's carried
#: ``minProperties``/``maxProperties`` and the verifier's fold did not, so a conjunct
#: narrowing a property count was narrower to the walk and UNDECIDED to the grader. §9 is
#: the rule that puts the fact here -- "sharing DATA is a different matter from sharing a
#: READING: the keyword table is the declared semantics, and both halves must read the same
#: declaration or the grade means nothing."
#:
#: The PAIRING is a column of its own because nothing else holds it: a ``minItems`` and a
#: ``maxItems`` constrain one quantity from opposite sides, which is what makes a draw
#: "inside the range" possible at all, and :data:`_AXES`' own comment in ``compiler.py``
#: says why they are not one axis -- "a child stating one says nothing about the other".
#: Deriving the partner by rewriting ``min`` to ``max`` in the keyword's own text would be
#: a reading of draft-07's SPELLING rather than of its semantics, and ``exclusiveMinimum``
#: is where that spelling stops being mechanical.
RANGES: tuple[tuple[str, str], ...] = (
    ("minimum", "maximum"),
    ("exclusiveMinimum", "exclusiveMaximum"),
    ("minLength", "maxLength"),
    ("minItems", "maxItems"),
    ("minProperties", "maxProperties"),
)

#: The ranges draft-07 spells INCLUSIVELY, which is §5's ``exclusiveMinimum`` row's own
#: distinction -- "``gt`` / ``lt`` on the type, **never ``ge`` / ``le``**.  The bundle
#: distinguishes ``minimum: 0`` from ``exclusiveMinimum: 0``, and the two differ on exactly
#: one instance".  A reader that has to name a value AT a bound needs this column: an
#: exclusive bound admits no instance at it, so "the bound exactly" is not a value class
#: the document has (``harness.value_classes``), while a fold orders the two the same way
#: and reads :data:`RANGES` alone.
EXCLUSIVE: frozenset[str] = frozenset({"exclusiveMinimum", "exclusiveMaximum"})


# --------------------------------------------------------------------------- #
# the readings
# --------------------------------------------------------------------------- #
#: Every keyword that pins the LOW end of a range, and every keyword that pins the high
#: one -- a projection of :data:`RANGES` and not a second list.
FLOORS: frozenset[str] = frozenset(low for low, _ in RANGES)
CEILINGS: frozenset[str] = frozenset(high for _, high in RANGES)


def range_of(keyword: str) -> tuple[str, str] | None:
    """The range ``keyword`` pins one end of, or ``None`` where it pins neither.

    ``(floor keyword, ceiling keyword)``, so a caller that needs the OTHER end -- to pin a
    draw inside the range, or to ask whether the node's own opposite bound forbids a value
    one step in -- reads it off the declaration rather than pairing the two itself.
    """
    for pair in RANGES:
        if keyword in pair:
            return pair
    return None


def constrains_container(word: str) -> frozenset[str]:
    """Every keyword whose row constrains an instance of this CONTAINER type.

    A PROJECTION of two columns already declared and not a third list of names
    (``adcp-client-python-3be.8``): §5's ``objects`` and ``arrays`` sub-grids are the
    keyword FAMILIES (:func:`grid_of`), and :data:`ARM` names the ones draft-07 cuts onto
    that type word.  The union is what "this keyword declares the instance to be an
    ``object``" means, which is the question ``intersect._container_kind`` asks of two
    declarations before it decides whether they declare ONE container.

    The two columns are needed TOGETHER and neither alone, which is what makes this a
    reading rather than a rename.  ``properties`` and ``required`` are object-only keywords
    in the STRUCTURE grid, so the grid misses them; :data:`ARM` deliberately omits
    ``patternProperties``, ``minProperties``, ``maxProperties`` and ``dependencies``,
    because a node stating one of those beside a type LIST refuses by name rather than
    being cut onto an arm, so the arm misses those.

    A word with no :data:`ARM` entry is not a container and gets the empty set, which is
    the answer ``_container_kind`` reads as "neither".
    """
    grid = {"object": OBJECTS, "array": ARRAYS}.get(word)
    if grid is None:
        return frozenset()
    return frozenset({k for k in TABLE if grid_of(k) == grid} | set(ARM.get(word, ())))


def pins_a_floor(keyword: str) -> bool:
    """Does a NARROWER value of this keyword move UP.

    The one question both halves ask of a bound, and the reason :data:`RANGES` is declared
    rather than held per reader: a floor rises as it narrows and a ceiling falls, so a
    fold and a draw both turn on this one bit and must turn on the same one.
    """
    return keyword in FLOORS



def cell(keyword: str, position: Position) -> Cell | None:
    """This keyword's answer at this position, or ``None`` where it has no row.

    ``None`` is the answer that refuses the document BY NAME, and since section 14 step 8
    it is the ONLY answer that refuses it at all: a keyword in none of sections 5, 6 and 7
    is one the bundle does not use, and the first document to carry one is loud rather
    than ignored.  It was never a ``REFUSE`` cell -- "the two have different reasons and a
    reader should not have to tell them apart by prose" -- and the other reason is gone,
    so a key with a row is admitted whatever its row says.
    """
    row = TABLE.get(keyword)
    if row is None:
        return None
    return row.at.get(position, row.default)


def rendered_at(position: Position) -> frozenset[str]:
    """Every keyword a faithful model RENDERS as a fact about a value here.

    **The set the document-side FOLD ranges over** (``harness.FOLDED_FACTS``, which is
    this set at ROOT): a conjunct's facts are carried into the node it composes and a
    union's branch agreement into the branches' common node, and a keyword missing from
    this set is one the fold silently refuses to carry -- so a declaration made at the
    composed pointer, which is where ``emit._folded`` writes it, cannot be found there
    by ``harness.check_widening``'s walk.  A hand-written list beside the fold is the
    one way the fold can be complete with respect to itself and blind to everything
    beyond it, so it is read off the declaration instead.
    """
    return frozenset(k for k in TABLE if (c := cell(k, position)) is not None and c.rendered)


def descends_at(position: Position) -> Mapping[str, Position]:
    """The structural keywords at this position and the position each one's
    subschema(s) occupy -- the ONE descent table, where today there are three.

    Declared here ahead of its readers, which were section 14 step 5's.  They are built:
    ``bundle.py``, ``schema/parse.py``, ``emit.py``, ``lower/union.py``, ``harness.py``
    and ``tests/test_nested_union_sibling.py`` all read this function, which is what
    "where today there are three" was pointed at -- so the sentence above is the ONE
    descent table's statement of fact and no longer a declaration waiting for a reader.
    """
    out: dict[str, Position] = {}
    for keyword in TABLE:
        answer = cell(keyword, position)
        if answer is not None and answer.descends is not None:
            out[keyword] = answer.descends
    return out


def conditional() -> tuple[str, ...]:
    """draft-07's CONDITIONAL, as the three keywords that spell it, in APPLICATION order.

    **Here because which keywords spell a conditional is a keyword decision, and §3 makes
    this module the one place one lives.**  Two readers need the same answer and neither
    may restate it: ``harness.own_facts`` declines to fold a conjunct's conditional into a
    node's own facts, and ``harness.conditionals`` collects the triples whole.  Written in
    either of those it is a literal keyword collection outside this module, which §3's
    census (``survey/arch_audit.keyword_collections``) refuses by name.

    **A TUPLE and not a frozenset, unlike :func:`owns_a_location`, because the ORDER is
    part of the answer.**  The three are one TRIPLE whose members mean nothing apart --
    draft-07 gives ``then`` and ``else`` no effect without an ``if`` -- so a reader
    building the triple has to write its keys in a fixed order or two readings of one
    document produce two differently-ordered mappings.  The order is the order draft-07
    applies them in: the condition, then the arm it selects when satisfied, then the arm it
    selects when it is not.

    **NOT derived from the descent column, and the reason is a measurement of the table
    rather than a preference.**  ``descends_at(Position.ROOT)`` answers ``RULE`` for
    ``if``, ``then``, ``else`` AND for ``not`` -- §5 gives all four the same cell
    (``Effect.RULE``, unrendered, descending to ``Position.RULE``) -- so the four are
    indistinguishable by every column the grid has.  A derivation would therefore be the
    descent set minus ``not``, which restates the decision while appearing to read it.
    The grid's own text is what separates them: ``if``'s cell says "With ``then`` /
    ``else`` -> a rule on the nearest class", and ``_COMBINATORS["else"]`` IS
    ``_COMBINATORS["then"]``.
    """
    return ("if", "then", "else")


def owns_a_location() -> frozenset[str]:
    """The keywords whose subschema OWNS the child instance location it descends to.

    **The frontier walk's own set, read off the ownership column** (:attr:`Cell.owns`,
    which states what owning is and why no other column answers it): ``harness._OWNS`` is
    this call, and a frontier item is grouped by the location an owner decides while a
    keyword that merely CO-STATES one is conjoined where it stands.  Section 3's monopoly
    is the reason it is a reading and not a tuple beside the walk -- "the table is the one
    place a keyword decision lives" -- and which keywords own a location is a keyword
    decision: changing it changes which positions a pin REPLACES, so the two halves must
    read one declaration or the frontier and the table can disagree silently.

    **Position-free, unlike :func:`rendered_at` and :func:`descends_at`**, and the
    asymmetry is the fact and not an omission: ownership is draft-07's applicability, the
    same at every position a keyword descends from, and the walk reads a node's KEYS
    without being told the node's position -- so a position-keyed reader would make every
    caller choose one arbitrarily and would answer the same thing at all of them.
    """
    return frozenset(
        k for k, row in TABLE.items() if any(c.owns for c in (row.default, *row.at.values()))
    )


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

    The question the parser's classification asks of a branch
    (``parse.presence_clause``) and of a node's annotations, and the one the screen asks
    in the other direction.  A
    key that annotates without constraining is not a declaration; a key with no row is,
    because a keyword the bundle did not use before could constrain anything.

    **One clause, where there were two**, since ``Effect.REFUSE`` retired: a cell that
    REFUSED was a declaration because the screen could refuse the document on it, and no
    cell can.  So a key with a row declares exactly when the node's own handler has to
    write something for it, and a key whose drop is merely REPORTED
    (:attr:`Cell.reported`) is not a declaration -- ``bundle.reported_drops`` reads the
    document for those, not this predicate, which is what keeps the report out of the set
    the screen can refuse on.
    """
    answer = cell(keyword, position)
    if answer is None:
        return not admitted_by_prefix(keyword)
    return lowers(answer)


def admitted_by_prefix(keyword: str) -> bool:
    """The one admission by SHAPE: a vendor extension cannot be a schema keyword."""
    return keyword.startswith(NAMESPACE)


#: The EFFECTS a keyword can have without changing what a node ADMITS: a symbol
#: (``NAME``), a fact a lowering carries (``ANNOTATION``), a fact the enclosing FIELD
#: carries, or nothing at all.  The complement is :data:`LOWERED` -- "the effects the
#: NODE'S OWN handler has to write code for" -- which is exactly the set that compiles to
#: a TYPE or a RULE and therefore narrows an instance.
#:
#: ``FIELD`` is here on §2's own sentence about the one keyword that reaches it: a
#: ``default`` "neither widens nor narrows what the class accepts".
CARRIED = frozenset({Effect.NAME, Effect.ANNOTATION, Effect.FIELD, Effect.NOTHING})


def _carried() -> frozenset[str]:
    """Every keyword this TABLE gives no admitting effect at any position (§3a).

    §3a: "Identity here is STRUCTURAL and ignores annotations ... because an annotation
    does not change what a node admits."  **DERIVED from this table and not listed**,
    which is the one declaration §9 gives this question: "a keyword handled in code but
    named in none of §5, §6 or §7 is an invented rule", and a hand-written list beside the
    table is how the two come to disagree -- the list said ``default`` was an annotation
    while the table says its cell is FIELD at PROP, and said ``discriminator`` while the
    table says NOTHING.  It also hid the collection from ``tests/test_keywords.py``'s
    census, which reads literal keyword collections and cannot read a derivation it has no
    reason to doubt.

    Two screens beside the effect, and both are about what a key IS rather than what it
    asserts:

    * a keyword the descent column DESCENDS into is a SECTION or a subschema holder, so
      two nodes differing in one differ in a node below -- it is not an annotation of
      this node whatever its own cell says;
    * a keyword admitted by the ``x-`` PREFIX is admitted by prefix at the point of use
      (``catalogue.identity``, ``catalogue.Admitted``, ``harness._content_key``), for the
      reason §6 admits it that way: "The ``x-`` namespace is admitted by prefix AND listed
      by name", and a prefix test cannot be a set member.

    Measured over this bundle: the derived set and the list it replaces produce the same
    15 entries, the same 124 untitled groups, the same 3 conflicts, the same 23
    same-document restatements and the same 22 restating positions.  What it adds is the
    21 document-level metadata keys (``version``, ``lastUpdated``, ``baseUrl``, ...) and
    ``errorMessage``, every one of which the table already says asserts nothing -- so
    the derivation is wider than the list in exactly the direction §3a's sentence is.
    """
    descends = frozenset(word for position in Position for word in descends_at(position))
    return frozenset(
        word
        for word, _ in TABLE.items()
        if (
            effects := {
                answer.effect
                for position in Position
                if (answer := cell(word, position)) is not None
            }
        )
        and effects <= CARRIED
        and word not in descends
        and not admitted_by_prefix(word)
    )


#: The keys whose value does not change what a node ADMITS, so two nodes differing only in
#: one of them admit the same instances (§3a): :func:`_carried`'s derivation, and beside it
#: the two keys the TABLE does not list at all.
#:
#: ``$id`` and ``example`` are a document's own declaration of where it lives and the
#: bundle's singular spelling of ``examples``.  Neither has a row, so neither has a cell
#: to derive an effect from, and both are stated here -- which is the residue a
#: derivation cannot reach and is why it is two names and not fourteen.
#:
#: **IT IS HERE AND NOT IN ``codegen/catalogue.py``, WHICH IS WHERE IT WAS, BECAUSE THERE
#: ARE TWO READERS ACROSS §9's BOUNDARY** (``adcp-client-python-lzzj.8``).  The catalogue
#: keys a layer's identity on it (``catalogue.Admitted``) and the verifier keys §8's
#: fixture memo on it (``harness._content_key``) -- and §9's import set does not let the
#: verifier read the catalogue, so a set declared there would have had to be restated in
#: the verifier.  :func:`_carried`'s own argument is that a list beside this table is how
#: the list and the table come to disagree; two derivations of one set is the same defect
#: one step further out.  ``catalogue.ANNOTATIONS`` is now this name.
ANNOTATIONS = _carried() | frozenset({"$id", "example"})


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
    constrain an instance, so none compiles to a type, a rule or a base".  So it is a
    projection and not a second list, and only section 5's seven sub-tables are declared
    (:attr:`Row.grid`), the family of a keyword being derivable from no other column.

    **:data:`REFUSED` is the EMPTY projection and this function never returns it.**
    ``docs/plan/architecture.md`` section 3: "section 7's projection is now the empty one,
    because ``Effect.REFUSE`` is gone and no row can be in it; the generator still writes
    the region, and the region being empty is what makes 'no keyword refuses' a fact the
    document holds rather than a claim its prose makes."  So the grid NAME survives, as
    the region's name -- the generator zips :data:`GRIDS` against the document's marked
    regions -- and no arm here can reach it.

    **A row that carries nothing but HOLDS a subschema is section 5's**, and
    ``definitions`` is why the descent column is read here: it compiles to nothing at
    every position and section 5 states it anyway, because what it holds reaches an
    instance through a ``$ref``.  Section 6's preamble is about what a keyword
    compiles to; a keyword holding a subschema is structure whatever it compiles to.
    """
    row = TABLE[keyword]
    cells = (row.default, *row.at.values())
    if any(c.effect in COMPILES for c in cells):
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
