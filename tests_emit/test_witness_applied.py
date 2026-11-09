"""**THE WITNESS HAS AN UPWARD READING**: the subject a CLASS names, graded.

``codegen/verify/witness.py`` builds one admitted value per NODE.  A class is not paired
with a node: ``docs/plan/architecture.md`` §8's pairing rule is that *"a branch class of a
root union is paired with its branch node read UNDER THE ROOT'S SIBLINGS"*, and
``adcp.types._base.applied_schema`` is how this project already reads that -- the
conjunction travelling beside the node as the applied schema rather than replacing it, with
the identity staying the POINTER's (§9).  ``SchemaBound.strict_validate`` validates a
payload against exactly that, so a witness built from the branch node ALONE is narrower
than the class it would be offered to, and offering it would grade 2,584 classes against
witnesses narrower than the classes.

:meth:`codegen.verify.witness.Construction.applied` is the upward reading and
:class:`codegen.verify.witness.Subject` is what it returns.  This file is the four clauses
that make it one:

* the conjunction is POINTERS of the record and no document this module minted --
  :func:`test_the_upward_reading_conjoins_only_pointers_the_record_holds`;
* the branch a pointer takes is an ANSWER and not a choice --
  :func:`test_the_upward_reading_answers_the_union_hops_the_pointer_itself_spells`;
* no node is serialised to identify one --
  :func:`test_the_subject_is_read_from_pointers_and_no_node_is_serialised`;
* **it moves no class out of its own subject** --
  :func:`test_the_upward_reading_moves_no_class_out_of_its_own_subject`.

**AND THE OBLIGATION ITSELF, which is RED and names every member of the set it is red on**:
:func:`test_no_class_s_witness_is_refused_by_its_own_subject` and
:func:`test_every_class_is_stamped_at_a_pointer_its_record_holds`.
``docs/plan/final-state.md``'s rule is the reason they are not ratchets: *"A READING HOLDS
OR IT DOES NOT.  Never M of N.  A fraction is a statement about the instrument, not about
the artifact."*  So neither carries a count, neither carries an allowlist, and the pairs
they are red on are named in the assertion where a reader of the failure sees them.

**WHAT THE UPWARD READING IS WORTH, measured here and quoted nowhere else**
(:func:`_verdicts`, and ``NODESET_CENSUS`` is how a verdict reads these figures).  Over
every pair of the graded tree, the node's own reading against the node's reading under the
conjunction that reaches it:

=================  ==========  =============================================
down               up          what it is
=================  ==========  =============================================
admitted           admitted    the pairing was already right there
refused            admitted    the gap this reading closes
no value           admitted    the conjunction supplied the missing statement
refused            refused     this file's first red
refused           no value     the conjunction admits nothing this can state
no value           no value     a pattern of a shape the reader declines
unreachable        unreachable  this file's second red
=================  ==========  =============================================

and the one transition that must be EMPTY is ``admitted -> anything else``, which is the
monotonicity :func:`test_the_upward_reading_moves_no_class_out_of_its_own_subject` asserts:
a conjunction with more statements in it admits fewer values, so a witness built under it is
still one the subject admits.

**ON ONE WORKER WITH THE OTHER WITNESS FILES** (``xdist_group``).  A warmed
:class:`codegen.verify.witness.Construction` is ~660 MB and ``tests/constructed.py`` holds
exactly one per process, so a second worker building its own pays the memory twice and
reports a second reading of one number.
"""

from __future__ import annotations

import ast
import collections
import pathlib

import compared
import constructed
import pytest
from nodeset import claimed, partitions

from adcp.types._base import applied_schema, schema_at
from codegen import bundle
from codegen.verify import witness

MODULE = pathlib.Path(witness.__file__)

#: The group ``tests/constructed.py``'s readers share.  Named here as the literal the other
#: witness modules use, because the marker is read by ``pytest-xdist`` off the mark and
#: there is no object to share.
pytestmark = pytest.mark.xdist_group("witness")


