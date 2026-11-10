"""The witness is CONSTRUCTED: ``codegen/verify/witness.py``'s four obligations, graded.

``adcp-client-python-hzio.1``'s DONE WHEN is the contents page of this file, one clause one
test:

* **every node of every portable document has a constructed value or a named reason it has
  none** -- :func:`test_every_node_has_a_value_or_a_named_reason_and_the_two_partition_it`;
* **the walk visits each node once** --
  :func:`test_each_key_is_built_once_and_the_memo_is_what_makes_the_walk_linear`;
* **no cap of any kind is introduced** --
  :func:`test_the_module_introduces_no_cap_of_any_kind`;
* **the construction reads the record as a mapping without re-deriving it** --
  :func:`test_nothing_on_the_construction_s_path_serialises_a_node_to_identify_it`.

Beside them are the three readings those clauses are only meaningful under: that the
identity is the pointer and never the text (``docs/plan/architecture.md`` §9), that a cycle
closes on a pointer already in progress rather than on a depth limit, and that coverage is
by constraint class rather than by sample (``docs/plan/rebuild-plan.md`` §8).

**THE CYCLE TESTS RUN OVER A SYNTHETIC RECORD AND THAT IS NOT A WEAKER GRADE -- it is the
only one available.**  Measured over all 1,059 portable documents, this bundle's records
contain ZERO back edges: ``codegen.bundle.record`` refuses a document whose references
cycle across documents, so a cycle can only be intra-document and 3.2 states none.  A check
of the cycle reading over the bundle alone would be green over an empty set, which is the
shape ``tests/nodeset.py`` exists to refuse.  So the back-edge rule is graded on records
written here, and :func:`test_this_bundle_states_no_cycle_so_the_cycle_rule_is_graded_on_a_record_written_here`
is what keeps the two halves of that sentence honest.
"""

from __future__ import annotations

import ast
import pathlib

import constructed
import jsonschema
import pytest
from fresh import BUNDLE
from nodeset import claimed, partitions, ratchet

from codegen import bundle, harness
from codegen.verify import witness

MODULE = pathlib.Path(witness.__file__)

#: A record whose ``$ref`` cycle is reached through an OPTIONAL property, so the
#: construction closes it by omitting the reference.
OPTIONAL_CYCLE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "Node": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "child": {"$ref": "#/definitions/Node"},
            },
        }
    },
    "type": "object",
    "required": ["root"],
    "properties": {"root": {"$ref": "#/definitions/Node"}},
}

#: The same cycle reached through a REQUIRED property, which is the case §9 answers with
#: "the minimal instance of the target" -- and where the minimal instance does not exist,
#: because a cycle of required keys admits no finite instance at all.
REQUIRED_CYCLE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "Node": {
            "type": "object",
            "required": ["name", "child"],
            "properties": {
                "name": {"type": "string"},
                "child": {"$ref": "#/definitions/Node"},
            },
        }
    },
    "$ref": "#/definitions/Node",
}

#: One node reached under two different conjunctions, which is what the STACK in the memo
#: key exists to distinguish: ``/definitions/Shared`` states a string, and the two
#: conjuncts that reach it state different length bounds about the same instance.
TWO_CONJUNCTIONS = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {"Shared": {"type": "string"}},
    "type": "object",
    "required": ["short", "long"],
    "properties": {
        "short": {"allOf": [{"$ref": "#/definitions/Shared"}, {"maxLength": 2}]},
        "long": {"allOf": [{"$ref": "#/definitions/Shared"}, {"minLength": 7}]},
    },
}


def _module() -> ast.Module:
    return ast.parse(MODULE.read_text())


# --------------------------------------------------------------------------- #
# totality: a value, or a named reason there is none
# --------------------------------------------------------------------------- #
def test_the_construction_ranges_over_every_portable_document() -> None:
    """The denominator, named, and the documents missing from it named individually.

    A record this walk cannot read is a refusal of ``codegen.bundle.record`` and would be
    a finding about the BUNDLE; what this refuses is the silent version, where the set
    shrinks and every claim over it stays green.
    """
    portable = claimed("portable", bundle.portable(BUNDLE))
    graded = claimed("graded records", constructed.records(), inside=portable)
    assert graded == portable, sorted(portable - graded)


def test_every_node_has_a_value_or_a_named_reason_and_the_two_partition_it() -> None:
    """``hzio.1``'s first DONE WHEN clause, as a PARTITION rather than two counts.

    *"Every node of every portable document has a constructed value or a named reason it
    has none."*  Total means total: the walk answers for every schema position
    ``codegen.bundle.nodes`` reaches, the answers divide into exactly the two kinds, and a
    reason is a SENTENCE rather than an empty string -- an approximation with no reason is
    the allowlist ``docs/plan/final-state.md`` reading 2 refuses.
    """
    built = constructed.whole()
    held, named = set(), set()
    for document, positions in constructed.pointers().items():
        for pointer in positions:
            answer = built.value(document, pointer)
            if answer.held:
                held.add((document, pointer))
            else:
                assert answer.reason, (document, pointer, answer)
                named.add((document, pointer))
    whole = {
        (document, pointer)
        for document, positions in constructed.pointers().items()
        for pointer in positions
    }
    partitions(whole, with_a_value=held, with_a_named_reason=named)


def test_a_value_the_construction_keeps_is_one_the_node_s_own_statements_admit() -> None:
    """The value is offered to the DOCUMENT, and a refused one is never kept.

    ``docs/plan/final-state.md`` reading 1's first check is *"construct a value from the
    document's own keywords; the class must admit it"* -- and a construction that handed a
    subject a value its own document refuses would be grading the subject against something
    nothing stands behind.  So the screen runs before the value is kept
    (:meth:`codegen.verify.witness.Construction.refusals`) and this is that invariant read
    back over the whole bundle.
    """
    built = constructed.whole()
    kept = claimed(
        "nodes with a value",
        [
            (document, pointer)
            for document, positions in constructed.pointers().items()
            for pointer in positions
            if built.value(document, pointer).held
        ],
    )
    refused = [
        (document, pointer, built.refusals(document, pointer, built.value(document, pointer).value))
        for document, pointer in sorted(kept)
        if built.refusals(document, pointer, built.value(document, pointer).value)
    ]
    assert not refused, refused[:5]


