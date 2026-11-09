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

from codegen import bundle
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
    over the 1,059 roots: 834 admit, 32 are REFUSED by their own document (16 of them at a
    ``oneOf``) and 193 have NO VALUE, dominated by a ``pattern`` on a required key.
    ``adcp-client-python-hzio.10`` owns the pattern reader and
    ``adcp-client-python-hzio.11`` the refused roots; ``adcp-client-python-hzio.9`` owns
    this gate and its instruction is to leave it red.  No ``xfail``, no skip and no
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


# --------------------------------------------------------------------------- #
# a pattern of four constructs is READ, and every other pattern is left unread
# --------------------------------------------------------------------------- #
#: One row per construct the reader reads, and the string the constructs name.  **The
#: expected value is written down and the MATCH is not**: every row's value is offered to
#: ``jsonschema``'s own draft-07 checker below, so a row this project believes and the
#: checker refuses is a red test rather than a witness some document would reject.
READ_PATTERNS = (
    ("^[A-Z]{3}$", "AAA"),
    ("^[A-Z]{2}$", "AA"),
    ("^sha256:[a-f0-9]{64}$", "sha256:" + "a" * 64),
    ("^[a-z][a-z0-9_]*$", "a"),
    ("^[a-zA-Z0-9_-]+$", "a"),
    ("^[A-Za-z0-9_.:-]{16,255}$", "A" * 16),
    ("^#[0-9a-fA-F]{6}$", "#000000"),
    # a literal run with no terminal anchor: ``pattern`` is a SEARCH, so the run itself is
    # a string the pattern finds in
    ("^https://", "https://"),
    ("^https://github\\.com/", "https://github.com/"),
    # a quantifier whose minimum is zero takes the atom zero times
    ("^\\.github/workflows/[A-Za-z0-9._/-]+\\.ya?ml$", ".github/workflows/A.yml"),
    # ``\d`` is a class with a first member; a class escape is read like a class
    ("^\\d+\\.\\d+$", "0.0"),
    # a complement class under a ``*`` is never asked for a member
    ("^[^\\u0000-\\u001F\\u007F]*$", ""),
    # a class states its own first member, whatever it is
    ("^[\\x20-\\x7E]+$", " "),
    ("^[!$&-;=@-~]+$", "!"),
    ("^[Aa][Uu][Dd][Ii][Oo]/", "AUDIO/"),
)

#: One row per construct the reader does NOT read, with the construct it names.  **This
#: list is the deliverable of ``adcp-client-python-hzio.10``'s refusal half**: a reader that
#: guessed at a group, an alternation, a lookaround or a complement would be the regex
#: engine ``docs/plan/architecture.md`` §2 says this module does not build.
UNREAD_PATTERNS = (
    ("^(?:0|[1-9]\\d*)\\.(?:0|[1-9]\\d*)$", "a group"),
    ("^[A-Z]{2}(-[A-Z0-9]{1,3})?$", "a group"),
    ("^([A-Z]{2}|global)$", "a group"),
    ("^P(?!$)(\\d+Y)?$", "a group"),
    ("\\S", "a class whose members it does not name"),
    ("^[^\\u0000-\\u001F]+$", "a class whose members it does not name"),
    ("^[a-z_]+:.+$", "a class whose members it does not name"),
    ("^(a)\\1$", "a group"),
    ("^[a-z]+?$", "a lazy or possessive quantifier"),
    ("^\\bword$", "the assertion '\\b'"),
    ("^a{2,3,4}$", "the quantifier '{2,3,4}'"),
    ("^[a-z$", "a class with no end"),
)


def _admits(schema: dict, value: object) -> list[str]:
    """Which of ``schema``'s keywords ``jsonschema`` refuses ``value`` on.

    The draft's OWN checker with ``format`` asserted, which is the checker
    :meth:`codegen.verify.witness.Construction.validator` builds -- so a reading graded
    here is graded by the instrument the construction itself is screened by, and never by
    a second engine that could disagree with it.
    """
    cls = jsonschema.validators.validator_for(schema, jsonschema.Draft7Validator)
    validator = cls(schema, format_checker=cls.FORMAT_CHECKER)
    return [error.validator for error in validator.iter_errors(value)]


