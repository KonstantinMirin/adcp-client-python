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

**A ``pattern`` OF FIVE CONSTRUCTS IS READ AND EVERY OTHER PATTERN IS LEFT UNREAD.**  An
anchor, a literal run, a character class, a quantifier and a GROUP are keywords the way
``minLength`` is a keyword, and the reading is the same reading: the class's FIRST member
repeated the quantifier's MINIMUM count, exactly as ``minLength: 3`` gives ``"aaa"``
(:func:`_atoms`, :func:`_patterned`).  ``^[A-Z]{3}$`` gives ``"AAA"`` and
``^sha256:[a-f0-9]{64}$`` gives ``"sha256:"`` and sixty-four ``"a"``\\ s.  **A PARENTHESIS
PLAYS ONE OF TWO ROLES AND THAT IS THE ONLY SIXTH THING HERE**: its contents are either
CONSUMED, which is a group, or ASSERTED of the characters after it, which is a positive
lookahead -- the five constructs read the contents either way (:func:`_opens`).

**A GROUP IS THE QUANTIFIER'S MINIMUM TOO** (:func:`_group`).  A group followed by ``?`` or
``*`` is taken ZERO times and contributes NOTHING; a group followed by ``+``, or by no
quantifier at all, is taken ONCE and its contents read by these same rules, recursively.
That is the same reading ``*`` on a character class already gets, applied to a construct
that holds a sequence instead of a member, so
``^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$`` gives ``"a"`` and the
``+`` spelling of its tail gives ``"a.a"``.  An ALTERNATION inside a group is read by taking
its FIRST ARM, and every other arm is read too (:func:`_group` carries why that is a reading
and not a choice between arms).

**A POSITIVE LOOKAHEAD IS SATISFIED AND NEVER SOLVED, AND THAT DISTINCTION IS THE WHOLE OF
IT** (:func:`_opens`, :func:`_asserts`).  A lookahead is an assertion AT a position, not a
construct that consumes text, so no new construct has to be read: its body is parsed by the
same arms a group's is (:func:`_arms`) and read into the string the BODY ITSELF admits, and
the characters after the position are required to begin with that string
(:func:`_demanded`).  Where a class emits one of those characters, the assertion's class and
the document's class are two statements about ONE character and the reading takes what both
admit (:func:`_both`, :func:`_asserted`) -- the same conjunction :func:`_bound` already
makes of two ``minLength``\\ s; where the character would come from a construct the minimum
reading takes none of, the assertion raises that quantifier's minimum inside the range it
already admits, which is the move :func:`_patterned` already makes for a ``minLength``.  So
``^P(?=.*[1-9])(?=\\d|T)(?:\\d+Y)?...$`` gives ``"P1Y"``: nothing worked backwards from what
the two lookaheads demand, and nothing generated a candidate and tested it.

**A COMPLEMENT CLASS NAMES WHAT IT EXCLUDES, SO THE READING IS THE FIRST CHARACTER THIS
READER NAMES THAT THE DOCUMENT DOES NOT EXCLUDE** (:data:`_VOCABULARY`, :func:`_unless`).
``[^...]``, ``\\S``, ``\\D`` and ``.`` state no members of their own and leave them to the
dialect, whose answer is every codepoint of the plane -- which is not a set a *document's
own first* can be taken from.  It does not have to be: :data:`_CLASS_ESCAPE` is the one
statement this module already makes about which characters it names, so its members in its
own order are the vocabulary a value is written from, and a complement is read by striking
what the document excludes from it.  ``^[^\\u0000-\\u001F\\u007F]+$`` gives ``"0"``, ``\\S``
gives ``"0"``, ``\\D`` gives ``"a"``.  That reading is NARROWER than the class the document
states and narrow is the sound direction -- every character it can produce is one the class
admits -- so the only cost is a complement that excludes the whole vocabulary, which is
DECLINED BY NAME.  Taking the plane's own first codepoint instead would put a constant here
and a NUL in a witness; taking a printable range would be this reader's literal.