def _roots() -> list[str]:
    """Every portable document whose record the construction ranges over, in one order.

    At PARAMETRIZE time, which is what makes the obligation below one assertion per
    document rather than one assertion over a total.  The set is
    ``tests/constructed.py``'s own and not a second reading of the bundle; a document the
    record refuses is absent from it and
    :func:`test_the_construction_ranges_over_every_portable_document` is what names that
    difference.
    """
    return sorted(constructed.records())


@pytest.mark.parametrize("document", _roots())
def test_the_document_admits_the_value_built_for_its_own_root(document: str) -> None:
    """**THE END-TO-END READING, STATED AS THE OBLIGATION AND NEVER AS A FRACTION.**

    :meth:`codegen.verify.witness.Construction.document_admits` walks one instance against
    the whole record, which is the only reading that answers for a ``not``, an ``if`` and a
    union at once -- the three the per-node screen strikes for §9's linearity reason.  Every
    document root has a value, and the document that states it admits it.

    **WHAT STOOD HERE WAS A RATCHET AND THE RATCHET IS DELETED.**  It asserted that at
    least 835 of the roots were admitted and that the figure could only rise.
    ``docs/plan/final-state.md`` forbids exactly that shape: *"A READING HOLDS OR IT DOES
    NOT.  Never M of N.  A fraction is a statement about the instrument, not about the
    artifact."*  A floor is an allowlist whose members are anonymous -- it names no
    document, so no document is ever owed a repair, and the 224 roots the figure excused
    were invisible to every reader of a green suite.

    **ONE ITEM PER DOCUMENT, AND NO COUNT ANYWHERE IN THIS GATE'S TEXT.**  A count is what
    goes stale and then gets believed; a parametrised item cannot, because the thing it
    names is the document.  A root the document refuses reports the KEYWORDS it was refused
    on and a root with no value reports the REASON it has none, so each red is already the
    beginning of its own repair.

    **AND THIS GATE IS RED TODAY, WHICH IS ITS PURPOSE RATHER THAN ITS DEFECT.**  Measured
    over the 1,059 roots: 1,050 admit, ONE builds a value its own document refuses
    (``core/macro-declaration.json``, ``adcp-client-python-hzio.13``), and EIGHT have NO
    VALUE -- every one of them a required ISO 8601 duration whose ``pattern`` states a
    LOOKAHEAD, which the reader declines by name rather than guesses at
    (:func:`test_a_lookaround_is_declined_by_name_and_never_read`).
    ``adcp-client-python-hzio.11`` closed the 32 roots that built a refused value and
    ``adcp-client-python-hzio.10`` and its group-reading successor closed 185 of the 193
    that had none.  ``adcp-client-python-hzio.9`` owns this gate and its instruction is to
    leave it red until both remainders are repaired.  No ``xfail``, no skip and no
    narrowing: a residue that is visible per document under its own name is the only honest
    form it can take.
    """
    built = constructed.whole()
    answer = built.value(document, "")
    assert answer.held, f"{document}: the construction reached no value for the root: {answer.reason}"
    refused = built.document_admits(document, answer.value)
    assert not refused, (
        f"{document}: the document refuses the value built for its own root on "
        f"{', '.join(refused)}"
    )


def test_no_root_builds_a_value_its_own_document_refuses() -> None:
    """``adcp-client-python-hzio.11``, **and the assertion is ZERO rather than a ceiling.**

    The gate above states the whole obligation per document and is red on every root the
    pattern reader still owes.  That makes its two halves indistinguishable to a reader of the
    suite: a root that STOPS building a refused value and starts having no value at all
    leaves the same test id red, so the repair and the regression look alike.  This names
    the half that is finished.

    **A ROOT THAT CANNOT BE BUILT BELONGS TO THE OTHER HALF AND IS NOT COUNTED HERE.**
    ``hzio.11``'s own instruction: *"a root that cannot be built goes to the no-value path
    with its reason -- it does not stay a refused value, and converting a refusal into a
    silent absence without a named reason is the failure mode to avoid."*  What forbids the
    silent absence is
    :func:`test_every_node_has_a_value_or_a_named_reason_and_the_two_partition_it` and
    :func:`test_every_reason_a_node_has_no_value_is_one_of_the_two_the_readings_name`, which
    together say that every absence carries a reason and that every reason is one of the
    named groups -- so the three roots ``hzio.11`` moved here
    (``core/forecast-dimension-geo.json``, ``core/placement.json`` and
    ``core/signal-coverage-forecast.json``) each report an unsolved ``pattern`` and none of
    them can hide.

    No count appears in the assertion, for the reason the gate above states: a count is what
    goes stale and then gets believed.  The set is empty or it names its members.
    """
    built = constructed.whole()
    refused = {
        document: built.document_admits(document, answer.value)
        for document in sorted(constructed.records())
        for answer in [built.value(document, "")]
        if answer.held and built.document_admits(document, answer.value)
    }
    assert not refused, refused


