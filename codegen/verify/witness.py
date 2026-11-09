"""The witness is CONSTRUCTED: one admitted value per node, read off the node's own
keywords, and one mutation per keyword the node states.

``docs/plan/architecture.md`` §2 ("The witness is CONSTRUCTED, so there is no corpus and
no store") and §9 ("The verifier"), ``docs/plan/final-state.md`` reading 1 and
``docs/plan/rebuild-plan.md`` §8 are this module's specification, and the three say one
thing four ways: *a value a node admits is READ OFF its keywords, never searched for in
the space they admit.*

``const`` gives its value, ``enum`` its first member, ``required`` its keys, a length or
count bound exactly that many, ``type`` the scalar or container the word names,
``properties`` an object over the required subset, and a ``$ref`` the value already built
for the pointer it names.

**BOTTOM-UP AND TOTAL.**  A node's value is a function of its children's, so a value
exists for every node and the cost of a document is one walk of it -- not "a value for
most nodes and a budget for the rest".  :class:`Construction` is that walk, and
:attr:`Construction.counters` is how the claim is read rather than asserted in prose:
:attr:`Counters.computed` is the number of keys the walk built and
:attr:`Counters.asked` the number of times one was wanted, so a second visit to a node is
a memo hit and shows up as the difference.

**THE KEY IS ``(document, pointer, stack)``** (:data:`Key`).  The stack is the resolution
path -- every pointer this answer was reached THROUGH, whether by a ``$ref`` or by a
conjunct co-describing the same instance -- which is what distinguishes one node reached
under two different conjunctions.  **Never the node's text**, which costs the whole
subtree to produce and is a different string for two nodes that are the same node reached
twice (§9's identity rule).  **Never bare ``id(node)``** either: an identity key is sound
only while the object it keys on is PINNED in the memo, and an unpinned temporary's
address is reused, so the key changes under the caller silently.

**A CYCLE CLOSES ON THE POINTER AND THERE IS NO DEPTH PARAMETER.**  A reference reaching a
pointer already on the stack is a back edge (:attr:`Source.BACK_EDGE`): the construction
completes by OMITTING it where the document makes the reference optional, and by taking
the target's minimal value (:meth:`Construction.floor`) where the document requires it.
The memo that makes the walk linear is the memo that closes the cycle, so a depth limit
would be a guess standing in for the detection and none is introduced here.

**WHERE CONSTRUCTION CANNOT REACH, THE DOCUMENT'S OWN ``examples`` IS THE VALUE**, and
failing that the fact is approximated with the reason named (:attr:`Source.APPROXIMATED`,
:attr:`Built.reason`).  An arbitrary ``pattern`` and a ``format`` nothing can state are
the two cases, and **this module builds no solver for either** -- not a regex engine, not
a format generator.  Refusing to build one is the decision, not an omission:
``docs/plan/final-state.md`` reading 1 says a document that states no example and admits
no value construction can produce "is an ask over a set of the bundle".

**THE SCREEN IS SHALLOW BY DESIGN, AND THAT IS §9's LINEARITY RULE.**  A value is offered
to the node's OWN statements (:meth:`Construction.refusals`) and never to its subtree: a
child's value was already screened at the child, so re-validating every subtree at every
ancestor would pay the sum of every subtree -- quadratic in the document and worse with
depth, which is the cost §9 says is "invisible at the call site".  The whole-document
reading exists too and is taken ONCE per document at its root
(:meth:`Construction.document_admits`), which is one more walk of one instance and not one
per node.
"""

from __future__ import annotations

import collections
import dataclasses
import enum
from collections.abc import Mapping, Sequence
from typing import Any

import jsonschema

from codegen import bundle, keywords

#: ``(document, pointer, stack)``.  §9's identity rule, spelled as a type: a node is named
#: by the document that holds it and the JSON Pointer that reaches it, and the stack is the
#: resolution path that answer was reached under.
Key = tuple[str, str, tuple[str, ...]]

#: Every keyword that holds a subschema, read off the one descent table rather than
#: restated (``docs/plan/architecture.md`` §11: the descent column is the one owner).
#: :meth:`Construction.refusals` strikes these from a node before offering a value to it,
#: because what each of them holds is a node of its own with a value of its own.
DESCENDS = frozenset(bundle.DESCENDS)

#: The keywords that descend AND state something about the instance at this node's own
#: location, so striking them outright would stop the screen from reading a fact the
#: construction had to satisfy.  Both are kept in their NON-descending spelling:
#: ``additionalProperties`` only as the boolean closure (a schema-valued one becomes
#: ``true``), and ``dependencies`` only in its required-keys form (a schema-valued entry is
#: dropped).  ``propertyNames`` is not here: it holds a schema, and the keys this
#: construction chose are screened against it by the node that holds it.
CLOSES_ITS_LOCATION = frozenset({"additionalProperties", "dependencies"})

#: ``$ref`` is NOT in the descent column -- a reference is not a subschema position -- and
#: it is struck from the screen anyway, which a measurement forced.
#:
#: draft-07's own reading is that a ``$ref`` beside other keywords IGNORES them, so a
#: reference node states nothing of its own and its value is the target's, screened at the
#: target.  Keeping it made ``evolve(schema={"$ref": ...})`` a FULL validation of the whole
#: target subtree -- 67,540 reference nodes in this bundle, each paying its target's depth
#: at the referring position, which is exactly the O(subtree)-per-node cost
#: ``docs/plan/architecture.md`` §9 says is "invisible at the call site".  It also reported
#: a referring node as refusing its own value on a ``not`` stated three levels inside the
#: target, which is a fact about the target's own node and is graded there.
STRUCK = DESCENDS | {"$ref"}

#: The literal cases a ``format`` admits, by format name -- **a table of CONSTANTS and not
#: a generator**, which is the whole of why it is permitted here.
#:
#: ``docs/plan/rebuild-plan.md`` §8 asks for "every case the format's own checker admits
#: rather than the case a generator finds most likely", so a format gets SEVERAL cases and
#: the first is the one the admitted value takes.  Every case here is asserted against
#: ``jsonschema``'s own draft-07 checker by
#: ``tests/test_witness_construction.py::test_every_format_case_is_one_the_draft_s_own_checker_admits``,
#: so a case this project believes and the checker refuses is a red test and not a silent
#: witness the document rejects.
#:
#: A format with no entry is one this project cannot state, and a node carrying it falls to
#: its own ``examples`` and then to an approximation -- which is the reading, not a gap.
FORMAT_CASES: Mapping[str, tuple[str, ...]] = {
    "date-time": (
        "2026-11-09T12:00:00Z",
        "2026-11-09T12:00:00+01:00",
        "2026-11-09T12:00:00.123456Z",
    ),
    "date": ("2026-11-09",),
    "time": ("12:00:00Z", "12:00:00+01:00"),
    "email": ("someone@example.com",),
    "hostname": ("example.com", "a"),
    "ipv4": ("192.0.2.1",),
    "ipv6": ("2001:db8::1",),
    # The authority-only case is FIRST and it is first because a measurement put it
    # there: 153 nodes state ``format: uri`` beside a ``pattern`` of the shape
    # ``^https://[^/?#@]+$``, which the path-bearing case refuses, and the one
    # remaining fallback for them was an ``examples`` member they do not state.
    "uri": ("https://example.com", "https://example.com/a", "urn:ietf:rfc:3986"),
    "uri-reference": ("https://example.com/a", "/a/b", ""),
    "uri-template": ("https://example.com/{id}",),
    "json-pointer": ("/a/b", ""),
    "relative-json-pointer": ("0", "1/a"),
    "regex": ("^a$",),
    "iri": ("https://example.com/a",),
    "iri-reference": ("https://example.com/a", "/a/b"),
    "idn-hostname": ("example.com",),
    "idn-email": ("someone@example.com",),
    "uuid": ("f81d4fae-7dec-11d0-a765-00a0c91e6bf6",),
}

#: The value each ``type`` word names when the node states nothing else about it.  **The
#: floor of the word and not a sample of it**: an empty string, zero, an empty container.
#: A bound then moves it (:func:`_string`, :func:`_number`), which is what "a length or
#: count bound exactly that many" means.
WORD_FLOOR: Mapping[str, Any] = {
    "null": None,
    "boolean": True,
    "string": "",
    "integer": 0,
    "number": 0,
    "array": (),
    "object": (),
}

#: The order a ``type`` LIST is read in when the node states one.  draft-07's list is an
#: alternation, so the admitted value takes ONE word of it -- the document's own first,
#: because the document's order is the only order that is the document's.  Every other word
#: is a value class of the ``type`` keyword (:meth:`Construction.classes`).
_CONTAINERS = frozenset({"object", "array"})

#: A sentinel for "this pointer has not been dereferenced", because ``None`` is a node a
#: record can legitimately hold at a position a pointer names.
_MISSING = object()


class Source(enum.StrEnum):
    """Where a node's value came from, which is the whole of what a reader needs.

    :attr:`CONSTRUCTED` and :attr:`STATED` are values; :attr:`APPROXIMATED` and
    :attr:`BACK_EDGE` are not, and :attr:`Built.held` is the one question that separates
    them.
    """

    #: Read off the node's own keywords.  The designed answer.
    CONSTRUCTED = "constructed"
    #: The document's own ``examples`` member, where the construction could not reach.
    STATED = "stated"
    #: No value, and :attr:`Built.reason` names why.  ``docs/plan/architecture.md`` §9's
    #: approximation: a fact the instrument cannot grade, reported rather than skipped.
    APPROXIMATED = "approximated"
    #: The construction of :attr:`Built.target` is in progress at this position, so the
    #: caller omits it where the document makes it optional and takes
    #: :meth:`Construction.floor` where the document requires it.
    BACK_EDGE = "back edge"