class Verdict(collections.namedtuple("Verdict", "state detail")):
    """One pair's answer: which part of the partition it falls in, and why.

    :attr:`state` is one of ``admitted``, ``refused``, ``no value``, ``unreachable`` or
    ``unpaired``, and :attr:`detail` is the KEYWORDS the subject refused on or the reason
    there was no value -- never a sentence this file composed, so a reader of a failure
    reads the document's own answer.
    """


def _record_pointer(ref) -> str | None:
    """The record-relative pointer a :class:`SchemaRef` names.

    ``codegen.verify.witness._local`` is the ONE reading of it, shared with the
    construction's own ``$ref`` handling: a ``SchemaRef`` spells ``#`` and ``#/oneOf/0``
    where the record's pointer space spells ``""`` and ``/oneOf/0``, and two spellings of
    that mapping is how a grader and a construction come to disagree about which node a
    class names.
    """
    return witness._local(ref.pointer)


def _carried(node: dict, record: dict) -> dict:
    """``node``'s statements at ITS OWN LOCATION, with a sole reference followed.

    ``allOf`` and ``type`` are dropped because they are the two the conjunction travels on
    (``applied_schema``'s last three lines), and a bare ``$ref`` is FOLLOWED because
    draft-07 reads a reference's target as the node's own statements and both walks take
    that hop without counting it.  One document of this bundle reaches it:
    ``core/requirements/catalog-field-binding.json#/oneOf/0`` is written
    ``{"$ref": "#/definitions/AssetPoolBinding"}``, which ``applied_schema`` leaves exactly
    as the document spells it -- the clause in ``through_the_store`` about a document's own
    local reference -- and which the construction reads through.
    """
    for _ in range(witness._STORE_HOPS):
        own = {k: v for k, v in node.items() if k not in ("allOf", "type")}
        ref = own.get("$ref")
        if len(own) != 1 or not isinstance(ref, str):
            return own
        target = witness._local(ref)
        if target is None:
            return own
        node = bundle.node_at(record, target)
    raise RecursionError("a sole reference does not settle")


def _subject_of(pair) -> dict:
    """The subject ``strict_validate`` validates against, for this pair.

    ``schema_at`` and not ``applied_schema`` directly, because ``schema_at`` is the accessor
    every production reader of a node goes through -- it resolves the record through the
    module the class was emitted into and puts the record's own storage back.  That is the
    schema half of ``SchemaBound.strict_validate``, which is the thing the witness has to
    agree with.
    """
    return schema_at(pair.ref, module=pair.module)


def _graded(pair, construction: witness.Construction, *, upward: bool) -> Verdict:
    """One pair's verdict, from one of the two readings.

    The screen is the DOCUMENT'S OWN VALIDATOR evolved onto the subject
    (:meth:`codegen.verify.witness.Construction.validator`), which is two decisions and both
    are measured elsewhere in this suite.  It carries the draft's own FORMAT CHECKER, so
    ``format: date-time`` asserts something -- a bare ``Draft7Validator`` makes it assert
    nothing and produces a false admission.  And it is rooted at the DOCUMENT, so a local
    ``$ref`` inside the subject resolves; handed the subject alone, ``jsonschema`` resolves
    ``#/`` within it and refuses every payload (``adcp.types._base._refuse_at`` carries that
    measurement).
    """
    document = pair.ref.document
    pointer = _record_pointer(pair.ref)
    if pointer is None or document not in constructed.records():
        return Verdict("unpaired", f"{pair.ref.pointer} is not a pointer of a graded record")
    try:
        subject = _subject_of(pair)
    except Exception as e:  # noqa: BLE001 -- the pairing's own failure, reported as one
        return Verdict("unpaired", f"schema_at raised {type(e).__name__}: {e}")
    try:
        built = (
            construction.applied(document, pointer)
            if upward
            else construction.value(document, pointer, (pointer,))
        )
    except Exception as e:  # noqa: BLE001 -- a pointer the record does not hold is a finding
        return Verdict("unreachable", f"{type(e).__name__}: {e}")
    if not built.held:
        return Verdict("no value", built.reason)
    refused = sorted(
        {
            error.validator
            for error in construction.validator(document)
            .evolve(schema=subject)
            .iter_errors(built.value)
            if isinstance(error.validator, str)
        }
    )
    return Verdict("admitted", "") if not refused else Verdict("refused", ",".join(refused))


