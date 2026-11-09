"""THE JUDGMENT PASS over §3a's PENDING sets, and the verdict each entry gets.

``docs/plan/architecture.md``, "THE JUDGMENT IS DATA, NEVER CODE": collection is
deterministic and so is generation, and the only thing that is not is **whether two
identical-looking types are the same subject.**  This module is the reading that question
is answered FROM -- never the answer.  It derives, per pending entry, which evidence the
bundle itself gives, and it prints the three-way outcome the table's author records.

**A SHARED FIELD SET IS A HYPOTHESIS, NOT A VERDICT**, and nothing here reads two class
definitions side by side: every input is the published bundle, through
:class:`codegen.catalogue.Admitted` and :func:`codegen.bundle.named_nodes`.

**THE VERDICT SET IS TWO AND THE AUTHOR'S OUTCOME SET IS THREE.**

* **COLLAPSE** -- one subject the bundle states more than once.  The evidence is that the
  bundle states ONE AND THE SAME NAME at every stating position, which is §3a's own ruling
  -- *"the property name the positions share | stated | take it"* -- and that no other
  entry of the layer derives that name, which is ``collect_shapes``' own first-fit rule.
  Collapsing mints nothing, because the word is the bundle's at every position.
* **SPLIT** -- two or more subjects that happen to state one structure.  §3a's derivation
  is the evidence and it is available at ONE layer only: *"an object's key holds the
  property NAMES, while an array's key over a scalar element holds no name at all --
  which is why the object layer can collapse on identity and the array layer must not"*.
  So an entry whose structure carries NO field names and whose positions the bundle names
  differently is two subjects by the bundle's own words at those positions.
* **UNDECIDABLE** -- the bundle gives no evidence either way, which is §3a's third local
  state, *"separate types pending a name ... the positions are plausibly one subject and
  nothing in the bundle names it"*.  **This is where a field set under DIFFERING property
  names lands, and the reason is that a property name is the FIELD's role and not the
  type's name**: ``total_budget`` and ``fee`` are both money and ``flight`` and
  ``accounting_period`` are not one period, and nothing in the bundle separates those two
  cases.  A `title` does, which is why #8735 is worth filing.

**WHAT A NAMED MEMBER DOES AND DOES NOT DECIDE.**  Nineteen of the pending entries have a
stating position the bundle's own ``$ref``\\ s reach, so that position's pointer is a name
the bundle gives.  **It names THAT POSITION's subject and not the entry's**: the bundle
writes ``#/definitions/money`` once and restates ``{amount, currency}`` at nine sites it
calls ``total_budget``, ``fee`` and ``execution_commitment``, and it writes
``#/definitions/ReportingReliabilityMeasurementPeriod`` once and restates ``{start, end}``
at a site it calls ``flight``.  One of those is plausibly one subject and one is plausibly
not, and a reading that collapsed on the named member alone would decide both the same way.
So a named node enters this pass as a name AT ITS POSITION, by the same reading every other
position gets, and it decides the entry only where the rest of the bundle agrees with it.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from codegen import bundle, catalogue, constraints

BUNDLE = Path("schemas/cache/3.2")

COLLAPSE = "COLLAPSE"
SPLIT = "SPLIT"
UNDECIDABLE = "UNDECIDABLE"


def name_at(pointer: str) -> str | None:
    """The name the bundle states for the node at ``pointer``, or ``None`` for none.

    §4's step 1 read at the LAST naming segment rather than over the whole chain: the
    question a verdict asks is what the bundle CALLS this position, and the chain above it
    is where the position lives.  ``catalogue.NAMING`` is the segment set and is derived
    from the descent column, so a keyword whose key is a name joins it by its own cell --
    and a ``definitions`` entry's key is read by the same sentence as a property's, which
    is what keeps a node the bundle NAMES from getting a privileged reading here.

    An ``items`` or a combinator index after the name does not change it -- the items of
    ``tags`` are still tags -- which is §4's own nested rule read for this purpose.
    """
    parts = [part for part in pointer.split("/") if part]
    for at in range(len(parts) - 1, 0, -1):
        if parts[at - 1] in catalogue.NAMING:
            return parts[at]
    return None


@dataclass(frozen=True)
class Judged:
    """One pending entry, the evidence the bundle gives for it, and the outcome."""

    layer: str
    key: catalogue.DecidedKey
    positions: tuple[catalogue.Shaped, ...]
    #: The names the bundle states over the positions, ``None`` for a position it names
    #: under none.
    names: frozenset[str | None]
    #: Does another entry of this layer derive the same single name?  ``collect_shapes``'
    #: first-fit rule: a candidate two entries derive has identified neither.
    shared_with_another_entry: bool
    #: Does this entry's structure carry FIELD NAMES at all?  True for every L2 entry by
    #: construction, and at L3 exactly where the element is an object -- which is §3a's
    #: "an array's key over a scalar element holds no name at all".
    carries_field_names: bool
    #: The stating positions the bundle's own ``$ref``\\ s reach, or that are document
    #: roots.  Reported, never a branch of the outcome -- see the module docstring.
    named: tuple[catalogue.Shaped, ...] = ()
    #: For an L3 entry, which layer beneath owns its ELEMENT (:func:`element_owner`); the
    #: empty string at L2, which states the structure itself.
    element: str = ""

    @property
    def one_name(self) -> str | None:
        only = next(iter(self.names)) if len(self.names) == 1 else None
        return only

    @property
    def outcome(self) -> str:
        if self.one_name is not None and not self.shared_with_another_entry:
            return COLLAPSE
        if self.one_name is None and len(self.names) > 1 and not self.carries_field_names:
            return SPLIT
        return UNDECIDABLE

    @property
    def evidence(self) -> str:
        """The sentence a reviewer checks the outcome against, in the bundle's own terms."""
        spelled = ", ".join(
            repr(name) for name in sorted(self.names, key=lambda n: (n is None, n))
        )
        if self.one_name is not None and not self.shared_with_another_entry:
            reached = " and the bundle's own $refs reach one of them" if self.named else ""
            return (
                f"the bundle names every one of the {len(self.positions)} positions "
                f"{self.one_name!r}, no other entry of {self.layer} derives that name"
                f"{reached}"
            )
        if self.one_name is not None:
            return (
                f"the bundle names every position {self.one_name!r}, and another entry of "
                f"{self.layer} derives that same name, so it identifies neither"
            )
        if self.names == frozenset({None}):
            return "no stating position sits under a name the bundle states"
        if not self.carries_field_names:
            return (
                f"the element carries no field names and the bundle names these positions "
                f"differently: {spelled}"
            )
        return f"the bundle names these positions differently: {spelled}"

    @property
    def defect(self) -> str:
        """The UPSTREAM defect this entry's verdict compensates for.

        One per outcome, and each is a sentence about the BUNDLE rather than about us --
        §3a: "an entry with no named defect is not a judgment, it is a preference, and it
        does not belong in the table".
        """
        n = len(self.positions)
        docs = len({p.document for p in self.positions})
        if self.element and OWNED[self.element] is None:
            # §3a's array derivation, read as what it means for a DEFECT: "the only thing
            # an array position can write twice is its ELEMENT -- and an element is owned by
            # a layer beneath".  Where the bundle already names that element, ``list[X]`` is
            # written once by construction and the entry records nothing the bundle did
            # wrong.  It stays in the PASS, because the pass accounts for every pending
            # entry, and it can never reach the override table, because the table takes only
            # entries that name a defect.
            return (
                f"NONE: the element is {self.element}, so the {n} positions in {docs} "
                "documents write one `list[X]` by construction and this entry records no "
                "defect of the bundle's"
            )
        if self.outcome == COLLAPSE:
            return (
                f"RESTATEMENT OF A NAMED SUBJECT: the bundle states this structure at {n} "
                f"positions in {docs} documents, calls every one of them "
                f"{self.one_name!r}, and joins them by no $ref -- so it defines one thing "
                f"{n} times"
            )
        if self.outcome == SPLIT:
            return (
                f"UNDECLARED COINCIDENCE: {n} positions in {docs} documents admit "
                "identically under names the bundle states differently, and the bundle "
                "says nothing about whether the coincidence is intended"
            )
        return (
            f"AN UNNAMED REPETITION: the bundle states this structure at {n} positions in "
            f"{docs} documents and titles it at none of them, so nothing in it tells a "
            "shared subject from a coincidental overlap"
        )

    @property
    def would_decide_it(self) -> str | None:
        """For an UNDECIDABLE entry, the one thing that turns it into a verdict."""
        if self.outcome != UNDECIDABLE:
            return None
        return (
            "a `title` at these positions: one string at every position says one subject "
            "and collapses the entry; two different strings say two subjects and split it"
        )

    @property
    def beneath_a_rule(self) -> bool:
        """Does any stating position sit inside an ``if``, ``then``, ``else`` or ``not``?

        ``adcp-client-python-q5g``'s set, and it is what separates an entry #8735 already
        asks about from one whose ask is still bare: #8735's denominator excludes these
        because a subschema inside a ``not`` has no subject and cannot be the object of a
        title ask.
        """
        return any(p.beneath_a_rule for p in self.positions)