def test_every_reason_a_node_has_no_value_is_one_of_the_two_the_readings_name() -> None:
    """``hzio.1``'s named exits, and nothing else is one.

    ``docs/plan/architecture.md`` §2: *"an arbitrary ``pattern`` and a ``format`` no checker
    can generate are the two cases: the keyword states a set the construction cannot
    enumerate."*  A reason naming anything else is either a defect in this module or a case
    the readings do not cover, and both are findings -- so the reasons are grouped and the
    groups are named here rather than counted.
    """
    built = constructed.whole()
    reasons = claimed("distinct reasons", built.counters.reasons)
    unnamed = [
        reason
        for reason in reasons
        if "is not solved" not in reason
        and "unsolved pattern" not in reason
        and "states no case" not in reason
        and "additionalProperties forbids" not in reason
        and "refuses its construction on pattern" not in reason
    ]
    assert not unnamed, unnamed


# --------------------------------------------------------------------------- #
# one walk per node, and the memo that makes it one
# --------------------------------------------------------------------------- #
def test_each_key_is_built_once_and_the_memo_is_what_makes_the_walk_linear() -> None:
    """``hzio.1``'s second DONE WHEN clause, proved by a counter and not claimed in prose.

    Three identities, and each one fails differently:

    * ``computed == len(memo)`` -- every key was built exactly once, because a key built
      twice would be counted twice and held once;
    * ``asked > computed`` -- the memo is LIVE.  ``docs/plan/architecture.md`` §9: *"a memo
      that is dead, keyed on something the answer does not depend on, or shadowed by a
      second uncached entry point is a defect in the model and not a missed saving"*;
    * ``computed`` within a small factor of the distinct pointers reached -- the stack in the
      key costs a constant and not a regime, which is the whole claim that carrying the
      resolution path is affordable.
    """
    built = constructed.whole()
    counters = built.counters
    nodes = claimed("schema positions", [(d, p) for d, ps in constructed.pointers().items() for p in ps])
    assert counters.computed == len(built._memo), (counters.computed, len(built._memo))
    assert counters.asked > counters.computed, (counters.asked, counters.computed)
    ratchet(
        "keys built per distinct pointer dereferenced",
        round(100 * counters.computed / counters.reached),
        at_most=200,
        because=(
            "the stack in the key splits one pointer into one answer per conjunction it is "
            "reached under; a reading that split it per REFERRER instead would push this "
            "into the hundreds and is the defect the ceiling catches"
        ),
    )
    assert counters.reached >= len(nodes) - 1, (counters.reached, len(nodes))


def test_the_only_entry_point_to_the_walk_is_the_memoised_one() -> None:
    """§9's *"shadowed by a second uncached entry point"*, read off the module's own AST.

    :meth:`codegen.verify.witness.Construction._construct` is the body and
    :meth:`codegen.verify.witness.Construction.value` is the memo, so a second caller of the
    body is a path the memo does not see.  One caller, asserted, because a figure about the
    cost is worth nothing if half the calls bypass the instrument.
    """
    calls = claimed(
        "calls to the construction body",
        [
            node.lineno
            for node in ast.walk(_module())
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "_construct"
        ],
    )
    assert len(calls) == 1, calls


# --------------------------------------------------------------------------- #
# no cap of any kind
# --------------------------------------------------------------------------- #
#: The names a cap arrives under.  ``docs/plan/architecture.md`` §9: *"a time budget, a
#: depth limit, a cap on examples: each is a parameter added so that an explosion stops
#: being visible"* -- so the rule is read on the PARAMETER NAMES of this module, which is
#: where such a thing has to appear to be settable.
CAP_NAMES = (
    "depth",
    "budget",
    "limit",
    "max_examples",
    "deadline",
    "timeout",
    "cap",
    "ceiling",
    "attempts",
    "tries",
    "rounds",
)


def test_the_module_introduces_no_cap_of_any_kind() -> None:
    """``hzio.1``'s third DONE WHEN clause, and ``hzio.6``'s rule arriving early.

    *"No budget, no depth limit, no example count, no wall-clock bound.  Not even with a
    generous default.  A knob whose setting can turn a check off is the thing this epic
    deletes."*  Read on every function and method signature in the module: a cap has to be
    a parameter to be a knob, and a parameter is what this looks for.
    """
    signatures = claimed(
        "parameters of this module",
        [
            (node.name, argument.arg)
            for node in ast.walk(_module())
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for argument in [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
                *([node.args.vararg] if node.args.vararg else []),
                *([node.args.kwarg] if node.args.kwarg else []),
            ]
        ],
    )
    found = [
        pair for pair in sorted(signatures) if any(name in pair[1] for name in CAP_NAMES)
    ]
    assert not found, found


def test_every_repetition_this_module_performs_counts_something_the_input_states() -> None:
    """**The hole the parameter-only reading leaves, and the one that was live in it.**

    :func:`test_the_module_introduces_no_cap_of_any_kind` reads SIGNATURES, on the argument
    that "a cap has to be a parameter to be a knob".  That is true of a knob and false of a
    cap: ``_STORE_HOPS = 8`` stood on this module's storage walk as a module CONSTANT read
    by two methods, settable by nobody and cutting a reading all the same -- the shape
    ``harness._OWN_DEPTH`` had, which is why
    ``tests_emit/test_no_cap_is_on_the_grading_path.py`` grew a constants clause for it
    there.  This is that clause for this module.

    **AND THE POPULATION IS THE REPETITIONS AND NOT THE CONSTANTS**, which is the whole
    reason this gate says anything: read as "no module constant counts a walk" it ranges
    over the constants, so deleting the last one makes it green over an EMPTY set and it
    decides nothing from then on -- ``docs/plan/final-state.md``'s *"a check that passes
    when nothing happens decides nothing"*.  Read this way the set is every ``range``-driven
    loop the module performs, which stays live as long as the module repeats anything at
    all, and the assertion is that each one counts something the INPUT states.

    What the module repeats over today is ``_demanded``'s ``atom.least``, ``_asserted``'s
    ``min(least, len(pending))``, and ``_array``/``_branch_classes``' ``len(members)``: a
    quantifier minimum the pattern states, that minimum against the assertions in hand, and
    the length of a collection built from the node.  Every one is a number off the document
    or off something derived from it, and none is a number this module chose, which is the
    property asserted rather than the list.  A chain the module
    FOLLOWS is not in here at all, which is the change this gate records:
    ``Construction.through`` and ``Construction._settles`` walk distinct pointers of one
    finite record and stop on the pointer already visited, so there is no count to repeat.
    """
    #: **THE MODULE BODY AND NOT ``ast.walk``**, a distinction this clause was written wrong
    #: first and then measured: walking the whole tree collects every LOCAL assignment too,
    #: so ``least`` and ``at`` read as module constants and the gate indicts the document's
    #: own quantifier minimum.  A clause that cannot tell the module's constant from the
    #: document's number forbids the reading instead of the cap.
    constants = {
        target.id
        for node in _module().body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int)
        if not isinstance(node.value.value, bool)
    }
    found = [
        (holder.name, node.iter)
        for holder in ast.walk(_module())
        if isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(holder)
        if isinstance(node, ast.For)
        if isinstance(node.iter, ast.Call)
        if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range"
    ]
    claimed(
        "range-driven repetitions of this module",
        {(where, ast.unparse(counts)) for where, counts in found},
    )
    counted = sorted(
        (where, ast.unparse(counts))
        for where, counts in found
        if any(
            isinstance(inner, ast.Name) and inner.id in constants
            for inner in ast.walk(counts)
        )
    )
    assert not counted, (
        f"{counted} repeats a walk one of this module's own constants counts "
        f"({sorted(constants)}); a repetition on the grading path counts something the "
        "document states or it is a cap"
    )