@dataclasses.dataclass(frozen=True, slots=True)
class Built:
    """One node's answer: a value, or a named reason it has none."""

    value: Any
    source: Source
    #: Why there is no value, or how the one there is was reached.  Empty for a plain
    #: construction, because a reason that is always written is a reason nobody reads.
    reason: str = ""
    #: For :attr:`Source.BACK_EDGE`, the pointer whose construction is in progress.
    target: str = ""

    @property
    def held(self) -> bool:
        """Is there a value here at all."""
        return self.source in (Source.CONSTRUCTED, Source.STATED)


@dataclasses.dataclass(frozen=True, slots=True)
class Class:
    """One constraint class a keyword at a node distinguishes.

    ``docs/plan/rebuild-plan.md`` §8: *"the construction covers the node's admissible
    space BY CONSTRAINT CLASS; it does not sample it"* -- every member of an ``enum``, both
    sides of each bound and the bound itself, and for a ``format`` every case the format's
    own checker admits.  A class is a value the DOCUMENT ADMITS; the values it refuses are
    :class:`Mutation`.
    """

    keyword: str
    #: Which class of the keyword this is -- ``"member 3"``, ``"at the bound"``, ``"inside
    #: the bound"``, ``"case 0"``.  Named rather than numbered, because the point of a
    #: class is to be able to report WHICH one a class refused.
    label: str
    value: Any


@dataclasses.dataclass(frozen=True, slots=True)
class Mutation:
    """One violation of ONE keyword the node states, at a named instance location.

    ``docs/plan/architecture.md`` §9: *"a mutation names the keyword it violates, which is
    what makes the second check more than a boolean"*, and the mutation is of the ADMITTED
    value rather than an arbitrary non-conforming one, so that changing exactly one stated
    fact isolates the keyword under test from every other keyword at the node.

    :attr:`location` is the instance path the change was made at, as a tuple of keys and
    indices -- ``()`` for the node's own value, ``("a",)`` for a property of it.  A refusal
    read anywhere else, or against any other keyword, has not shown the subject carries
    this keyword (:meth:`Construction.refusals`).
    """

    keyword: str
    label: str
    value: Any
    location: tuple[Any, ...]


@dataclasses.dataclass
class Counters:
    """**Every memo and every claimed funnel carries a counter the gate reads** (§9).

    A memo nothing reaches, a cap the walk actually terminates on, a pass stated to run
    once that runs twice: each is silent in the artifact and loud here.  So these are part
    of the cost model and not a later improvement to it, and
    ``tests/test_witness_construction.py`` asserts the identities between them rather than
    printing them.
    """

    #: How many times a value was WANTED, counting every entry into
    #: :meth:`Construction.value`.
    asked: int = 0
    #: How many keys were BUILT.  ``asked - computed`` is the memo's hit count, and
    #: ``computed == len(memo)`` is what "one walk per node" means as an equality.
    computed: int = 0
    #: How many distinct ``(document, pointer)`` pairs the walk DEREFERENCED, so that
    #: ``computed / reached`` is the cost of carrying the stack in the key.
    reached: int = 0
    #: Back edges detected, and of those the ones a required position had to floor.
    back_edges: int = 0
    floored: int = 0
    #: How many nodes fell to their own ``examples``, and how many to an approximation.
    stated: int = 0
    approximated: int = 0
    #: Shallow screens run, and how many of them the node refused -- which is what makes
    #: the fallback to ``examples`` a measurement rather than a guess.
    screened: int = 0
    refused: int = 0
    #: Mutations built, and the ones DISCARDED because the document admitted them.  *"A
    #: mutation the document still admits is a defect in the mutation, not a failure of the
    #: class -- so every mutation is offered to the DOCUMENT first and discarded if the
    #: document admits it, with the discard reported rather than silent."*
    mutations: int = 0
    discarded: int = 0
    #: Why nodes have no value, by reason.  The honest half of the coverage account.
    reasons: collections.Counter[str] = dataclasses.field(default_factory=collections.Counter)
    #: Why a mutation was discarded, by keyword.
    discards: collections.Counter[str] = dataclasses.field(default_factory=collections.Counter)


# --------------------------------------------------------------------------- #
# reading one node's own statements
# --------------------------------------------------------------------------- #
def _bound(views: Sequence[Mapping[str, Any]], keyword: str) -> Any:
    """The TIGHTEST value several co-describing statements give one bound.

    ``keywords.pins_a_floor`` is the one bit this turns on -- a floor rises as it narrows
    and a ceiling falls -- and it is read off the declaration rather than from the
    keyword's spelling, which is ``codegen/keywords.py``'s own stated reason for holding
    :data:`codegen.keywords.RANGES`.
    """
    stated = [v[keyword] for v in views if isinstance(v.get(keyword), (int, float))]
    if not stated:
        return None
    return max(stated) if keywords.pins_a_floor(keyword) else min(stated)