def pending(
    admitted: catalogue.Admitted, layer: str, standing: dict[str, int]
) -> list[tuple[catalogue.DecidedKey, tuple[catalogue.Shaped, ...]]]:
    """§3a's PENDING set for one structural layer: the entries nothing in the bundle NAMES.

    Read off ``collect_shapes``' own parts and never re-derived (§3a: "a derived reading of
    the bundle is an argument, not something a callee recomputes"):

    * at L2, an ENTRY the bundle titles at no position -- :attr:`ShapeEntry.title` is
      ``None``, which is §4's steps 2 and 3 -- plus :attr:`Shapes.declaring_nothing`, whose
      members are untitled by the same test and are reported rather than collected;
    * at L3, :attr:`Shapes.untitled`, which is the whole of the layer that collects
      nothing.
    """
    shapes = catalogue.collect_shapes(admitted, layer, standing)
    out: list[tuple[catalogue.DecidedKey, tuple[catalogue.Shaped, ...]]] = []
    if layer == "L2":
        out += [
            (entry.key, entry.positions)
            for entry in shapes.entries.values()
            if entry.title is None
        ]
        out += [(group[0].key, group) for group in shapes.declaring_nothing]
    else:
        out += [(group[0].key, group) for group in shapes.untitled]
    return out


def _carries_field_names(admitted: catalogue.Admitted, layer: str, at: catalogue.Shaped) -> bool:
    """Does this entry's structure carry FIELD NAMES, or only a container?

    §3a's one asymmetry between the two structural layers: "an object's key holds the
    property NAMES, while an array's key over a scalar element holds no name at all".  An
    L2 position holds a non-empty ``properties`` by :func:`catalogue.shape_states`' own
    screen, so the question is only ever asked of an array -- and it is asked of the
    ELEMENT, resolved through the same ``$ref`` reading the key is computed under.
    """
    if layer == "L2":
        return True
    node = bundle.node_at(admitted.document(at.document), at.pointer)
    element = node.get("items")
    if not isinstance(element, dict):
        return False
    resolved = admitted.of(at.document, element)
    return isinstance(resolved, dict) and bool(resolved.get("properties"))