def test_no_clock_and_no_randomness_is_reachable_from_the_construction() -> None:
    """A wall-clock bound and a draw are the two caps that do not look like parameters.

    A construction reading a clock has a wall-clock bound whatever the signature says, and
    one reading a random source is a SAMPLER wearing the word "construct" -- which is the
    instrument this epic replaces, not an implementation of it.
    """
    imports = claimed(
        "modules this one imports",
        [
            name.name.split(".")[0]
            for node in ast.walk(_module())
            if isinstance(node, ast.Import)
            for name in node.names
        ]
        + [
            (node.module or "").split(".")[0]
            for node in ast.walk(_module())
            if isinstance(node, ast.ImportFrom)
        ],
    )
    assert not (imports & {"time", "random", "secrets", "hypothesis", "datetime"}), imports


# --------------------------------------------------------------------------- #
# a cycle closes on the pointer
# --------------------------------------------------------------------------- #
def test_this_bundle_states_no_cycle_so_the_cycle_rule_is_graded_on_a_record_written_here() -> None:
    """The measurement that makes the two tests below the only available grade.

    ``codegen.bundle.record`` refuses a document whose references cycle across documents, so
    a back edge in a record can only be intra-document -- and bundle 3.2 states none.  Said
    out loud and asserted, because "graded on a synthetic record" reads as a weaker check
    until the alternative is shown to be an empty set.
    """
    built = constructed.whole()
    assert built.counters.back_edges == 0, built.counters.back_edges
    assert built.counters.floored == 0, built.counters.floored


def test_a_cycle_through_an_optional_reference_closes_by_omitting_it() -> None:
    """§9's first half: *"the construction completes by omitting the reference where the
    document makes it optional"*.

    And the value is offered to the document, which is what says the omission was legal:
    ``child`` is not required, so an instance without it is one the document admits.
    """
    built = witness.Construction({"cycle.json": OPTIONAL_CYCLE})
    answer = built.value("cycle.json", "")
    assert answer.held, answer
    assert answer.value == {"root": {"name": ""}}, answer.value
    assert not built.document_admits("cycle.json", answer.value)
    assert built.counters.back_edges == 0, "an omitted optional reference is never entered"


def test_a_cycle_through_a_required_reference_reports_that_no_finite_instance_exists() -> None:
    """§9's second half, and the case where the minimal instance does not exist.

    *"By taking the minimal instance of the target where the document requires it"* -- a
    document whose required keys cycle has no finite instance, so there is no minimal one
    to take.  The honest answer is the named reason, and the back edge is COUNTED: the
    detection is what terminated the walk, and a reading that terminated on a depth limit
    would leave this counter at zero.
    """
    built = witness.Construction({"cycle.json": REQUIRED_CYCLE})
    answer = built.value("cycle.json", "")
    assert not answer.held, answer
    assert "cycle of required keys" in answer.reason, answer.reason
    assert built.counters.back_edges >= 1, built.counters.back_edges
    assert built.counters.floored >= 1, built.counters.floored


def test_the_cycle_terminates_with_no_depth_parameter_anywhere_in_the_call() -> None:
    """The negative half of the clause: it is the POINTER that closed it.

    Both cyclic records above terminate, and the module has no parameter a caller could
    have set to make them terminate (:func:`test_the_module_introduces_no_cap_of_any_kind`).
    What this adds is that the termination is visible in the memo: the keys built for the
    cyclic record are finite and each names a pointer of that record.
    """
    built = witness.Construction({"cycle.json": OPTIONAL_CYCLE})
    built.value("cycle.json", "")
    keys = claimed("keys built for a cyclic record", built._memo)
    for document, pointer, stack in keys:
        assert document == "cycle.json"
        assert pointer == "" or bundle.node_at(OPTIONAL_CYCLE, pointer) is not None
        assert all(isinstance(entry, str) for entry in stack), stack


# --------------------------------------------------------------------------- #
# the identity is the pointer, never the text
# --------------------------------------------------------------------------- #
def test_the_key_is_the_document_the_pointer_and_the_stack_and_nothing_else() -> None:
    """§9's identity rule, read off every key the whole-bundle walk built.

    *"A node's identity is its pointer, never its text.  Serialising a structure to key it,
    hash it or compare it re-derives what the walk already carries."*  A key here is three
    strings and a tuple of strings; the test that no key is a serialisation is this one
    plus the pointer resolving in its own document.
    """
    built = constructed.whole()
    keys = claimed("memo keys", built._memo)
    for document, pointer, stack in keys:
        assert document in constructed.records(), document
        assert pointer == "" or pointer.startswith("/"), pointer
        assert all(entry == "" or entry.startswith("/") for entry in stack), stack