def _verdicts() -> dict[str, tuple[Verdict, Verdict]]:
    """Every pair of the graded tree, under BOTH readings, computed once.

    ``(downward, upward)`` per pair, because the obligation and the thing that makes it
    satisfiable are one measurement: the upward reading's whole claim is that it moves pairs
    INTO their own subject and none out of it, and a file that computed only the upward half
    could assert the first and not the second.

    Held on the module, for ``tests/constructed.py``'s own reason: two derivations of one
    number is how a verdict comes to disagree with the gate it cites.
    """
    if not _HELD:
        down = witness.Construction(constructed.records())
        up = witness.Construction(constructed.records())
        for pair in compared.pairs():
            _HELD[f"{pair.ref.document}{pair.ref.pointer}"] = (
                _graded(pair, down, upward=False),
                _graded(pair, up, upward=True),
            )
    return _HELD


#: **TWO constructions and not one**, because the two readings share a memo key: the
#: downward call keys on ``(document, pointer, (pointer,))`` and the upward one on
#: ``(document, pointer, (pointer, *besides))``, which do not collide -- but the NODE memo
#: and the validator memo are shared and would make the second reading's cost a function of
#: the first's order.  Separate objects is what keeps each number the reading's own.
_HELD: dict[str, tuple[Verdict, Verdict]] = {}


def _by_state(which: int, state: str) -> set[str]:
    return {name for name, row in _verdicts().items() if row[which].state == state}


# --------------------------------------------------------------------------- #
# the conjunction is pointers, and the identity is the pointer's
# --------------------------------------------------------------------------- #
def test_the_upward_reading_conjoins_only_pointers_the_record_holds() -> None:
    """**§9's identity rule, as the one property that makes it satisfiable.**

    *"A pointer names a node of a document; it cannot name a value that composition minted.
    A verifier whose working objects are composed texts therefore has no pointer to key on
    and reaches for content by necessity."*  So every statement
    :class:`codegen.verify.witness.Subject` conjoins is a POINTER, and this is the
    assertion that it is one the record actually holds -- a pointer the record does not
    hold would be a minted one wearing a pointer's spelling.
    """
    construction = constructed.whole()
    pairs = claimed("paired classes", (f"{p.ref.document}{p.ref.pointer}" for p in compared.pairs()))
    assert pairs  # claimed() asserts it; named here so the denominator is visible
    nowhere: dict[str, list[str]] = {}
    conjoined = 0
    for pair in compared.pairs():
        pointer = _record_pointer(pair.ref)
        if pointer is None or pair.ref.document not in constructed.records():
            continue
        read = construction.subject(pair.ref.document, pointer)
        conjoined += len(read.besides)
        missing = [
            statement
            for statement in read.besides
            if construction.through(pair.ref.document, statement)[1] is witness._MISSING
        ]
        if missing:
            nowhere[f"{pair.ref.document}{pair.ref.pointer}"] = missing
    assert not nowhere, nowhere
    claimed("conjoined statements", range(conjoined))


def test_the_upward_reading_answers_the_union_hops_the_pointer_itself_spells() -> None:
    """One pick per union hop of the pointer, at the index the pointer spells.

    The enclosing node's union is IN the conjunction, and
    :meth:`codegen.verify.witness.Construction._reach` descends a union's first branch by
    default -- so a subject at ``#/oneOf/1`` would be conjoined with branch 0, which is a
    statement the document does not make about it.
    :attr:`codegen.verify.witness.Subject.picks` is the pointer's own answer, and this
    asserts it IS the pointer's: the picks are the union segments of the pointer, in order,
    with the index that follows each one.
    """
    construction = constructed.whole()
    wrong: dict[str, object] = {}
    answered = 0
    for pair in compared.pairs():
        pointer = _record_pointer(pair.ref)
        if pointer is None or pair.ref.document not in constructed.records():
            continue
        read = construction.subject(pair.ref.document, pointer)
        answered += len(read.picks)
        parts = [part for part in pointer.lstrip("/").split("/") if part]
        spelled = [
            index for index, part in enumerate(parts) if part in witness.UNIONS
        ]
        if len(spelled) != len(read.picks):
            wrong[f"{pair.ref.document}{pair.ref.pointer}"] = (len(spelled), read.picks)
            continue
        for at, (union, taken) in zip(spelled, read.picks, strict=True):
            if not union.endswith(f"/{parts[at]}") or str(taken) != parts[at + 1]:
                wrong[f"{pair.ref.document}{pair.ref.pointer}"] = (parts, read.picks)
    assert not wrong, wrong
    claimed("union hops answered by the pointer", range(answered))