def judged(admitted: catalogue.Admitted, standing: dict[str, int]) -> list[Judged]:
    """Every pending entry of both structural layers, with its evidence and its outcome."""
    names = bundle.named_nodes(admitted.dir)
    out: list[Judged] = []
    for layer in ("L2", "L3"):
        groups = pending(admitted, layer, standing)
        #: The first-fit rule over the WHOLE layer, which cannot be known one entry at a
        #: time: a name two entries derive has identified neither.
        derived: Counter[str] = Counter()
        for _, group in groups:
            stated = {name_at(p.pointer) for p in group}
            if len(stated) == 1 and None not in stated:
                derived[next(iter(stated))] += 1
        for key, group in groups:
            stated = frozenset(name_at(p.pointer) for p in group)
            one = next(iter(stated)) if len(stated) == 1 else None
            out.append(
                Judged(
                    layer=layer,
                    key=key,
                    positions=group,
                    names=stated,
                    shared_with_another_entry=one is not None and derived[one] > 1,
                    carries_field_names=_carries_field_names(admitted, layer, group[0]),
                    element="" if layer == "L2" else element_owner(admitted, group[0]),
                    named=tuple(
                        p
                        for p in group
                        if p.is_a_root or p.pointer in names.get(p.document, frozenset())
                    ),
                )
            )
    return out


#: What OWNS an L3 entry's element, which is what decides the ask it is filed under.
#:
#: §3a: "an element is owned by a layer beneath: a reference, an object, a constrained
#: scalar, an enumeration, a composition, or a scalar with no type to write".  Measured over
#: the 237 pending array entries, **all six cases are occupied and none is empty**: 148 a
#: document the bundle names, 3 a node it names, 21 an L2 object, 31 an L1 constrained
#: scalar, 14 an L0 vocabulary, 9 a composition, 11 a bare scalar.  So the array layer owes
#: no ask of its own, and an entry whose element is already named owes none at all.
OWNED = {
    "a DOCUMENT the bundle names": None,
    "a NAMED NODE the bundle names": None,
    "an L0 vocabulary": None,
    "a composition": None,
    "a bare scalar, no type to write": None,
    "an L1 constrained scalar": "adcontextprotocol/adcp#8525",
    "an L2 object": "adcontextprotocol/adcp#8735",
}