def test_one_node_reached_under_two_conjunctions_gets_two_keys_and_two_values() -> None:
    """What the STACK in the key is FOR, shown by the case that needs it.

    ``/definitions/Shared`` is one node.  Reached under a conjunct stating ``maxLength: 2``
    it admits a different set from the same node reached under ``minLength: 7``, so one
    answer for both would be wrong in one of the two places -- which is the defect
    ``Fixtures._pin``'s key has, measured: it omits the ``depth`` its answer depends on and
    serves a truncated answer first-writer-wins to a caller that had budget.
    """
    built = witness.Construction({"two.json": TWO_CONJUNCTIONS})
    for pointer, _ in bundle.nodes(TWO_CONJUNCTIONS):
        built.value("two.json", pointer)
    answer = built.value("two.json", "")
    assert answer.held, answer
    assert len(answer.value["long"]) >= 7, answer.value
    assert len(answer.value["short"]) <= 2, answer.value
    reached = claimed(
        "keys naming the shared node",
        [key for key in built._memo if key[1] == "/definitions/Shared"],
    )
    assert len(reached) > 1, reached
    stacks = claimed("stacks the shared node was reached under", [key[2] for key in reached])
    assert () in stacks, stacks


def test_nothing_on_the_construction_s_path_serialises_a_node_to_identify_it() -> None:
    """``hzio.1``'s fourth DONE WHEN clause, and §9's *"decided by"*.

    *"No serialisation being reachable from the grading path, with the library's own named
    as the exception and nothing of ours beside them."*  Read on the module's AST: a
    ``json.dumps``, a ``repr`` used as a key, a ``pickle`` or a ``hash`` of a node each
    re-derive what the pointer already carries, and §9 measures the cost -- *"a hash key
    reads as O(1) and is O(subtree) underneath, so a walk that keys each node on its own
    serialisation pays the sum of every subtree."*
    """
    names = claimed(
        "names this module calls",
        [
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            for node in ast.walk(_module())
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
        ],
    )
    assert not (names & {"dumps", "dump", "loads", "pickle", "sha256", "md5", "blake2b"}), names


def test_the_construction_reads_the_record_and_never_rebuilds_it() -> None:
    """The reader rule: *"readers of the record MUST NOT REBUILD IT."*

    A reader that rebuilds forfeits the identity its caller carried and every memo above it
    stops hitting.  Read as an OBJECT IDENTITY: the node the construction hands back for a
    pointer is the very object the record holds at that pointer, not a copy of it.
    """
    built = constructed.whole()
    sample = claimed(
        "pointers checked for identity",
        [
            (document, pointer)
            for document, positions in sorted(constructed.pointers().items())[:40]
            for pointer in positions[:20]
        ],
    )
    for document, pointer in sorted(sample):
        assert built.node(document, pointer) is bundle.node_at(
            constructed.records()[document], pointer
        ), (document, pointer)


# --------------------------------------------------------------------------- #
# the pattern is READ by five constructs, in either of two roles: CONSUME or ASSERT
# --------------------------------------------------------------------------- #
def _bundle_patterns() -> dict[str, int]:
    """Every distinct ``pattern`` the bundle's records state, with how many nodes state it.

    The positions are the weight a declined construct carries, which is the figure
    ``codegen/verify/witness.py``'s own docstring quotes -- so it is derived here from the
    same records the construction walks rather than copied from a row's description of
    them.
    """
    out: dict[str, int] = {}
    for record in constructed.records().values():
        for _pointer, node in bundle.nodes(record):
            if isinstance(node, dict) and isinstance(node.get("pattern"), str):
                out[node["pattern"]] = out.get(node["pattern"], 0) + 1
    return out


def test_every_pattern_the_reader_reads_yields_a_string_that_pattern_admits() -> None:
    """The reading is offered to the PATTERN ITSELF, through the project's own screen.

    ``adcp-client-python-hzio.10``'s rule and the one this check exists for: *"the value is
    checked against the pattern before it is used, by the document's own checker rather
    than by the reader's belief about what it produced"*.  A reader returning a string its
    own pattern refuses is a defect, and the only instrument that can say so is a checker
    the reader does not share -- ``codegen.harness.conforms``, which is also what attaches
    the draft's ``format`` checker, never a bare validator.

    **Over the bundle's own distinct patterns and not over examples written here**, because
    the set this claims to range over is the set the compiler meets.  The patterns the
    reader DECLINES are the other half and are named by
    :func:`test_a_pattern_the_reader_declines_names_the_construct_it_stopped_at`.
    """
    read = claimed(
        "distinct patterns the reader reads",
        [text for text in _bundle_patterns() if witness._patterned(text, 0, None).held],
        inside=_bundle_patterns(),
    )
    refused = [
        (text, witness._patterned(text, 0, None).value)
        for text in sorted(read)
        if harness.conforms(
            {"type": "string", "pattern": text}, witness._patterned(text, 0, None).value
        )
        is not True
    ]
    assert not refused, refused