def test_the_subject_is_read_from_pointers_and_no_node_is_serialised() -> None:
    """**Never the node's text** (§9), asserted over the upward reading's own source.

    ``tests/test_witness_construction.py`` already holds this for the construction's path;
    the upward reading is a second path to the same memo and the same rule applies to it.
    A serialisation ANYWHERE in :meth:`codegen.verify.witness.Construction.subject`,
    :meth:`~codegen.verify.witness.Construction.through` or
    :meth:`~codegen.verify.witness.Construction.applied` is a key on content, which costs
    the whole subtree to produce and is a different string for two nodes that are the same
    node reached twice.
    """
    serialising = {"dumps", "repr", "pickle", "sha256", "md5", "blake2b"}
    found: dict[str, list[str]] = {}
    for node in ast.walk(ast.parse(MODULE.read_text())):
        if not isinstance(node, ast.FunctionDef) or node.name not in (
            "subject",
            "through",
            "applied",
        ):
            continue
        calls = [
            inner.func.attr if isinstance(inner.func, ast.Attribute) else inner.func.id
            for inner in ast.walk(node)
            if isinstance(inner, ast.Call)
            and isinstance(inner.func, (ast.Attribute, ast.Name))
        ]
        reached = sorted(set(calls) & serialising)
        if reached:
            found[node.name] = reached
    assert not found, found
    graded = claimed("upward reading's functions", found.keys() | {"subject", "through", "applied"})
    assert graded == {"subject", "through", "applied"}, sorted(graded)


# --------------------------------------------------------------------------- #
# the partition, and what the reading is worth
# --------------------------------------------------------------------------- #
def test_every_paired_class_falls_in_exactly_one_part_of_the_upward_reading() -> None:
    """The denominator and the four outcomes, as a PARTITION rather than four counts.

    ``tests/nodeset.py``: *"two sets whose sizes sum correctly can still both miss a member
    and double-count another"*, so the parts are named and the unaccounted member is
    reported by name.  This asserts nothing about WHICH part a pair falls in -- the two
    tests below do that -- and it is what makes those two claims about a set rather than
    about whatever the derivation happened to reach.
    """
    partitions(
        _verdicts(),
        admitted=_by_state(1, "admitted"),
        refused=_by_state(1, "refused"),
        no_value=_by_state(1, "no value"),
        unreachable=_by_state(1, "unreachable"),
        unpaired=_by_state(1, "unpaired"),
    )


def test_the_upward_reading_moves_no_class_out_of_its_own_subject() -> None:
    """**The monotonicity, which is the whole safety argument for the upward reading.**

    A conjunction with MORE statements in it admits FEWER values, so a witness built under
    the conjunction that reaches a pointer is still one the pointer's own node admits -- and
    therefore still one the subject admits.  The cost of conjoining more is an approximation
    where no value satisfies the surplus; it is never a witness the subject refuses.

    That is an argument, and this is the measurement: **no pair whose downward witness its
    subject admits is anything other than admitted under the upward reading.**  The set the
    assertion names is the set that falsifies it, so a reader of a failure sees which class
    the reading broke and what it broke it on.
    """
    moved = {
        name: row[1]
        for name, row in _verdicts().items()
        if row[0].state == "admitted" and row[1].state != "admitted"
    }
    assert not moved, moved
    claimed("classes the upward reading moves INTO their own subject", {
        name
        for name, row in _verdicts().items()
        if row[0].state != "admitted" and row[1].state == "admitted"
    })