def _words(views: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """The ``type`` words every co-describing statement admits, in the first one's order.

    An intersection and not a union: two statements about one instance both hold, so a
    word only one of them names is not admitted.  The ORDER is the first statement that
    names any, because the document's own order is the only order that is the document's.
    """
    lists = []
    for view in views:
        word = view.get("type")
        if isinstance(word, str):
            lists.append((word,))
        elif isinstance(word, list) and all(isinstance(w, str) for w in word):
            lists.append(tuple(word))
    if not lists:
        return ()
    admitted = set(lists[0])
    for other in lists[1:]:
        admitted &= set(other)
    return tuple(w for w in lists[0] if w in admitted)


def _implied(views: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """The container or scalar the node's OTHER keywords declare, where no ``type`` does.

    ``docs/plan/rebuild-plan.md`` §8's entailment, which it states for a union -- *"a union
    every branch of which declares an object has declared an object as surely as ``type:
    object`` does -- the same entailment the keyword reading already makes for ``contains``
    implying an array"*.  Read off :func:`codegen.keywords.constrains_container` and
    :data:`codegen.keywords.ARM` so the set of keywords that declare a type is the declared
    one and not a list written here.
    """
    stated = {k for view in views for k in view}
    for word in ("object", "array"):
        if stated & keywords.constrains_container(word):
            return (word,)
    for word in ("string", "integer"):
        if stated & keywords.ARM[word]:
            return (word,)
    return ()


def _string(views: Sequence[Mapping[str, Any]]) -> Built:
    """The string the node's own string keywords state it admits.

    ``format`` first, because a formatted node's admitted set is the format's and a
    padded string is not in it; then the length bound, exactly as many characters as it
    demands.  A ``pattern`` is where the construction STOPS -- there is no regex engine
    here and there will not be one -- so the caller falls to the document's own
    ``examples``.
    """
    low = _bound(views, "minLength") or 0
    high = _bound(views, "maxLength")
    for view in views:
        named = view.get("format")
        if isinstance(named, str):
            cases = FORMAT_CASES.get(named)
            if cases is None:
                return Built(None, Source.APPROXIMATED, f"format {named!r} states no case")
            fitting = [c for c in cases if len(c) >= low and (high is None or len(c) <= high)]
            if not fitting:
                return Built(
                    None,
                    Source.APPROXIMATED,
                    f"no stated case of format {named!r} fits the length bound",
                )
            return Built(fitting[0], Source.CONSTRUCTED)
    for view in views:
        if isinstance(view.get("pattern"), str):
            return Built(None, Source.APPROXIMATED, f"pattern {view['pattern']!r} is not solved")
    if high is not None and high < low:
        return Built(None, Source.APPROXIMATED, "the length bounds admit no string")
    return Built("a" * low, Source.CONSTRUCTED)


def _step(open_low: float, high: float | None, open_high: float | None, *, whole: bool) -> float:
    """How far past an EXCLUSIVE floor the first admitted value sits.

    One for an ``integer``, because draft-07's integers are the integers.  For a
    ``number`` it is one too **unless the node's own ceiling is nearer than that**, and
    then it is half the distance to the ceiling -- which is not a guess but the only
    reading the node's two bounds leave: ``{"type": "number", "exclusiveMinimum": 0,
    "exclusiveMaximum": 1}`` admits no integer at all, and a step of one lands outside
    the node while the node admits an interval.  Measured: that one node shape accounts
    for 293 of the approximations this reading removes.
    """
    if whole:
        return 1
    ceiling = high if high is not None else open_high
    if ceiling is None or ceiling - open_low > 1:
        return 1
    return (ceiling - open_low) / 2


def _number(views: Sequence[Mapping[str, Any]], *, whole: bool) -> Built:
    """The number the node's own ordering keywords state it admits.

    The FLOOR of the admitted range and not a point inside it, which is the same reading a
    length bound gets.  An exclusive bound admits no instance AT it
    (:data:`codegen.keywords.EXCLUSIVE`), so the step in is one -- integral for an
    ``integer``, and one for a ``number`` too, because a fraction chosen here would be a
    guess where the document states none.
    """
    low = _bound(views, "minimum")
    exclusive_low = _bound(views, "exclusiveMinimum")
    high = _bound(views, "maximum")
    exclusive_high = _bound(views, "exclusiveMaximum")
    floor = 0 if low is None else low
    if exclusive_low is not None:
        floor = max(floor, exclusive_low + _step(exclusive_low, high, exclusive_high, whole=whole))
    multiple = _bound(views, "multipleOf")
    if isinstance(multiple, (int, float)) and multiple > 0:
        steps = -(-floor // multiple)
        floor = steps * multiple
    if whole:
        floor = int(floor) if float(floor).is_integer() else int(floor) + 1
    if high is not None and floor > high:
        return Built(None, Source.APPROXIMATED, "the ordering bounds admit no number")
    if exclusive_high is not None and floor >= exclusive_high:
        return Built(None, Source.APPROXIMATED, "the ordering bounds admit no number")
    return Built(floor, Source.CONSTRUCTED)


# --------------------------------------------------------------------------- #
# the construction
# --------------------------------------------------------------------------- #
class Construction:
    """One memo, one validator per document, and no cap of any kind.

    Built over the RECORDS -- ``codegen.bundle.record``'s self-contained documents, read as
    a MAPPING and never re-derived.  ``docs/plan/architecture.md`` §9: *"the verifier never
    calls ``schema.parse``; it reads the document of record as a mapping, because what it
    grades is what the document states and not what the walk made of it."*  And the reader
    rule beside it: a reader of the record must not rebuild it, because a reader that
    rebuilds forfeits the identity its caller carried and every memo above it stops
    hitting.  So the pointer travels with the call and nothing here copies a subtree.
    """

    def __init__(self, records: Mapping[str, Mapping[str, Any]]) -> None:
        self._records = dict(records)
        self._validators: dict[str, Any] = {}
        self._memo: dict[Key, Built] = {}
        self._floors: dict[tuple[str, str], Built] = {}
        self._nodes: dict[tuple[str, str], Any] = {}
        self.counters = Counters()

    # -- the document's own halves ----------------------------------------- #
    def validator(self, document: str) -> Any:
        """**ONE validator per document** (§9), built where the document is read.

        The reference registry and the resolver are properties of the DOCUMENT and not of a
        visit, so they outlive every node in it.  A per-node validator rebuilds the
        registry, re-resolves every reference and discards what it learned -- the pointer
        memo and the validator lifetime being the same rule applied to the two halves of
        the check.  A node's own screen is this validator ``evolve``\\ d onto the node,
        which keeps the resolution base the document's root so a ``#/definitions`` pointer
        still resolves.

        ``format`` is ASSERTED, with the DRAFT'S OWN checker rather than the global
        registry: the global one carries every checker any draft defines, so it would
        assert ``uuid`` against a draft-07 document, which draft-07 does not define as a
        format -- the SDK inventing a constraint.
        """
        held = self._validators.get(document)
        if held is None:
            record = self._records[document]
            cls = jsonschema.validators.validator_for(record, jsonschema.Draft7Validator)
            held = cls(record, format_checker=cls.FORMAT_CHECKER)
            self._validators[document] = held
        return held

    def node(self, document: str, pointer: str) -> Any:
        """The node at a pointer, read off the record as a mapping -- and PINNED.

        ``codegen.bundle.node_at`` is the one dereferencing, shared with the compiler's own
        half: a pointer segment holding a ``/`` or a ``~`` is escaped by RFC 6901's two
        escapes and two spellings of that would be two readings of one grammar.

        **Held by ``(document, pointer)``, which is the same linearity argument the value
        memo makes.**  Dereferencing walks from the record's root, so a reader that asks
        twice pays the depth twice -- and the construction asks for one node several times
        (once per view, once per screen).  The record is immutable for the life of this
        object, so the answer cannot go stale, and the entry PINS the node: an identity key
        over an unpinned temporary is the defect §9's identity rule names, and nothing here
        can acquire it while every node the walk has seen is held.
        """
        key = (document, pointer)
        held = self._nodes.get(key, _MISSING)
        if held is _MISSING:
            held = bundle.node_at(self._records[document], pointer)
            self._nodes[key] = held
            self.counters.reached += 1
        return held

    # -- the walk ---------------------------------------------------------- #
    def value(
        self,
        document: str,
        pointer: str = "",
        stack: tuple[str, ...] = (),
        besides: tuple[str, ...] = (),
    ) -> Built:
        """**THE ONE ENTRY POINT, and it is memoised** (§9).

        *"Memoisation here is the design and not an optimisation.  One answer per node per
        document, keyed on the pointer, is what makes the cost linear, the budget
        unnecessary and the cycle closed."*  A second uncached entry point would shadow
        this one and is the defect that reading names, so :meth:`_construct` is private and
        nothing else calls it.

        **``besides`` IS THE REST OF THE CONJUNCTION ABOUT THIS ONE INSTANCE**, and it is
        not a second key.  One instance location can be described from several schema
        positions at once -- the node's own ``properties`` entry and a ``oneOf`` branch's
        entry for the same key -- and the value for that location is built from ALL of
        them (:meth:`_views`).  Every caller that passes ``besides`` puts the same pointers
        on the ``stack``, so :data:`Key` already distinguishes the answer that depended on
        them from the answer that did not, and the key stays the three things §9's identity
        rule names.  **A caller that passed one and not the other would be asking the memo
        to serve an answer built from a conjunction it was not keyed on**, which is the
        defect ``Fixtures._pin`` was measured to have.
        """
        key: Key = (document, pointer, stack)
        self.counters.asked += 1
        held = self._memo.get(key)
        if held is not None:
            return held
        # Written BEFORE the construction and read by nothing until it returns: the memo
        # is what closes a cycle, and a key whose construction is in progress has to be
        # findable.  The stack is what carries that -- a pointer already on it is a back
        # edge -- so no placeholder value is parked here and no second structure holds
        # "in progress".
        built = self._construct(document, pointer, stack, besides)
        self._memo[key] = built
        self.counters.computed += 1
        if built.source is Source.STATED:
            self.counters.stated += 1
        elif built.source is Source.APPROXIMATED:
            self.counters.approximated += 1
            self.counters.reasons[built.reason] += 1
        elif built.source is Source.BACK_EDGE:
            self.counters.back_edges += 1
        return built

    def floor(self, document: str, pointer: str, seen: frozenset[str] = frozenset()) -> Built:
        """The target's MINIMAL value, for a back edge at a position the document REQUIRES.

        §9: a reference reaching a pointer whose construction is in progress *"completes by
        omitting the reference where the document makes it optional, and by taking the
        minimal instance of the target where the document requires it."*  Minimal is the
        word's own floor (:data:`WORD_FLOOR`) over the required keys whose own floor does
        not re-enter -- so a required key reached twice is DROPPED with the reason named,
        which is the honest answer: a cycle of required keys admits no finite instance at
        all, and that is a defect in the document rather than a budget to spend.

        ``seen`` is in the key for the reason ``Fixtures._pin``'s omission of it is a
        measured defect in the sampler this replaces: its memo key left out the ``depth``
        its answer depended on, so a truncated answer computed at low residual depth was
        served first-writer-wins to a caller that had budget.  An answer that depends on
        the in-progress set is keyed on the in-progress set.
        """
        if pointer in seen:
            return Built(None, Source.APPROXIMATED, "a cycle of required keys admits no instance")
        if not seen:
            cached = self._floors.get((document, pointer))
            if cached is not None:
                return cached
        node = self.node(document, pointer)
        built = self._floor(document, pointer, node, seen | {pointer})
        if not seen:
            self._floors[(document, pointer)] = built
        return built

    def _floor(self, document: str, pointer: str, node: Any, seen: frozenset[str]) -> Built:
        """The floor's one reading, and **a required key it cannot reach is REPORTED**.

        ``docs/plan/architecture.md`` §9 asks for "the minimal instance of the target where
        the document requires it", and a document whose required keys CYCLE has no finite
        instance at all -- so there is no minimal one to take, and the honest answer is the
        named reason rather than a partial object the document refuses.  Dropping the key
        silently was measured on a synthetic record (``tests/test_witness_construction.py``
        carries both): it produced ``{"name": "", "child": {"name": ""}}`` for a node whose
        ``required`` names ``child``, which the document refuses on ``required`` one level
        down -- a witness that is not one.
        """
        if not isinstance(node, Mapping):
            return Built(None, Source.CONSTRUCTED)
        ref = node.get("$ref")
        if isinstance(ref, str):
            target = _local(ref)
            if target is None:
                return Built(None, Source.APPROXIMATED, f"{ref!r} is not a pointer of the record")
            return self.floor(document, target, seen)
        if "const" in node:
            return Built(node["const"], Source.CONSTRUCTED)
        members = node.get("enum")
        if isinstance(members, list) and members:
            return Built(members[0], Source.CONSTRUCTED)
        words = _words([node]) or _implied([node])
        word = words[0] if words else "null"
        if word == "object":
            placed: dict[str, Any] = {}
            for name in _required([node]):
                at = f"{pointer}/properties/{bundle.escape_key(name)}"
                inner = self.floor(document, at, seen)
                if not inner.held:
                    return Built(
                        None,
                        Source.APPROXIMATED,
                        f"the minimal instance needs {name!r}: {inner.reason}",
                    )
                placed[name] = inner.value
            return Built(placed, Source.CONSTRUCTED)
        if word == "array":
            least = _bound([node], "minItems")
            count = int(least) if isinstance(least, (int, float)) else 0
            if count == 0:
                return Built([], Source.CONSTRUCTED)
            if not isinstance(node.get("items"), Mapping):
                return Built([None] * count, Source.CONSTRUCTED)
            inner = self.floor(document, f"{pointer}/items", seen)
            if not inner.held:
                return Built(
                    None, Source.APPROXIMATED, f"the minimal instance needs an element: {inner.reason}"
                )
            return Built([inner.value] * count, Source.CONSTRUCTED)
        if word == "string":
            return _string([node])
        if word in ("integer", "number"):
            return _number([node], whole=word == "integer")
        return Built(WORD_FLOOR.get(word), Source.CONSTRUCTED)

    def _construct(
        self, document: str, pointer: str, stack: tuple[str, ...], besides: tuple[str, ...] = ()
    ) -> Built:
        """One node's value, bottom-up over its children's.

        The cascade is the keyword reading and nothing else: a ``$ref`` is the value
        already built for the pointer it names, a ``const`` is its value, an ``enum`` its
        first member, and a ``type`` the scalar or container the word names, over the
        statements every co-describing conjunct makes about this one instance.

        **AND A VALUE IS OFFERED TO THE KEYWORDS THAT DECIDE BETWEEN THE NODE'S OWN
        ALTERNATIVES BEFORE IT IS KEPT** (:meth:`_decides`).  ``oneOf`` admits an instance
        satisfying EXACTLY ONE branch, so a value satisfying two is refused exactly as one
        satisfying none is -- which means picking a branch is only half the reading, and
        making the value fail every OTHER branch is the other half.  The same holds from the
        other side for a sibling ``not``: a value read off the positive keywords alone has
        not consulted the statement that forbids it.  So the branch retry below is driven by
        those three keywords rather than by the shallow screen, which strikes them
        (:data:`STRUCK`).

        **THE DECIDERS ORDER THE ALTERNATIVES; THEY NEVER TAKE A VALUE AWAY.**  Where no
        alternative the node states satisfies them, the value the node's own screen admits is
        still the value -- the node is one position in a composition and the whole-document
        reading (:meth:`document_admits`) is where a composition is graded.  A decider that
        could delete a value would turn a conjunction this reading cannot yet satisfy into an
        unexplained absence, and ``docs/plan/final-state.md`` reading 2 is that an absence
        with no named reason is an allowlist.
        """
        node = self.node(document, pointer)
        if node is True:
            return Built(None, Source.CONSTRUCTED)
        if node is False:
            return Built(None, Source.APPROXIMATED, "a false schema admits nothing")
        if not isinstance(node, Mapping):
            return Built(None, Source.CONSTRUCTED)

        # draft-07, and ``jsonschema``'s own reading of it: a ``$ref`` beside other
        # keywords IGNORES them, so the value is the target's and nothing else's.
        ref = node.get("$ref")
        if isinstance(ref, str):
            target = _local(ref)
            if target is None:
                return Built(None, Source.APPROXIMATED, f"{ref!r} is not a pointer of the record")
            if target in stack:
                return Built(None, Source.BACK_EDGE, f"{target} is in progress", target)
            # ``besides`` TRAVELS THROUGH THE REFERENCE, and leaving it behind here was
            # measured: draft-07's rule is that a ``$ref`` ignores the keywords BESIDE IT AT
            # ITS OWN NODE, not that it ignores what another position states about the same
            # instance.  ``core/macro-translation-target.json`` declares
            # ``dialect_semantic`` as a ``$ref`` to a string and a consequent declares the
            # same key as a ``$ref`` to the 75-member macro ``enum``; dropping the second at
            # this line built the string's floor and the document refused it on ``enum``.
            return self.value(document, target, (*stack, target), besides)

        views = self._views(document, pointer, stack, None, besides)
        built, settled = self._settled(document, views)
        if built.source is Source.BACK_EDGE:
            return built
        screened = built.held and not self.refusals(document, pointer, built.value)
        if screened and not self._decides(document, settled, built.value):
            return built
        first, chosen, elected = built, settled, built if screened else None
        empty = None if built.held else built
        # The default branch of the union the picks range over IS the round above, so the
        # retry starts at the second: a pick is a different reading of the SAME node and
        # not a second node, which is what makes this a sum over one union's branches.
        for pick in self._picks(document, settled)[1:]:
            built, settled = self._settled(
                document, self._views(document, pointer, stack, pick, besides), pick
            )
            if built.source is Source.BACK_EDGE:
                return built
            if not built.held:
                empty = empty or built
                continue
            if self.refusals(document, pointer, built.value):
                continue
            if not self._decides(document, settled, built.value):
                return built
            if elected is None:
                elected, chosen = built, settled
        answer = self._stated(document, pointer, chosen, elected or first)
        if answer is not (elected or first):
            return answer
        if elected is not None and empty is not None and empty.reason:
            # **EVERY BRANCH THIS READING CAN BUILD IS ONE THE NODE'S OWN UNION REFUSES, AND
            # A BRANCH IT CANNOT BUILD IS THE ONE THE UNION WOULD HAVE ADMITTED.**  So the
            # fact to report is that branch's missing value and not the kept one's refusal:
            # ``core/signal-coverage-forecast.json`` conjoins ``dimensions.contains`` (``kind:
            # signal``) into its element, which leaves the ``oneOf``'s signal branch as the
            # only one that admits the result -- and that branch requires a ``signal_id``
            # matching ``^[a-zA-Z0-9_-]+$``, which this module does not solve.  Reporting the
            # ``oneOf`` would name the symptom at the wrong node; reporting the pattern names
            # the obstruction, and it is the obstruction ``adcp-client-python-hzio.10`` owns.
            return empty
        return answer

    def _settled(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        pick: tuple[str, int] | None = None,
    ) -> tuple[Built, tuple[tuple[str, tuple[str, ...]], ...]]:
        """The value, with every conditional the value's own content DECIDES folded in.

        ``docs/plan/rebuild-plan.md`` §8: *"a consequent is a scope of its own and not a
        conjunct -- read as a conjunct, a document's thirty consequents demand a single
        value satisfying all thirty scenarios at once, and none exists."*  So a consequent
        is folded in only where the value MATCHES its condition, which is the same
        partition the section asks of a conditional's value classes: *"a conditional's
        subject is TWO classes -- the condition matching and the condition not matching."*

        **THIS LOOP IS NOT A CAP AND HAS NO PARAMETER.**  It terminates on the node's own
        statements: an arm is folded in at most once (``taken``), so the number of rounds is
        bounded by the number of conditional arms the node states, and a round that folds
        nothing in is the last.  A value that changes its own condition's verdict is
        therefore re-asked exactly as many times as the document gives it arms to be asked
        about, and the figure is the document's rather than a budget's.

        **AND A CONSEQUENT IS REACHED EXACTLY AS A CONJUNCT IS** (:meth:`_reach`), which a
        measurement forced.  ``{"if": ..., "then": {"$ref": "#/definitions/Shared1"}}`` is
        the commonest spelling of a consequent in this bundle, and folding the position in
        WITHOUT the transparent walk reads a node whose only keyword is ``$ref`` -- so the
        ``required`` the consequent actually states is invisible and the value is built as
        though the condition had not matched.  Measured over the 1,059 document roots:
        ``core/placement.json``, ``core/transformer-param.json``,
        ``governance/check-governance-response.json`` and ``signals/get-signals-request.json``
        each built a root value their own document refuses for exactly this reason, on the
        ``required`` or the ``anyOf`` the unreached consequent states.

        It also returns the views it ENDED with, because the consequent a value selects is
        part of what the node states about that value: the keywords that decide between the
        node's alternatives (:meth:`_decides`) and its other stated cases (:meth:`_stated`)
        are both read over the settled set and not over the set before the fold.
        """
        taken: set[str] = set()
        settled = tuple(views)
        built = self._from(document, settled)
        while True:
            arms = tuple(
                arm for arm in self._arms(document, settled, built) if arm[0] not in taken
            )
            if not arms:
                return built, settled
            taken.update(at for at, _ in arms)
            fresh = tuple(v for v in self._reach(document, arms, pick) if v not in settled)
            settled = (*settled, *fresh)
            built = self._from(document, settled)
            if built.source is Source.BACK_EDGE:
                return built, settled

    def _arms(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        built: Built,
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """The consequent of each conditional this value's own content selects.

        The condition is asked in FULL -- an ``if`` is a statement about the whole instance
        and a shallow reading of it would select the wrong arm -- and that costs the ``if``
        subtree once per enclosing node, which is a sum over the document's conditions and
        not a walk per node.  :func:`codegen.keywords.conditional` names the three keywords,
        so the arms are the declared ones and not a list written here.
        """
        if not built.held:
            return ()
        out: list[tuple[str, tuple[str, ...]]] = []
        for at, path in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping) or not isinstance(node.get("if"), Mapping):
                continue
            matched = not list(
                self.validator(document).evolve(schema=node["if"]).iter_errors(built.value)
            )
            arm = "then" if matched else "else"
            if isinstance(node.get(arm), Mapping):
                out.append((f"{at}/{arm}", (*path, f"{at}/{arm}")))
        return tuple(out)

    def _stated(
        self,
        document: str,
        pointer: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        built: Built,
    ) -> Built:
        """Every OTHER case the node's own keywords state, and then its ``examples``.

        Two steps and both are the node's own statements, which is what keeps this a
        construction rather than a search.

        **The other stated cases first.**  A ``format`` names several cases
        (:data:`FORMAT_CASES`) and :func:`_string` takes the first; a sibling ``pattern``
        can refuse exactly that one -- ``{"format": "uri", "pattern":
        "^https://[^/?#@]+$"}`` is the measured shape -- and the node's own next case is
        then the answer.  Reading a pattern to TEST a candidate is not solving it: the
        screen is the document's own validator and the candidate came from the node.

        **Then ``docs/plan/final-state.md`` reading 1's ``examples``:** *"the document's own
        stated instance is the schema's statement about itself, it needs no generator, and
        it survives any transformation that preserves what the document admits."*  Screened
        exactly as a constructed value is -- an ``examples`` member the node REFUSES is an
        upstream defect to be filed and never a witness -- and where none is admitted the
        fact is approximated with the construction's own reason carried forward.

        **AND THE SCREEN HERE READS THE DECIDERS TOO** (:meth:`_decides`), which is what
        makes this the answer for a ``not`` whose own statement is an ``enum``:
        ``core/assets/vast-tracker-asset.json`` states its event's 36-member ``enum`` at one
        conjunct and ``{"not": {"enum": [...9 of them]}}`` at the next, so the first member
        is a value the document refuses and the tenth is the one it admits.  Choosing a
        LATER member of the node's own ``enum`` is a reading of the node and the exclusion
        is read off the sibling's own statement -- there is no search here and no solver.

        **A value the node's own screen admits is never DELETED by a decider.**  Where no
        stated case satisfies them, the value comes back unchanged and the composition is
        graded where a composition is graded (:meth:`document_admits`).  The approximation
        below is reached on the same condition it always was: the node's OWN keywords refuse
        the construction.
        """
        for where, _ in views:
            stated = self.node(document, where)
            if not isinstance(stated, Mapping):
                continue
            named = stated.get("format")
            for case in FORMAT_CASES.get(named, ()) if isinstance(named, str) else ():
                if not self.refusals(document, pointer, case) and not self._decides(
                    document, views, case
                ):
                    return Built(case, Source.CONSTRUCTED)
            members = stated.get("enum")
            for member in members if isinstance(members, list) else ():
                if not self.refusals(document, pointer, member) and not self._decides(
                    document, views, member
                ):
                    return Built(member, Source.CONSTRUCTED)
        for where, _ in views:
            stated = self.node(document, where)
            members = stated.get("examples") if isinstance(stated, Mapping) else None
            if not isinstance(members, list):
                continue
            for member in members:
                if not self.refusals(document, pointer, member) and not self._decides(
                    document, views, member
                ):
                    return Built(member, Source.STATED, "the node's own examples")
        if built.held:
            named = ", ".join(k for k, _ in self.refusals(document, pointer, built.value))
            if not named:
                return built
            return Built(None, Source.APPROXIMATED, f"the node refuses its construction on {named}")
        return built if built.source is Source.APPROXIMATED else Built(
            None, Source.APPROXIMATED, built.reason or "no keyword states a value"
        )

    def _views(
        self,
        document: str,
        pointer: str,
        stack: tuple[str, ...],
        pick: tuple[str, int] | None = None,
        besides: tuple[str, ...] = (),
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Every statement about THIS instance, as ``(pointer, stack)`` and never as text.

        ``docs/plan/rebuild-plan.md`` §8: *"a fixture position is every instance location
        the node decides, with its value constructed from the CONJUNCTION of every
        statement about it"* -- several conjuncts can each state part of what one location
        must satisfy, so one value for the location is the answer that cannot be empty where
        a value per conjunct is the empty intersection.

        An ``allOf`` conjunct co-describes, so **the reference under it is TRANSPARENT: the
        walk reads through it and keeps looking below.**  An ``anyOf``/``oneOf`` branch is an
        ALTERNATIVE, so ONE branch is taken -- ``pick``'s, the document's own first by
        default -- and the rest are value classes of that keyword (:meth:`classes`).
        **Nothing under ``not`` or ``if`` is read here at all**: under a restriction a
        statement WIDENS, so reading one as a conjunct would NARROW the admitted set rather
        than describe it.  A consequent is read by :meth:`_arms`, and only where the value
        matches its condition -- *"a consequent is a scope of its own and not a conjunct"*.

        ``pick`` NAMES ONE UNION AND ONE OF ITS BRANCHES, ``(pointer of the keyword,
        index)``, and every other union in the view set takes its document's own first
        branch.  **One union varied, which is what makes a branch retry a SUM and not a
        product** -- and the union it names is the one any co-describing conjunct states and
        not only the one the node states itself, which is a correction a measurement forced:
        ``core/media-buy-frequency-cap.json`` states its ``anyOf`` at ``/allOf/0`` and its
        ``not`` at ``/allOf/1``, so a retry that could only vary a union spelled at the node
        itself had exactly one reading of that node available and it is the one the document
        refuses.

        ``besides`` SEEDS the walk with the rest of the conjunction about this instance, for
        the case the walk cannot find from the pointer alone: a key described both by the
        node's own ``properties`` and by a branch's entry for the same key is one location
        with two statements, and only its parent knows both positions.
        """
        return self._reach(document, [(pointer, stack), *((at, stack) for at in besides)], pick)

    def _reach(
        self,
        document: str,
        seeds: Sequence[tuple[str, tuple[str, ...]]],
        pick: tuple[str, int] | None = None,
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """The transparent walk itself, from any set of positions describing one instance.

        **ONE walk, shared by :meth:`_views` and by :meth:`_settled`'s fold of a
        consequent**, because a consequent states what it states through a ``$ref`` and an
        ``allOf`` exactly as a conjunct does.  Two spellings of this walk is two readings of
        draft-07's composition grammar, and the one that was missing read a ``{"$ref": ...}``
        consequent as a node stating nothing.
        """
        out: list[tuple[str, tuple[str, ...]]] = []
        pending = list(seeds)
        while pending:
            at, path = pending.pop(0)
            if (at, path) in out:
                continue
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            ref = node.get("$ref")
            if isinstance(ref, str):
                target = _local(ref)
                if target is not None and target not in path:
                    pending.append((target, (*path, target)))
                continue
            out.append((at, path))
            for keyword, suffix, _, _ in bundle.subschemas(node):
                if keyword == "allOf":
                    pending.append((f"{at}{suffix}", (*path, f"{at}{suffix}")))
                elif keyword in ("anyOf", "oneOf"):
                    union = f"{at}/{keyword}"
                    index = pick[1] if pick is not None and pick[0] == union else 0
                    if suffix == f"/{keyword}/{index}":
                        pending.append((f"{at}{suffix}", (*path, f"{at}{suffix}")))
        return tuple(out)

    def _picks(
        self, document: str, views: Sequence[tuple[str, tuple[str, ...]]]
    ) -> tuple[tuple[str, int], ...]:
        """Which union to vary and in what order -- the document's own branch order.

        ONE union, the first the view set states, with ``oneOf`` before ``anyOf`` at one
        position because an exclusive alternation is the stronger statement.  The retry is a
        SUM over that keyword's branches: ``oneOf`` admits an instance through EXACTLY one
        branch, so a value merged from the first branch and the node's own statements can be
        one a LATER branch also admits -- which the ``oneOf`` refuses, for a reason that is
        the construction's and not the subject's.

        The second union in a view set is NOT varied, and that is the product this refuses to
        pay: ``docs/plan/architecture.md`` §9 calls a cross-product over the unions in a
        subtree a defect of the approach rather than a cost to control.
        """
        for at, _ in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            for keyword in ("oneOf", "anyOf"):
                members = node.get(keyword)
                if isinstance(members, list) and len(members) > 1:
                    return tuple((f"{at}/{keyword}", i) for i in range(len(members)))
        return ()

    def _decides(
        self, document: str, views: Sequence[tuple[str, tuple[str, ...]]], value: Any
    ) -> tuple[str, ...]:
        """The keywords that decide BETWEEN this node's alternatives, and refuse this value.

        ``oneOf``, ``anyOf`` and ``not``: the three the shallow screen strikes
        (:data:`STRUCK`) and the three no child can answer for, because each is a statement
        about how the node's OWN alternatives relate to one another.  A ``oneOf`` branch
        cannot know it must exclude its siblings, and a ``not``'s subject is the instance at
        the node that states it -- so a value read off the positive keywords alone has
        consulted neither.

        **THIS IS NOT THE SHALLOW SCREEN AND IT IS NOT THE WHOLE DOCUMENT.**  It ranges over
        exactly the three keywords, at exactly the positions this node's own view set states
        them, which is what keeps §9's linearity: the 215,019 schema positions of this
        bundle state a ``oneOf`` at 2,243 of them, an ``anyOf`` at 4,996 and a ``not`` at
        3,984, so the cost is one validation at one node in twenty and never a walk per node.
        ``if`` is absent on purpose: :meth:`_arms` folds the arm the value selects into the
        view set, so a conditional is READ rather than screened.
        """
        out: list[str] = []
        for at, _ in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            stated = {k: node[k] for k in ("oneOf", "anyOf", "not") if k in node}
            if not stated:
                continue
            out.extend(
                error.validator
                for error in self.validator(document).evolve(schema=stated).iter_errors(value)
                if isinstance(error.validator, str)
            )
        return tuple(out)

    def _from(
        self, document: str, views: Sequence[tuple[str, tuple[str, ...]]]
    ) -> Built:
        """The value the merged statements name, by the ``type`` word they agree on."""
        nodes = [self.node(document, at) for at, _ in views]
        nodes = [n for n in nodes if isinstance(n, Mapping)]
        if not nodes:
            return Built(None, Source.CONSTRUCTED)
        for node in nodes:
            if "const" in node:
                return Built(node["const"], Source.CONSTRUCTED)
        for node in nodes:
            members = node.get("enum")
            if isinstance(members, list) and members:
                return Built(members[0], Source.CONSTRUCTED)
        words = _words(nodes) or _implied(nodes)
        if not words:
            return Built(None, Source.CONSTRUCTED)
        word = words[0]
        if word == "object":
            return self._object(document, views, nodes)
        if word == "array":
            return self._array(document, views, nodes)
        if word == "string":
            return _string(nodes)
        if word in ("integer", "number"):
            return _number(nodes, whole=word == "integer")
        return Built(WORD_FLOOR[word], Source.CONSTRUCTED)

    def _object(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        nodes: Sequence[Mapping[str, Any]],
    ) -> Built:
        """An object over the REQUIRED subset, and no key the document does not demand.

        A key several statements describe gets ONE value built from all of them, which is
        what hands the other describing pointers to :meth:`value` as ``besides`` AND puts
        them on the stack: *"grouping by the pointer instead hands the same location two
        independent pins, and two pins on one location do not narrow the node -- they empty
        it."*

        **THE REST OF THE CONJUNCTION USED TO TRAVEL ON THE STACK ALONE, WHICH IS A KEY AND
        NOT A READING, AND THAT WAS THIS ROW'S LARGEST CAUSE.**  The stack distinguished the
        answer; nothing read the positions it carried, so the value for a key described
        twice was built from the FIRST position and the second was discarded.  The second is
        where the discriminator lives: measured over the 1,059 document roots, a ``status``
        declared by the envelope's ``enum`` and by a ``oneOf`` branch's ``const`` took the
        enum's first member and so satisfied NO branch of the ``oneOf``, which is nine of
        the sixteen roots ``adcp-client-python-hzio.11`` names -- and the same omission is
        the ``const`` at ``core/warning.json``, the ``enum`` at
        ``core/macro-translation-target.json`` and the ``minProperties`` at
        ``core/package-delivery-metric-value.json``.

        ``minProperties`` then demands keys the
        ``properties`` table may not name, and where ``propertyNames`` or
        ``patternProperties`` is what admits them the construction stops: a key matching a
        pattern is a regex to solve and there is no solver here.
        """
        placed: dict[str, Any] = {}
        demanded = _required(nodes)
        for name in _dependent(nodes, demanded):
            demanded = (*demanded, name) if name not in demanded else demanded
        for name in demanded:
            where = [
                (f"{at}/properties/{bundle.escape_key(name)}", path)
                for at, path in views
                if isinstance(self.node(document, at), Mapping)
                and name in (self.node(document, at).get("properties") or {})
            ]
            if not where:
                if _closed(nodes):
                    return Built(
                        None,
                        Source.APPROXIMATED,
                        f"required names {name!r}, which additionalProperties forbids",
                    )
                placed[name] = None
                continue
            at, path = where[0]
            besides = tuple(p for p, _ in where[1:])
            inner = self.value(document, at, (*path, *besides), besides)
            if inner.source is Source.BACK_EDGE:
                self.counters.floored += 1
                inner = self.floor(document, inner.target)
            if not inner.held:
                return Built(
                    None,
                    Source.APPROXIMATED,
                    f"required {name!r} has no value: {inner.reason}",
                )
            placed[name] = inner.value
        least = _bound(nodes, "minProperties")
        if isinstance(least, int) and len(placed) < least:
            spare = self._spare(document, views, placed, least - len(placed))
            if not spare.held:
                return spare
            placed.update(spare.value)
        return Built(placed, Source.CONSTRUCTED)

    def _spare(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        placed: Mapping[str, Any],
        wanted: int,
    ) -> Built:
        """The keys ``minProperties`` demands beyond the required ones.

        A declared ``properties`` entry first, because a key the document NAMES is a key
        the construction can reach.  Failing that the key is a free choice and the
        construction makes one -- ``docs/plan/rebuild-plan.md`` §8 says exactly that of a
        mapping value -- unless ``propertyNames`` or ``patternProperties`` is what decides
        which names are admitted, where the choice is a regex to solve.
        """
        extra: dict[str, Any] = {}
        for at, path in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            for name in node.get("properties") or {}:
                if len(extra) >= wanted:
                    break
                if name in placed or name in extra:
                    continue
                inner = self.value(document, f"{at}/properties/{bundle.escape_key(name)}", path)
                if inner.held:
                    extra[name] = inner.value
        if len(extra) >= wanted:
            return Built(extra, Source.CONSTRUCTED)
        for node in [self.node(document, at) for at, _ in views]:
            if not isinstance(node, Mapping):
                continue
            if "propertyNames" in node or "patternProperties" in node:
                return Built(
                    None,
                    Source.APPROXIMATED,
                    "minProperties needs a key only an unsolved pattern admits",
                )
            if node.get("additionalProperties") is False:
                return Built(
                    None,
                    Source.APPROXIMATED,
                    "minProperties needs a key additionalProperties forbids",
                )
        for at, path in views:
            node = self.node(document, at)
            sub = node.get("additionalProperties") if isinstance(node, Mapping) else None
            while len(extra) < wanted:
                name = f"k{len(extra)}"
                if isinstance(sub, Mapping):
                    inner = self.value(document, f"{at}/additionalProperties", path)
                    if not inner.held:
                        return Built(None, Source.APPROXIMATED, f"a mapping value: {inner.reason}")
                    extra[name] = inner.value
                else:
                    extra[name] = None
            break
        if len(extra) < wanted:
            return Built(None, Source.APPROXIMATED, "minProperties names no reachable key")
        return Built(extra, Source.CONSTRUCTED)

    def _array(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        nodes: Sequence[Mapping[str, Any]],
    ) -> Built:
        """Exactly as many items as the count bound demands, each the element's own value.

        One element value, reused -- the element is one node and its value is built once,
        which is the array's half of "no subtree is constructed twice".  ``uniqueItems``
        beside a count above one is where that stops: distinct members need distinct
        values, and where the element states an ``enum`` its members are the distinct ones
        and otherwise the construction says so.

        **THE ELEMENT IS DESCRIBED BY EVERY VIEW THAT DECLARES IT, and a ``contains`` beside
        an ``items`` describes it too** -- so both travel as ``besides`` and the member is
        built from the conjunction.  ``core/signal-coverage-forecast.json`` is the measured
        shape: one conjunct declares ``dimensions.items`` and the next states
        ``dimensions.contains``, and a member built from ``items`` alone leaves the
        ``contains`` with nothing to find -- so the document refused the array on
        ``contains`` and the construction had reported nothing.  Where that conjunction
        admits no value the array has none either, with the conjunction's own reason
        carried: an array whose ``contains`` no member can satisfy admits no instance, and
        saying so is the answer rather than an array the document refuses.
        """
        least = _bound(nodes, "minItems")
        count = int(least) if isinstance(least, (int, float)) else 0
        tuples = [
            (f"{at}/items", path, node["items"])
            for at, path in views
            for node in [self.node(document, at)]
            if isinstance(node, Mapping) and isinstance(node.get("items"), list)
        ]
        if tuples:
            at, path, members = tuples[0]
            out = []
            for index in range(len(members)):
                inner = self.value(document, f"{at}/{index}", path)
                if not inner.held:
                    return Built(None, Source.APPROXIMATED, f"a tuple member: {inner.reason}")
                out.append(inner.value)
            return Built(out, Source.CONSTRUCTED)
        wanted = [
            (f"{at}/contains", path)
            for at, path in views
            for node in [self.node(document, at)]
            if isinstance(node, Mapping) and isinstance(node.get("contains"), Mapping)
        ]
        element = [
            (f"{at}/items", path)
            for at, path in views
            for node in [self.node(document, at)]
            if isinstance(node, Mapping) and isinstance(node.get("items"), Mapping)
        ]
        if wanted:
            count = max(count, 1)
        if not element:
            if not wanted:
                return Built([None] * count, Source.CONSTRUCTED)
            at, path = wanted[0]
            besides = tuple(p for p, _ in wanted[1:])
        else:
            at, path = element[0]
            besides = tuple(p for p, _ in (*element[1:], *wanted))
        if count == 0:
            return Built([], Source.CONSTRUCTED)
        inner = self.value(document, at, (*path, *besides), besides)
        if inner.source is Source.BACK_EDGE:
            if count == 0:
                return Built([], Source.CONSTRUCTED)
            self.counters.floored += 1
            inner = self.floor(document, inner.target)
        if not inner.held:
            return Built(None, Source.APPROXIMATED, f"an element: {inner.reason}")
        if count > 1 and any(node.get("uniqueItems") is True for node in nodes):
            return self._distinct(document, at, path, count)
        return Built([inner.value] * count, Source.CONSTRUCTED)

    def _distinct(
        self, document: str, at: str, path: tuple[str, ...], count: int
    ) -> Built:
        """``count`` distinct members, where the element's own keywords name that many."""
        node = self.node(document, at)
        members = node.get("enum") if isinstance(node, Mapping) else None
        if isinstance(members, list) and len(members) >= count:
            return Built(list(members[:count]), Source.CONSTRUCTED)
        classes = self.classes(document, at, path)
        values: list[Any] = []
        for case in classes:
            if case.value not in values:
                values.append(case.value)
        if len(values) >= count:
            return Built(values[:count], Source.CONSTRUCTED)
        return Built(
            None,
            Source.APPROXIMATED,
            f"uniqueItems demands {count} members and the element states {len(values)}",
        )

    # -- the screen -------------------------------------------------------- #
    def refusals(
        self, document: str, pointer: str, value: Any
    ) -> tuple[tuple[str, tuple[Any, ...]], ...]:
        """Which of the node's OWN keywords refuse this value, and WHERE.

        ``(keyword, instance location)`` per refusal, because §9 asks the second check to
        read a refusal *"at its location and against its cause"*: a subject that refuses
        for some other reason has not been shown to carry the keyword at all, so a boolean
        is not the answer this needs.

        **The node's own statements and not its subtree**, which is §9's linearity rule
        applied to the screen: every child's value was screened at the child, so
        re-validating every subtree at every ancestor pays the sum of every subtree.
        :meth:`document_admits` is the whole-document reading and is taken once per
        document.
        """
        self.counters.screened += 1
        node = self.node(document, pointer)
        if not isinstance(node, Mapping):
            return ()
        own = _own(node)
        if not own:
            return ()
        found = [
            (error.validator, tuple(error.absolute_path))
            for error in self.validator(document).evolve(schema=own).iter_errors(value)
            if isinstance(error.validator, str)
        ]
        if found:
            self.counters.refused += 1
        return tuple(found)

    def document_admits(self, document: str, value: Any) -> tuple[str, ...]:
        """Which keywords the WHOLE document refuses a root value on, over its whole tree.

        One walk of one instance per document, which is why this is here and not inside
        :meth:`refusals`: the shallow screen is per node and this is per document, so
        neither multiplies the other.
        """
        return tuple(
            sorted(
                {
                    error.validator
                    for error in self.validator(document).iter_errors(value)
                    if isinstance(error.validator, str)
                }
            )
        )

    # -- coverage by constraint class --------------------------------------- #
    def classes(
        self, document: str, pointer: str = "", stack: tuple[str, ...] = ()
    ) -> tuple[Class, ...]:
        """Every value class the node's own keywords distinguish, all of them ADMITTED.

        ``docs/plan/rebuild-plan.md`` §8: *"for each keyword the node states, the
        construction takes the classes that keyword distinguishes -- every member of an
        ``enum``, both sides of each bound and the bound itself, and for a ``format`` every
        case the format's own checker admits rather than the case a generator finds most
        likely."*  That is what makes "never tighter" a claim about every value the
        document admits rather than about the values something happened to produce.

        Every class is SCREENED against the node before it is offered, so a class the
        document does not in fact admit -- a bound an exclusive sibling excludes, a branch
        a conjunct refuses -- is not handed to a subject as though the document stood
        behind it.
        """
        built = self.value(document, pointer, stack)
        node = self.node(document, pointer)
        if not isinstance(node, Mapping):
            return ()
        out: list[Class] = []
        if built.held:
            out.append(Class("", "the admitted value", built.value))
        nodes = [
            node
            for at, _ in self._views(document, pointer, stack)
            for node in [self.node(document, at)]
            if isinstance(node, Mapping)
        ]
        out.extend(_value_classes(nodes))
        for keyword, cases in _bound_classes(nodes, built).items():
            out.extend(Class(keyword, label, value) for label, value in cases)
        out.extend(self._branch_classes(document, pointer, stack))
        return tuple(
            case for case in out if not self.refusals(document, pointer, case.value)
        )

    def _branch_classes(
        self, document: str, pointer: str, stack: tuple[str, ...]
    ) -> tuple[Class, ...]:
        """One class per branch of a union, and one per arm of a type list.

        A union branch is an ALTERNATIVE, so each branch is a class of the keyword rather
        than a conjunct of it -- which is the same reading :meth:`_views` makes when it
        takes the first branch and leaves the rest to here.
        """
        node = self.node(document, pointer)
        if not isinstance(node, Mapping):
            return ()
        out: list[Class] = []
        for keyword in ("anyOf", "oneOf"):
            members = node.get(keyword)
            if not isinstance(members, list):
                continue
            for index in range(len(members)):
                at = f"{pointer}/{keyword}/{index}"
                inner = self.value(document, at, (*stack, at))
                if inner.held:
                    out.append(Class(keyword, f"branch {index}", inner.value))
        words = node.get("type")
        if isinstance(words, list):
            for word in words:
                if not isinstance(word, str) or word in _CONTAINERS:
                    continue
                arm = {k: v for k, v in node.items() if k in keywords.ARM.get(word, ())}
                built = _from_word(word, [{**arm, "type": word}])
                if built.held:
                    out.append(Class("type", f"the {word} arm", built.value))
        return tuple(out)

    # -- the mutations ------------------------------------------------------ #
    def mutations(
        self, document: str, pointer: str = "", stack: tuple[str, ...] = ()
    ) -> tuple[Mutation, ...]:
        """ONE violation per keyword the node states, each one the DOCUMENT refuses.

        ``docs/plan/architecture.md`` §9: the invalid set is *"one violation per keyword the
        node states -- a required key dropped, a type replaced, a value outside an
        ``enum``, a bound exceeded by one"*, and the count is a SUM: a node stating ``k``
        keywords owes ``k`` mutations and one admitted value, never a product.

        **ONE KEYWORD AT A TIME, which is the whole design.**  A mutation that violates two
        keywords proves nothing about either, so each one changes exactly one stated fact
        and the rest of the value is the admitted one -- **and the DOCUMENT is who says
        whether it succeeded.**  The surviving set is the one where the document names
        EXACTLY the targeted keyword, which is a stricter reading than "the keyword is among
        the reasons" and it is stricter on purpose: measured over this bundle, 23,506 of
        196,544 candidates are refused on the targeted keyword AND on another, and 14,233 of
        those are a ``type`` mutation at a node that also states an ``enum`` -- where no
        isolating mutation of ``type`` exists at all, because every value of another type is
        also outside the enum.  Offering one would be offering a mutation that proves nothing
        about either keyword.

        **AND EVERY MUTATION IS OFFERED TO THE DOCUMENT FIRST.**  A mutation the document
        still admits is a defect in the MUTATION and not a failure of the subject, so it is
        discarded here -- counted on :attr:`Counters.discarded` and named on
        :attr:`Counters.discards`, because a silent discard is a check that did not run.
        The surviving ones carry the keyword the document named and the location it named
        it at, which is what lets the second check read a refusal against its cause.
        """
        built = self.value(document, pointer, stack)
        if not built.held:
            return ()
        node = self.node(document, pointer)
        if not isinstance(node, Mapping):
            return ()
        out: list[Mutation] = []
        for keyword, label, candidate, location in _candidates(node, built.value):
            self.counters.mutations += 1
            found = self.refusals(document, pointer, candidate)
            named = [where for name, where in found if name == keyword]
            if not named:
                self.counters.discarded += 1
                self.counters.discards[f"{keyword}: the document admits it"] += 1
                continue
            beside = sorted({name for name, _ in found} - {keyword})
            if beside:
                self.counters.discarded += 1
                self.counters.discards[f"{keyword}: not isolated, also {beside[0]}"] += 1
                continue
            out.append(Mutation(keyword, label, candidate, named[0]))
            if named[0] != location:
                # The document named a different location than the change was made at,
                # which is the document's answer and not ours: the mutation carries what
                # the document said, so the subject is asked about the same place.
                self.counters.discards[f"{keyword} (relocated)"] += 1
        return tuple(out)


# --------------------------------------------------------------------------- #
# the readings that need no memo
# --------------------------------------------------------------------------- #
def _local(ref: str) -> str | None:
    """The record-relative pointer a ``$ref`` names, or ``None`` where it names none.

    A record is self-contained -- ``codegen.bundle.record`` inlines every cross-document
    reference -- so what is left is a fragment of the record itself, and anything else is a
    reference the record could not resolve.
    """
    if ref == "#":
        return ""
    if ref.startswith("#/"):
        return ref[1:]
    return None


def _required(nodes: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """The keys every co-describing statement demands: a UNION, in first-stated order.

    A union and not an intersection, because two statements about one instance both hold
    and a key either of them requires is a key the instance must carry.
    """
    out: list[str] = []
    for node in nodes:
        names = node.get("required")
        if not isinstance(names, list):
            continue
        for name in names:
            if isinstance(name, str) and name not in out:
                out.append(name)
    return tuple(out)


def _dependent(nodes: Sequence[Mapping[str, Any]], placed: Sequence[str]) -> tuple[str, ...]:
    """The keys a ``dependencies`` entry demands once a placed key triggers it.

    The required-keys form only.  A schema-valued entry is a node of its own, graded there,
    and conjoining it here would be reading a consequent as a conjunct.
    """
    out: list[str] = []
    for node in nodes:
        table = node.get("dependencies")
        if not isinstance(table, Mapping):
            continue
        for key, demanded in table.items():
            if key not in placed or not isinstance(demanded, list):
                continue
            for name in demanded:
                if isinstance(name, str) and name not in placed and name not in out:
                    out.append(name)
    return tuple(out)


def _closed(nodes: Sequence[Mapping[str, Any]]) -> bool:
    """Does any statement forbid a key its ``properties`` does not name."""
    return any(node.get("additionalProperties") is False for node in nodes)


def _own(node: Mapping[str, Any]) -> dict[str, Any]:
    """The node's OWN statements: what it says about the instance at its own location.

    Every keyword that holds a subschema is struck (:data:`STRUCK`), because what it holds
    is a node of its own whose value was screened there -- and that is what keeps the
    screen linear.  :data:`CLOSES_ITS_LOCATION`'s two are kept in their NON-descending
    spelling, so ``additionalProperties: false`` still closes the mapping and a
    ``dependencies`` list still demands its keys, while neither pulls a subtree in.

    **AND A CLOSURE CARRIES THE KEY NAMES IT CLOSES OVER, which is a correction a
    measurement forced.**  ``additionalProperties: false`` beside a struck ``properties``
    does not mean "the declared keys and no others" -- it means NO KEY AT ALL, because the
    keyword's own reading is relative to the names its siblings declare.  Striking the
    siblings and keeping the closure reported 7,689 nodes as refusing their own
    construction, every one of them a defect in this reading rather than in the value.  So
    the names come with it, as ``true`` -- a schema that admits anything, which is exactly
    "this key is declared and what it holds is screened at its own node".

    **``not``, ``if``, ``then`` AND ``else`` ARE STRUCK, and the alternative was measured.**
    They are the node's own statements in one sense, and §9's rule is "no check ranges over
    more than one node's own statements" in another, so the question is empirical: keeping
    all four whole in the screen moved 2,395 nodes from a constructed value to an
    approximation, took the shallow screen's refusals from 174 to 4,279, and left the
    document-level reading exactly where it was -- 835 roots admitted either way.  A
    restriction read at a PARENT asks the parent's own minimal value to satisfy a
    consequent's whole subtree, which is the subtree the consequent's own node is graded on.
    So they are struck here, :meth:`Construction._arms` is what folds the matching
    consequent into the value, and :meth:`Construction.document_admits` is where a
    conditional and a ``not`` are read -- once per document, over one instance.
    """
    out = {}
    for key, value in node.items():
        if key not in STRUCK:
            out[key] = value
        elif key in CLOSES_ITS_LOCATION:
            kept = _non_descending(key, value)
            if kept is not None:
                out[key] = kept
    if out.get("additionalProperties") is False:
        for key in ("properties", "patternProperties"):
            declared = node.get(key)
            if isinstance(declared, Mapping):
                out[key] = dict.fromkeys(declared, True)
    return out


def _non_descending(keyword: str, value: Any) -> Any:
    """The part of a descending keyword's value that states a fact about THIS location."""
    if keyword == "additionalProperties":
        return False if value is False else None
    if keyword == "dependencies" and isinstance(value, Mapping):
        kept = {k: v for k, v in value.items() if isinstance(v, list)}
        return kept or None
    return None


def _from_word(word: str, nodes: Sequence[Mapping[str, Any]]) -> Built:
    """One scalar word's own value, for a reader that has the word and not the walk."""
    if word == "string":
        return _string(nodes)
    if word in ("integer", "number"):
        return _number(nodes, whole=word == "integer")
    return Built(WORD_FLOOR.get(word), Source.CONSTRUCTED)


def _value_classes(nodes: Sequence[Mapping[str, Any]]) -> tuple[Class, ...]:
    """Every member of an ``enum``, every stated case of a ``format``, and a ``const``."""
    out: list[Class] = []
    for node in nodes:
        if "const" in node:
            out.append(Class("const", "the stated constant", node["const"]))
        members = node.get("enum")
        if isinstance(members, list):
            out.extend(
                Class("enum", f"member {index}", member) for index, member in enumerate(members)
            )
        named = node.get("format")
        if isinstance(named, str):
            out.extend(
                Class("format", f"{named} case {index}", case)
                for index, case in enumerate(FORMAT_CASES.get(named, ()))
            )
    return tuple(out)


def _bound_classes(
    nodes: Sequence[Mapping[str, Any]], built: Built
) -> dict[str, list[tuple[str, Any]]]:
    """**Both sides of each bound and the bound itself**, as values the document ADMITS.

    An inclusive bound admits an instance AT it, so the bound itself is a class; an
    exclusive one does not (:data:`codegen.keywords.EXCLUSIVE`), so its classes are the step
    in and nothing at it.  The side OUTSIDE the bound is not a class at all -- it is the
    bound's mutation (:func:`_candidates`).
    """
    out: dict[str, list[tuple[str, Any]]] = {}
    for node in nodes:
        for keyword in keywords.FLOORS | keywords.CEILINGS:
            stated = node.get(keyword)
            if not isinstance(stated, (int, float)) or isinstance(stated, bool):
                continue
            step = -1 if keyword in keywords.CEILINGS else 1
            inside = stated + step if keyword in keywords.EXCLUSIVE else stated
            cases = [("at the bound", _shaped(keyword, inside, built))]
            further = inside + step
            if keywords.range_of(keyword) == ("minimum", "maximum") or further >= 0:
                cases.append(("inside the bound", _shaped(keyword, further, built)))
            out.setdefault(keyword, []).extend(
                (label, value) for label, value in cases if value is not None
            )
    return out


def _shaped(keyword: str, size: float, built: Built) -> Any:
    """A value of the admitted value's own shape, sized to a bound.

    A bound on a LENGTH or a COUNT is a statement about a container, so the class is the
    container resized; a bound on a NUMBER is a statement about the value itself.
    """
    if keyword in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
        return size
    if keyword in ("minLength", "maxLength"):
        return "a" * int(size) if isinstance(built.value, str) else None
    if keyword in ("minItems", "maxItems"):
        if not isinstance(built.value, list):
            return None
        filler = built.value[0] if built.value else None
        return [filler] * int(size)
    if keyword in ("minProperties", "maxProperties") and isinstance(built.value, dict):
        if len(built.value) >= size:
            return dict(list(built.value.items())[: int(size)])
        extra = {f"k{i}": None for i in range(int(size) - len(built.value))}
        return {**built.value, **extra}
    return None


#: The value each ``type`` word is replaced BY when ``type`` is the keyword under mutation
#: -- a value of a word the node does NOT admit, which is what a type mutation is.  Read in
#: order, so the first word the node does not state is the one taken.
_OTHER_WORD: tuple[tuple[str, Any], ...] = (
    ("string", "not of the stated type"),
    ("integer", -987654321),
    ("boolean", False),
    ("array", []),
    ("object", {}),
    ("null", None),
)


def _candidates(
    node: Mapping[str, Any], value: Any
) -> tuple[tuple[str, str, Any, tuple[Any, ...]], ...]:
    """One candidate mutation per keyword the node states, as ``(keyword, label, value,
    location)``.

    **Derived, never hand-written** -- ``docs/plan/architecture.md`` §9's own list: a
    required key dropped, a type replaced, a value outside an ``enum``, a bound exceeded by
    one, a ``const`` changed.  Each one changes exactly ONE stated fact of the admitted
    value, and the location is where the change was made.
    """
    out: list[tuple[str, str, Any, tuple[Any, ...]]] = []
    if "const" in node:
        out.append(("const", "the constant changed", _unlike(node["const"]), ()))
    members = node.get("enum")
    if isinstance(members, list) and members:
        out.append(("enum", "outside the enum", _outside(members), ()))
    words = node.get("type")
    stated = {words} if isinstance(words, str) else set(words or ())
    if stated:
        for word, other in _OTHER_WORD:
            if word not in stated:
                out.append(("type", f"a {word} where the type is {sorted(stated)}", other, ()))
                break
    names = node.get("required")
    if isinstance(names, list) and isinstance(value, dict):
        for name in names:
            if isinstance(name, str) and name in value:
                out.append(
                    ("required", f"{name!r} dropped", {k: v for k, v in value.items() if k != name}, ())
                )
                break
    for keyword in keywords.FLOORS | keywords.CEILINGS:
        bound = node.get(keyword)
        if not isinstance(bound, (int, float)) or isinstance(bound, bool):
            continue
        step = 1 if keyword in keywords.CEILINGS else -1
        over = bound + step if keyword not in keywords.EXCLUSIVE else bound
        beyond = _shaped(keyword, over, Built(value, Source.CONSTRUCTED))
        if beyond is not None:
            out.append((keyword, "exceeded by one", beyond, ()))
    pattern = node.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str):
        out.append(("pattern", "a string the pattern refuses", "\x00 not a match \x00", ()))
    named = node.get("format")
    if isinstance(named, str) and isinstance(value, str):
        out.append(("format", f"a string {named} refuses", "\x00 not a format \x00", ()))
    if node.get("uniqueItems") is True and isinstance(value, list) and value:
        out.append(("uniqueItems", "a repeated member", [value[0], value[0]], ()))
    if node.get("additionalProperties") is False and isinstance(value, dict):
        out.append(
            ("additionalProperties", "an undeclared key", {**value, "\x00undeclared": None}, ())
        )
    multiple = node.get("multipleOf")
    if isinstance(multiple, (int, float)) and multiple > 1 and isinstance(value, (int, float)):
        out.append(("multipleOf", "not a multiple", value + multiple / 2, ()))
    return tuple(out)


def _unlike(value: Any) -> Any:
    """A value of the same JSON type that is not this one, so only ``const`` is violated."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return f"{value}\x00"
    if isinstance(value, (int, float)):
        return value + 1
    if isinstance(value, list):
        return [*value, None]
    if isinstance(value, dict):
        return {**value, "\x00": None}
    return "not the constant"


def _outside(members: Sequence[Any]) -> Any:
    """A value no member of the ``enum`` equals, of the first member's own JSON type."""
    first = members[0]
    if isinstance(first, bool):
        spare = [m for m in (True, False) if m not in members]
        return spare[0] if spare else "not a member"
    if isinstance(first, str):
        candidate = "\x00"
        while candidate in members:
            candidate += "\x00"
        return candidate
    if isinstance(first, (int, float)):
        return max(m for m in members if isinstance(m, (int, float))) + 1
    return "not a member"