def test_a_group_is_taken_its_quantifiers_minimum_number_of_times() -> None:
    """The construct this reading ADDS, and the minimum is the whole of it.

    A group followed by ``?`` or ``*`` is taken ZERO times and contributes nothing; a group
    followed by ``+``, or by no quantifier, is taken ONCE; ``{n,m}`` is taken *n* times.
    That is the same reading ``*`` on a character class already gets, which is why the
    cases below are stated beside the class spellings that already produce the same string
    -- a reading that treated a group differently from a class under one quantifier would
    show up here as a disagreement between the two columns.

    **AND EACH EXPECTATION IS CHECKED BY THE PATTERN TOO**, not only compared with a string
    written here: a case whose expected value its own pattern refuses would be this test
    asserting the reader's defect rather than the reading, which is the failure mode
    ``hzio.10``'s rule names.
    """
    cases = {
        # a group taken zero times, against the class spelling of the same minimum
        "^a(bc)?$": "a",
        "^a(bc)*$": "a",
        "^a[bc]*$": "a",
        # a group taken once, its contents read by the same rules
        "^a(bc)+$": "abc",
        "^a(bc)$": "abc",
        "^a(?:bc){2}$": "abcbc",
        # nested, which is the recursion: the inner group's own quantifier decides
        "^a(b(cd)?)+$": "ab",
        "^a(b(cd)+)?$": "a",
        # the bundle's own two domain patterns, the `*` and the `+` spelling
        "^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$": "a",
        "^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$": "a.a",
        # an alternation inside a group: the FIRST arm, and every arm still parsed
        "^-?(?:0|[1-9][0-9]*)$": "0",
        "^(?:0|[1-9][0-9]*)\\.(?:0|[1-9][0-9]*)$": "0.0",
    }
    for text, expected in sorted(cases.items()):
        built = witness._patterned(text, 0, None)
        assert built.held, (text, built.reason)
        assert built.value == expected, (text, built.value, expected)
        assert harness.conforms({"type": "string", "pattern": text}, expected) is True, text


def test_a_positive_lookahead_is_SATISFIED_and_never_solved() -> None:
    """**CONSUME OR ASSERT IS THE DISTINCTION, and it is the whole of this reading.**

    A lookahead is an assertion AT a position, not a construct that consumes text, so the
    reader does not have to decide what the assertion demands and work backwards -- which
    is the thing ``codegen/verify/witness.py`` refuses to be, and the refusal stands.  What
    it does instead needs no construct it did not already read: the body is parsed by the
    same arms a group's is, read into the string the BODY ITSELF admits, and the characters
    after the position are required to begin with that string.  Where a class emits one of
    them the two classes are statements about ONE character and the reading takes what both
    admit; where the character would come from a group the minimum reading takes none of,
    the assertion raises that group's minimum inside the range its own ``?`` already admits.

    So ``^P(?=.*[1-9])(?=\\d|T)(?:\\d+Y)?...$`` gives ``"P1Y"`` -- and every case here is
    checked by its OWN pattern through ``codegen.harness.conforms``, never by a string
    written here, because a reader that returned a value its pattern refuses would otherwise
    be graded against this file's belief about what it produced
    (``adcp-client-python-hzio.10``'s rule).
    """
    cases = {
        # the bundle's own two duration patterns, which are why this reading exists
        "^P(?=.*[1-9])(?=\\d|T)(?:\\d+Y)?(?:\\d+M)?(?:\\d+D)?"
        "(?:T(?=\\d)(?:\\d+H)?(?:\\d+M)?(?:\\d+S)?)?$": "P1Y",
        "^P(?=\\d|T)(?=.*\\d)(?:\\d+Y)?(?:\\d+M)?(?:\\d+D)?"
        "(?:T(?=\\d)(?:\\d+H)?(?:\\d+M)?(?:\\d+S)?)?$": "P0Y",
        # the assertion and the class that emits the character are conjoined
        "^a(?=b)b$": "ab",
        "^(?=[a-z])[a-z0-9]+$": "a",
        "^(?=[c-z])[a-z]$": "c",
        # the assertion raises an optional group's minimum, which its own `?` admits
        "^A(?=X)(?:XY)?$": "AXY",
        # an assertion over a class a quantifier takes none of demands nothing
        "^a(?=b*)c$": "ac",
        # a lookahead inside a group the reading takes zero times asserts nothing
        "^a(?:b(?=c)c)?$": "a",
    }
    for text, expected in sorted(cases.items()):
        built = witness._patterned(text, 0, None)
        assert built.held, (text, built.reason)
        assert built.value == expected, (text, built.value, expected)
        assert harness.conforms({"type": "string", "pattern": text}, expected) is True, text


def test_a_complement_class_is_read_as_the_vocabulary_the_document_does_not_exclude() -> None:
    """**A COMPLEMENT NAMES WHAT IT EXCLUDES, so the reading needs a set to strike it FROM.**

    ``[^...]``, ``\\S``, ``\\D`` and ``.`` state no members of their own: they leave them to
    the dialect, and the dialect's answer is every codepoint of the plane.  That is not a set
    a *document's own first* can be taken from, so the reading is the first character
    :data:`codegen.verify.witness._VOCABULARY` names that the document does not exclude --
    and the vocabulary is not a constant invented for this: it is
    :data:`codegen.verify.witness._CLASS_ESCAPE`'s own members in its own order, which is the
    one statement this module already makes about which characters it names.

    **THE READING IS NARROWER THAN THE CLASS AND THAT IS THE SOUND DIRECTION.**  Every
    character the vocabulary holds is one the complement admits, so a value this produces is
    still a value the class admits -- asserted below by the pattern's own checker, which is
    the only instrument that can say so.  The one case it cannot answer is a complement that
    excludes the whole vocabulary, and that is DECLINED BY NAME rather than widened to a
    character this reader would have chosen.
    """
    cases = {
        # the two documents this reading exists for
        "^[^\\u0000-\\u001F\\u007F]+$": "0",
        "\\S": "0",
        # the shorthand complements, read off the positive table they complement
        "^\\D+$": "a",
        # a dot is a complement over the line terminators and nothing else
        "^[a-z_]+:.+$": "a:0",
        # a complement a quantifier takes ZERO of still reads, as it always did
        "^[^\\u0000-\\u001F\\u007F]*$": "",
        "^(/[^\\s]*)$": "/",
        # the bundle's own URL shapes, which were declined for this one reason
        "^https://[^/?#@]+$": "https://0",
        "^https://[^/?#@]+(?:/[^?#]*)?(?:\\?[^#]*)?$": "https://0",
        # a complement conjoined with an assertion is still one character, read once
        "^(?=[a-z])[^0-9]+$": "a",
    }
    for text, expected in sorted(cases.items()):
        built = witness._patterned(text, 0, None)
        assert built.held, (text, built.reason)
        assert built.value == expected, (text, built.value, expected)
        assert harness.conforms({"type": "string", "pattern": text}, expected) is True, text

    # `\S` and `.` read as the WHOLE vocabulary, and that is a DERIVATION rather than a
    # coincidence only while no character the reader writes is whitespace or a line
    # terminator.  A vocabulary that grows one is a failure here, not a silent drift.
    assert not set(witness._VOCABULARY) & set(witness._WHITESPACE), witness._VOCABULARY
    assert not set(witness._VOCABULARY) & set(witness._LINE_TERMINATOR), witness._VOCABULARY
    assert witness._ANY == witness._ranged(witness._VOCABULARY)
    for text, named in {
        "^\\W+$": "a complement that excludes every character it names",
        "^[^0-9A-Za-z_]+$": "a complement that excludes every character it names",
        "^\\s+$": "a class whose members it does not name",
    }.items():
        built = witness._patterned(text, 0, None)
        assert not built.held, (text, built.value)
        assert named in built.reason, (text, built.reason)