# --------------------------------------------------------------------------- #
# the obligation, and it is red
# --------------------------------------------------------------------------- #
def test_no_class_s_witness_is_refused_by_its_own_subject() -> None:
    """**Reading 1's first check, at the CLASS's own subject, and it is RED by a named set.**

    ``docs/plan/architecture.md`` §9's first assertion is that the constructed value the
    document admits is a value the class accepts.  Before the class can be asked, the value
    has to be one the class's own SUBJECT admits -- the node under the conjunction that
    reaches it -- because a witness the subject refuses says nothing about the class at all:
    ``strict_validate`` would refuse it on the document's behalf and the class would take no
    part in the outcome.

    **RED, with every member named and no allowlist** (``docs/plan/final-state.md``: *"A
    READING HOLDS OR IT DOES NOT.  Never M of N."*).  The set is the ``not``/``const``
    family ``adcp-client-python-hzio.11`` owns, read at the class rather than at the
    document root -- a value built from the positive keywords without consulting a sibling
    that forbids -- plus ``core/macro-declaration.json`` (``adcp-client-python-hzio.13``),
    and ``adcp-client-python-hzio.14`` is the row that closes it.  Each member carries the
    KEYWORDS its subject refused on, which is the document's own answer and not a sentence.
    """
    refused = {name: _verdicts()[name][1].detail for name in _by_state(1, "refused")}
    assert not refused, refused


def test_every_class_is_stamped_at_a_pointer_its_record_holds() -> None:
    """**A class whose pointer the record does not hold cannot be constructed AT, and it is
    RED by a named set.**

    ``applied_schema`` reaches these pointers by substituting a conjoined statement's own
    value for a key the node's own text does not spell -- its ``adcp-client-python-xid``
    clause -- so ``schema_at`` resolves and ``strict_validate`` has a subject.  The
    construction has no such substitution and must not acquire one: §9's rule is *"do not
    decide a position the bundle does not hold from a view of it"*, and a pointer the record
    does not hold is exactly such a position.  So the finding is the POINTER and not the
    witness: a class is stamped where its document states nothing.

    ``adcp-client-python-hzio.15`` is the row.  Named rather than counted, for the reason
    the test above gives.
    """
    nowhere = {name: _verdicts()[name][1].detail for name in _by_state(1, "unreachable")}
    assert not nowhere, nowhere


def test_the_two_readings_of_a_class_s_subject_are_the_same_pointer() -> None:
    """``applied_schema`` and :meth:`~codegen.verify.witness.Construction.subject` agree
    about WHICH NODE a class names, which is the half of the agreement that must be exact.

    The two readings differ in what they CONJOIN -- :class:`codegen.verify.witness.Subject`
    names the three places and the direction -- and that difference is bounded by the
    monotonicity above.  What cannot differ is the node at the foot of the walk: a class
    graded against one node and constructed at another is two subjects wearing one pointer.
    So this asserts the node ``applied_schema`` ends at IS the node the record holds at the
    pointer -- each read through a SOLE reference, which is the one hop both walks take and
    which neither counts as a statement (``through_the_store``: *"it carries nothing and
    answers nothing"*).  The two keywords the conjunction travels on, ``allOf`` and ``type``,
    are left out, because they are exactly where the two readings are allowed to differ and
    :func:`test_the_upward_reading_moves_no_class_out_of_its_own_subject` is what bounds
    that difference.
    """
    construction = constructed.whole()
    differs: dict[str, str] = {}
    graded = 0
    for pair in compared.pairs():
        pointer = _record_pointer(pair.ref)
        document = pair.ref.document
        if pointer is None or document not in constructed.records():
            continue
        record = constructed.records()[document]
        try:
            applied = applied_schema(record, pair.ref.pointer)
        except Exception:  # noqa: BLE001 -- the unreachable set above owns this
            continue
        where, node = construction.through(document, pointer)
        if node is witness._MISSING:
            continue
        own = _carried(applied, record)
        theirs = _carried(node, record)
        graded += 1
        if own != theirs:
            differs[f"{document}{pair.ref.pointer}"] = (
                f"applied_schema ends at keys {sorted(own)} and the record holds "
                f"{sorted(theirs)} at {where!r}"
            )
    assert not differs, differs
    claimed("classes whose two subjects are compared", range(graded))
