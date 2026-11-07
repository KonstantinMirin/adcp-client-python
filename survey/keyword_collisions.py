# noqa: INP001  -- `survey/` carries no `__init__.py` and all 15 scripts in it report this
# one finding. It is a statement about the DIRECTORY, not about this file, and silencing it
# here is a suppression with an owner rather than an exemption: the fix is `survey/__init__.py`
# or a measured per-file-ignore, which is filed as a row and is not this lane's to land.
"""Count the enum values that collide with a reserved word or an enum PROTOCOL of an SDK target.

::

    PYTHONPATH=.:src ./.venv/bin/python survey/keyword_collisions.py \
        --bundle schemas/cache/3.2.8 --table survey/keyword-collisions-3.2.8.tsv
    PYTHONPATH=.:src ./.venv/bin/python survey/keyword_collisions.py \
        --bundle schemas/cache/3.3.0-beta.4 --table survey/keyword-collisions-3.3.0-beta.4.tsv

READ-ONLY over the bundle; it opens no network and imports no wheel.  The four targets'
reserved-word sets live in ``survey/reserved-words.json`` -- committed as DATA with the
normative source of each -- so the figure is re-derivable without trusting a predicate
somebody typed here, and the two sets a running interpreter can confirm are cross-checked
against it on every run (:func:`load_sets`).

**THERE ARE TWO COLLISION CLASSES AND THEY ARE COUNTED SEPARATELY, BECAUSE THE SECOND IS
THE ONE THAT MATTERS.**

:data:`HARD` -- the value is a word the language RESERVES.  ``pass`` and ``global`` are
Python's.  This class is real and it is also easy to dismiss: the answer is a trailing
underscore, which is PEP 8's own and which ``datamodel-code-generator`` already applies, so
upstream's shipped wheel carries ``pass_ = 'pass'`` and ``global_ = 'global'`` and imports
cleanly.  A reader's reaction is *"so append an underscore"*, and they are not wrong.

:data:`PROTOCOL` -- the value is a member of the ATTRIBUTE PROTOCOL that every enum in the
language already has.  ``name`` and ``value`` are Python's ``Enum.name`` and ``Enum.value``;
``name`` is also Java's ``Enum.name()`` beside ``values()``, ``ordinal()`` and
``valueOf()``.  **Nothing breaks**, which is exactly why nobody noticed -- and why it is
worse than a break.  A build error is fixed on day one; this ships, and the cost appears
only when a person opens the generated module and reads four spellings that look alike and
mean four different things::

    Kind.NAME          # the member
    Kind.name          # IF a binding also bound the value-faithful attribute: the same
                       # object -- but it reads as protocol access, not as a member
    Kind.NAME.name     # 'NAME'  -- the identifier
    Kind.NAME.value    # 'name'  -- the wire value

This repository's answer is that the second line does not exist: ``Kind.name`` raises
``AttributeError`` and the migration note says to write ``Kind.NAME``
(``adcp.types._base.MEMBER_NAMES_TAKEN`` is the set that refuses it).  That is a decision
about DX and not a limitation -- CPython's ``enum`` uses ``DynamicClassAttribute`` precisely
so that a member MAY be called ``name``, and upstream's wheel does write ``name = 'name'``.
So the protocol class costs no language the ability to express the value; it costs every
binding in every language a permanently ambiguous read, and it costs the schema author one
word at authoring time to avoid.  That asymmetry is what this script is measured for.

**THE BUNDLE IS AN ARGUMENT AND THERE IS NO DEFAULT**, which is ``codegen/bundle.py``'s rule
read for a survey: an ask that goes UPSTREAM has to be measured over a bundle that is
UPSTREAM'S, and this repository carries four of which only two are
(:data:`UPSTREAM_BUNDLES`; see each directory's ``.provenance.json``, whose
``upstream.repository`` names ``adcontextprotocol/adcp`` for those two and the fork for
``schemas/cache/3.2`` and ``schemas/cache/3.3``).  A default here would be the one way this
script could produce a figure about our own fork and have it read as a figure about
upstream.

**THE PROJECTIONS ARE EXCLUDED AND THE EXCLUSION IS REPORTED AS A NUMBER.**
``codegen.bundle.PROJECTIONS`` names ``bundled/`` and ``mcp/``, which re-cut the same nodes
per transport -- so an occurrence there is one authoring decision counted again.  On
``schemas/cache/3.2.8`` that is 213,516 of 220,053 occurrences, a factor of 33: a figure
taken without the exclusion would say the problem is thirty times its size.  (On
``schemas/cache/3.3.0-beta.4`` the exclusion is 0 HERE, because that bundle's vendor
transform already dropped the 614 projection documents before they reached the tree; 3.2.8's
is the comparable figure.)

**WHAT A LANGUAGE'S OWN CASING CONVENTION DOES TO ITS OWN RESERVED WORDS IS MEASURED AND NOT
ASSUMED.**  Every Go keyword, every Go predeclared identifier, all 51 Java keywords, Java's
three literals and every ECMAScript reserved word is entirely lower-case; Python's 35 are
lower-case but for ``True``, ``False`` and ``None``, which still MOVE under ``str.upper``.
So Go's capitalised exported identifier, Java's UPPER_SNAKE constant and our own UPPER_SNAKE
member each escape their language's whole HARD class by construction.

**AND THE COLLISION THAT NO CONVENTION ESCAPES IS THE FOLD**: two values in ONE enum
differing only by case or by a separator become one identifier under any derivation that has
to handle a kebab value at all, because handling ``media-buy`` means splitting on the
separator and re-casing the words.  :func:`folds` measures it, and the one instance in both
upstream bundles -- ``formats/canonical/html5.json#/properties/clicktag_macro``'s
``clickTag`` beside ``clickTAG`` -- is what ``codegen.lower.enum.two_members_spell_one_name``
already routes to a ``Literal`` with no enum class and so no importable symbol per member.

:data:`DISPOSITION` is the judgment half and it is a TABLE rather than a predicate: per
measured position, whether an ADDITIVE phase-1 replacement is possible, what to propose, and
why.  :func:`check_dispositions` refuses a run where the census reaches a position the table
has no row for, so the proposals in the upstream ask cannot drift from the measurement they
are proposals about.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from codegen.bundle import PROJECTIONS, escape_key  # noqa: E402  (the sys.path line above)
from codegen.lower.enum import member_name, their_spelling  # noqa: E402

#: The reserved-word sets, as data.  Read and not restated: see that file's own ``_`` key.
SETS = Path(__file__).resolve().parent / "reserved-words.json"

#: The two bundles in this repository that are UPSTREAM'S.  Named so a run over anything
#: else prints the warning; it is not a whitelist and ``--bundle`` accepts any path.
UPSTREAM_BUNDLES = ("schemas/cache/3.2.8", "schemas/cache/3.3.0-beta.4")

#: The four target languages, in the order every report and every column group uses them.
TARGETS = ("python", "typescript", "go", "java")

#: **The HARD class, per target**: sets whose words the language RESERVES.  The answer to a
#: hit is a mangling, and every target has a conventional one.
HARD: dict[str, tuple[str, ...]] = {
    "python": ("hard_keywords",),
    "typescript": ("reserved_words", "strict_mode_reserved_words", "type_position_keywords"),
    "go": ("keywords", "predeclared_identifiers"),
    "java": ("keywords", "literals"),
}

#: **The PROTOCOL class, per target**: sets whose words name a member of the attribute
#: protocol an enum in that language ALREADY has.  A hit is not a compile error in any of
#: the four, which is the whole point -- see the module docstring's four-line block.  Go has
#: no entry because a Go enum is a set of typed constants with no member protocol at all:
#: the language gives the constant no ``.name`` and no ``.value`` to collide with.
PROTOCOL: dict[str, tuple[str, ...]] = {
    "python": ("enum_protocol",),
    "typescript": ("object_prototype",),
    "go": (),
    "java": ("enum_members",),
}

#: The keys under which a JSON Schema document's CHILD keys are arbitrary names rather than
#: keywords.  A document declaring a property literally called ``enum`` or ``const`` would
#: otherwise be read as declaring one.  Measured over all four bundles: 0 such properties,
#: so the guard fires nowhere today and is here because a walk that would miscount is not
#: made correct by the bundle happening not to exercise it.
NAME_POSITIONS = frozenset(
    {"properties", "patternProperties", "definitions", "$defs", "dependentSchemas", "dependentRequired"}
)

#: Everything outside an ASCII identifier, for the Go and Java derivations.  Deliberately
#: NOT shared with ``codegen.lower.enum``: that module's ``_OUTSIDE_AN_IDENTIFIER`` is a
#: statement about ``datamodel-code-generator``'s sanitiser and this one is a statement about
#: a word boundary in a Go or Java identifier.  One regex for two questions is how two
#: readings come to be mistaken for one.
_SEPARATOR = re.compile(r"[^0-9A-Za-z]+")

#: A lower-to-upper transition inside a word, which is where a camel-aware UPPER_SNAKE split
#: puts an underscore (``clickTag`` -> ``CLICK_TAG``).
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

#: Everything a FOLD drops: the comparison two values survive only if they differ by more
#: than case and punctuation.
_FOLD = re.compile(r"[^0-9a-z]")

VERDICT_FINE = "fine"
VERDICT_MANGLE = "needs mangling"
VERDICT_IMPOSSIBLE = "cannot be expressed"


class Position(NamedTuple):
    """One string value at one place in one document."""

    document: str
    pointer: str
    #: ``enum`` or ``const`` -- the keyword that put the value here, and the whole of the
    #: phase-1 question.  A value may be ADDED to an ``enum`` without breaking a producer or
    #: a consumer, because an enum that gains a member accepts strictly more; a ``const``
    #: has no such move, because widening it means replacing the keyword.
    keyword: str
    value: str
    #: The other string values of the same ``enum`` node, in document order; empty for a
    #: ``const``.  Carried because a replacement that collides with a sibling is worse than
    #: the problem it fixes.
    siblings: tuple[str, ...]


class Disposition(NamedTuple):
    """What the upstream ask should request for one position, and why."""

    #: ``additive``, ``const-widening`` or ``decline``.
    phase1: str
    #: The value to propose, or ``""`` where the row declines.
    propose: str
    reason: str


#: **The judgment half, as a table.**  One row per measured position whose value is in
#: Python's HARD or PROTOCOL class -- the 16 positions the upstream ask is about.  Keyed by
#: ``(document, pointer)`` so a row names a PLACE and never a word: the ten ``name``
#: positions do not take one answer, and a predicate over the word would have given them one.
#:
#: ``additive``
#:     the value is an ``enum`` member and the replacement can be LISTED BESIDE IT in the
#:     same array.  An enum that gains a member accepts strictly more than before, so this
#:     is non-breaking by construction and can land in any 3.x release.
#: ``const-widening``
#:     the value is a ``const``, so there is no member to add.  The replacement needs
#:     ``const: "x"`` to become ``enum: ["x", "y"]`` -- which still accepts strictly more and
#:     is still non-breaking, but is a structural edit to a discriminator rather than a
#:     one-line append.  This is the one case the ask has to state separately, because the
#:     "nobody is affected" argument is weaker for a schema shape change than for an append.
#: ``decline``
#:     the value is a PROJECTION SELECTOR over a response's own field set, so it is REQUIRED
#:     to equal a property name.  Changing it means renaming that property, which is a real
#:     wire change and not a free one -- the ask does not make it.  These positions also cost
#:     Python and Java nothing but the ambiguous read, so declining them loses little.
DISPOSITION: dict[tuple[str, str], Disposition] = {
    # ---- `pass`: three nodes, all plain enum members, all additive ---------------
    ("enums/binary-verdict.json", "/enum/0"): Disposition(
        "additive",
        "passed",
        "Siblings: fail. `passed` collides with no sibling and with no reserved word in any "
        "of the four targets. Adding `failed` beside `fail` in the same release would keep "
        "the pair symmetric, which is a nicety and not part of the ask.",
    ),
    (
        "content-standards/get-media-buy-artifacts-response.json",
        "/oneOf/0/properties/artifacts/items/properties/local_verdict/enum/0",
    ): Disposition(
        "additive",
        "passed",
        "Siblings: fail, unevaluated. `passed` collides with neither.",
    ),
    (
        "core/registry-event.json",
        "/$defs/compliancePayload/properties/tracks/additionalProperties/enum/0",
    ): Disposition(
        "additive",
        "passed",
        "Siblings: fail, partial, skip, silent, warning, unknown, skipped. This node ALREADY "
        "carries both `skip` and `skipped`, so a past participle is native to its own "
        "vocabulary; `passed` collides with no sibling.",
    ),
    # ---- `global`: one node, additive --------------------------------------------
    ("error-details/rate-limited.json", "/properties/scope/enum/2"): Disposition(
        "additive",
        "agent",
        'Siblings: account, tool. The node describes "What the limit applies to" and both '
        "siblings are ENTITIES rather than scope qualifiers, so the third should be one too. "
        "`agent` is the protocol's own noun for the thing that holds the account and serves "
        "the tool; `service` is the alternative if `agent` reads too narrow. Neither is "
        "reserved in any of the four targets.",
    ),
    # ---- `name`: four PROJECTION SELECTORS, declined ------------------------------
    ("creative/list-creatives-request.json", "/properties/fields/items/enum/1"): Disposition(
        "decline",
        "",
        "A field-projection selector: the value names the creative's own `name` property, and "
        "every other member of this enum names a property too (creative_id, format_id, "
        "assets, ...). Changing it means renaming the property or minting a second selector "
        "for one field.",
    ),
    ("enums/creative-sort-field.json", "/enum/2"): Disposition(
        "decline",
        "",
        "A sort-field selector over the creative's own properties, beside created_date, "
        "updated_date, status, assignment_count. Same reason as the projection selectors.",
    ),
    ("media-buy/product-fields.json", "/items/enum/1"): Disposition(
        "decline",
        "",
        "A field-projection selector over the product's own properties; the document's own "
        'title is "Product Response Fields" and its description says "Required product_id '
        'and name fields are always returned".',
    ),
    ("signals/get-signals-request.json", "/properties/fields/items/enum/3"): Disposition(
        "decline",
        "",
        "A field-projection selector over the signal definition's own properties; the "
        "description names `name` among the fields "
        '"always included when required by the response schema".',
    ),
    # ---- `name`: five SEMANTIC members, additive ---------------------------------
    (
        "core/signal-definition.json",
        "/properties/onboarder/properties/match_keys/items/enum/0",
    ): Disposition(
        "additive",
        "full_name",
        "Siblings: address, email, postal, lat_long, mobile_id, cookie_id, ip, customer_id, "
        "phone. These are KINDS OF IDENTIFIER and not property names, so the value is free. "
        "`full_name` is identity resolution's own word and collides with no sibling.",
    ),
    (
        "core/signal-definition-enrichment.json",
        "/properties/onboarder/properties/match_keys/items/enum/0",
    ): Disposition(
        "additive",
        "full_name",
        "The same node restated in a second document, with the same ten members; the two must "
        "move together or the pair stops agreeing.",
    ),
    ("sponsored-intelligence/si-identity.json", "/properties/consent_scope/items/enum/0"): Disposition(
        "additive",
        "full_name",
        "Siblings: email, shipping_address, phone, locale -- categories of consented data, "
        "not property names. `full_name` collides with no sibling.",
    ),
    ("enums/right-use.json", "/enum/2"): Disposition(
        "additive",
        "personal_name",
        "Siblings: likeness, voice, endorsement, motion_capture, signature, catchphrase, sync, "
        "background_music, editorial, commercial, ai_generated_image. The member's own "
        "description is \"Use of a person's name in advertising or promotional materials\", so "
        "`personal_name` states what the member means and reads with `likeness` and "
        "`signature`.",
    ),
    ("brand.json", "/definitions/color_ref/properties/kind/enum/0"): Disposition(
        "additive",
        "palette_key",
        "The discriminator of color_ref; siblings value, surface. The definition's own "
        'description says "Use kind=name for palette lookup keys in colors", so `palette_key` '
        "is the schema's own gloss. MUST move together with the `const` at "
        "/definitions/color_ref/oneOf/0/properties/kind/const, which is a const-widening row.",
    ),
    # ---- `value`: one enum member and one const ----------------------------------
    ("brand.json", "/definitions/color_ref/properties/kind/enum/1"): Disposition(
        "additive",
        "hex",
        "Siblings name, surface. The branch this discriminates requires the `value` property, "
        'which is a $ref to hex_color, and the description says "kind=value for a literal hex '
        "color\" -- so `hex` states it (`literal` is the alternative). MUST move together with "
        "the `const` at /definitions/color_ref/oneOf/1/properties/kind/const.",
    ),
    ("brand.json", "/definitions/color_ref/oneOf/0/properties/kind/const"): Disposition(
        "const-widening",
        "palette_key",
        "A `const` inside a oneOf branch, so there is no member to append to: accepting both "
        'spellings means `{"const": "name"}` becomes `{"enum": ["name", "palette_key"]}`. That '
        "still accepts strictly more and is still non-breaking, but it is a structural edit "
        "rather than a one-line append -- and the branch's `required` list also names the "
        "`name` PROPERTY, which this ask does not propose renaming.",
    ),
    ("brand.json", "/definitions/color_ref/oneOf/1/properties/kind/const"): Disposition(
        "const-widening",
        "hex",
        'The same move for the second branch: `{"const": "value"}` becomes '
        '`{"enum": ["value", "hex"]}`.',
    ),
}


def _say(line: str = "") -> None:
    print(line)  # noqa: T201  -- this script's output channel, as in codegen/__main__.py


def load_sets() -> dict[str, Any]:
    """The four targets' reserved-word sets, with the two a live interpreter can confirm.

    **The cross-check is the reason for loading them from a file at all.**  A committed list
    makes the figure re-derivable; a committed list that has drifted from the language makes
    it re-derivably wrong.  Python is the one target whose sets this interpreter HOLDS, so
    those two are compared against ``keyword.kwlist`` and ``keyword.softkwlist`` and a
    mismatch raises instead of printing a number.  Every set's stated ``count`` is checked
    against its own list for the same reason, which is what catches a word deleted by a bad
    edit in the three sets no interpreter here can confirm.
    """
    import keyword

    blob = json.loads(SETS.read_text())
    for key, live in (("hard_keywords", keyword.kwlist), ("soft_keywords", keyword.softkwlist)):
        stated = blob["python"][key]["words"]
        if sorted(stated) != sorted(live):
            msg = (
                f"survey/reserved-words.json python.{key} has drifted from this interpreter's: "
                f"stated-not-live {sorted(set(stated) - set(live))}, "
                f"live-not-stated {sorted(set(live) - set(stated))}"
            )
            raise SystemExit(msg)
    for language, group in blob.items():
        if language == "_":
            continue
        for name, entry in group.items():
            if isinstance(entry, dict) and "words" in entry and len(entry["words"]) != entry["count"]:
                msg = (
                    f"survey/reserved-words.json {language}.{name} states count "
                    f"{entry['count']} and lists {len(entry['words'])}"
                )
                raise SystemExit(msg)
    return blob


def census(bundle: Path) -> tuple[list[Position], collections.Counter[str], int, int]:
    """Every ``enum`` string value and every ``const`` string of the bundle's documents.

    Returns the positions, the per-keyword count of occurrences EXCLUDED because they sit
    under a projection directory, the number of ``enum`` nodes walked, and the number of
    documents walked.

    Every ``*.json`` under the bundle is walked, and not only ``codegen.bundle.portable``'s
    population: ``index.json``, ``manifest.json`` and ``manifest.schema.json`` describe the
    bundle rather than a message, so the compiler does not emit them -- but they are
    documents an author wrote, and a binding generator pointed at the artifact would read
    them.  They contribute 0 of either keyword in both upstream bundles, which is a
    measurement and not a reason to have left them out.
    """
    positions: list[Position] = []
    excluded: collections.Counter[str] = collections.Counter()
    nodes = 0
    documents = 0
    for path in sorted(bundle.rglob("*.json")):
        relative = path.relative_to(bundle)
        projection = relative.parts[0] in PROJECTIONS
        documents += not projection
        document = relative.as_posix()
        stack: list[tuple[object, str | None, str]] = [(json.loads(path.read_bytes()), None, "")]
        while stack:
            node, parent_key, pointer = stack.pop()
            if isinstance(node, dict):
                for key, child in node.items():
                    here = f"{pointer}/{escape_key(key)}"
                    named = parent_key in NAME_POSITIONS
                    if not named and key == "enum" and isinstance(child, list):
                        strings = tuple(v for v in child if isinstance(v, str))
                        if projection:
                            excluded["enum"] += len(strings)
                        else:
                            nodes += 1
                            positions += [
                                Position(document, f"{here}/{index}", "enum", value, strings)
                                for index, value in enumerate(child)
                                if isinstance(value, str)
                            ]
                    if not named and key == "const" and isinstance(child, str):
                        if projection:
                            excluded["const"] += 1
                        else:
                            positions.append(Position(document, here, "const", child, ()))
                    stack.append((child, key, here))
            elif isinstance(node, list):
                stack += [(child, None, f"{pointer}/{index}") for index, child in enumerate(node)]
    return positions, excluded, nodes, documents


# --------------------------------------------------------------------------- derivations


def go_exported(value: str) -> str:
    """The exported Go identifier a generator mints for one enum value.

    Split on every run of non-alphanumerics AND on a lower-to-upper transition, title-case
    each word, concatenate -- which is what ``oapi-codegen`` and ``go-swagger`` do, and what
    any derivation that must accept ``media-buy`` has to do: ``Media-buy`` is not an
    identifier, so the separator has to go, and once the words are split they have to be
    re-cased to stay readable.

    **The minimal alternative is stated because it is the only one that keeps the fold apart,
    and it cannot do the job.**  Capitalising the first rune alone maps ``clickTag`` and
    ``clickTAG`` to two identifiers -- but it maps ``media-buy`` to ``Media-buy``, so no
    generator can use it.  The collision this reports is therefore a property of the Go
    requirement and not of one generator's taste.
    """
    words = [part for chunk in _CAMEL.split(_SEPARATOR.sub(" ", value)) for part in chunk.split() if part]
    out = "".join(word[:1].upper() + word[1:].lower() for word in words)
    return out if out and not out[0].isdigit() else f"X{out}"


def java_constant(value: str) -> str:
    """The UPPER_SNAKE Java enum constant for one value (JLS 21 section 6.1's convention)."""
    words = [part for chunk in _CAMEL.split(_SEPARATOR.sub("_", value)) for part in chunk.split("_") if part]
    out = "_".join(word.upper() for word in words)
    return out if out and not out[0].isdigit() else f"V_{out}"


def folds(positions: list[Position]) -> list[tuple[str, str, tuple[str, ...]]]:
    """Every ``enum`` node where two values differ ONLY by case or by a separator.

    One row per colliding group, as ``(document, node pointer, the values)``.  The fold is
    the lower-cased value with every non-alphanumeric removed, which is the coarsest of the
    three derivations above and therefore reports a collision wherever any of them would:
    :func:`go_exported`, :func:`java_constant` and ``codegen.lower.enum.member_name`` all map
    two values with one fold to one identifier.
    """
    by_node: dict[tuple[str, str], list[str]] = {}
    for position in positions:
        if position.keyword != "enum":
            continue
        by_node.setdefault((position.document, position.pointer.rsplit("/", 1)[0]), []).append(position.value)
    out = []
    for (document, node), values in sorted(by_node.items()):
        grouped: dict[str, list[str]] = {}
        for value in values:
            grouped.setdefault(_FOLD.sub("", value.lower()), []).append(value)
        out += [
            (document, node, tuple(sorted(set(group))))
            for group in grouped.values()
            if len(set(group)) > 1
        ]
    return out


# --------------------------------------------------------------------------- the verdicts


def membership(value: str, sets: dict[str, Any]) -> list[str]:
    """Every reserved-word set of every target this value is in, as ``language.set``."""
    return [
        f"{language}.{name}"
        for language, group in sets.items()
        if language != "_"
        for name, entry in group.items()
        if isinstance(entry, dict) and "words" in entry and value in entry["words"]
    ]


def classes(value: str, sets: dict[str, Any]) -> dict[str, frozenset[str]]:
    """Per target, which of ``hard`` and ``protocol`` this value is in.  The central split.

    Both, one or neither.  ``name`` is in Python's ``protocol`` and Java's ``protocol`` and in
    nobody's ``hard``; ``pass`` is in Python's ``hard`` alone; ``package`` is in the ``hard``
    class of three of the four.
    """
    present = set(membership(value, sets))
    return {
        language: frozenset(
            label
            for label, keys in (("hard", HARD[language]), ("protocol", PROTOCOL[language]))
            if any(f"{language}.{key}" in present for key in keys)
        )
        for language in TARGETS
    }


def verdicts(value: str, sets: dict[str, Any], *, fold_collides: bool) -> dict[str, str]:
    """One of the three verdicts per target, under that target's own enum-constant convention.

    ``fold_collides`` is :func:`folds`' answer for this value's own node and it OVERRIDES the
    reserved-word reading in the three targets that derive an identifier: a value whose
    identifier a sibling has already taken cannot be a constant at all, whatever word it is.

    **A PROTOCOL hit is ``fine`` here and that is the honest answer, not a softening.**  None
    of the four targets refuses ``name`` as a constant: Python's ``DynamicClassAttribute``
    admits it, Java puts fields and methods in separate namespaces, TypeScript's member names
    are ``PropertyName``s, and Go has no member protocol at all.  The cost of the protocol
    class is the ambiguous read described in the module docstring, which no verdict in
    ``{fine, needs mangling, cannot be expressed}`` can express -- so it is reported as its
    own count instead of being smuggled into this one.
    """
    kinds = classes(value, sets)
    if fold_collides:
        # Every target that mints an identifier per member loses the enum class; TypeScript
        # does not, because a member name may be a quoted string and needs no derivation.
        return {
            "python": VERDICT_IMPOSSIBLE,
            "typescript": VERDICT_FINE,
            "go": VERDICT_IMPOSSIBLE,
            "java": VERDICT_IMPOSSIBLE,
        }
    return {
        # Our compiler upper-cases (`codegen.lower.enum.member_name`), which escapes all 35 --
        # so the canonical member is fine and the keyword cost lands on the value-faithful
        # second spelling that upstream's wheel carries. Reported as `needs mangling` because
        # that spelling is what every mainstream Python generator emits.
        "python": VERDICT_MANGLE if "hard" in kinds["python"] else VERDICT_FINE,
        # An enum member's name is a PropertyName, which admits any IdentifierName and so
        # every reserved word, and may also be a quoted string. Measured against tsc 5.9.3.
        "typescript": VERDICT_FINE,
        # Exported identifiers are capitalised and all 69 reserved words are lower-case.
        "go": VERDICT_FINE,
        # UPPER_SNAKE escapes all 51 keywords, the three literals and the six Enum members --
        # and a constant is a FIELD, which would not have collided with a method even verbatim.
        "java": VERDICT_FINE,
    }


def dx_cost(value: str, sets: dict[str, Any]) -> str:
    """What the value costs a reader of the generated code, where a verdict says ``fine``.

    ``-``
        nothing.
    ``<x>_``
        the trailing-underscore mangling -- PEP 8's "single trailing underscore ... to avoid
        conflicts with a Python keyword", which ``datamodel-code-generator`` applies and
        upstream's shipped wheel therefore carries (``pass_ = 'pass'``, ``global_ =
        'global'``).  Derived by :func:`codegen.lower.enum.their_spelling` rather than written
        out, so this column and upstream's own wheel cannot come apart.
    ``protocol-shadow``
        the value names a member of the language's own enum protocol.  Nothing breaks and
        nothing is mangled: upstream's wheel writes ``name = 'name'`` plainly, because only a
        true keyword gets the underscore.  The cost is the four-spelling read in the module
        docstring, and it is the one cost in this script that no compiler reports.
    """
    if any("protocol" in labels for labels in classes(value, sets).values()):
        return "protocol-shadow"
    spelled = their_spelling(value)
    return spelled if spelled is not None and spelled != value else "-"


def check_dispositions(positions: list[Position], sets: dict[str, Any]) -> list[str]:
    """Every position :data:`DISPOSITION` owes a row for and has none.  Empty is the pass.

    The population is the ask's: a value in Python's HARD or PROTOCOL class.  A row the census
    does NOT reach is reported too -- a proposal about a position that has moved is a proposal
    nobody can act on.
    """
    owed = {
        (position.document, position.pointer)
        for position in positions
        if "python" in {language for language, labels in classes(position.value, sets).items() if labels}
    }
    return [f"no DISPOSITION row for {d}#{p}" for d, p in sorted(owed - set(DISPOSITION))] + [
        f"DISPOSITION row for {d}#{p} reaches no position" for d, p in sorted(set(DISPOSITION) - owed)
    ]


# --------------------------------------------------------------------------- the table


COLUMNS = (
    "bundle",
    "value",
    "positions",
    "enum_positions",
    "const_positions",
    "class",
    "sets",
    "python",
    "typescript",
    "go",
    "java",
    "our_member_name",
    "their_attribute",
    "dx_cost",
    "go_identifier",
    "java_constant",
    "phase1",
    "propose",
    "documents",
    "pointers",
)


def rows(bundle_name: str, positions: list[Position], sets: dict[str, Any]) -> list[dict[str, str]]:
    """One row per COLLIDING value: it is in some target's set, or its fold is taken."""
    taken = {value for _, _, values in folds(positions) for value in values}
    grouped: dict[str, list[Position]] = {}
    for position in positions:
        if membership(position.value, sets) or position.value in taken:
            grouped.setdefault(position.value, []).append(position)
    out = []
    for value, group in sorted(grouped.items()):
        collides = value in taken
        verdict = verdicts(value, sets, fold_collides=collides)
        kinds = classes(value, sets)
        dispositions = {DISPOSITION[(p.document, p.pointer)] for p in group if (p.document, p.pointer) in DISPOSITION}
        out.append(
            {
                "bundle": bundle_name,
                "value": value,
                "positions": str(len(group)),
                "enum_positions": str(sum(1 for p in group if p.keyword == "enum")),
                "const_positions": str(sum(1 for p in group if p.keyword == "const")),
                "class": " ".join(
                    [*sorted({f"{lang}:{label}" for lang, labels in kinds.items() for label in labels})]
                    + (["fold"] if collides else [])
                )
                or "-",
                "sets": " ".join(membership(value, sets)) or "-",
                "python": verdict["python"],
                "typescript": verdict["typescript"],
                "go": verdict["go"],
                "java": verdict["java"],
                "our_member_name": member_name(value),
                "their_attribute": their_spelling(value) or "-",
                "dx_cost": dx_cost(value, sets),
                "go_identifier": go_exported(value),
                "java_constant": java_constant(value),
                "phase1": " ".join(sorted({d.phase1 for d in dispositions})) or "-",
                "propose": " ".join(sorted({d.propose for d in dispositions if d.propose})) or "-",
                "documents": " ".join(sorted({p.document for p in group})),
                "pointers": " ".join(f"{p.document}#{p.pointer}" for p in sorted(group)),
            }
        )
    return out


def report(bundle: Path, sets: dict[str, Any], table: Path | None) -> int:
    """The counts, the table and the dispositions -- the whole of what this script says."""
    name = bundle.as_posix()
    if name not in UPSTREAM_BUNDLES:
        _say(
            f"!! {name} is not one of this repository's upstream bundles {UPSTREAM_BUNDLES}.\n"
            f"!! Read {name}/.provenance.json: an ask measured over our own fork is wrong.\n"
        )
    positions, excluded, nodes, documents = census(bundle)
    enum_values = [p for p in positions if p.keyword == "enum"]
    consts = [p for p in positions if p.keyword == "const"]
    collisions = rows(name, positions, sets)

    _say(f"bundle                              {name}")
    _say(f"documents walked                    {documents}")
    _say(f"enum nodes                          {nodes}")
    _say(f"enum string values                  {len(enum_values)}      <- THE DENOMINATOR")
    _say(f"const strings                       {len(consts)}")
    _say(f"positions                           {len(positions)}")
    _say(
        f"EXCLUDED under {'/ '.join(PROJECTIONS)}/        {sum(excluded.values())} "
        f"(enum {excluded['enum']}, const {excluded['const']})"
    )
    _say()

    folded = folds(positions)
    hard: collections.Counter[str] = collections.Counter()
    protocol: collections.Counter[str] = collections.Counter()
    not_fine: collections.Counter[str] = collections.Counter()
    for row in collisions:
        count = int(row["positions"])
        kinds = classes(row["value"], sets)
        for language in TARGETS:
            hard[language] += count if "hard" in kinds[language] else 0
            protocol[language] += count if "protocol" in kinds[language] else 0
            not_fine[language] += count if row[language] != VERDICT_FINE else 0
    _say(f"{'':14}{'KEYWORD':>10}{'PROTOCOL':>10}{'not fine':>10}   (positions)")
    for language in TARGETS:
        _say(f"  {language:12}{hard[language]:>10}{protocol[language]:>10}{not_fine[language]:>10}")
    _say()
    _say("per set, positions")
    by_set: collections.Counter[str] = collections.Counter()
    for row in collisions:
        for entry in row["sets"].split():
            if entry != "-":
                by_set[entry] += int(row["positions"])
    for entry, count in sorted(by_set.items()):
        _say(f"  {entry:48}{count:>6}")
    _say()
    _say("the ask's own population, per value")
    for row in collisions:
        kinds = classes(row["value"], sets)
        labels = sorted({label for language, these in kinds.items() if language == "python" for label in these})
        if labels:
            _say(
                f"  {row['value']:12} {' '.join(labels):10} {row['positions']:>3} positions "
                f"(enum {row['enum_positions']}, const {row['const_positions']})  "
                f"ours {row['our_member_name']}, theirs {row['their_attribute']}"
            )
    _say()
    _say(f"enum nodes with a case/separator FOLD collision   {len(folded)}")
    for document, node, values in folded:
        _say(f"  {document}#{node}   {' '.join(values)}  ->  {java_constant(values[0])} / {go_exported(values[0])}")
    _say()
    _say("the ask's own population (Python HARD + PROTOCOL), by what phase 1 can do for it")
    by_phase: collections.Counter[str] = collections.Counter()
    reached = {(p.document, p.pointer) for p in positions}
    for key, disposition in DISPOSITION.items():
        if key in reached:
            by_phase[disposition.phase1] += 1
    for phase, count in sorted(by_phase.items()):
        _say(f"  {phase:48}{count:>6}")
    _say()
    complaints = check_dispositions(positions, sets)
    for complaint in complaints:
        _say(f"!! {complaint}")
    if table is not None:
        lines = ["\t".join(COLUMNS), *("\t".join(row[column] for column in COLUMNS) for row in collisions)]
        table.write_text("\n".join(lines) + "\n")
        _say(f"wrote {table}  ({len(collisions)} colliding values)")
    return 1 if complaints else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="measure enum-value collisions with the SDK targets")
    parser.add_argument("--bundle", required=True, type=Path, help="the bundle directory to measure")
    parser.add_argument("--table", type=Path, default=None, help="where to write the TSV")
    args = parser.parse_args(argv)
    return report(args.bundle, load_sets(), args.table)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