def test_the_lookarounds_this_reader_declines_are_declined_by_name() -> None:
    """The line this reading stops at, and the stop is a NAMED refusal rather than a parse.

    Three spellings state what a reading cannot take a first member of.  ``(?!`` and
    ``(?<!`` say what the text must NOT be, and *"the first STRING that is not this"* is a
    choice no vocabulary answers -- a complement over CHARACTERS is
    :func:`codegen.verify.witness._unless`, and the set of strings is not one a table names;
    ``(?<=`` says it of characters the reading has already emitted, so satisfying it would
    mean revising a reading that is finished.

    **AND THE HONEST STOPS OF THE READING THAT WAS ADDED ARE HERE TOO**, because a reading
    that answered an assertion it could not satisfy with a cap, a default or a literal is
    the failure mode ``adcp-client-python-4ipm`` names: an assertion with nothing in common
    with the class that emits the character, an assertion no construct after it reaches, and
    an assertion over a class whose members the reader does not name are each declined with
    the construct named.
    """
    for text, named in {
        "^a(?!b)c$": "the lookahead '(?!'",
        "^a(?<=b)c$": "the lookbehind '(?<='",
        "^a(?<!b)c$": "the lookbehind '(?<!'",
        "^a(?=b)c$": "an assertion and a class that admit nothing in common",
        "^a(?=b)$": "an assertion no construct after it reaches",
        "^(?=.{3})[a-z]+$": "an assertion no construct after it reaches",
        "^(?=\\s)[a-z]+$": "an assertion over a class whose members it does not name",
        "^a(?=b)*b$": "a quantified lookahead",
        "^a(?=b)(?=c)b$": "two assertions that admit nothing in common",
    }.items():
        built = witness._patterned(text, 0, None)
        assert not built.held, (text, built.value)
        assert named in built.reason, (text, built.reason)


def test_the_bundles_own_lookaround_patterns_split_on_consume_versus_assert() -> None:
    """The half a document actually pays for, derived from the bundle and not listed here.

    The split is the reading's own line and nothing else: a pattern whose only lookaround is
    POSITIVE is read, and a pattern stating one of the three declined spellings is declined
    with the spelling named.  Both sides are asserted so that neither a pattern silently
    falling off the read side nor one silently joining it passes unnoticed -- and a read
    pattern's value is offered to the pattern itself, which is the only instrument that can
    say the reading was right.
    """
    stated = claimed(
        "distinct patterns of the bundle that state a lookaround",
        [
            text
            for text in _bundle_patterns()
            if any(spelling in text for spelling in ("(?=", "(?!", "(?<=", "(?<!"))
        ],
        inside=_bundle_patterns(),
    )
    for text in sorted(stated):
        built = witness._patterned(text, 0, None)
        declined = any(spelling in text for spelling in ("(?!", "(?<=", "(?<!"))
        assert built.held is not declined, (text, built.value, built.reason)
        if declined:
            assert "lookahead '(?!'" in built.reason or "lookbehind" in built.reason, (
                text,
                built.reason,
            )
        else:
            assert (
                harness.conforms({"type": "string", "pattern": text}, built.value) is True
            ), (text, built.value)


def test_a_pattern_the_reader_declines_names_the_construct_it_stopped_at() -> None:
    """**THE DECLINED LIST IS A DELIVERABLE AND NOT A FAILURE**, so it is read here.

    ``hzio.10``'s rule for everything the five constructs do not cover: *"a pattern whose
    shape this reader does not cover is NOT attempted -- the document's own ``examples`` is
    the value, and failing that the fact is approximated with the pattern quoted"*.  What
    makes that honest rather than a silent gap is that the reason names the CONSTRUCT: a
    declined pattern reporting only that it was declined tells no reader which reading is
    missing, which is the shape a residue hides in.

    So every declined pattern quotes its own text and names a construct, and no reader of
    this suite has to go looking for the list.
    """
    declined = claimed(
        "distinct patterns the reader declines",
        [text for text in _bundle_patterns() if not witness._patterned(text, 0, None).held],
        inside=_bundle_patterns(),
    )
    nameless = []
    for text in sorted(declined):
        reason = witness._patterned(text, 0, None).reason
        stopped = reason.split("is not solved", 1)[-1].lstrip(": ").strip()
        if repr(text) not in reason or not stopped:
            nameless.append((text, reason))
    assert not nameless, nameless