def test_the_four_constructs_are_read_and_the_string_they_name_is_the_pattern_s_own() -> None:
    """``hzio.10``'s reading: an anchor, a literal run, a character class and a quantifier.

    *"Produce the class's first member repeated the minimum count.  This is reading the
    keyword, exactly as ``minLength: 3`` -> ``"aaa"`` is already read."*  Each row states
    the string the constructs name, and then the DRAFT'S OWN CHECKER is asked whether the
    pattern admits it -- the expected value is this project's claim and the match is
    ``jsonschema``'s, which is the only split under which a row can be wrong and red.
    """
    rows = claimed("patterns of the read shape", READ_PATTERNS)
    for pattern, wanted in sorted(rows):
        built = witness._patterned(pattern, 0, None)
        assert built.held, (pattern, built.reason)
        assert built.value == wanted, (pattern, built.value, wanted)
        assert built.reason == witness.READ_FROM_A_PATTERN, (pattern, built.reason)
        assert not _admits({"type": "string", "pattern": pattern}, built.value), (pattern, built.value)


def test_a_pattern_of_any_other_shape_is_not_attempted_and_the_construct_is_NAMED() -> None:
    """The refusal half, which is the whole of why the reading above is allowed to be small.

    *"A pattern whose shape the reader does not cover is NOT attempted: the document's own
    ``examples`` is the value, and failing that the fact is approximated with the pattern
    quoted."*  So every row here has NO value, and the reason carries both the pattern's own
    text and the construct the reader stopped at -- a reason naming neither would leave the
    unread shapes anonymous, which is the allowlist ``docs/plan/final-state.md`` reading 2
    refuses.
    """
    rows = claimed("patterns of an unread shape", UNREAD_PATTERNS)
    for pattern, construct in sorted(rows):
        built = witness._patterned(pattern, 0, None)
        assert not built.held, (pattern, built.value)
        assert repr(pattern) in built.reason, (pattern, built.reason)
        assert construct in built.reason, (pattern, construct, built.reason)


def test_a_length_bound_beside_a_pattern_is_met_by_the_quantifier_s_own_range() -> None:
    """The siblings, which the value has to satisfy too.

    ``hzio.10``: *"a ``minLength``/``maxLength`` beside the pattern must be satisfied
    too"*.  A ``minLength`` above the atoms' own minimum is met by repeating a class as
    many times as ITS OWN quantifier admits, and a bound no repetition reaches is reported
    with the bound named rather than approached with a string the node refuses.
    """
    grown = witness._patterned("^[a-z]+$", 5, None)
    assert grown.value == "aaaaa", grown
    assert not _admits({"type": "string", "pattern": "^[a-z]+$", "minLength": 5}, grown.value)
    inside = witness._patterned("^[A-Za-z0-9_.:-]{1,255}$", 16, 255)
    assert inside.value == "A" * 16, inside
    too_short = witness._patterned("^[A-Z]{2}$", 0, 1)
    assert not too_short.held and "maxLength 1" in too_short.reason, too_short
    too_long = witness._patterned("^[A-Z]{2}$", 3, None)
    assert not too_long.held and "minLength 3" in too_long.reason, too_long


#: A node whose ``format`` and ``pattern`` each refuse the other's first answer:
#: ``https://example.com`` is the ``uri`` case and the pattern refuses it, and the string
#: the pattern names is a ``uri`` the node admits.  Measured in bundle 3.2, twice.
FORMAT_BESIDE_A_PATTERN = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["link"],
    "properties": {
        "link": {"type": "string", "format": "uri", "pattern": "^https://github\\.com/"}
    },
}

#: Two conjuncts stating two different patterns about ONE instance.  Their intersection is
#: not read: the shallow screen reads one node's own statements, so a value the first
#: pattern alone admits would be a witness nothing checked.
TWO_PATTERNS = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "allOf": [{"type": "string", "pattern": "^[a-z]+$"}, {"pattern": "^[0-9]+$"}],
}


def test_a_format_beside_a_pattern_still_passes_and_the_reading_is_the_node_s_next_case() -> None:
    """Both keywords hold of one instance, so both have to hold of the one value.

    :func:`codegen.verify.witness._string` offers the ``format``'s own case first, because a
    formatted node's admitted set is the format's; where a sibling pattern refuses every
    case the format states, the string the PATTERN names is the node's own next statement
    (:meth:`codegen.verify.witness.Construction._stated`) -- and it is screened, so what is
    kept is admitted on both keywords by the document's own checker.
    """
    built = witness.Construction({"both.json": FORMAT_BESIDE_A_PATTERN})
    answer = built.value("both.json", "")
    assert answer.held, answer.reason
    assert answer.value == {"link": "https://github.com/"}, answer.value
    assert not built.document_admits("both.json", answer.value)