**THIS IS NOT A REGEX ENGINE AND MUST NOT BECOME ONE**: there is no backtracking, no
candidate generation, no negative lookaround, no lookbehind, no backreference, no
alternation outside a group and no class subtraction here, and a pattern stating any of them
is NOT ATTEMPTED -- the document's own ``examples`` is the value and failing that the fact
is approximated with the pattern QUOTED (:func:`_atoms` names the construct it stopped at).
**THE DECLINED LOOKAROUNDS ARE DECLINED BY NAME** rather than left to fall out of a group's
parse (:func:`_opens`): ``(?!`` and ``(?<!`` state what the text must NOT be, and the first
string that is not something is a choice no vocabulary answers; ``(?<=`` states it of
characters the reading has already emitted.  An assertion whose demands no construct after
it reaches is declined too (:func:`_sequence`), so the stop stays honest and is never
replaced by a cap or a literal.  Measured over bundle 3.2: 107 of 110 distinct patterns and
7,488 of 7,638 pattern-bearing positions are of the read shape; the 3 that are not are TWO
negative lookaheads and one anchor inside a group's arm.

**WHERE CONSTRUCTION CANNOT REACH, THE DOCUMENT'S OWN ``examples`` IS THE VALUE**, and
failing that the fact is approximated with the reason named (:attr:`Source.APPROXIMATED`,
:attr:`Built.reason`).  A ``pattern`` of an unread shape and a ``format`` nothing can state
are the two cases, and **this module builds no generator for either** -- not a regex
engine, not a format generator.  Refusing to build one is the decision, not an omission:
``docs/plan/final-state.md`` reading 1 says a document that states no example and admits
no value construction can produce "is an ask over a set of the bundle".

**AND THE VALUE THE READING PRODUCES IS CHECKED BY THE DOCUMENT'S OWN CHECKER BEFORE IT IS
USED**, never by the reader's belief about what it produced: :meth:`Construction.refusals`
offers it to the node's own statements -- the ``pattern`` itself, and every ``minLength``,
``maxLength`` and ``format`` beside it -- and a value the node refuses is not kept.  A
reader returning a string its own pattern refuses is therefore a defect this module's own
screen catches, which is why the reading may be as small as it is.

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
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, NamedTuple

import jsonschema
import referencing.exceptions
from jsonschema import _utils as _jsonschema_utils

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


# --------------------------------------------------------------------------- #
# the document's validator: one per document, no message nobody reads, and the
# resolution amortised  (``adcp-client-python-hzio.3``, evidence ``adcp-client-python-2i99``)
# --------------------------------------------------------------------------- #
#: What stands where an error message would, on every reading below.
#:
#: **Nothing in this module reads one.**  :meth:`Construction.refusals` reads
#: ``error.validator`` and ``error.absolute_path``; :meth:`Construction.document_admits`
#: reads ``error.validator`` alone.  ``adcp-client-python-2i99`` measured what the library
#: nevertheless builds for them -- 17.0 GB of 192.6 GB allocated in one run, of which
#: 12.103 GB is one line: a ``oneOf`` error whose message recursively ``repr``\\ s whole
#: merged subschema dicts of ~16 KB each, 725,375 times, at ~43x ``_PyUnicodeWriter``
#: realloc amplification.  **The check that wants a keyword asks for a keyword.**
#:
#: A CONSTANT and not an empty string, because an error that reaches a human by some path
#: this module does not have should say why it carries nothing rather than carry nothing.
#:
#: **AND IT IS SHORT BECAUSE A LONG ONE IS THE SAME DEFECT SMALLER.**  Measured over this
#: bundle's construction: the library's own messages on THIS path total 656,026 bytes over
#: 15,778 errors -- 41 bytes each, because a shallow screen's errors are over small values --
#: so a 110-byte explanation here cost 1,203,124 bytes and made the figure WORSE.  The
#: sentence belongs in this comment, where it is written once; what the error carries is the
#: pointer back to it.
NO_MESSAGE = "unrendered (witness.NO_MESSAGE)"

_equal = _jsonschema_utils.equal
_ensure_list = _jsonschema_utils.ensure_list


def _quiet_type(validator: Any, types: Any, instance: Any, schema: Any) -> Any:
    if not any(validator.is_type(instance, word) for word in _ensure_list(types)):
        yield jsonschema.ValidationError(NO_MESSAGE)


def _quiet_enum(validator: Any, enums: Any, instance: Any, schema: Any) -> Any:
    if all(not _equal(each, instance) for each in enums):
        yield jsonschema.ValidationError(NO_MESSAGE)


def _quiet_const(validator: Any, const: Any, instance: Any, schema: Any) -> Any:
    if not _equal(instance, const):
        yield jsonschema.ValidationError(NO_MESSAGE)


def _quiet_not(validator: Any, not_schema: Any, instance: Any, schema: Any) -> Any:
    if validator.evolve(schema=not_schema).is_valid(instance):
        yield jsonschema.ValidationError(NO_MESSAGE)


def _quiet_contains(validator: Any, contains: Any, instance: Any, schema: Any) -> Any:
    if not validator.is_type(instance, "array"):
        return
    if not any(
        validator.evolve(schema=contains).is_valid(element) for element in instance
    ):
        yield jsonschema.ValidationError(NO_MESSAGE)


def _quiet_any_of(validator: Any, anyOf: Any, instance: Any, schema: Any) -> Any:
    all_errors: list[Any] = []
    for index, subschema in enumerate(anyOf):
        errs = list(validator.descend(instance, subschema, schema_path=index))
        if not errs:
            break
        all_errors.extend(errs)
    else:
        yield jsonschema.ValidationError(NO_MESSAGE, context=all_errors)


def _quiet_one_of(validator: Any, oneOf: Any, instance: Any, schema: Any) -> Any:
    subschemas = enumerate(oneOf)
    all_errors: list[Any] = []
    for index, subschema in subschemas:
        errs = list(validator.descend(instance, subschema, schema_path=index))
        if not errs:
            break
        all_errors.extend(errs)
    else:
        yield jsonschema.ValidationError(NO_MESSAGE, context=all_errors)
    # The library's own second clause, and the PROBES stay: a ``oneOf`` an instance
    # satisfies through two branches is refused, and nothing but the probe decides that.
    # What goes is the SENTENCE it was refused with.
    if any(validator.evolve(schema=each).is_valid(instance) for _, each in subschemas):
        yield jsonschema.ValidationError(NO_MESSAGE)


#: The keyword readings this module substitutes for the library's, **by the one property
#: that puts them here: their message renders the INSTANCE or a SUBSCHEMA**, so its cost is
#: the size of the value rather than a constant, and no caller in this module reads it.
#:
#: ``tests/test_witness_construction.py`` asserts two things about this table and neither
#: is a restatement of it: that each entry agrees with the library's own reading on the set
#: of ``(keyword, location)`` pairs over every value this construction builds, and that no
#: keyword whose library message renders a whole value is MISSING from it -- read off
#: ``inspect.getsource`` of the draft's own ``VALIDATORS``, so a library that grows one
#: reddens here instead of quietly costing what this removes.
QUIET: Mapping[str, Any] = {
    "type": _quiet_type,
    "enum": _quiet_enum,
    "const": _quiet_const,
    "not": _quiet_not,
    "contains": _quiet_contains,
    "anyOf": _quiet_any_of,
    "oneOf": _quiet_one_of,
}

#: The keywords whose library message renders a BOUND or a KEY NAME and is therefore
#: constant-cost, so they stay the library's.  Named rather than inferred, because the gate
#: above partitions the draft's own keyword set and a keyword in neither half is a keyword
#: nobody decided about.
CONSTANT_COST = frozenset(
    {
        "maxItems",
        "minItems",
        "maxLength",
        "minLength",
        "maxProperties",
        "minProperties",
        "maximum",
        "minimum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "multipleOf",
        "pattern",
        "required",
        "dependencies",
        "additionalProperties",
        "uniqueItems",
    }
)


def _reading(cls: Any, counters: "Counters") -> Any:
    """``cls`` with the three re-derivations ``adcp-client-python-2i99`` measured removed.

    **ONE CLASS PER (DRAFT, CONSTRUCTION), built where the document is read**, so the memos
    below live exactly as long as the :class:`Construction` that owns them and are dropped
    with it.  Nothing here is a process global and nothing is patched at import time, which
    is the lifetime rule ``codegen/harness.py``'s own sharings are held to.

    **(1) THE ``$ref`` RESOLUTION IS AMORTISED.**  The library's own ``$ref`` reading calls
    ``Resolver.lookup`` on every visit, and ``lookup`` does ``urldefrag(urljoin(...))`` and
    then walks the pointer SEGMENT BY SEGMENT, building a ``Resource`` per segment, with no
    memo anywhere: ``adcp-client-python-2i99`` counted 1,156,366 lookups in one run of the
    population, every one of them re-deriving an answer about a bundle that is fixed at load
    time.  The memo's key is ``(registry, base_uri, dynamic scope, ref)``, which is the whole
    of what ``lookup`` reads -- so it is keyed on everything the answer depends on, which is
    the defect ``Fixtures._pin``'s key had and this one does not.  ``Resolved`` is immutable
    and the library's own, so a hit hands back the same object a miss would have built.
    :attr:`Counters.lookups` and :attr:`Counters.lookup_hits` are the hit rate.

    **(2) NO ``Resource`` IS BUILT TO ASK A NODE WITH NO ``$id`` WHETHER IT HAS ONE.**  The
    library's ``descend`` builds ``specification.create_resource(schema)`` for every node of
    every visit purely to call ``Resolver.in_subresource``, which returns ``self`` UNCHANGED
    when the resource has no id -- 31,029,263 of 31,032,069 Resources in the measured
    grading pass, 99.99%.  draft-07's id reading is ``$id`` where the node states one and ``None``
    otherwise, so a node whose keys hold neither ``$id`` nor ``id`` cannot change the
    resolver: this hands ``descend`` the resolver it would have arrived at and the Resource
    is never built.  **The predicate is the library's own and not a guess about it** --
    ``tests/test_witness_construction.py`` asserts that for every node of every record the
    shortcut and ``in_subresource`` agree.

    **(3) NO MESSAGE IS BUILT ON A PATH THIS MODULE'S CALLERS DISCARD** (:data:`QUIET`).
    """
    lookups: dict[tuple[Any, ...], Any] = {}
    #: Pinned, which is the same argument :meth:`Construction.node` makes: a key over an
    #: identity is sound only while the object it names is held, and the registry a
    #: ``Resolved`` carries must outlive the key that names it.
    pinned: list[Any] = []

    def _ref(validator: Any, ref: str, instance: Any, schema: Any) -> Any:
        resolver = validator._resolver
        if resolver is None:  # the legacy resolver path, which this module never takes
            yield from validator._validate_reference(ref=ref, instance=instance)
            return
        key = (id(resolver._registry), resolver._base_uri, resolver._previous, ref)
        counters.lookups += 1
        held = lookups.get(key)
        if held is None:
            try:
                held = resolver.lookup(ref)
            except referencing.exceptions.Unresolvable as err:
                # The library's own wrapping, repeated here because a caller catching
                # ``jsonschema``'s error by name must keep catching it: a reference the
                # record could not resolve is a finding about the BUNDLE and it has to
                # arrive wearing the name every other reader of this library expects.
                raise jsonschema.exceptions._WrappedReferencingError(err) from err
            lookups[key] = held
            pinned.append(resolver._registry)
        else:
            counters.lookup_hits += 1
        yield from validator.descend(instance, held.contents, resolver=held.resolver)

    def skipped() -> None:
        counters.resource_skipped += 1

    return without_an_idless_resource(
        jsonschema.validators.extend(cls, validators={**QUIET, "$ref": _ref}), skipped
    )


def without_an_idless_resource(cls: Any, counted: Any = None) -> Any:
    """``cls`` with the ``Resource`` a node stating no ``$id`` does not need not built.

    ``jsonschema``'s ``descend`` builds ``specification.create_resource(schema)`` for every
    node of every visit and hands it to ``Resolver.in_subresource``, which returns ``self``
    UNCHANGED when the resource has no id.  Measured over the suite's grading pass of this
    tree: **31,029,263 of 31,032,069 Resources carry no ``$id`` at all -- 99.99%** -- and
    each one exists to answer "this node has no ``$id``" once per visit
    (``adcp-client-python-2i99``: *"create_resource + Resource.id + _legacy_dollar_id +
    in_subresource = ~400 samples = 2.27% = 3.3 s + 414 MB, spent re-answering 'this node
    has no $id' once per (node, instance) visit"*).

    **The predicate is draft-07's own id reading and not a guess about it.**
    ``_legacy_dollar_id`` answers ``None`` for a node that states no ``$id``, and
    ``in_subresource`` returns the resolver unchanged for a ``None`` id -- so a node whose
    keys hold neither ``$id`` nor ``id`` cannot move the resolver, and handing ``descend``
    the resolver it would have arrived at is the same answer without the object.
    ``tests/test_witness_construction.py`` asserts the agreement against the library over
    every node of every record, so a draft whose id reading is not draft-07's reddens.

    ``counted`` is called once per skip, or is ``None`` for a caller with no counter of its
    own.  A CALLABLE and not a counter object, because the two callers keep their counts in
    two places -- :class:`Counters` here and
    :data:`codegen.harness.VALIDATOR_COUNTERS` there -- and this function has no business
    knowing which.
    """
    library_descend = cls.descend

    def descend(
        self: Any,
        instance: Any,
        schema: Any,
        path: Any = None,
        schema_path: Any = None,
        resolver: Any = None,
    ) -> Any:
        if (
            resolver is None
            and self._ref_resolver is None
            and type(schema) is dict
            and "$id" not in schema
            and "id" not in schema
        ):
            if counted is not None:
                counted()
            resolver = self._resolver
        return library_descend(self, instance, schema, path, schema_path, resolver)

    cls.descend = descend
    return cls


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


#: **The hops that do NOT move to another instance**, read off the one descent column
#: (``codegen.keywords.descends_at``) rather than written out, which is §3's rule for a
#: keyword collection: a conjunct (``Position.CONJ``), a branch (``Position.BRANCH``) and
#: the conditional's two ARMS are each a statement about the instance the enclosing node
#: already describes, so a pointer that takes one of them names the SAME instance under one
#: more statement.
#:
#: **``if`` and ``not`` are NOT here, and that is agreement rather than a reading of
#: draft-07.**  Both descend to ``Position.RULE`` beside ``then`` and ``else``, so the
#: column cannot separate them -- ``codegen.keywords.conditional`` says so in those words
#: -- and ``adcp.types._base.applied_schema``, which is the subject a CLASS is graded
#: against, treats a hop into either as a hop to a different instance: it resets the
#: enclosing ``type`` and reads every held statement AT THAT KEY.  :meth:`Construction.subject`
#: has to name the same conjunction that function names, so the set is the arms and not the
#: four, and ``conditional()[1:]`` is "the arms" spelled as a reading of the declaration.
SAME_INSTANCE = frozenset(
    k
    for k, position in bundle.DESCENDS.items()
    if position in (keywords.Position.CONJ, keywords.Position.BRANCH)
) | frozenset(keywords.conditional()[1:])

#: The CONJUNCT list's keyword and the two UNION keywords, each read off the same column as
#: :data:`SAME_INSTANCE` rather than spelled.  :meth:`Construction.subject` needs the two
#: apart: a hop into the conjunct list must not hold that list's own siblings at a pointer
#: inside one of them, and a hop into a union is an ANSWER the pointer already gives.
CONJUNCT = frozenset(
    k for k, position in bundle.DESCENDS.items() if position is keywords.Position.CONJ
)
UNIONS = keywords.combinators(keywords.Position.ROOT)

#: **Every keyword whose subschema describes the SAME INSTANCE as the node stating it**, read
#: off the same descent column: a conjunct (``CONJ``), a branch (``BRANCH``) and a RULE
#: (``RULE`` -- a ``not``, an ``if`` and its two arms).
#:
#: :data:`SAME_INSTANCE` is this set WITHOUT ``not`` and ``if``, and the two answer different
#: questions.  That one answers which hop of a POINTER keeps the conjunction travelling, and
#: ``adcp.types._base.applied_schema`` -- which the subject must agree with -- resets at those
#: two.  This answers which subschema OF A STATEMENT talks about the value the statement is
#: about, and a ``not``'s subject and an ``if``'s condition both do.  :meth:`Construction._names`
#: is the one reader, and it reads a statement's own text for KEY NAMES and nothing else.
ABOUT_ONE_INSTANCE = frozenset(
    k
    for k, position in bundle.DESCENDS.items()
    if position
    in (keywords.Position.CONJ, keywords.Position.BRANCH, keywords.Position.RULE)
)


class Subject(NamedTuple):
    """**The subject a CLASS names: the node at its pointer under the conjunction that
    reaches it** -- as POINTERS, never as a minted document.

    ``docs/plan/architecture.md`` §9's identity rule is what forces this shape.  A pointer
    names a node of a document; it cannot name a value composition minted, so a verifier
    whose working object is a composed TEXT has no pointer to key on and reaches for content
    by necessity.  The conjunction therefore "travels beside the node as the applied schema
    rather than replacing it, and the identity stays the POINTER's": :attr:`pointer` is the
    identity, :attr:`besides` is the rest of the conjunction as pointers OF THE SAME RECORD,
    and nothing here is a dict this module assembled.

    **WHY AN UPWARD READING IS NEEDED AT ALL, in the words of the lane that found it.**
    :meth:`Construction._views` walks DOWN from the node and never up, so at
    ``#/oneOf/0`` it builds a value for the branch alone -- and a branch CLASS is not the
    branch node: it is the branch node conjoined with everything its root applies to the
    same instance.  ``adcp.types._base.applied_schema`` is how this project already reads
    that, ``SchemaBound.strict_validate`` validates against exactly it, and a witness built
    from the branch alone is NARROWER than the class it would be offered to.  Measured over
    the 2,584 pairs of the committed tree
    (``tests_emit/test_witness_applied.py::test_the_upward_witness_is_admitted_by_the_class_s_own_subject``):
    the downward reading alone puts 2,212 witnesses inside the class's own subject and 245
    outside it; this reading puts 2,415 inside and 30 outside.

    **WHAT IT CONJOINS, and it is ``applied_schema``'s own walk read for pointers.**  At
    each hop of the pointer: a hop that does not move to another instance
    (:data:`SAME_INSTANCE`) adds the ENCLOSING node -- and, where the hop is not through the
    conjunct list itself, each member of that node's own ``allOf`` -- to the held set; a hop
    that DOES move to another instance reads every held statement AT THAT KEY and drops the
    ones silent there.  That is ``_conjunction`` and ``_descended`` with the dicts left out,
    and it is why every member of :attr:`besides` is a pointer the record holds.

    **AND THE BRANCH THE POINTER TOOK IS AN ANSWER AND NOT A CHOICE** (:attr:`picks`).  The
    enclosing node's ``oneOf`` is in the held set, and :meth:`Construction._reach` descends a
    union's FIRST branch by default -- so a subject at ``#/oneOf/1`` would be conjoined with
    branch 0, which is a statement the document does not make about it.  The pointer already
    says which branch, so each union hop is recorded here and the walk takes that index.
    Measured: without it, 199 of 2,584 subjects named a pointer the record does not hold at
    all, because the conjunction walked into the wrong branch.

    **WHERE THIS IS WIDER THAN ``applied_schema``, AND THE DIRECTION IS THE SAFE ONE.**  An
    enclosing node arrives here WHOLE, where ``_conjunction`` assembles a conjunct out of
    ``SAME_INSTANCE_FACTS`` (plus ``SAME_INSTANCE_RULES`` at a branch hop) and leaves the
    node's other keywords behind.  So this reading can hold a statement the class's subject
    does not -- the enclosing node's own ``enum`` or bound, or its rules at a hop that
    inherits none.  A conjunction with MORE statements in it admits FEWER values, so a
    witness built under it is still one the subject admits: the cost is an approximation
    where no value satisfies the surplus (measured: 122 nodes with no value become 134), and
    never a witness the subject refuses.  The one direction that is not safe is a ``type``
    the enclosing node states and the node CONTRADICTS, where ``applied_schema`` keeps the
    node's word and this reading intersects to none; it is 3 of the 30 named refusals and
    ``adcp-client-python-hzio.14`` owns it.
    """

    #: The node's own pointer -- the identity, and the only thing a key is taken from.
    pointer: str
    #: The rest of the conjunction about this one instance, as pointers of the same record.
    besides: tuple[str, ...]
    #: ``(pointer of the union keyword, index)`` for each union hop the pointer itself took.
    picks: tuple[tuple[str, int], ...]


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

    #: **ONE VALIDATOR PER DOCUMENT** (§9, ``adcp-client-python-hzio.3``): how many ROOT
    #: validators this construction built.  ``validators == len(records)`` is the claim
    #: stated as an equality rather than as prose, and a per-call construction would put it
    #: at the number of calls instead.
    validators: int = 0
    #: ``(registry, base_uri, scope, ref) -> Resolved`` (:func:`_reading`).
    #: ``lookup_hits / lookups`` is the hit rate the row owes a figure for.
    lookups: int = 0
    lookup_hits: int = 0
    #: Visits that did NOT build a ``Resource`` to ask a node with no ``$id`` whether it has
    #: one.  The library builds one per node per visit and discards 99.99% of them.
    resource_skipped: int = 0

    #: **THE UPWARD READING'S OWN CENSUS** (:class:`Subject`, :meth:`Construction.subject`).
    #: How many subjects were WALKED.
    #:
    #: **AND THERE IS NO MEMO HERE, which is this row's own answer to
    #: ``adcp-client-python-hzio.7``'s rule.**  One was written and measured first: over the
    #: 2,584 pairs of the committed tree it took 2,584 misses and ZERO hits, because every
    #: caller on that population asks for one subject once.  "A memo with zero hits over the
    #: graded population is a defect -- it is either dead or keyed on something the answer
    #: does not depend on", so it was deleted rather than kept with a hit rate of nothing.
    #: The walk it held is a handful of dict lookups per pointer segment and
    #: :meth:`Construction.node` -- which DOES hit -- is where its cost actually sits.
    subjects: int = 0
    #: How many statements the upward reading conjoined, and how many subjects conjoined
    #: NOTHING -- a subject at a document root conjoins nothing by construction, so
    #: ``bare`` is the root count and anything else is a walk that found no ancestor.
    conjoined: int = 0
    bare: int = 0
    #: How many union hops a pointer answered for itself (:attr:`Subject.picks`).  ONE
    #: branch per union the pointer passes through, so this is a figure about the pointers
    #: and never a budget.
    answered: int = 0

    #: **How many values took a KEY to its own next case because a decider refused the
    #: first** (:meth:`Construction._recased`).  The conditional's counterpart to the union
    #: branch retry, and the figure that says how much of the population it serves -- a
    #: reading with zero firings over the graded population is dead code by
    #: ``adcp-client-python-hzio.7``'s own rule and this is where that shows.
    recased: int = 0


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


def _enumerated(views: Sequence[Mapping[str, Any]]) -> list[Any] | None:
    """The members every co-describing ``enum`` admits, in the first one's order.

    ``None`` where no statement lists any, which is not the same answer as the empty list:
    the first means the keyword is unstated and the value comes from elsewhere, the second
    means the statements together admit nothing.  An INTERSECTION for the reason
    :func:`_words` gives for ``type`` -- two statements about one instance both hold, so a
    member only one of them lists is not admitted -- and the ORDER is the first statement's,
    because the document's own order is the only order that is the document's.
    """
    admitted: list[Any] | None = None
    for view in views:
        stated = view.get("enum")
        if not isinstance(stated, list):
            continue
        if admitted is None:
            admitted = list(stated)
        else:
            admitted = [member for member in admitted if member in stated]
    return admitted


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


# --------------------------------------------------------------------------- #
# the five constructs a pattern is READ by, in either of two roles: CONSUME or ASSERT
# --------------------------------------------------------------------------- #
#: What a class ESCAPE admits, first member first -- a table of CONSTANTS and not a
#: generator, which is the same reason :data:`FORMAT_CASES` is permitted here.  An escape
#: absent from this table is one whose members this reader does not NAME
#: (:data:`_UNNAMED_CLASS`) or a construct it does not read at all (:func:`_escaped`).
_CLASS_ESCAPE: Mapping[str, str] = {
    "d": "0123456789",
    "w": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
}

#: **THE CHARACTERS THIS READER WRITES A VALUE FROM**, in :data:`_CLASS_ESCAPE`'s own
#: order, and the whole of why a COMPLEMENT is readable without a universe being chosen
#: here.  A class stated as a complement -- ``[^...]``, ``\S``, ``.`` -- names what it
#: EXCLUDES and leaves its members to the dialect, and the dialect's answer is every
#: codepoint of the plane, which is not a set this reader can take a *document's own first*
#: from.  It does not have to: the one statement this module already makes about which
#: characters it names is :data:`_CLASS_ESCAPE`, so the reading is **the first character
#: the reader NAMES that the document does not exclude** (:func:`_unless`).
#:
#: That is narrower than the class the document states, and narrower is the SAFE direction:
#: every character here is one the complement admits, so a value this produces is still a
#: value the class admits -- the screen's own obligation -- and the only cost is a complement
#: excluding every character named, which is DECLINED by name rather than guessed at.
#: Choosing the plane's own first codepoint instead would be a constant written here and a
#: NUL in a witness; choosing a printable range would be a literal of this reader's.
_VOCABULARY: str = "".join(dict.fromkeys(_CLASS_ESCAPE["d"] + _CLASS_ESCAPE["w"]))

#: The whitespace ``\s`` names: the UNION of ECMA-262's ``WhiteSpace`` and
#: ``LineTerminator`` productions -- draft-07 says ``pattern`` is an ECMA-262 regex -- and
#: the four codepoints python's own ``re`` adds to ``\s`` (``\x1c``-``\x1f``, ``\x85``).
#: Both are named because the two dialects that matter here are different ones: the DOCUMENT
#: states ECMA-262 and the CHECKER that grades every value this module produces is
#: ``jsonschema``'s python ``re``.
#:
#: **IT IS HERE TO EXCLUDE BY AND NEVER TO TAKE FROM**, and that is why naming the union is
#: the safe direction rather than a hedge: a wider exclusion can only SHRINK what ``\S``
#: admits, never let a character either dialect calls whitespace through.  The same fact
#: reads both ways -- no member of this set is in :data:`_VOCABULARY`, so ``\s`` has no first
#: member this reader will write (:data:`_UNNAMED_CLASS`) and ``\S`` excludes nothing the
#: reader writes.  Measured: ``\S`` therefore reads as the WHOLE vocabulary, and
#: ``tests_emit/test_witness_construction.py`` asserts the disjointness that makes that
#: true, so a vocabulary that ever grows a whitespace member is a failure and not a drift.
_WHITESPACE: str = (
    "\t\n\x0b\x0c\r\x1c\x1d\x1e\x1f\x20\x85\xa0"
    "\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f\u205f\u3000\ufeff"
)

#: What ``.`` excludes: ECMA-262's LineTerminator, and nothing else.  ``.`` is a COMPLEMENT
#: class like any other: reading a negated class that spells this set out while declining
#: the shorthand for it would be the reader stopping at a SPELLING, not at a construct.
#: No member of it is in :data:`_VOCABULARY` either, so ``.`` reads as the whole vocabulary
#: -- the set is named so the READING is right rather than so the answer comes out right.
_LINE_TERMINATOR: str = "\n\r\u2028\u2029"

#: The class escapes this reader does not name a member of -- ``\s`` alone.  Its members are
#: the whitespace a document almost never means and none of them is in :data:`_VOCABULARY`,
#: so there is no first member here to take.  A quantifier may still take it ZERO times,
#: which is why this is an unnamed member rather than an outright refusal.
#:
#: **THE COMPLEMENTS ARE NO LONGER HERE** (:data:`_COMPLEMENT_ESCAPE`): "the first character
#: that is not a digit" IS answerable once the reader has said which characters it writes,
#: and answering it from :data:`_VOCABULARY` is a reading rather than a choice.
_UNNAMED_CLASS = frozenset("s")

#: What a COMPLEMENT class escape EXCLUDES -- the positive class each one is the complement
#: of, read off the same table the positive spelling is read off, so the pair cannot drift.
#: ``\W`` excludes every word character and :data:`_VOCABULARY` is word characters only, so
#: ``\W`` admits nothing here and is declined by name; ``\S`` excludes whitespace, which the
#: vocabulary holds none of, so it admits the whole of it.
_COMPLEMENT_ESCAPE: Mapping[str, str] = {
    "S": _WHITESPACE,
    "D": _CLASS_ESCAPE["d"],
    "W": _CLASS_ESCAPE["w"],
}

#: How a value READ OFF A PATTERN says so, on :attr:`Built.reason` -- which is that field's
#: second half, *"how the one there is was reached"*.  A marker and not a sentence, because
#: what reads it is a measurement over the whole bundle: the obligation that every value
#: this reading produces is one its own node admits is only checkable if the values it
#: produced can be told from the values the other readings did.
READ_FROM_A_PATTERN = "the pattern's own constructs"

#: The zero-width assertions, which are not atoms: a pattern stating one is not read.
#: ``^`` and ``$`` at the pattern's two ends are the anchors :func:`_atoms` reads; anywhere
#: else, and in every other spelling, an assertion is a construct this reader stops at.
_ASSERTIONS = frozenset("AbBGzZ")

#: The characters that open a construct this reader does not read, with the construct NAMED
#: -- an unbalanced group, a TOP-LEVEL alternation, an interior anchor and a quantifier with
#: nothing in front of it.  ``docs/plan/architecture.md`` §2's rule, as a table: the reader
#: stops, the document's own ``examples`` is asked, and the pattern is quoted in the reason.
#:
#: ``(`` is NOT here -- :func:`_group` reads it -- and ``)`` and ``|`` are here only in the
#: positions that reach this table at all, which is OUTSIDE a group (:func:`_sequence` is
#: what breaks on them inside one).  **A TOP-LEVEL ALTERNATION IS NOT THE SAME CONSTRUCT AS
#: AN ALTERNATION INSIDE A GROUP**, and that is why one is read and the other is not: in
#: ``^a|b$`` the anchors bind to the two ARMS and not to the alternation, so the ``^`` and
#: ``$`` :func:`_atoms` strips are not statements about the whole pattern and the sequence
#: between them is not the whole of what the reading has to produce.
_UNREAD = {
    ")": "a group that never opened",
    "|": "an alternation outside a group",
    "^": "an anchor inside the pattern",
    "$": "an anchor inside the pattern",
    "*": "a quantifier with no atom",
    "+": "a quantifier with no atom",
    "?": "a quantifier with no atom",
    "{": "a quantifier with no atom",
}


class _Unread(Exception):
    """The pattern states a construct this reader does not read, and ``str`` NAMES it.

    An exception and not a sentinel because the readings nest -- a class inside an atom
    inside a group inside the sequence, a group inside a group, and a group's own five
    constructs inside a lookahead's body -- and a shape the reader stops at has to stop all
    of them at once.  Every raise names the CONSTRUCT rather than the position, because what
    the reason has to carry is why this pattern was left unread.
    """


#: A character class as the RANGES the document lists, in the DOCUMENT'S OWN ORDER --
#: ``[a-f0-9]`` is ``((97, 102), (48, 57))`` and its first member is therefore ``"a"``.
#: Ranges rather than the characters themselves because a class is CONJOINED here
#: (:func:`_both`): where a lookahead asserts ``[1-9]`` of a character a ``\d`` emits, the
#: two are statements about ONE character and what it may be is what both admit -- and the
#: overlap of two ranges is arithmetic on four endpoints, where expanding a class that
#: spells a range over the whole plane in order to compare it would cost the whole plane.
_Ranges = tuple[tuple[int, int], ...]


def _ranged(members: str) -> _Ranges:
    """The characters ``members`` lists, as one-point ranges in the order it lists them."""
    return tuple((ord(found), ord(found)) for found in members)


def _both(ours: _Ranges, theirs: _Ranges) -> _Ranges:
    """The characters BOTH classes admit, in ``ours``' own order -- EMPTY where none.

    Two statements about one character, read exactly as :func:`_bound` reads two
    ``minLength``\\ s about one string: the admitted set is the INTERSECTION and the reading
    takes its first member.  Nothing is tried and rejected -- the overlap of two ranges is
    arithmetic on their endpoints -- which is what keeps a lookahead's conjunction a reading
    rather than a search over the characters the two classes hold.
    """
    out: list[tuple[int, int]] = []
    for low, high in ours:
        out.extend(
            sorted(
                (max(low, start), min(high, end))
                for start, end in theirs
                if max(low, start) <= min(high, end)
            )
        )
    return tuple(out)


def _unless(excluded: _Ranges) -> _Ranges:
    """A COMPLEMENT class: the characters this reader NAMES that ``excluded`` does not hold.

    A complement says what it EXCLUDES and leaves its members to the dialect, so there is no
    *document's own first* to take -- the dialect's answer is the plane.  :data:`_VOCABULARY`
    is the one statement this module already makes about which characters it names, and the
    reading is its first member the document does not exclude: ``[^\\u0000-\\u001F\\u007F]``
    gives ``"0"`` because ``"0"`` is the first character this reader writes and the document
    excludes only control characters.

    **EMPTY IS A RESULT AND IT IS DECLINED BY NAME** (:func:`_patterned`), not widened: a
    complement that excludes every character the reader names -- ``\\W`` over a vocabulary of
    word characters -- is a class this reading cannot answer, and saying so is the honest
    answer.  Nothing here reaches past the vocabulary to find a member, because the member it
    would find is one this reader chose rather than one the document named.
    """
    return tuple(
        (point, point)
        for point in (ord(found) for found in _VOCABULARY)
        if not any(low <= point <= high for low, high in excluded)
    )


#: What ``.`` admits, read once: the vocabulary less ECMA-262's LineTerminator.
_ANY: _Ranges = _unless(_ranged(_LINE_TERMINATOR))


@dataclasses.dataclass(frozen=True, slots=True)
class _Atom:
    """One construct of a pattern: what it admits, and how many times it may repeat.

    :attr:`members` is the class as the ranges the document lists it in
    (:data:`_Ranges`), or ``None`` where the class is one whose members the reader does not
    name; :attr:`member` is the FIRST of them, which is the one the reading takes.  A
    ``None`` member is fatal only where the count is above zero (:func:`_patterned`),
    because a quantifier that admits zero repetitions never asks what the class holds.
    """

    members: _Ranges | None
    least: int
    most: int | None

    @property
    def member(self) -> str | None:
        """The class's FIRST member -- the one the reading takes."""
        return chr(self.members[0][0]) if self.members else None


def _escaped(text: str, at: int) -> tuple[str | None, int, bool]:
    """One ``\\``-escape: ``(what it admits, the index after it, is it a class)``.

    A class escape gives its members (:data:`_CLASS_ESCAPE`), ``None`` where it is one this
    reader does not name; ``\\xNN`` and ``\\uNNNN`` give the character they spell; a
    punctuation escape gives the character itself.  **An escape that is a LETTER or a DIGIT
    and is not in the tables is not read**: a digit is a backreference or an octal escape
    and a letter is a construct with semantics of its own, and guessing at either is the
    engine this module refuses to be.

    **A COMPLEMENT ESCAPE GIVES WHAT IT DOES NOT EXCLUDE** (:data:`_COMPLEMENT_ESCAPE`,
    :func:`_unless`), read off the same table its positive spelling is read off: ``\\S`` is
    the vocabulary less the whitespace ``\\s`` names, and the empty answer a complement over
    the whole vocabulary gives is declined by name rather than widened.
    """
    if at >= len(text):
        raise _Unread("a trailing backslash")
    found = text[at]
    if found in _CLASS_ESCAPE:
        return _CLASS_ESCAPE[found], at + 1, True
    if found in _COMPLEMENT_ESCAPE:
        excluded = _COMPLEMENT_ESCAPE[found]
        return "".join(c for c in _VOCABULARY if c not in excluded), at + 1, True
    if found in _UNNAMED_CLASS:
        return None, at + 1, True
    if found in _ASSERTIONS:
        raise _Unread(f"the assertion '\\{found}'")
    if found == "x" and at + 3 <= len(text):
        return chr(int(text[at + 1 : at + 3], 16)), at + 3, False
    if found == "u" and at + 5 <= len(text):
        return chr(int(text[at + 1 : at + 5], 16)), at + 5, False
    if found.isalnum():
        raise _Unread(f"the escape '\\{found}'")
    return found, at + 1, False


def _members(text: str, at: int) -> tuple[_Ranges | None, int]:
    """A character class, from its ``[`` -- ``(the ranges it admits, the index after it)``.

    The FIRST MEMBER IS THE DOCUMENT'S OWN FIRST: the class is read left to right and the
    first thing it lists is the one the value takes, so ``[a-f0-9]`` gives ``"a"`` and
    ``[-a-z]`` gives ``"-"``.  The whole class is read because a member the reader cannot
    parse is a construct it has not understood -- a POSIX class, a subtraction -- and a
    pattern it has not understood is one it leaves unread; **and the whole class is KEPT**,
    in the document's own order, because a lookahead asserting of this same character makes
    the two classes statements about one character and :func:`_both` needs more of each than
    its head.

    **A NEGATED CLASS NAMES WHAT IT EXCLUDES, AND THE RANGES IT LISTS ARE READ AS THE
    EXCLUSION** (:func:`_unless`).  ``[^\\u0000-\\u001F\\u007F]`` is the characters this
    reader writes that are not control characters, which is ``"0"`` onward; the ranges are
    collected by the SAME loop either way, because what ``[^`` changes is what the loop's
    answer MEANS and not how the members are parsed.  A negated class the reader can answer
    nothing for -- every character it names excluded -- comes back EMPTY and is declined by
    name at :func:`_patterned`.

    **AND A MEMBER WHOSE CHARACTERS THE READER DOES NOT NAME MAKES THE WHOLE CLASS UNNAMED**
    (``None``), negated or not: ``[^\\s]`` states an exclusion over a set this reader has no
    members for, so it cannot say which characters survive it, and a quantifier admitting
    zero repetitions makes the question moot anyway.

    The two ``]`` spellings draft-07's own grammar gives are read: a ``]`` immediately after
    ``[`` or ``[^`` is a literal member, and anywhere else it closes.
    """
    at += 1
    negated = at < len(text) and text[at] == "^"
    at += 1 if negated else 0
    admits: list[tuple[int, int]] = []
    unnamed = False
    stated = False
    if at < len(text) and text[at] == "]":
        admits, stated, at = [(ord("]"), ord("]"))], True, at + 1
    while at < len(text) and text[at] != "]":
        if text[at] == "\\":
            member, at, holds_a_class = _escaped(text, at + 1)
            if holds_a_class:
                if member is None:
                    unnamed = True
                else:
                    admits.extend(_ranged(member))
                stated = True
                continue
        else:
            member, at = text[at], at + 1
        stated = True
        if at + 1 < len(text) and text[at] == "-" and text[at + 1] != "]":
            if text[at + 1] == "\\":
                high, at, holds_a_class = _escaped(text, at + 2)
                if holds_a_class:
                    raise _Unread("a range over a class escape")
            else:
                high, at = text[at + 1], at + 2
            if high is None or member is None or ord(high) < ord(member):
                raise _Unread("a range that admits nothing")
            admits.append((ord(member), ord(high)))
        elif member is None:
            unnamed = True
        else:
            admits.append((ord(member), ord(member)))
    if at >= len(text):
        raise _Unread("a class with no end")
    if not stated:
        raise _Unread("a class that admits nothing")
    if unnamed:
        return None, at + 1
    return (_unless(tuple(admits)) if negated else tuple(admits)), at + 1


def _count(text: str, at: int) -> tuple[int, int | None, int]:
    """An atom's quantifier: ``(least, most, the index after it)``, ``most`` ``None`` for
    unbounded.

    The four spellings draft-07's own grammar gives -- ``*``, ``+``, ``?`` and ``{n}`` in
    its three forms -- and nothing else.  A LAZY or POSSESSIVE quantifier is not read: it
    admits the same strings its greedy spelling does, but reading it would be reading a
    MATCHING strategy, and a reader that starts interpreting the engine's search is the
    engine.  An atom with no quantifier repeats exactly once, which is the grammar's own
    default and not a choice made here.
    """
    if at >= len(text):
        return 1, 1, at
    found = text[at]
    if found in "*+?":
        least, most = {"*": (0, None), "+": (1, None), "?": (0, 1)}[found]
        at += 1
    elif found == "{":
        close = text.find("}", at)
        if close < 0:
            raise _Unread("a quantifier with no end")
        stated = text[at + 1 : close].split(",")
        if len(stated) > 2 or not stated[0].isdigit() or not all(p.isdigit() or not p for p in stated):
            raise _Unread(f"the quantifier '{text[at : close + 1]}'")
        least = int(stated[0])
        most = least if len(stated) == 1 else (int(stated[1]) if stated[1] else None)
        at = close + 1
    else:
        return 1, 1, at
    if at < len(text) and text[at] in "?+":
        raise _Unread("a lazy or possessive quantifier")
    return least, most, at


def _opens(text: str, at: int) -> tuple[int, bool]:
    """A ``(`` -- ``(the index its first arm STARTS at, does it ASSERT rather than consume)``.

    **CONSUME OR ASSERT IS THE WHOLE OF WHAT THIS DECIDES**, and it is a test on TWO
    characters.  ``(`` and ``(?:`` open a group whose contents the reading CONSUMES -- the
    two differ only in whether the engine would capture, and nothing here captures.
    ``(?=`` opens a positive lookahead, whose contents the reading never emits and instead
    ASSERTS of the characters that follow (:func:`_asserts`).

    **AND SATISFYING AN ASSERTION IS NOT SOLVING ONE.**  A lookahead is an assertion AT a
    position and not a construct that consumes text, so nothing has to work backwards from
    what it demands: its body is read by these same constructs into the string the body
    ITSELF admits, and the characters after the position are required to begin with that
    string (:func:`_demanded`).  What this module refuses to be is a reader that decided
    what ``(?=.*[1-9])`` demands and searched for a string meeting it; reading the body the
    way every other group's arm is read, and conjoining the result into the class that
    emits the character, is the reading it already does twice over.

    **EVERY OTHER ``(?`` OPTION IS DECLINED, named by its own two characters.**  A NEGATIVE
    lookahead (``(?!``) and a negative lookbehind (``(?<!``) state what the text must NOT
    be, and "the first STRING that is not this" is a choice no vocabulary answers -- a
    complement over characters is :func:`_unless`, and there is no such reading over strings,
    whose set is not one a table names; a positive LOOKBEHIND (``(?<=``) states it of
    characters the reading has already emitted, which would mean revising a reading that is
    finished.  A named group, an inline flag, a comment, an atomic group and a conditional
    each carry semantics of their own, and a reader that treated them as a plain group
    would be guessing at them.
    """
    if not text.startswith("(?", at):
        return at + 1, False
    third = text[at + 2 : at + 3]
    if third == "=":
        return at + 3, True
    if third == "!":
        raise _Unread("the lookahead '(?!'")
    if third == "<":
        fourth = text[at + 3 : at + 4]
        if fourth in ("=", "!"):
            raise _Unread(f"the lookbehind '(?<{fourth}'")
        raise _Unread("a named group")
    if third == ":":
        return at + 3, False
    if not third:
        raise _Unread("a group with no end")
    raise _Unread(f"the group option '(?{third}'")


def _arms(text: str, at: int) -> tuple[tuple[tuple[_Atom, ...], ...], int]:
    """The arms of a parenthesised construct, from the index its FIRST arm starts at.

    ``(the arms, the index after the ``)``)``.  Shared by the construct that CONSUMES its
    contents (:func:`_group`) and the one that ASSERTS them (:func:`_asserts`), because an
    arm is parsed the same way whichever role the parenthesis plays -- which is the whole
    reason a lookahead needs no reading of its own.
    """
    arms: list[tuple[_Atom, ...]] = []
    while True:
        atoms, at = _sequence(text, at, nested=True)
        arms.append(atoms)
        if at >= len(text):
            raise _Unread("a group with no end")
        closed = text[at] == ")"
        at += 1
        if closed:
            return tuple(arms), at


def _group(
    text: str, at: int, pending: Sequence[_Ranges]
) -> tuple[tuple[_Atom, ...], int]:
    """A group from its first arm's index -- ``(the atoms it contributes, the index after)``.

    **A GROUP IS READ BY ITS QUANTIFIER'S MINIMUM, exactly as a character class is.**
    ``(...)?`` and ``(...)*`` are taken ZERO times and contribute NO atoms at all;
    ``(...)+``, and a group with no quantifier, are taken ONCE; ``(...){n,m}`` is taken *n*
    times.  Nothing here is a choice: ``?`` says the group may be absent and the reading
    takes the absence the way ``minLength: 0`` takes the empty string and the way ``[a-z]*``
    already takes no character.  The contents are read by :func:`_sequence`, which reaches
    this function again for a group inside a group, so the recursion is the construct's own
    nesting and not a search.

    **AN ASSERTION STILL IN HAND RAISES THAT MINIMUM TO ONE**, which is the move
    :func:`_patterned` already makes for a ``minLength`` above the atoms' own minimum: a
    statement about the instance that the minimum reading does not satisfy is met by taking
    a quantifier HIGHER INSIDE THE RANGE IT ALREADY ADMITS.  ``(?:\\d+Y)?`` is taken zero
    times where nothing is asserted of the characters after it and ONCE where a lookahead
    has demanded one of them, and the group's own ``?`` is what says the second is
    admitted.  Where the quantifier admits no repetition at all (``(...){0}``) the minimum
    stands and the demand goes unmet, which :func:`_sequence` declines by name.

    **THE GROUP'S OWN ``most`` IS DROPPED, and that is a stated limit rather than an
    oversight.**  :func:`_patterned` grows a reading to meet a ``minLength`` by repeating an
    atom its own quantifier admits more of; a group's atoms are INLINED here, so they can
    still grow individually, but the group cannot be repeated a second time to reach a
    bound.  A ``minLength`` no reading reaches is reported by :func:`_patterned` rather than
    approached, so the limit costs an approximation and never a wrong string.

    **AN ALTERNATION INSIDE A GROUP IS READ BY TAKING ITS FIRST ARM, AND EVERY ARM IS READ.**
    The first arm is the DOCUMENT'S OWN FIRST, taken exactly as :func:`_members` takes a
    class's first member and as an ``enum``'s first member is taken: the arms are compared
    with nothing, no arm is tried and rejected, and no property of the produced string
    decides which arm is used.  That is what makes it a reading -- what would make it
    solving is choosing the arm that gets some other keyword satisfied, which is a search
    over the arms and is not done.  The other arms are nonetheless parsed in full, for
    :func:`_members`' reason: an arm this reader cannot parse is a construct it has not
    understood, and a pattern it has not understood is one it leaves unread.  ``(?:0|[1-9]
    [0-9]*)`` therefore gives ``"0"`` -- but only because ``[1-9][0-9]*`` parsed as well.
    """
    arms, at = _arms(text, at)
    least, most, at = _count(text, at)
    if least == 0 and pending and (most is None or most >= 1):
        least = 1
    return arms[0] * least, at


def _asserts(text: str, at: int, pending: list[_Ranges]) -> int:
    """A positive lookahead from its first arm's index -- the index after it.

    **IT CONTRIBUTES NO ATOM.**  That is the distinction this whole reading turns on: a
    group's contents are CONSUMED and appear in the string, a lookahead's are ASSERTED of
    the characters that follow and appear in nothing.  The body is parsed by
    :func:`_arms` -- the same arms, the same first-arm reading -- and :func:`_demanded`
    records what it names against the characters not yet emitted.

    **A QUANTIFIED LOOKAHEAD IS DECLINED.**  ``(?=a)*`` repeats an assertion that consumes
    nothing, which is a statement about the engine's loop rather than about the instance,
    and ``(?=a)?`` asserts something the match need not satisfy at all.
    """
    arms, after = _arms(text, at)
    least, most, after = _count(text, after)
    if (least, most) != (1, 1):
        raise _Unread("a quantified lookahead")
    _demanded(arms[0], pending)
    return after


def _demanded(atoms: Sequence[_Atom], pending: list[_Ranges]) -> None:
    """Record an assertion's body as per-character demands on the characters not yet emitted.

    ``pending[i]`` is the class the i-th character still to be emitted must come from.

    **THE BODY'S OWN MINIMUM READING IS THE DEMAND**, which is the reading everywhere else
    in this module: an atom its quantifier admits zero of demands nothing, so ``.*[1-9]``
    demands one ``[1-9]`` AT the position and nothing before it.  That is STRONGER than the
    assertion -- ``.*[1-9]`` is satisfied by a ``[1-9]`` anywhere at or after the position --
    and stronger is what a construction needs rather than a weakness: the body's minimum
    reading is a string the BODY ITSELF admits, so a remainder beginning with it satisfies
    the assertion, and no weaker demand had to be characterised to know that.

    **TWO ASSERTIONS AT ONE POSITION ARE CONJOINED** (:func:`_both`), which is how
    ``^P(?=.*[1-9])(?=\\d|T)`` reads: ``[1-9]`` and ``\\d`` are two statements about the
    character after the ``P``, so what that character may be is what both admit.  A demand
    over a class whose members this reader does not name is declined, for :func:`_members`'
    reason: ``\\s`` is the one class left with no member to take, so there is nothing to
    demand of a character it would assert.
    """
    at = 0
    for atom in atoms:
        if not atom.least:
            continue
        members = atom.members
        if members is None:
            raise _Unread("an assertion over a class whose members it does not name")
        for _ in range(atom.least):
            if at == len(pending):
                pending.append(members)
            else:
                shared = _both(pending[at], members)
                if not shared:
                    raise _Unread("two assertions that admit nothing in common")
                pending[at] = shared
            at += 1


def _asserted(atom: _Atom, pending: list[_Ranges]) -> _Atom:
    """``atom``, with every demand standing against the characters it emits CONJOINED in.

    A lookahead leaves in ``pending`` statements about the characters that follow it, and
    this atom is what emits them -- so the class it takes its member from is the class BOTH
    statements admit (:func:`_both`), and the demands it covered are spent.  **This is the
    CHECK the ruling asks for and not a solve**: the demand is read off the assertion's own
    body, the class is read off the document, and what the character may be is the overlap.
    A demand and a class with nothing in common is a position no string satisfies, declined
    by name rather than answered with a string the pattern would refuse.

    **AND A DEMAND RAISES THIS ATOM'S MINIMUM TO ONE** where its quantifier admits a
    repetition, for :func:`_group`'s reason: ``[a-z]*`` under a demand for an ``[a-z]`` is
    taken once, exactly as a ``minLength`` above the atoms' own minimum is met by taking a
    quantifier higher inside the range it already admits.
    """
    if not pending:
        return atom
    least = atom.least
    if least == 0 and (atom.most is None or atom.most >= 1):
        least = 1
    members = atom.members
    for _ in range(min(least, len(pending))):
        if members is None:
            raise _Unread("an assertion over a class whose members it does not name")
        members = _both(members, pending.pop(0))
        if not members:
            raise _Unread("an assertion and a class that admit nothing in common")
    return _Atom(members, least, atom.most)


def _sequence(text: str, at: int, *, nested: bool) -> tuple[tuple[_Atom, ...], int]:
    """The atoms from ``at`` onward -- ``(them, the index it stopped at)``.

    One pass left to right, each atom with its own quantifier, a group inlined as the atoms
    it CONSUMES (:func:`_group`) and a lookahead recorded as what it ASSERTS of the atoms
    after it (:func:`_asserts`).  :func:`_opens` is where those two are told apart and this
    is the one place the fork is taken.  ``nested`` says whether this sequence is one group
    ARM: an arm ends at the ``)`` that closes its group or at the ``|`` that starts the next
    arm, and at the top level those two characters have no group to belong to and are a
    construct the reader stops at (:data:`_UNREAD` carries why the top-level alternation in
    particular is a different construct from the one :func:`_group` reads).

    **A DEMAND NO CONSTRUCT AFTER IT REACHES IS DECLINED, BY NAME.**  A lookahead whose
    demands are still in hand when the sequence ends asserts something of characters this
    reading does not emit, and nothing later will supply them.  That is the honest stop the
    ruling preserves: the assertion is left unsatisfied and the pattern left unread, never
    answered with a string the pattern refuses.
    """
    out: list[_Atom] = []
    pending: list[_Ranges] = []
    while at < len(text):
        found = text[at]
        if nested and found in (")", "|"):
            break
        if found == "(":
            first, asserts = _opens(text, at)
            if asserts:
                at = _asserts(text, first, pending)
                continue
            inlined, at = _group(text, first, pending)
            for atom in inlined:
                out.append(_asserted(atom, pending))
            continue
        if found == "[":
            members, at = _members(text, at)
        elif found == "\\":
            spelled, at, _holds_a_class = _escaped(text, at + 1)
            members = None if spelled is None else _ranged(spelled)
        elif found == ".":
            members, at = _ANY, at + 1
        elif found in _UNREAD:
            raise _Unread(_UNREAD[found])
        else:
            members, at = _ranged(found), at + 1
        least, most, at = _count(text, at)
        out.append(_asserted(_Atom(members, least, most), pending))
    if pending:
        raise _Unread("an assertion no construct after it reaches")
    return tuple(out), at


def _atoms(pattern: str) -> tuple[_Atom, ...]:
    """The pattern as a sequence of :class:`_Atom`, or :class:`_Unread` naming the construct.

    **THE ANCHORS ARE READ AS ANCHORS AND NOT AS ATOMS.**  A leading ``^`` and a trailing
    ``$`` say where the match sits, which is what lets the sequence between them be the
    whole of what the reading has to produce; ``$`` in any other position, and ``^`` outside
    a class, is an assertion this reader stops at.  An UNANCHORED pattern is read too and
    needs no special case: draft-07's ``pattern`` is a SEARCH rather than a full match, so
    the string the atoms name is found in itself -- which is why ``^https://`` gives
    ``"https://"`` and a bare ``\\S`` gives the one character it names, ``"0"``.

    **AN EMPTY TUPLE IS A READING AND NOT A FAILURE, once a group can be taken zero times.**
    ``^(?:ab)?$`` states a construct and takes none of it, so the string it names is the
    empty one -- which the pattern admits.  What states NO construct is a pattern with
    nothing between its anchors, and that is the one this refuses: the emptiness is read off
    the TEXT rather than off the atom count, so the two cases stay distinguishable.
    """
    text = pattern[1:] if pattern.startswith("^") else pattern
    if text.endswith("$") and not text.endswith("\\$"):
        text = text[:-1]
    if not text:
        raise _Unread("a pattern that states no atom")
    atoms, _ = _sequence(text, 0, nested=False)
    return atoms


def _patterned(pattern: str, low: int, high: int | None) -> Built:
    """The string the pattern's own five constructs name, inside the node's length bound.

    Each class's first member repeated the quantifier's MINIMUM count, which is the whole
    reading -- and then the length bound, which is a statement about the same instance and
    so has to hold of the same string.  A quantifier's RANGE is what makes that possible: a
    ``minLength`` above the atoms' own minimum is met by repeating a class the number of
    times its own quantifier admits, and a bound no repetition of the atoms can reach is
    reported rather than approached.
    """
    try:
        atoms = _atoms(pattern)
    except _Unread as why:
        return Built(None, Source.APPROXIMATED, f"pattern {pattern!r} is not solved: {why}")
    counts = [atom.least for atom in atoms]
    length = sum(counts)
    if high is not None and length > high:
        return Built(
            None,
            Source.APPROXIMATED,
            f"pattern {pattern!r} is not solved under maxLength {high}: it admits nothing shorter",
        )
    index = len(atoms) - 1
    while length < low and index >= 0:
        atom = atoms[index]
        room = (low - length) if atom.most is None else atom.most - counts[index]
        if atom.member is None or room <= 0:
            index -= 1
            continue
        grown = min(room, low - length)
        counts[index] += grown
        length += grown
    if length < low:
        return Built(
            None,
            Source.APPROXIMATED,
            f"pattern {pattern!r} is not solved under minLength {low}: it admits nothing longer",
        )
    out = []
    for atom, count in zip(atoms, counts):
        if count == 0:
            continue
        if atom.member is None:
            return Built(
                None,
                Source.APPROXIMATED,
                f"pattern {pattern!r} is not solved: "
                + (
                    "a complement that excludes every character it names"
                    if atom.members == ()
                    else "a class whose members it does not name"
                ),
            )
        out.append(atom.member * count)
    return Built("".join(out), Source.CONSTRUCTED, READ_FROM_A_PATTERN)


def _patterns(views: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """The DISTINCT patterns the co-describing statements state, in first-stated order."""
    out: list[str] = []
    for view in views:
        stated = view.get("pattern")
        if isinstance(stated, str) and stated not in out:
            out.append(stated)
    return tuple(out)


def _string(views: Sequence[Mapping[str, Any]]) -> Built:
    """The string the node's own string keywords state it admits.

    ``format`` first, because a formatted node's admitted set is the format's and a
    padded string is not in it; then the ``pattern``, read by its own five constructs
    (:func:`_patterned`); then the length bound, exactly as many characters as it demands.
    A pattern of an unread shape is where the construction STOPS, and the caller falls to
    the document's own ``examples``.

    **TWO DIFFERENT PATTERNS ON ONE INSTANCE ARE NOT READ.**  Two co-describing conjuncts
    each stating a pattern demand a string in the INTERSECTION of two languages, and
    intersecting them is solving rather than reading -- so the fact is approximated with
    both quoted.  A value the first pattern alone admits would be a witness nothing
    checked: the shallow screen reads one node's own statements, so a conjunct's pattern is
    graded at the conjunct and not here.
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
    stated = _patterns(views)
    if len(stated) > 1:
        return Built(
            None,
            Source.APPROXIMATED,
            f"pattern {stated[0]!r} is not solved beside {stated[1]!r} at one instance",
        )
    if stated:
        return _patterned(stated[0], low, high)
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
        #: The validator CLASS this construction reads with, per draft the bundle declares
        #: (:func:`_reading`).  One class per draft and not per document, because what the
        #: class carries is the resolution memo and the quiet readings -- both of which are
        #: this construction's and not one document's -- while what a DOCUMENT gets is one
        #: INSTANCE of it, which is the registry and the resolver §9 names.
        self._reading: dict[Any, Any] = {}
        self._memo: dict[Key, Built] = {}
        self._floors: dict[tuple[str, str], Built] = {}
        self._nodes: dict[tuple[str, str], Any] = {}
        #: :meth:`subtree`'s memo, keyed like every other answer here.  Separate from
        #: :attr:`_memo` because the two hold different types for one key -- a single
        #: admitted value against the whole witness set of a subtree -- and §9's rule is
        #: one answer per node per document, not one object per node per document.
        self._subtrees: dict[Key, tuple[Class, ...]] = {}
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

        **AND THE READING IS :func:`_reading`'s AND NOT THE LIBRARY'S**
        (``adcp-client-python-hzio.3``, evidence ``adcp-client-python-2i99``).  The root
        construction is where ``jsonschema`` builds the ``Resource``, the ``Registry`` and
        the ``Resolver``, so it is the one place that has to happen once per document; the
        three repairs that make the per-NODE half linear -- the resolution memo, the
        Resource that is not built, and the message that is not rendered -- travel on the
        validator CLASS, which is why they are installed there and not here.
        """
        held = self._validators.get(document)
        if held is None:
            record = self._records[document]
            cls = jsonschema.validators.validator_for(record, jsonschema.Draft7Validator)
            reading = self._reading.get(cls)
            if reading is None:
                reading = _reading(cls, self.counters)
                self._reading[cls] = reading
            held = reading(record, format_checker=reading.FORMAT_CHECKER)
            self._validators[document] = held
            self.counters.validators += 1
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

        **AND THE RECORD'S OWN STORAGE HOP IS TAKEN MID-WALK WHERE -- AND ONLY WHERE -- THE
        PLAIN DEREFERENCE WOULD RAISE** (:meth:`_hoisted`).  ``codegen.bundle.record`` stores
        each distinct subtree once and writes a reference at every other occurrence, so a
        pointer whose own text walks INTO a hoisted subtree walks into the reference instead,
        and the segment after it has no key to index.  ``adcp.types._base.through_the_store``
        is "the one hop that makes the hoisting invisible to a pointer" and
        ``applied_schema`` takes it before every segment for exactly this reason; this method
        took it only at the foot (:meth:`through`), so the two disagreed about which pointers
        the record holds.

        **Gated so that nothing which resolves today moves**, which is ``applied_schema``'s
        own discipline at its own substitution clause: a pointer the plain walk reaches takes
        the plain walk, and a pointer NEITHER walk reaches still raises -- so a class stamped
        at a position the record does not hold stays loud.  Measured: one of the five
        ``adcp-client-python-hzio.15`` names,
        ``media-buy/refine-proposals-response.json#/properties/results/items/oneOf/0/properties/proposals/items``,
        is a pointer the record HOLDS through one such hop and the other four are not.
        """
        key = (document, pointer)
        held = self._nodes.get(key, _MISSING)
        if held is _MISSING:
            try:
                held = bundle.node_at(self._records[document], pointer)
            except (KeyError, IndexError, TypeError, ValueError):
                held = self._hoisted(document, pointer)
            self._nodes[key] = held
            self.counters.reached += 1
        return held

    def _hoisted(self, document: str, pointer: str) -> Any:
        """``pointer`` dereferenced with the record's own storage hop taken before each segment.

        One segment at a time, each read through :meth:`through`, because the hoisting is the
        record's storage decision and not a statement the document makes -- "it carries
        nothing and answers nothing".  The pointer that comes out is the document's own
        pointer and the node is the document's own node; nothing is composed and nothing is
        minted, which is what keeps §9's identity rule satisfiable here.

        It RAISES where the hop does not reach either -- the only caller is :meth:`node`'s own
        fallback and a position neither walk holds is a finding
        (``adcp-client-python-hzio.15``) rather than something to answer with an empty schema.

        **IT READS THE RECORD DIRECTLY AND NOT THROUGH :meth:`node`**, which is not a
        micro-decision: :meth:`node` is this method's own caller, so settling a segment
        through it would re-enter here at the same pointer and recur without bound.  Measured
        the hard way -- ``RecursionError`` at 195 pairs and a monotonicity the gate caught.
        """
        record = self._records[document]
        at = ""
        for part in [p for p in pointer.lstrip("/").split("/") if p]:
            at = f"{self._settles(document, record, at)}/{part}"
        return bundle.node_at(record, self._settles(document, record, at))

    def _settles(self, document: str, record: Mapping[str, Any], at: str) -> str:
        """``at`` with the record's own storage reference followed, as a POINTER.

        :meth:`through`'s reading without the memo, because its caller is :meth:`node` and
        this one is :meth:`node`'s own fallback.  It terminates the same way and for the
        same reason that method carries: the chain walks DISTINCT pointers of one finite
        record, so the pointer already visited is the back edge and there is no count here.
        """
        seen: set[str] = set()
        while at not in seen:
            seen.add(at)
            node = bundle.node_at(record, at)
            if not (isinstance(node, Mapping) and len(node) == 1):
                return at
            ref = node.get("$ref")
            if not isinstance(ref, str):
                return at
            target = _local(ref)
            if target is None:
                return at
            at = target
        raise RecursionError(f"{document}{at}: a storage reference does not settle")

    def through(self, document: str, pointer: str) -> tuple[str, Any]:
        """The pointer a SOLE ``$ref`` node forwards to, with the node there -- or ``_MISSING``.

        **The record's text is a DAG and its pointers are not** (``docs/plan/architecture.md``):
        ``codegen.bundle.record`` stores each distinct subtree once and writes a reference at
        every other occurrence, and ``adcp.types._base.through_the_store`` is the one hop that
        makes the hoisting invisible to a pointer.  :meth:`subject` takes the same hop for the
        same reason and with one more consequence: a held statement left as a storage
        reference holds no key at all, so the next hop of the pointer would drop it and a
        statement the document makes about an instance two hops down would silently stop
        being conjoined.  Returning the pointer it forwarded TO is what keeps the held set
        pointers of the record rather than nodes this module is carrying.

        A node whose ONE key is a local ``$ref`` and nothing else, which is the only node the
        hoisting writes; a document's own reference beside a ``description`` is left exactly
        as the document spells it, because following those would change what the subject
        conjoins at 1,158 positions for a storage decision that touches none.

        ``_MISSING`` for a pointer the record does not hold, which is what makes the descent
        in :meth:`subject` total: ``_descended``'s rule is that a statement silent at a key
        drops out, and "the record has no node there" is how silence is spelled as a pointer.

        **AND IT TERMINATES ON THE POINTER AND NOT ON A COUNT**, which is where
        ``_STORE_HOPS = 8`` stood.  That constant's own comment said it was a bound no record
        ``codegen.bundle.record`` can write could reach, and measured the sentence was TRUE:
        over the graded population the longest chain is **1 hop** across 2,988 calls, 279 of
        which take one, and no record states a cycle.  It is deleted anyway, because
        ``adcp-client-python-hzio.6``'s rule does not turn on whether a cap is reached today
        -- *"a parameter with a generous default is the same cap with a politer name"* -- and
        the next bundle, not this reading, would decide when 8 began to cut.

        The termination it stood in for is already present and is exact: every hop moves to a
        DIFFERENT pointer of ONE finite record, so a chain either settles or revisits a
        pointer, and the revisited pointer IS the cycle -- ``seen`` is the whole terminator
        and it names the back edge rather than counting toward it.  That is strictly more
        complete than the count, since a nine-hop chain would now settle instead of raising,
        and the hang the old comment feared is still prevented.
        :meth:`_settles` is the same walk without the memo and reads the same way;
        ``tests_emit/test_witness_construction.py`` is where the absence of the number is a
        gate, over the module's repetitions rather than over its constants.
        """
        seen: set[str] = set()
        while pointer not in seen:
            seen.add(pointer)
            try:
                node = self.node(document, pointer)
            except (KeyError, IndexError, TypeError, ValueError):
                return pointer, _MISSING
            if not (isinstance(node, Mapping) and len(node) == 1):
                return pointer, node
            ref = node.get("$ref")
            if not isinstance(ref, str):
                return pointer, node
            target = _local(ref)
            if target is None:
                return pointer, node
            pointer = target
        raise RecursionError(f"{document}{pointer}: a storage reference does not settle")

    # -- the upward reading ------------------------------------------------- #
    def subject(self, document: str, pointer: str) -> Subject:
        """**The subject a CLASS at this pointer names**, as pointers -- see :class:`Subject`.

        ``adcp.types._base.applied_schema``'s walk, read for the POINTERS it conjoins instead
        of for the dict it assembles.  The two must not disagree, so the clauses below are
        that function's own clauses in its own order, and
        ``tests_emit/test_witness_applied.py`` is where the agreement is MEASURED over every
        pair of the tree rather than asserted in prose.

        **NOT MEMOISED, and :attr:`Counters.subjects` says why**: one was written and took
        2,584 misses and zero hits over the graded population, which
        ``adcp-client-python-hzio.7`` calls a defect rather than a saving.  What the walk
        reads it reads through :meth:`node`, whose memo does hit.
        """
        self.counters.subjects += 1
        held: list[str] = []
        #: **§8's THIRD pairing rule, as pointers**: the SIBLING conjuncts of a conjunct
        #: list the pointer CUTS INTO.  Held apart from :data:`held` and not merged into it,
        #: because ``applied_schema`` resets this list at every cut and keeps the other --
        #: see the clause at the ``CONJUNCT`` hop below.
        siblings: list[str] = []
        picks: list[tuple[str, int]] = []
        at = ""
        parts = [part for part in pointer.lstrip("/").split("/") if part]
        index = 0
        while index < len(parts):
            part = parts[index]
            if part in SAME_INSTANCE:
                # The hop stays on this instance, so the ENCLOSING node is a statement about
                # it -- which is ``_conjunction``'s own clause -- and so is each member of
                # that node's own ``allOf``, UNLESS the hop is into that list: at an
                # ``allOf`` hop the list the pointer is entering is this node's own, and
                # holding it as a whole statement would state every sibling conjunct at a
                # pointer inside one of them.  ``_conjunction``'s ``through != "allOf"`` is
                # the same clause, and ``siblings`` below is where that list goes instead.
                where, node = self.through(document, at)
                if isinstance(node, Mapping):
                    held.append(where)
                    if part not in CONJUNCT:
                        held.extend(self._conjuncts(document, where, node))
                if part in CONJUNCT:
                    # **THE SIBLING CONJUNCTS, which is ``applied_schema``'s ``cutting`` /
                    # ``siblings`` pair read for pointers.**  draft-07 holds every member of
                    # an ``allOf`` against the SAME instance, so at ``/allOf/1`` the other
                    # members are statements about this instance and not facts the class
                    # added -- and where the pointer continues BELOW the conjunct, each
                    # sibling's declaration at the same keys is what holds against the
                    # instance the node describes.  Measured: without this clause, 11 of the
                    # 30 refusals ``adcp-client-python-hzio.14`` names are a value built
                    # without a statement the subject conjoins, every one of them with the
                    # subject's error inside ``allOf/0`` -- the sibling.
                    #
                    # **A SECOND CUT DROPS THE FIRST ONE'S SIBLINGS** rather than guessing
                    # how the two compose, which is ``applied_schema``'s own rule at the same
                    # place ("a conjunct of a conjunct would need a reading of which of the
                    # outer siblings' nodes answers the inner cut, and this rule makes
                    # none").  The assignment -- not an ``extend`` -- is that rule.
                    siblings = (
                        self._conjuncts(
                            document, where, node, skip=f"/{part}/{parts[index + 1]}"
                        )
                        if isinstance(node, Mapping)
                        else []
                    )
                if part in bundle.HELD_IN_A_LIST:
                    taken = int(parts[index + 1])
                    if part in UNIONS:
                        # The pointer says WHICH branch, so the union is answered and not
                        # chosen.  :class:`Subject` carries the measurement.
                        picks.append((f"{at}/{part}", taken))
                    at = f"{at}/{part}/{taken}"
                    index += 2
                    continue
                at = f"{at}/{part}"
                index += 1
                continue
            # The hop moves to a DIFFERENT instance, and it moves every statement held
            # against this one to that same instance: draft-07 applies ``allOf/0/properties/x``
            # and ``properties/x`` to one value.  A statement silent at the key says nothing
            # about it and drops out, which is ``_descended``'s own totality.
            #
            # **ONE operation and not two**: a sibling travels by exactly what a held
            # statement travels by, which is ``applied_schema``'s own sentence at this hop
            # ("the two lists differ in where they came from and not in how they travel").
            held = self._descended(document, held, part)
            siblings = self._descended(document, siblings, part)
            at = f"{at}/{part}"
            index += 1
        # A sibling conjunct is a conjunct of THIS node, so it joins the enclosing
        # statements at the foot -- ``applied_schema``'s ``[*conjoined, *siblings]``.
        besides = tuple(
            dict.fromkeys(
                statement for statement in (*held, *siblings) if statement != pointer
            )
        )
        read = Subject(pointer, besides, tuple(picks))
        self.counters.conjoined += len(besides)
        self.counters.answered += len(picks)
        if not besides:
            self.counters.bare += 1
        return read

    def _conjuncts(
        self, document: str, where: str, node: Mapping[str, Any], skip: str = ""
    ) -> list[str]:
        """The pointers of ``node``'s own conjunct list, each READ THROUGH THE STORE.

        ``codegen.bundle.subschemas`` is the ONE descent step and it spells the suffix, so a
        conjunct's pointer is read off the same walk the compiler's own census reads and
        never assembled from a keyword name.

        **AND EACH IS RESOLVED AS IT IS HELD, which a measurement forced.**  The record
        stores a repeated subtree once and writes a reference at every other occurrence, so a
        conjunct held as the reference holds NO KEY AT ALL -- and :meth:`_descended`'s next
        hop then drops it, silently, exactly as :meth:`through`'s own docstring says it
        would.  ``adcp.types._base._conjunction`` resolves a spliced conjunct at the same
        place and for the same reason.  Measured: the two ``indicators`` classes of
        ``media-buy/get-media-buys-response.json`` hold ``core/indicator.json`` as a sibling
        conjunct stored once, and the unresolved pointer dropped at the ``properties`` hop --
        so the class was graded without the ``required`` its subject states.

        ``skip`` is the ONE suffix the pointer itself is entering, which is what makes this
        the SIBLINGS at a cut and the whole list everywhere else.
        """
        out: list[str] = []
        for keyword, suffix, _, _ in bundle.subschemas(node):
            if keyword not in CONJUNCT or suffix == skip:
                continue
            resolved, member = self.through(document, f"{where}{suffix}")
            if isinstance(member, Mapping):
                out.append(resolved)
        return out

    def _descended(
        self, document: str, statements: Sequence[str], part: str
    ) -> list[str]:
        """Every pointer in ``statements`` read AT ``part``, with the silent ones dropped.

        ``adcp.types._base._descended`` with the dicts left out: one hop of a pointer
        applied to the statements held against the instance the hop is LEAVING, because
        draft-07 applies ``allOf/0/properties/x`` and ``properties/x`` to one value.  A
        statement that says nothing at this key drops out, which is what makes the descent
        total rather than partial, and **"the record has no node there" is how silence is
        spelled as a pointer** (:meth:`through`'s ``_MISSING``).

        One function because :meth:`subject` descends TWO lists -- the enclosing statements
        and the sibling conjuncts -- and that function's own sentence at the same hop is
        that "the two lists differ in where they came from and not in how they travel".
        """
        out: list[str] = []
        for statement in statements:
            where, node = self.through(document, f"{statement}/{part}")
            if isinstance(node, Mapping):
                out.append(where)
        return out

    def applied(self, document: str, pointer: str = "") -> Built:
        """**The witness for the subject a CLASS at this pointer names**, and the one entry
        point a grader of a class uses.

        :meth:`value` builds the value a NODE's own keywords state; this builds the value the
        node states UNDER the conjunction that reaches it, which is the subject
        ``SchemaBound.strict_validate`` validates against.  The two are the same call with
        the conjunction supplied: :attr:`Subject.besides` is handed to :meth:`value` as the
        rest of the conjunction about this instance AND put on the stack, which is the rule
        :meth:`value`'s own docstring states -- *"a caller that passed one and not the other
        would be asking the memo to serve an answer built from a conjunction it was not keyed
        on"*.

        **THE KEY IS STILL ``(document, pointer, stack)``, and :attr:`Subject.picks` does not
        join it.**  The picks are a function of the pointer -- they are the branch indices the
        pointer itself spells -- so two calls that disagree about them are two different
        pointers, and the stack already carries the conjunction they were read with.  A pick
        reaches no CHILD's call either: a child is another instance location and the branch
        this instance took says nothing about it, so :meth:`_object` and :meth:`_array`
        pass none and the forcing lives for exactly one frame.
        """
        read = self.subject(document, pointer)
        return self.value(
            document, pointer, (pointer, *read.besides), read.besides, read.picks
        )

    # -- the walk ---------------------------------------------------------- #
    def value(
        self,
        document: str,
        pointer: str = "",
        stack: tuple[str, ...] = (),
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
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

        **``answered`` IS THE BRANCH A UNION IN THE CONJUNCTION HAS ALREADY BEEN GIVEN**, and
        it is :attr:`Subject.picks` -- never a caller's choice.  :meth:`applied` is its one
        source: a subject at ``#/oneOf/1`` holds the enclosing node, whose ``oneOf`` the walk
        would otherwise read at its FIRST branch, so the index the pointer itself spells
        travels with the call.  It is NOT in :data:`Key` and does not need to be: the picks
        are a function of the pointer, so two calls that disagree about them are two different
        pointers, and ``stack`` already distinguishes the conjunction the answer was built
        under.  Nothing inherits it -- a child instance's branch is not this one's -- so it
        lives for one frame.
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
        built = self._construct(document, pointer, stack, besides, answered)
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
        self,
        document: str,
        pointer: str,
        stack: tuple[str, ...],
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
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
            return self.value(document, target, (*stack, target), besides, answered)

        views = self._views(document, pointer, stack, None, besides, answered)
        built, settled = self._settled(document, views, None, answered)
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
        for pick in self._picks(document, settled, answered)[1:]:
            built, settled = self._settled(
                document,
                self._views(document, pointer, stack, pick, besides, answered),
                pick,
                answered,
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
        answered: tuple[tuple[str, int], ...] = (),
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
            fresh = tuple(
                v for v in self._reach(document, arms, pick, answered) if v not in settled
            )
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

        **AND THE PATTERN'S OWN READING IS ONE OF THOSE CASES** (:func:`_patterned`), which
        is where the ``format``/``pattern`` pair comes out right in BOTH directions:
        :func:`_string` offers the format's case because a formatted node's admitted set is
        the format's, and where a sibling pattern refuses every case the format states, the
        string the pattern itself names is the node's own next statement.
        ``{"format": "uri", "pattern": "^https://github\\.com/"}`` is the measured shape --
        no case of ``uri`` matches it and the reading gives ``"https://github.com/"``, which
        the node admits on both keywords.  Screened like every other candidate, so a reading
        the ``format`` refuses is not kept.

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

        **AND THE SAME READING AT A KEY A DECIDER READS** (:meth:`_recased`), which is this
        clause's own sentence one level down: a ``not`` whose subject names a key is the
        ``vast-tracker-asset`` shape with the ``enum`` at the CHILD instead of at the node,
        and the loop above cannot reach it because an object node states no ``enum`` of its
        own.  Where the deciders refuse the built object, the key the deciding statement
        itself names takes its own next value class.

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
        nodes = [
            node
            for at, _ in views
            for node in [self.node(document, at)]
            if isinstance(node, Mapping)
        ]
        read = _patterns(nodes)
        if len(read) == 1:
            reading = _patterned(read[0], _bound(nodes, "minLength") or 0, _bound(nodes, "maxLength"))
            if reading.held and not self.refusals(document, pointer, reading.value):
                return reading
        recased = self._recased(document, pointer, views, built)
        if recased is not None:
            return recased
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

    def _recased(
        self,
        document: str,
        pointer: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        built: Built,
    ) -> Built | None:
        """The built object with ONE key taken to its own next value class.

        **THE CONDITIONAL'S AND THE NEGATION'S COUNTERPART TO THE UNION BRANCH RETRY**
        (``adcp-client-python-hzio.13``: *"nothing varies an enum member at a key an ``if``
        names"*).  :meth:`_picks` varies one union's branches because a value merged from a
        union's first branch can be one a later branch also admits; the same is true of a key
        whose first ``enum`` member is the member a ``not`` forbids or an ``if`` selects an
        unsatisfiable consequent on, and nothing varied it.

        **THE KEY IS READ OFF THE DECIDING STATEMENT'S OWN TEXT and the VALUE off the key's
        own keywords**, so neither is a search.  :meth:`_names` answers which keys a statement
        names; :meth:`classes` answers which values the key's node admits -- "every member of
        an ``enum``, both sides of each bound and the bound itself", each already screened
        against the key's own node.  There is no solver here and nothing is enumerated that
        the document does not state.

        **A SUM AND NOT A PRODUCT**, which is :meth:`_picks`' own rule at this keyword: one
        key is varied at a time and the first candidate the node's screen admits and the
        deciders accept is the answer, so the cost is the sum over the named keys of their own
        class counts and never a cross-product over the object's keys.
        ``docs/plan/architecture.md`` §9 calls that cross-product a defect of the approach
        rather than a cost to control.

        ``None`` where the deciders accept the value already, where the value is not an
        object, or where no named key's own classes satisfy them -- and then the caller's
        last clause stands: a value the node's own screen admits is never DELETED by a
        decider.
        """
        if not built.held or not isinstance(built.value, Mapping):
            return None
        if not self._decides(document, views, built.value):
            return None
        for name in self._names(document, views, built.value):
            describing = [
                (f"{at}/properties/{bundle.escape_key(name)}", path)
                for at, path in views
                for node in [self.node(document, at)]
                if isinstance(node, Mapping) and name in (node.get("properties") or {})
            ]
            if not describing:
                continue
            at, path = describing[0]
            besides = tuple(p for p, _ in describing[1:])
            for case in self.classes(document, at, (*path, *besides)):
                if case.value == built.value.get(name):
                    continue
                candidate = {**built.value, name: case.value}
                if self.refusals(document, pointer, candidate):
                    continue
                if not self._decides(document, views, candidate):
                    self.counters.recased += 1
                    return Built(candidate, Source.CONSTRUCTED)
        return None

    def _names(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        value: Any,
    ) -> tuple[str, ...]:
        """The keys the statements that REFUSE this value name, in the document's own order.

        One statement at a time and only the ones that refuse: a decider the value already
        satisfies says nothing about which key to vary, and asking it would widen the set for
        no reading.  Then the keys are read off that statement's own subtree -- every
        ``properties`` entry it declares and every ``required`` member it demands, following
        the record's own storage reference and every subschema the ONE descent table names
        (:func:`codegen.bundle.subschemas`), because a ``not`` states its subject through an
        ``anyOf`` of ``$ref``\\ s as readily as inline and the key names are the same either
        way.

        **Terminating on the pointer set and not on a depth**, which is §9's own rule for a
        walk in this module: a pointer already seen is not walked again, so the walk is
        bounded by the statement's own subtree and no bound is introduced here.
        """
        out: list[str] = []
        for at, _ in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            stated = {k: node[k] for k in ("oneOf", "anyOf", "not") if k in node}
            if not stated:
                continue
            for keyword in stated:
                refused = any(
                    True
                    for _ in self.validator(document)
                    .evolve(schema={keyword: stated[keyword]})
                    .iter_errors(value)
                )
                if not refused:
                    continue
                pending = [
                    f"{at}{suffix}"
                    for held, suffix, _, _ in bundle.subschemas(node)
                    if held == keyword
                ]
                seen: set[str] = set()
                while pending:
                    where, held = self.through(document, pending.pop(0))
                    if where in seen or not isinstance(held, Mapping):
                        continue
                    seen.add(where)
                    for key in held.get("properties") or ():
                        if key not in out:
                            out.append(key)
                    for key in held.get("required") or ():
                        if isinstance(key, str) and key not in out:
                            out.append(key)
                    # Only the subschemas that talk about THIS instance: a
                    # ``properties`` entry's own ``required`` is a statement about
                    # another value and its key names are not this object's.
                    pending.extend(
                        f"{where}{suffix}"
                        for inner, suffix, _, _ in bundle.subschemas(held)
                        if inner in ABOUT_ONE_INSTANCE
                    )
        return tuple(out)

    def _views(
        self,
        document: str,
        pointer: str,
        stack: tuple[str, ...],
        pick: tuple[str, int] | None = None,
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
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

        ``answered`` is :attr:`Subject.picks`, and it reaches the walk through here for the
        same reason ``besides`` does: a conjunction the pointer's own ancestors supply
        carries the ancestors' unions with it, and the branch each of those is to be read at
        is the one the POINTER spells.
        """
        return self._reach(
            document, [(pointer, stack), *((at, stack) for at in besides)], pick, answered
        )

    def _reach(
        self,
        document: str,
        seeds: Sequence[tuple[str, tuple[str, ...]]],
        pick: tuple[str, int] | None = None,
        answered: tuple[tuple[str, int], ...] = (),
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """The transparent walk itself, from any set of positions describing one instance.

        **ONE walk, shared by :meth:`_views` and by :meth:`_settled`'s fold of a
        consequent**, because a consequent states what it states through a ``$ref`` and an
        ``allOf`` exactly as a conjunct does.  Two spellings of this walk is two readings of
        draft-07's composition grammar, and the one that was missing read a ``{"$ref": ...}``
        consequent as a node stating nothing.

        **A UNION'S BRANCH IS TAKEN FROM THREE PLACES AND IN ONE ORDER**: ``pick``, which is
        the retry varying ONE union and therefore beats everything; ``answered``, which is the
        branch the POINTER being constructed already spelled (:attr:`Subject.picks`); and
        failing both the document's own first branch.  The order is forced -- a retry that
        could not override an answered union would have exactly one reading of a subject
        available, and an answered union read at its first branch is the defect
        :class:`Subject` measures at 199 pairs.
        """
        out: list[tuple[str, tuple[str, ...]]] = []
        given = dict(answered)
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
                    if pick is not None and pick[0] == union:
                        index = pick[1]
                    else:
                        index = given.get(union, 0)
                    if suffix == f"/{keyword}/{index}":
                        pending.append((f"{at}{suffix}", (*path, f"{at}{suffix}")))
        return tuple(out)

    def _picks(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        answered: tuple[tuple[str, int], ...] = (),
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

        **A UNION THE POINTER HAS ALREADY ANSWERED IS NOT VARIED** (``answered``,
        :attr:`Subject.picks`).  The retry exists because a value merged from a union's FIRST
        branch can be one a later branch also admits, so reading the later branches is a
        different reading of the same node; a union whose branch the pointer itself spells is
        not a reading this walk gets to choose -- varying it would grade the class at
        ``#/oneOf/1`` against branch 2's value, which is a statement about another class.
        """
        given = {union for union, _ in answered}
        for at, _ in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            for keyword in ("oneOf", "anyOf"):
                members = node.get(keyword)
                if (
                    isinstance(members, list)
                    and len(members) > 1
                    and f"{at}/{keyword}" not in given
                ):
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
        """The value the merged statements name, by the ``type`` word they agree on.

        **AN ``enum`` SEVERAL STATEMENTS STATE IS AN INTERSECTION AND NOT THE FIRST OF
        THEM**, the same reading :func:`_words` already makes of ``type``: two statements
        about one instance both hold, so a member only one of them lists is not admitted.
        Taking the first statement's first member was measured: ``creative/creative-status-
        changed-webhook.json`` lists six states for ``transition.to`` and narrows them to
        ``["pending_review", "rejected"]`` in the consequent its own ``from`` selects, and
        the construction read ``"processing"`` off the wider list -- a value the document
        refuses on ``enum``, at a node whose conjunction it had already reached.  A ``const``
        is the same statement with one member, so it is screened against every stated
        ``enum`` rather than returned ahead of them.
        """
        nodes = [self.node(document, at) for at, _ in views]
        nodes = [n for n in nodes if isinstance(n, Mapping)]
        if not nodes:
            return Built(None, Source.CONSTRUCTED)
        admitted = _enumerated(nodes)
        for node in nodes:
            if "const" in node:
                if admitted is not None and node["const"] not in admitted:
                    continue
                return Built(node["const"], Source.CONSTRUCTED)
        if admitted:
            return Built(admitted[0], Source.CONSTRUCTED)
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
        the construction can reach.  Then the key a ``patternProperties`` entry or a
        ``propertyNames`` schema admits, which are the two places a document states what a
        name may be: **a ``patternProperties`` key is its pattern READ** (:func:`_patterned`,
        the same five constructs a string value is read by) and a ``propertyNames`` key is
        the value already built for that schema's own node -- so neither is a choice made
        here.  Failing all three the key is a free choice and the construction makes one;
        ``docs/plan/rebuild-plan.md`` §8 says exactly that of a mapping value.
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
        for at, path in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            table = node.get("patternProperties")
            for stated in table if isinstance(table, Mapping) else ():
                if len(extra) >= wanted:
                    break
                named = _patterned(stated, 0, None)
                if not named.held or named.value in placed or named.value in extra:
                    continue
                inner = self.value(
                    document, f"{at}/patternProperties/{bundle.escape_key(stated)}", path
                )
                if inner.held:
                    extra[named.value] = inner.value
            if len(extra) >= wanted or not isinstance(node.get("propertyNames"), Mapping):
                continue
            named = self.value(document, f"{at}/propertyNames", path)
            if not isinstance(named.value, str) or named.value in placed or named.value in extra:
                continue
            sub = node.get("additionalProperties")
            inner = (
                self.value(document, f"{at}/additionalProperties", path)
                if isinstance(sub, Mapping)
                else Built(None, Source.CONSTRUCTED)
            )
            if inner.held:
                extra[named.value] = inner.value
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
        values, and the element's OWN SUBTREE is where they come from -- one value with one
        field varied per member (:meth:`_distinct`), which is the reading an element that
        states an ``enum`` and an element that states an object both answer to.

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

        **AND SEVERAL ``contains`` DEMAND SEVERAL MEMBERS, one each, which is the keyword's
        own reading rather than a count this module chose.**  draft-07's ``contains`` is
        satisfied by SOME member, so two statements of it are two existential claims and one
        value conjoined from both satisfies them only where they agree; where they do not,
        a single member repeated satisfies exactly one and the document refuses the array on
        the other.  ``media-buy/request-proposals-response.json`` is the measured shape:
        ``purchase_continuation``'s legacy branch states ``losses.contains`` twice at its own
        conjuncts and a third time in the consequent its own ``source_adcp_version``
        selects, over an element ``enum`` of exactly those three members -- so the document
        admits the three-member array and the one-member reading built two of them and was
        refused on ``contains`` (``adcp-client-python-hzio.14``).

        The count such a set demands is the number of STATEMENTS, bounded by the node's own
        ``maxItems``: a bound the document states is a fact and not a budget, and where it
        is below that number the document admits no instance -- which the node's own screen
        then says, at ``maxItems``, rather than this reading guessing.
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
            # ONE member per existential statement, bounded by the node's own ceiling.
            most = _bound(nodes, "maxItems")
            demanded = max(count, len(wanted))
            count = min(demanded, int(most)) if isinstance(most, (int, float)) else demanded
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
        if len(wanted) > 1:
            built = self._one_each(
                document,
                element,
                wanted,
                count,
                distinct=any(node.get("uniqueItems") is True for node in nodes),
            )
            if built is not None:
                return built
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

    def _one_each(
        self,
        document: str,
        element: Sequence[tuple[str, tuple[str, ...]]],
        wanted: Sequence[tuple[str, tuple[str, ...]]],
        count: int,
        *,
        distinct: bool,
    ) -> Built | None:
        """One member per ``contains`` statement, each built from the ELEMENT and that one.

        The array's half of :meth:`_views`' own rule, read for an EXISTENTIAL keyword: a
        ``contains`` describes SOME member, so the statement to build a member from is the
        element's declaration conjoined with exactly ONE of them -- never with all of them at
        once, which is the universal reading and the one that empties the intersection where
        two of them disagree.

        ``None`` where this reading has nothing to add, and the caller then takes the
        one-member reading unchanged.  Two cases: a member the element and its ``contains``
        admit no value for, and a set whose members come out EQUAL under a ``uniqueItems``
        that forbids it -- there :meth:`_distinct` varies the element over its own subtree
        and this reading has no better answer than the one already there.
        The short list is padded with its FIRST member, because ``minItems`` above the number
        of existential statements is a count and says nothing about what fills it.
        """
        out: list[Any] = []
        for one, where in wanted:
            seed, path = element[0] if element else (one, where)
            besides = (
                (*(p for p, _ in element[1:]), one) if element else ()
            )
            member = self.value(document, seed, (*path, *besides), besides)
            if member.source is Source.BACK_EDGE:
                return None
            if not member.held:
                return None
            out.append(member.value)
        if distinct and (
            len(out) < count
            or any(
                out[i] == out[j]
                for i in range(len(out))
                for j in range(i + 1, len(out))
            )
        ):
            return None
        while 0 < len(out) < count:
            out.append(out[0])
        return Built(out[:count], Source.CONSTRUCTED)

    def _distinct(
        self, document: str, at: str, path: tuple[str, ...], count: int
    ) -> Built:
        """``count`` distinct members, VARIED over the element's OWN SUBTREE.

        ``uniqueItems`` beside a count above one asks for distinct MEMBERS, and distinct
        members of an OBJECT element are not distinct values of one node: they are one value
        with one FIELD varied, which is :meth:`subtree`'s own reading -- *"the node's admitted
        value with exactly ONE location replaced by one class of the node at that
        location"*.  So the source here is the subtree witness set and not
        :meth:`classes`, and the difference is the whole of this method: ``classes`` reads
        the element's own keywords, which for an object element distinguish ONE class -- the
        admitted value -- so the construction had one member where the document admits two.
        Measured at both nodes this bundle states (``creative/list-creatives-response.json``
        and ``media-buy/get-media-buys-response.json``, each at
        ``approval_scopes`` over the ``Scoped creative approval`` element): one class, SIX
        distinct subtree values, and the document admits two scoped approvals that differ in
        any field, so the schema was satisfiable and the construction had declined it.

        **AND IT TERMINATES ON THE ELEMENT'S OWN STRUCTURE AND NEVER ON A COUNT OF
        ATTEMPTS.**  :meth:`subtree` walks the nodes the element REACHES, once each, keyed
        and memoised like every other answer and closing a cycle on the pointer -- so what
        bounds the variation is how many nodes the element has and how many classes each of
        them distinguishes.  A member limit, a retry count or a depth parameter here would be
        a number this module chose standing in for a fact the element states, which is the
        one thing ``docs/plan/architecture.md`` §9 forbids by name.

        **EVERY CANDIDATE IS OFFERED TO THE ELEMENT WHOLE, which is where this screen is
        DEEPER than :meth:`refusals` and the only place that is true.**  A member stands
        alone at its own instance location, so what has to admit it is the element's whole
        node -- not the element's own keywords.  §9's shallow screen is sound for a value
        READ OFF a node, because each child's value was screened at the child; it is not
        sound for a value LIFTED past a conjunction the screen strikes, and the measurement
        says so: of the six distinct values at each of those two nodes, THREE are values the
        element refuses -- ``approval_status: "partially_approved"`` on the narrowing
        ``enum`` the element's own ``allOf`` states, ``"rejected"`` on the ``required``
        ``rejection_reason`` its first consequent demands, and a ``rejection_reason`` beside
        ``"pending_review"`` on the ``not`` its second states.  Taken shallowly, three of
        six members would have been values the document refuses.  The cost is one validation
        of one small value per candidate at the nodes that state ``uniqueItems`` beside a
        count -- six in this bundle -- and not a second screen at every node, which is the
        quadratic reading §9 strikes.

        An element that states an ``enum`` needs no special case and has none: its members
        are value classes of its own node, so :meth:`classes` contributes them and they are
        the first thing the subtree walk holds.  Measured over the four nodes whose element
        is the three-member ``losses`` ``enum`` against ``minItems: 2``, the members and
        their order are the document's own either way.

        Fewer than ``count`` distinct admitted members is still the honest answer and still
        says so, with the number the element reached.
        """
        node = self.node(document, at)
        whole = (
            self.validator(document).evolve(schema=node) if isinstance(node, Mapping) else None
        )
        values: list[Any] = []
        for case in self.subtree(document, at, path):
            if case.value in values:
                continue
            if whole is not None and not whole.is_valid(case.value):
                continue
            values.append(case.value)
            if len(values) == count:
                return Built(values, Source.CONSTRUCTED)
        return Built(
            None,
            Source.APPROXIMATED,
            f"uniqueItems demands {count} members and the element admits {len(values)}",
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
        self,
        document: str,
        pointer: str = "",
        stack: tuple[str, ...] = (),
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
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

        **``besides`` AND ``answered`` ARE :meth:`applied`'s TWO ARGUMENTS AND THEY MEAN
        THE SAME THING HERE** (:meth:`admits`).  A class is a whole value at this instance
        location, so it is built from the whole conjunction about that location -- and at a
        BRANCH pointer the rest of that conjunction is the enclosing node's.  Measured over
        the graded population before they were threaded through: all 239 pairs whose witness
        set came out empty were branch pointers, every class built at the branch node alone
        being one the applied schema refuses.
        """
        built = self.value(document, pointer, stack, besides, answered)
        node = self.node(document, pointer)
        if not isinstance(node, Mapping):
            return ()
        out: list[Class] = []
        if built.held:
            out.append(Class("", "the admitted value", built.value))
        views = self._views(document, pointer, stack, None, besides, answered)
        nodes = [
            node
            for at, _ in views
            for node in [self.node(document, at)]
            if isinstance(node, Mapping)
        ]
        out.extend(_value_classes(nodes))
        out.extend(_pattern_classes(nodes))
        for keyword, cases in _bound_classes(nodes, built).items():
            out.extend(Class(keyword, label, value) for label, value in cases)
        out.extend(self._branch_classes(document, views, besides, answered))
        return tuple(
            case for case in out if not self.refusals(document, pointer, case.value)
        )

    def _branch_classes(
        self,
        document: str,
        views: Sequence[tuple[str, tuple[str, ...]]],
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
    ) -> tuple[Class, ...]:
        """One class per branch of a union, and one per arm of a type list.

        A union branch is an ALTERNATIVE, so each branch is a class of the keyword rather
        than a conjunct of it -- which is the same reading :meth:`_views` makes when it
        takes the first branch and leaves the rest to here.

        **OVER THE VIEW SET AND NOT OVER THE NODE ALONE**, which is the correction the same
        measurement forces as the arguments above: a union about this instance can be stated
        by a co-describing conjunct rather than by the node itself --
        ``core/media-buy-frequency-cap.json`` states its ``anyOf`` at ``/allOf/0`` -- and a
        reading that only looked at the node had no class for its branches.  The branch's
        own value is built under the rest of the conjunction for :meth:`classes`' reason.

        **A UNION THE POINTER ITSELF ANSWERS CONTRIBUTES NO CLASS, and that clause is what
        keeps this from manufacturing a failure.**  :attr:`Subject.picks` is the branch the
        pointer SPELLS -- a class at ``#/oneOf/0`` is paired with branch 0, and branch 1's
        value is one the document admits at the ROOT and the class at branch 0 is right to
        refuse.  Offering it here would report that correctness as a narrowing.
        """
        decided = dict(answered)
        out: list[Class] = []
        for where, path in views:
            node = self.node(document, where)
            if not isinstance(node, Mapping):
                continue
            for keyword in ("anyOf", "oneOf"):
                members = node.get(keyword)
                if not isinstance(members, list) or f"{where}/{keyword}" in decided:
                    continue
                for index in range(len(members)):
                    at = f"{where}/{keyword}/{index}"
                    inner = self.value(
                        document, at, (*path, at, *besides), besides, answered
                    )
                    if inner.held:
                        out.append(Class(keyword, f"branch {index} of {where or '#'}", inner.value))
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
    def admits(self, document: str, pointer: str = "") -> tuple[Class, ...]:
        """**THE FIRST CHECK'S WITNESS SET for the subject a CLASS at this pointer names**,
        and the one entry point a grader of a class uses.

        :meth:`applied` is this method's shape for the single admitted value and carries the
        reasoning: a class is paired with its node read UNDER THE CONJUNCTION that reaches
        it, which is what ``SchemaBound.strict_validate`` validates against, so a witness
        built from the node ALONE is narrower than the class it is offered to.  The two are
        the same call with :attr:`Subject.besides` supplied as the rest of the conjunction
        AND put on the stack, which is :meth:`value`'s own rule.

        ``codegen.harness.check_admits`` is the caller, and it is the whole of the first
        check's witness set: no instance is drawn, nothing is sampled, and the set is a
        function of ``(document, pointer)`` and of nothing else -- which is
        ``docs/plan/final-state.md`` reading 1's *"both checks are a function of (class,
        document) and of nothing else"*, and the reason the check costs the same cold as
        warm.
        """
        read = self.subject(document, pointer)
        return self.subtree(
            document, pointer, (pointer, *read.besides), read.besides, read.picks
        )

    def subtree(
        self,
        document: str,
        pointer: str = "",
        stack: tuple[str, ...] = (),
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
    ) -> tuple[Class, ...]:
        """**THE FIRST CHECK'S WITNESS SET: one value per node of the subtree this node
        reaches**, each lifted to a whole value at THIS node.

        ``docs/plan/architecture.md`` §9: *"the valid witness is not one value per node: it
        is one value per node of the subtree the node reaches, each node contributing its
        own and no node contributing a combination."*  :meth:`classes` is the node's own
        contribution and this is the recursion over it.

        **WHY IT IS NOT :meth:`classes`, measured.**  ``classes`` reads the node's OWN
        keywords, which yields 5,027 classes over the 2,586 graded pairs -- 1.9 each -- and
        finds ONE pair narrower than its document, where walking the instance's leaves finds
        hundreds.  Reading 1 says every class accepts every value its document admits, and a
        string leaf three levels down whose own node states a length its parent never
        mentions is such a value: no witness built at the parent reaches it.  That gap was
        not a defect of the constructor, it was §9's own sentence, and the clause above is
        the sentence changed.

        **ONE SLOT AT A TIME, WHICH IS WHAT KEEPS THE BOUND ON COMBINATIONS.**  A lifted
        witness is the node's admitted value with exactly ONE location replaced by one class
        of the node at that location -- never two locations at once, never a product over
        locations.  So the set is a SUM over the subtree's nodes of each node's own classes,
        which is what §9's "linear in the document's nodes, each visited once" means once
        reach and multiplicity are told apart: a subtree walk visits each node once where a
        cross-product would visit each path.

        **AND EVERY LIFTED VALUE IS OFFERED TO THE DOCUMENT**, exactly as ``classes``
        screens its own: a class the inner node admits can still be one the ENCLOSING node
        refuses -- a conjunct about the same key, a ``oneOf`` that stops being satisfied by
        exactly one branch -- and a value the document refuses is a :class:`Mutation` and
        has no business in this set.  The screen is why the failure direction here is
        "finds fewer than it should" and never "reports a narrowing that is not one".

        Memoised on ``(document, pointer, stack)`` like every other answer, and the memo is
        seeded EMPTY before the recursion so a back edge contributes nothing rather than
        hanging -- the pointer closes the cycle here for the same reason it closes it in
        :meth:`value`, and no depth parameter is introduced.
        """
        key = (document, pointer, stack)
        held = self._subtrees.get(key)
        if held is not None:
            return held
        #: Seeded before the recursion, so a reference reaching a pointer already in
        #: progress answers "no witnesses from here" instead of recurring for ever.
        self._subtrees[key] = ()
        base = self.value(document, pointer, stack, besides, answered)
        out: list[Class] = list(self.classes(document, pointer, stack, besides, answered))
        if base.held:
            for slot, at, path, more in self._slots(
                document, pointer, stack, base.value, besides, answered
            ):
                for inner in self.subtree(document, at, path, more):
                    lifted = _substituted(base.value, slot, inner.value)
                    if lifted is _MISSING:
                        continue
                    if not self.refusals(document, pointer, lifted):
                        out.append(Class(inner.keyword, f"at {slot}: {inner.label}", lifted))
        self._subtrees[key] = tuple(out)
        return self._subtrees[key]

    def _slots(
        self,
        document: str,
        pointer: str,
        stack: tuple[str, ...],
        value: Any,
        besides: tuple[str, ...] = (),
        answered: tuple[tuple[str, int], ...] = (),
    ) -> Iterator[tuple[tuple[Any, ...], str, tuple[str, ...], tuple[str, ...]]]:
        """Each child position of this node that has a LOCATION in ``value``.

        ``(slot, pointer, stack, besides)``: the slot is the one-segment instance location,
        and the rest is the child node's, read through :meth:`_views` so a conjunct's
        ``properties`` is reached exactly as :meth:`_object` reaches it -- one descent, and
        not a second reading of which keyword descends where.

        **ONE ENTRY PER INSTANCE LOCATION AND NEVER ONE PER DESCRIBING POSITION**, which is
        :meth:`_object`'s own rule for the same descent: *"a key several statements describe
        gets ONE value built from all of them"*, because *"two pins on one location do not
        narrow the node -- they empty it"*.  The first describing position is the child's
        pointer and the rest are its ``besides``, so a key the node's own ``properties`` and
        a conjunct's entry both describe contributes one subtree walk under the whole
        conjunction rather than two under halves of it.

        **``properties`` and ``items`` ONLY, and the omission is named rather than
        silent.**  A mapping value (``additionalProperties``, ``patternProperties``) and a
        tuple-form ``items`` list also have locations, and a witness at one of them is a
        witness this set does not yet carry.  They are left out because the key is a free
        choice at those positions and this method would have to make it, which is a second
        reading of :meth:`_spare`'s decision; the measured cost of the omission is reported
        beside the coverage rather than assumed to be nil.
        """
        views = self._views(document, pointer, stack, None, besides, answered)
        #: Grouped by the instance LOCATION, in the order the views state it, so the
        #: entry below is one per location with every describing position in it.
        keys: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
        items: list[tuple[str, tuple[str, ...]]] = []
        for at, path in views:
            node = self.node(document, at)
            if not isinstance(node, Mapping):
                continue
            declared = node.get("properties")
            if isinstance(declared, Mapping) and isinstance(value, Mapping):
                #: **EVERY DECLARED KEY, not only the ones the admitted value placed.**  The
                #: admitted value is minimal, so it carries the required keys and omits the
                #: optional ones -- and a node under an optional property is a node the
                #: subtree REACHES, which is the clause this method implements.
                #: :func:`_substituted` places the key and the enclosing node's screen
                #: decides whether the placement is one the document admits.
                for name in declared:
                    if isinstance(name, str):
                        keys.setdefault(name, []).append(
                            (f"{at}/properties/{bundle.escape_key(name)}", path)
                        )
            if isinstance(node.get("items"), Mapping) and isinstance(value, list) and value:
                items.append((f"{at}/items", path))
        #: ``(*path, *more)`` and not ``(*path, at, *more)``, which is :meth:`_object`'s and
        #: :meth:`_array`'s own spelling of the child's key: a caller that put the child's
        #: own pointer on the stack would key the same answer differently from them and the
        #: memo would miss on every child the walk already built.
        for name, where in keys.items():
            at, path = where[0]
            more = tuple(p for p, _ in where[1:])
            yield (name,), at, (*path, *more), more
        if items:
            at, path = items[0]
            more = tuple(p for p, _ in items[1:])
            yield (0,), at, (*path, *more), more

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


def _pattern_classes(nodes: Sequence[Mapping[str, Any]]) -> tuple[Class, ...]:
    """A string each stated ``pattern`` ADMITS, read off the pattern's own atoms.

    **The class a ``pattern`` distinguishes, which is the same rule as an ``enum``'s
    members and a ``format``'s cases** (:func:`_value_classes`): the keyword divides the
    strings that match from the strings that do not, and the class on the matching side is
    a value the document admits.  The far side is that keyword's MUTATION
    (:func:`_candidates`) and is not a class.

    **AND IT IS NOT THE SAME VALUE AS THE ADMITTED ONE, which is why it is a class at all.**
    :func:`_string` reads ``format`` FIRST, so a node stating ``format: uri`` beside
    ``pattern: ^https://`` takes ``https://example.com`` from the format table and the
    pattern's own minimal match is never offered.  Measured over the graded population: that
    value is ``'https://'`` -- a string the pattern matches, the document admits, and
    pydantic's URL type refuses with ``url_parsing``, "empty host" -- and it is the finding
    at 40 of the 68 pairs the deleted leaf sampler reached and the construction did not.

    **DERIVED FROM THE KEYWORD AND NOT DRAWN FROM IT.**  What the sampler did here was
    ``hypothesis.strategies.from_regex`` with an EXAMPLE COUNT on it; :func:`_patterned`
    reads the pattern's atoms and quantifiers and takes the document's own first member of
    each, so the witness is a function of the pattern alone and the count is gone with the
    draw.
    """
    low = _bound(nodes, "minLength")
    high = _bound(nodes, "maxLength")
    out: list[Class] = []
    for pattern in _patterns(nodes):
        built = _patterned(pattern, int(low) if isinstance(low, (int, float)) else 0, high)
        if built.held:
            out.append(Class("pattern", f"a string {pattern!r} admits", built.value))
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


def _substituted(value: Any, slot: tuple[Any, ...], new: Any) -> Any:
    """``value`` with the single location ``slot`` replaced by ``new``, or :data:`_MISSING`.

    One segment, which is :meth:`Construction.subtree`'s whole bound on multiplicity: a
    substitution that could reach two locations at once would make the witness set a product
    over locations where §9 states a sum over nodes.  The recursion composes depth by
    lifting one segment per level, so a leaf three levels down is reached by three
    one-segment substitutions and never by a path expression.

    :data:`_MISSING` where the slot names nothing in this value -- a key the admitted value
    did not place because the document makes it optional, an index an empty array has no
    member at.  Such a position has no witness to lift and that is a fact about the value
    rather than a failure.
    """
    if len(slot) != 1:
        return _MISSING
    where = slot[0]
    if isinstance(where, str) and isinstance(value, Mapping):
        #: **A KEY THE ADMITTED VALUE OMITS IS PLACED, NOT SKIPPED**, which is what takes the
        #: witness set from 143 of the sampler's 293 to its full reach.  The admitted value
        #: carries the REQUIRED keys (that is what makes it minimal), so every node under an
        #: OPTIONAL property was unreachable: its document states what the value there must
        #: satisfy, the class must accept it, and no witness built at the parent reached it.
        #: Placing the key is still one segment and still a sum -- one witness per node, with
        #: the enclosing node's screen deciding whether the placement is admissible.
        return {**value, where: new}
    if isinstance(where, bool):
        return _MISSING
    if isinstance(where, int) and isinstance(value, list) and len(value) > where:
        return [*value[:where], new, *value[where + 1 :]]
    return _MISSING


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