def test_the_pattern_reader_imports_no_regular_expression_machinery() -> None:
    """It READS a pattern to produce a string; it never asks whether a string matches.

    ``docs/plan/architecture.md`` §2: *"This project builds no solver for a keyword it
    cannot read."*  The reading added for a group is where that line is easiest to cross --
    a group with an alternation invites trying an arm and checking the result -- so the
    rule is read on the module's IMPORTS, where a matcher would have to appear.  Every
    accept-or-refuse verdict about a produced string belongs to the document's own checker
    (:meth:`codegen.verify.witness.Construction.refusals`), and a module that cannot match
    cannot take that verdict back.
    """
    imports = claimed(
        "modules this one imports",
        [
            name.name.split(".")[0]
            for node in ast.walk(_module())
            if isinstance(node, ast.Import)
            for name in node.names
        ]
        + [
            node.module.split(".")[0]
            for node in ast.walk(_module())
            if isinstance(node, ast.ImportFrom) and node.module
        ],
    )
    assert not imports & {"re", "regex", "sre_compile", "sre_parse"}, sorted(imports)


# --------------------------------------------------------------------------- #
# coverage is by constraint class, not by sample
# --------------------------------------------------------------------------- #
def test_every_format_case_is_one_the_draft_s_own_checker_admits() -> None:
    """:data:`codegen.verify.witness.FORMAT_CASES` is a table of CONSTANTS, so it is checked.

    ``docs/plan/rebuild-plan.md`` §8 asks for *"every case the format's own checker admits
    rather than the case a generator finds most likely"*, and the checker is the DRAFT'S
    own rather than the global registry -- the global one carries every checker any draft
    defines, so it would assert ``uuid`` against a draft-07 document, which draft-07 does
    not define as a format.

    A format the installed checker cannot decide contributes nothing here and is named, so
    the table is not graded as though a missing validator were a pass.
    """
    checker = jsonschema.Draft7Validator.FORMAT_CHECKER
    decidable = claimed(
        "formats this table states that the draft's checker can decide",
        [name for name in witness.FORMAT_CASES if name in checker.checkers],
    )
    for name in sorted(decidable):
        for case in witness.FORMAT_CASES[name]:
            assert checker.conforms(case, name), (name, case)


def test_an_enum_contributes_every_member_as_a_class_and_a_bound_both_sides_of_itself() -> None:
    """``docs/plan/rebuild-plan.md`` §8's coverage rule, on the keywords that have classes.

    *"For each keyword the node states, the construction takes the classes that keyword
    distinguishes: every member of an ``enum``, both sides of each bound and the bound
    itself."*  That is what makes "never tighter" a claim about every value the document
    admits rather than about the values something happened to produce -- so an ``enum``
    whose third member is missing from the classes is a hole in the claim and not a missing
    sample.
    """
    built = constructed.whole()
    enums = claimed(
        "nodes stating an enum of their own",
        [
            (document, pointer)
            for document, record in sorted(constructed.records().items())
            for pointer, node in bundle.nodes(record)
            if isinstance(node.get("enum"), list) and node["enum"]
        ],
    )
    thin = []
    for document, pointer in sorted(enums):
        node = built.node(document, pointer)
        covered = {
            _hashable(case.value) for case in built.classes(document, pointer) if case.keyword == "enum"
        }
        wanted = {
            _hashable(member)
            for member in node["enum"]
            if not built.refusals(document, pointer, member)
        }
        if wanted - covered:
            thin.append((document, pointer, sorted(wanted - covered, key=repr)))
    assert not thin, thin[:5]


def test_a_bound_contributes_the_bound_itself_and_a_value_inside_it() -> None:
    """The bound half of the same rule, on a node written here so both ends are stated.

    An inclusive bound admits an instance AT it and an exclusive one does not
    (:data:`codegen.keywords.EXCLUSIVE`), so the classes of an exclusive bound are the step
    in and nothing at it -- and the value OUTSIDE a bound is not a class at all, it is that
    bound's mutation.
    """
    record = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "integer",
        "minimum": 3,
        "maximum": 9,
    }
    built = witness.Construction({"bound.json": record})
    classes = claimed("classes of a two-sided bound", built.classes("bound.json", ""))
    values = {case.value for case in classes}
    assert {3, 9} <= values, values
    assert not (values & {2, 10}), values


def test_every_class_the_construction_offers_is_one_the_node_admits() -> None:
    """A class is a value the DOCUMENT ADMITS, or it is not a class.

    An un-admitted "class" handed to a subject grades the subject against a value nothing
    stands behind, which is the same defect as a witness the document refuses.  So the
    classes are screened before they are offered and this reads that back over the bundle.
    """
    built = constructed.whole()
    stated = claimed(
        "nodes stating a keyword with classes",
        [
            (document, pointer)
            for document, record in sorted(constructed.records().items())
            for pointer, node in bundle.nodes(record)
            if {"enum", "const", "format"} & set(node)
        ],
    )
    bad = []
    for document, pointer in sorted(stated):
        bad.extend(
            (document, pointer, case.keyword, case.label)
            for case in built.classes(document, pointer)
            if built.refusals(document, pointer, case.value)
        )
    assert not bad, bad[:5]


def _hashable(value: object) -> object:
    """A value usable in a set, for the comparison and for nothing else.

    An ``enum`` member can be a list or an object, which no set holds -- and its ``repr``
    is used HERE, in a test's own comparison of two sets of members, and never as a node's
    identity.  That distinction is §9's: the rule is about the construction's keys, and a
    test comparing two member lists is not keying a node.
    """
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


@pytest.fixture(autouse=True, scope="module")
def _warm() -> None:
    """One walk for the whole module, so no test's figures depend on the order."""
    constructed.whole()