def test_two_patterns_about_one_instance_are_not_intersected() -> None:
    """The reader reads ONE pattern, and two statements of it are two languages.

    Intersecting them is solving rather than reading, so the fact is approximated with both
    quoted -- and the node that states each one grades its own, which is where a value for
    either is screened.
    """
    built = witness.Construction({"two.json": TWO_PATTERNS})
    answer = built.value("two.json", "")
    assert not answer.held, answer
    assert "'^[a-z]+$'" in answer.reason and "'^[0-9]+$'" in answer.reason, answer.reason


def test_every_value_read_off_a_pattern_is_one_its_own_node_admits() -> None:
    """**THE VALUE IS CHECKED BY THE DOCUMENT'S OWN CHECKER AND NOT BY THE READER.**

    ``hzio.10``: *"A reader returning a string its own pattern refuses is a defect the gate
    catches."*  So this ranges over every position of every portable document whose value
    came off a pattern (:data:`codegen.verify.witness.READ_FROM_A_PATTERN`) and asks three
    independent questions of it: the node's own screen, every ``pattern``, ``minLength``,
    ``maxLength`` and ``format`` any statement about that instance makes, and the whole node
    struck of nothing but the keywords that describe OTHER locations.  Each is
    ``jsonschema``'s answer rather than this module's.
    """
    built = constructed.whole()
    read = claimed(
        "positions holding a value read off a pattern",
        [
            (document, pointer)
            for document, positions in sorted(constructed.pointers().items())
            for pointer in positions
            if built.value(document, pointer).reason == witness.READ_FROM_A_PATTERN
            and built.value(document, pointer).held
        ],
    )
    bad = []
    for document, pointer in sorted(read):
        value = built.value(document, pointer).value
        if built.refusals(document, pointer, value):
            bad.append((document, pointer, value, built.refusals(document, pointer, value)))
        for at, _ in built._views(document, pointer, ()):
            view = built.node(document, at)
            if not isinstance(view, dict):
                continue
            stated = {k: v for k, v in view.items() if k in ("pattern", "minLength", "maxLength", "format")}
            refused = _admits({"type": "string", **stated}, value) if stated else []
            if refused:
                bad.append((document, pointer, at, stated, value, refused))
        own = {k: v for k, v in built.node(document, pointer).items() if k not in witness.STRUCK}
        refused = _admits(own, value)
        if refused:
            bad.append((document, pointer, own, value, refused))
    assert not bad, bad[:5]


def test_the_patterns_this_bundle_states_are_each_read_or_NAMED_unread() -> None:
    """The coverage account for ``pattern``, as a PARTITION over the bundle's own patterns.

    Every distinct pattern any portable document states falls into exactly one of two: the
    reader produces a string its own pattern admits, or the reader names the construct it
    stopped at.  Neither part may be empty and nothing may be in both, which is what makes
    "66 of 110" a reading rather than a claim -- and the unread part is NAMED rather than
    counted, so the shapes this module does not cover are visible under their own text.
    """
    stated = claimed(
        "distinct patterns the bundle states",
        {
            node["pattern"]
            for record in constructed.records().values()
            for _pointer, node in bundle.nodes(record)
            if isinstance(node, dict) and isinstance(node.get("pattern"), str)
        },
    )
    read, unread = set(), set()
    for pattern in sorted(stated):
        built = witness._patterned(pattern, 0, None)
        if built.held:
            assert not _admits({"type": "string", "pattern": pattern}, built.value), (pattern, built.value)
            read.add(pattern)
        else:
            assert repr(pattern) in built.reason, (pattern, built.reason)
            unread.add(pattern)
    partitions(stated, read_by_their_constructs=read, left_unread_and_named=unread)


def test_the_pattern_reading_matches_nothing_and_the_module_runs_no_regex() -> None:
    """**IT IS A READER AND NOT AN ENGINE, read off the module's own imports.**

    ``hzio.10``: *"This is NOT a regex engine and must not become one."*  The structural
    half of that is here: nothing in this module imports ``re``, so there is no matching,
    no backtracking and no search anywhere on the construction's path.  Every decision about
    whether a value satisfies a pattern is ``jsonschema``'s -- the document's own checker,
    through :meth:`codegen.verify.witness.Construction.refusals`.
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
    assert "re" not in imports, imports
    assert "regex" not in imports, imports
    assert "sre_parse" not in imports, imports


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