#: The keywords that make an element a CONSTRAINED SCALAR, which is #8525's own layer.
#: Derived from the module that spells them, so a constraint joining the layer joins this.
_L1 = frozenset(keyword for keyword, _ in constraints.SPELLING)


def element_owner(admitted: catalogue.Admitted, at: catalogue.Shaped) -> str:
    """Which layer beneath owns this array entry's element.  §3a's own six cases."""
    element = bundle.node_at(admitted.document(at.document), at.pointer).get("items")
    if not isinstance(element, dict):
        return "a bare scalar, no type to write"
    if "$ref" in element:
        target = admitted.target(at.document, element["$ref"])
        if target is not None and target[1] == "":
            return "a DOCUMENT the bundle names"
        return "a NAMED NODE the bundle names"
    if element.get("enum") or "const" in element:
        return "an L0 vocabulary"
    if element.get("properties"):
        return "an L2 object"
    if _L1.intersection(element):
        return "an L1 constrained scalar"
    if {"anyOf", "oneOf", "allOf"}.intersection(element):
        return "a composition"
    return "a bare scalar, no type to write"


def ask_for(row: Judged) -> str:
    """The ask this entry is filed under, derived and never assigned.

    Three axes, each a reading rather than a choice:

    * **inside a rule** -- ``adcp-client-python-q5g``'s carve-out, and it is BARE.  #8735's
      own denominator excludes these 26 entries because a subschema inside a ``not`` has no
      subject and cannot be the object of a title ask, so the ask cannot be filed until
      that row closes the screen to §3a's depth;
    * **L2** -- ``adcontextprotocol/adcp#8735``, whose set is exactly these 95 entries over
      255 positions;
    * **L3** -- the ELEMENT's layer's ask (:data:`OWNED`), because the array layer collects
      nothing and owes nothing: #8735 posts the array set in three comments "for
      completeness and **not** as an ask", and this is the derivation behind that sentence.
    """
    if row.beneath_a_rule:
        return "adcp-client-python-q5g (BARE: #8735's denominator excludes a node inside a rule)"
    if row.layer == "L2":
        return "adcontextprotocol/adcp#8735"
    owed = OWNED[row.element]
    if owed is None:
        return (
            f"none owed: the element is {row.element}, so `list[X]` is written once by "
            "construction and there is nothing here to name"
        )
    return f"{owed} (the element's layer: {row.element})"


def digest(key: catalogue.DecidedKey) -> str:
    """A short stable name for an admitted key, for a reader and for a gate to join on.

    The key itself is the whole admitted set written out -- a megabyte for one entry at the
    wide end -- so a checked-in table carrying it would be 30 MB of text no reviewer reads.
    The POSITIONS are what identifies the entry to a reader; this is what identifies it to a
    diff, and it moves exactly when the admitted set does.

    **THIS IS A READER'S NAME FOR AN ENTRY AND NOT THE ENTRY'S IDENTITY**, which is why it
    is the one place that may render a decided key (``catalogue.DecidedKey``) and
    ``catalogue.Admitted.key`` is the rendering it uses: a digest is bytes by definition,
    so a reading that needs bytes renders here, once, for 109 table rows -- and every
    checked-in row keeps the name it had, because these are the same bytes the key was
    hashed from before the layers stopped carrying text.
    """
    return hashlib.sha256(repr(key).encode()).hexdigest()[:16]


def table(rows: list[Judged]) -> dict:
    """The verdict table, as the data a reviewer reads and a gate ranges over."""
    return {
        "over": "docs/plan/architecture.md §3a's PENDING sets at L2 and L3",
        "derivation": "survey/judgment.py, over schemas/cache/3.2",
        "entries": [
            {
                "layer": row.layer,
                "outcome": row.outcome,
                "key": digest(row.key),
                "positions": [f"{p.document}#{p.pointer or '/'}" for p in row.positions],
                "evidence": row.evidence,
                "defect": row.defect,
                "ask": ask_for(row),
                **({"element": row.element} if row.element else {}),
                **({"would_decide_it": row.would_decide_it} if row.would_decide_it else {}),
            }
            for row in rows
        ],
    }


