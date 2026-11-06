"""Property-based conformance harness for a (JSON Schema document, model) pair.

Knows nothing about any particular schema vocabulary, directory layout, code
generator or model package.  Its whole input is:

  * ``schema``  - a JSON Schema document, as a dict, with every ``$ref`` already
                  resolved (use ``resolve`` below, or resolve it yourself).
                  ``resolve`` inlines a fresh copy of a subtree at every site
                  that references it, so it costs O(paths through the ref
                  graph) -- affordable for one document, and not for a bundle:
                  it left 63 of 1,033 unresolvable at any practical budget.
                  For a whole population use ``codegen.resolved_cache``, which
                  memoizes per URI and composes by reference. This module does
                  not import it, and must not: ``selfcheck`` asserts that
                  ``harness`` imports nothing beyond its four libraries and
                  stdlib, so the choice belongs to the caller.
  * ``model``   - anything ``pydantic.TypeAdapter`` accepts: a BaseModel subclass,
                  a RootModel, an Enum, a bare annotation, a union alias.
  * ``accept``  - the entry point an instance is offered through, SUPPLIED by the
                  caller.  It used to be sniffed off the model with ``getattr``,
                  and sniffing cannot tell a model that has no entry point from
                  one whose entry point is missing: the fallback was the model's
                  CONSTRUCTOR, which is not an accepted set, so a model that
                  should have had one was graded wide and green.  The caller
                  knows which it is; this module does not and now does not guess.

**ONE CLASS AGAINST ONE SCHEMA, AND NO ITERATION OVER KEYWORDS** (section 6).  Per
pair, each of these happens and each is O(1) in the document's keyword count:

  the accepts check (``check_accepts``)
      schema -> payload -> model: an instance the schema admits, the model admits.
      It then DUMPS what it constructed and validates the dump against the same
      document (``AcceptsResult.round_tripped``), which is the one thing in this
      module that reads what the class does with a value rather than whether it
      took it.

  the liveness check (``check_liveness``)
      one payload the DOCUMENT refuses, routed through the entry point the caller
      supplies -- ``strict_validate``, whose schema half answers.  It proves that
      class's schema half is CONNECTED and that the ref it names resolves to the
      document it names.  It is not a measurement of the class: pydantic is
      deliberately less strict than the schema, so a refusal says the document
      answered (D4).

  the widening obligation (``check_widening``)
      every approximation the artifact declares, put to a draw: the value class the
      dropped keyword distinguishes is offered to the model, which has to accept it.
      A declaration no draw can earn is a narrowing wearing a declaration.

**WHAT THIS MODULE USED TO DO AND NO LONGER DOES, and the reason is stronger than
its cost.**  The refuses check mutated ONE KEYWORD at a time, drew an instance the
mutated schema accepts, and passed it to the caller's ``accept`` -- which validates
against THE DOCUMENT before constructing.  So a step site asserted that
``jsonschema`` rejects a payload violating the schema it was handed, and the
generated class took no part in the outcome: on ``core/pagination-request.json`` a
model with ``Any`` on every field accepted, refused 75 of 75 instances and recorded
no wrong acceptance, exactly as a faithful one did.  27,791 of those sites over the
graded population were the suite's entire wall clock, spent on a property of a
third-party validator.  A payload the schema refuses is informative
about the WIRING and nothing else, so ``check_liveness`` sends exactly one.

**There is no process-global canonicalisation memo here**, and the documents this
grades arrive as the DOCUMENT OF RECORD (``bundle.record``, which inlines every
cross-document ``$ref`` and rewrites nothing), so the one recursion reference
resolution needs has happened before the harness sees anything.  What remains is the
library's own: ``merged`` re-enters ``canonicalish``
for every subschema it sorts, so one ``from_schema`` call re-canonicalises the same
subtrees of one document.  ``canonicalisation_shared_within_one_call`` shares those
for the duration of ONE check and drops them on the way out -- its docstring carries
the measurement that forces it, and why that is not the unbounded process-global
dict section 6 deleted.
"""

from __future__ import annotations

import copy
import ctypes
import ctypes.util
import functools
import hashlib
import importlib
import itertools
import json
import pkgutil
import re
import traceback
import zlib
from collections import Counter
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, NamedTuple

import hypothesis
import hypothesis_jsonschema
import jsonschema
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st
from hypothesis.errors import HypothesisException
from hypothesis.internal.conjecture.engine import BUFFER_SIZE as _HYPOTHESIS_BUFFER_SIZE
from hypothesis_jsonschema import _canonicalise as _hjs_canon
from hypothesis_jsonschema import _from_schema as _hjs_from
from hypothesis_jsonschema import from_schema
from hypothesis_jsonschema._canonicalise import HypothesisRefResolutionError
from hypothesis_jsonschema._resolve import LocalResolver
from pydantic import TypeAdapter, ValidationError

from adcp.types._base import (
    APPROXIMATIONS,
    KINDS,
    UNDERDETERMINED,
    Approximation,
    SchemaBound,
    SchemaRef,
)
from codegen import attribution, bundle, dump_exemptions, keywords
from codegen.keywords import Position, Rung

# --------------------------------------------------------------------------- #
# formats
# --------------------------------------------------------------------------- #
# hypothesis_jsonschema ignores a `format` it does not know, silently and without
# a warning, which turns an unsupported format into arbitrary text and so into a
# false direction-1 failure.  A caller supplies a strategy per format its
# documents use; `missing_formats` says which ones still need one.
BUILTIN_FORMATS: frozenset[str]
try:  # the name is private, so degrade rather than break on an upgrade
    from hypothesis_jsonschema._from_schema import STRING_FORMATS as _BF

    BUILTIN_FORMATS = frozenset(_BF)
except ImportError:  # pragma: no cover
    BUILTIN_FORMATS = frozenset()


#: **The ``format`` strategies the LIBRARY does not ship**, for a caller to hand back as
#: ``custom_formats``.
#:
#: Declared here and not by each caller, because there are two of them and a drift between
#: them is silent in the direction that matters: the suite grading with a strategy the RUN
#: does not have makes the run's verdict table report ``missing_formats`` on pairs the suite
#: passes, and a reader comparing the two would be comparing two instruments.  It is a fact
#: about :data:`BUILTIN_FORMATS` -- which formats this library ships a strategy for -- and
#: that is a fact this module already reads.
#:
#: The bundle uses three formats at a schema position in the graded tree: ``uri`` (35
#: sites), ``date-time`` (27) and ``uuid`` (1).  The library ships the first two.
#:
#: **Each entry is GRADED before it is trusted**, by ``check_format_strategy``: a strategy
#: emitting values the format itself refuses makes every site using it pass vacuously, and
#: a vacuous pass is reported by nothing.
#: ``tests/test_emit.py::test_every_format_strategy_is_graded_before_it_is_trusted`` is the
#: reading, and it asserts over this dict rather than over a copy of it.
FORMAT_STRATEGIES: dict[str, st.SearchStrategy] = {"uuid": st.uuids().map(str)}


def format_occurrences(schema: Any) -> Counter[str]:
    """Every ``format`` annotation at a schema position, COUNTED.

    ``formats_used`` is this, deduped. The count is the separate question: a format
    used once and a format used 46 times are the same membership and very different
    populations, and a verdict read off a population nobody counted is a verdict
    over however many sites there turned out to be -- including none.
    """
    out: Counter[str] = Counter()

    def rec(node: Any) -> None:
        if isinstance(node, list):
            for v in node:
                rec(v)
            return
        if not isinstance(node, dict):
            return
        f = node.get("format")
        if isinstance(f, str):
            out[f] += 1
        for k, v in node.items():
            if k in _DESCEND_MAP and isinstance(v, dict):
                for vv in v.values():
                    rec(vv)
            elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
                rec(v)
            elif k in _DESCEND_LIST and isinstance(v, list):
                rec(v)

    rec(schema)
    return out


def formats_used(schema: Any) -> set[str]:
    """Every ``format`` value appearing at a SCHEMA POSITION in a document.

    Position is the whole of it, and a walk that ignores position reports formats
    that do not exist. ``examples``, ``example``, ``default``, ``const`` and
    ``enum`` hold INSTANCE data, so a dict beneath one of them is a value: its
    ``format`` key is a data field with a name that collides, not a format
    annotation, and no generator ever consults it. A bundle met here illustrated a
    field-mapping object whose own ``format`` property named a date layout, inside
    an ``examples`` array, at 46 places. The blanket walk reported that layout as an
    uncovered format and a strategy was written for it; the strategy covered nothing
    and its only effect would have been to stop ``missing_formats`` saying so. That
    is strictly worse than the silence it was meant to fix, because the silence is
    reported and the quiet is not.

    Skipping those five keyword NAMES wherever they appear is not the same fix and
    is wrong: a property may legitimately be named ``default``, and in that bundle 95
    were. So this descends only where a subschema can legally appear, by the same
    tables ``steps`` descends (declared with it below, so the two walks cannot come
    to disagree about what a schema position is).
    """
    return set(format_occurrences(schema))


def missing_formats(schema: Any, custom_formats: Mapping[str, Any]) -> set[str]:
    """Formats the document uses that neither the library nor the caller covers."""
    return formats_used(schema) - BUILTIN_FORMATS - set(custom_formats)


# --------------------------------------------------------------------------- #
# resolution
# --------------------------------------------------------------------------- #
def _inlined(doc: Any, resolver: LocalResolver) -> Any:
    """``doc`` with every ``$ref`` under it inlined ONCE, and the same object placed at
    every occurrence.

    **THIS IS** ``bundle.recorded``'s **OWN RULE, APPLIED TO THE LOCAL REFERENCE THAT
    INLINER LEAVES**, and the reason it is written here rather than delegated is the
    reason stated at :func:`bundle.recorded`: "an inliner that changes nothing needs no
    fold."  The library's ``resolve_all_refs`` was what stood here, and it does two
    things beside inlining that this does not:

    * it CANONICALISES at every reference.  ``merged([siblings, target])`` calls
      ``canonicalish``, whose first statement is
      ``json.loads(encode_canonical_json(schema))`` -- a round trip of the WHOLE subtree
      through text, at every one of its own recursive calls, so one node's resolution
      writes and re-reads its text once per ancestor above every subschema of it.  This
      is the same disease ``codegen.bundle``'s memo had and the same cure: nothing here
      is keyed on, or rebuilt from, the text of a subtree.
    * it holds NO MEMO, so a document whose text is a DAG is walked as the tree that
      DAG unfolds to.  ``bundle.stored``'s whole point is that the record's text is a
      DAG -- ``core/mcp-webhook-payload.json``'s 957,187 nodes are 6,442 distinct ones,
      one of them placed 1,957 times -- and ``bundle.expanded`` below hands that sharing
      straight through.  Keyed on ``id``, the walk costs the DAG and not its unfolding.

    MEASURED on ``core/creative-localization-readback.json``, whose
    ``#/definitions/resolvedAssets`` is 2,213,256 bytes of TEXT inside a document whose
    distinct content is 140,208 bytes: resolving
    ``#/properties/variants/items/oneOf/0`` -- a node of 2,290 bytes holding two
    references to that one entry -- did not finish in 341.5 s under the library's
    resolver, with ``tracemalloc`` reporting 19.7 MiB flat at ``json/decoder.py`` for
    the whole of it.  The cost was never retention; it was the text round trip.

    **The POSITION is carried because the sibling rule reads it** and for no other
    reason: :func:`bundle._beside` is called here, so "which side wins where the
    referring node and its target both state a key" is answered in ONE place for both
    inliners.  Measured over the 3.2 bundle's records: 394 distinct ``$ref``-bearing
    nodes, 57 of which carry a sibling, and every one of those 57 siblings is
    ``description`` or ``deprecated`` -- an annotation, so the referring value wins and
    nothing constraining is at stake today.

    **A ``definitions`` / ``$defs`` ENTRY is not descended, and that is the one place
    this is narrower than** :func:`bundle.recorded`.  ``bundle.reaches`` is the reading:
    validation and the lowering "start at a declared pointer and descend by assertion
    keywords, which never cross a section boundary", and this copy has exactly two
    readers -- ``jsonschema`` and ``from_schema`` -- which both descend that way.  So an
    entry inlined here would add text no reader of the copy consults, and the text is
    not free: ``hypothesis_jsonschema``'s own validator cache keys on
    ``json.dumps(schema, sort_keys=True)``.  The reference in the entry is left as the
    record writes it, which is what the library's resolver did too (it descends neither
    keyword), so no position loses an inlining it had.

    A reference that resolves THROUGH ITSELF raises rather than recursing, which is the
    answer the library gave by ``RecursionError``: :func:`check_pair` catches either and
    grades the unresolved node, so the outcome is the same and the diagnosis is better.
    """
    #: The inlined answer per key, and the key's first component is ``id``, so every node
    #: this is handed has to stay alive for the call -- ``kept`` is what keeps it.  The
    #: nodes are ``bundle.expanded``'s, built by the caller and dropped with it.
    held: dict[tuple[int, str, Position], Any] = {}
    kept: list[Any] = []
    #: The references open on THIS path, which is the cycle guard.  A path and not a
    #: visited set, for ``bundle._Where``'s reason: a diamond is not a cycle.
    chasing: set[str] = set()

    def walk(node: Any, position: Position) -> Any:
        if not isinstance(node, dict):
            return node
        key = (id(node), resolver.resolution_scope, position)
        if key in held:
            return held[key]
        uri = node.get("$ref")
        if isinstance(uri, str):
            url, target = resolver.resolve(uri)
            if url in chasing:
                raise HypothesisRefResolutionError(
                    f"$ref:{uri!r} resolves through itself at {url!r}"
                )
            chasing.add(url)
            resolver.push_scope(url)
            try:
                placed = walk(target, position)
            finally:
                resolver.pop_scope()
                chasing.discard(url)
            #: Only where a sibling exists, because ``_beside`` builds a fresh mapping
            #: and a bare ``{"$ref": ...}`` -- 337 of the 394 -- has nothing to put in
            #: one.  Placing the shared object itself is what makes the occurrences free.
            #: ``_beside`` and not a second spelling of §4's sibling rule, which is what
            #: the private name buys: ``tests/test_accepts_corpus.py`` patches that very
            #: object as the seam a perturbation replaces, so one rule has one site and
            #: one perturbation reaches both inliners.
            out = placed if len(node) == 1 else bundle._beside(placed, node, position)  # noqa: SLF001
        else:
            done = {
                suffix: walk(sub, holds)
                for _, suffix, sub, holds in bundle.subschemas(node)
                if isinstance(sub, dict) and holds is not Position.DEF
            }
            out = {
                k: bundle.rebuilt(k, v, done, missing=_itself) if k in bundle.DESCENDS else v
                for k, v in node.items()
            }
        held[key] = out
        kept.append(node)
        return out

    return walk(doc, Position.ROOT)


def _itself(one: object) -> object:
    """What a value :func:`bundle.subschemas` did not reach becomes: itself.

    ``bundle.rebuilt`` defaults to a DEEP COPY, for the reason stated there -- "a record
    that aliased the bundle's own object would let one reader's edit reach another's".
    Nothing it could alias here is the bundle's: :func:`resolve` hands this
    ``bundle.expanded``'s output, which rebuilds every mapping and every list it walks,
    so the whole of what :func:`_inlined` reads is already a copy of the record made for
    this one call.  ``bundle.stored`` passes the identity for the same kind of reason.
    """
    return one


def resolve(
    schema: dict, *, store: Mapping[str, Any], base_uri: str = "", referrer: Any = None
) -> dict:
    """Inline every ``$ref`` the node holds, against the document it is a node of.

    **CONFINED TO DRAWING, and that is the whole of what it is for now.**
    ``docs/plan/architecture.md`` §4 keeps the payload generator's resolver inside the
    accepts check, where it may canonicalise its own copy because that copy is an
    instrument of ONE check and is not the document.  :func:`check_accepts` is the one
    caller, it hands the copy to ``from_schema`` and to nothing else, and nothing
    downstream reads what it writes.  The DOCUMENT is ``bundle.record``'s, which inlines
    and rewrites nothing -- so the six folds that undid this resolver's rewritings are
    deleted (§9) and none of them can come back by this door.

    **AND THE COPY IS NO LONGER CANONICALISED EITHER**, which is the licence §4 grants
    being declined rather than withdrawn: :func:`_inlined` says what the delegation cost
    and why nothing downstream wanted it.  ``from_schema`` canonicalises what it is
    handed, so a draw pays that once, inside the draw, over the schema it is actually
    going to generate from -- which is the pair's own cost and not resolution's.

    ``store`` maps an absolute URI to the document at it.  A ``$ref`` that is not
    in the store raises, by the resolver's design: it never fetches remotely.

    ``referrer`` is what a LOCAL pointer (``#/definitions/x``) resolves against, and
    it defaults to ``schema`` -- which is right for a whole document and wrong for a
    NODE of one.  ``bundle.record`` inlines a cross-document reference and leaves a
    local one, so a nested node's own ``$ref`` is a pointer into the DOCUMENT ROOT:
    given the node as its own referrer, the resolver raises
    ``_RefResolutionError: Unresolvable JSON pointer``.  Pass the document and the
    same call inlines it (``salesagent-j3k2l.28``).
    """
    #: **THE RECORD'S OWN STORAGE IS PUT BACK HERE AND NOT LEFT TO THE RESOLVER**, which
    #: is ``bundle.expanded``'s whole reason.  ``bundle.stored`` writes a repeated subtree
    #: once and references it at each occurrence, and a resolver that holds no memo merges
    #: a FRESH resolution at every ``$ref``, so delegating the storage to one reintroduces
    #: exactly the duplication the storage removed -- measured at 0.02 s per pair with the
    #: expansion here against 3.4 s without it over ``adagents.json``'s 25 pairs.
    #: Expanded here the generator is handed the same content and the same sharing it was
    #: handed before the storage existed.
    #:
    #: The SCOPE is expanded too, and against itself: it is what a local pointer resolves
    #: against, so a storage reference left in it would resolve to a node holding another
    #: reference that would then have to be chased per occurrence.
    #:
    #: **AND THE ``copy.deepcopy`` THAT STOOD HERE IS GONE WITH THE LIBRARY CALL IT
    #: PROTECTED.**  ``resolve_all_refs`` mutates the mapping it is handed, so a copy was
    #: the only thing between it and the record; :func:`_inlined` writes nothing it did
    #: not build.  What it reads is already a copy -- ``bundle.expanded`` rebuilds every
    #: mapping and every list it walks -- so the deep copy was a second one, of the
    #: document AND of the node, per pair.
    scope = referrer if referrer is not None else schema
    doc = bundle.expanded(schema, scope)
    scope = bundle.expanded(scope, scope)
    resolver = LocalResolver(base_uri=base_uri, referrer=scope, store=dict(store))
    return _inlined(doc, resolver)


def strategy(schema: dict, custom_formats: Mapping[str, Any]) -> st.SearchStrategy:
    return from_schema(schema, custom_formats=dict(custom_formats))


# --------------------------------------------------------------------------- #
# §8: a referenced document is a FIXTURE at a referring position, not a draw
# --------------------------------------------------------------------------- #
#: **The positions at which a referenced document describes an instance of ITS OWN**, read
#: off the descent column rather than named.  §8's rule is that "every subtree a class
#: reaches through a reference is a document with a pair of its own, graded there -- so at
#: the referring position the instrument needs one instance that document admits and one it
#: refuses, not a generated space."  The subtree has to describe its own instance for that
#: to be true: a PROP value, an ELEM member, a MAPV or KEY value and a DEF entry each name
#: a position of the payload that the referenced document, and nothing else, decides.
#:
#: **A CONJ, a RULE, a ``not`` and a ``oneOf`` branch are NOT such positions, and this is
#: the one clause the rule as written does not carry** (measured, see :class:`Fixtures`).
#: A conjunct co-describes the ENCLOSING instance, so two references at two conjuncts of one
#: ``allOf`` are two documents deciding one value -- and substituting each one's own fixture
#: independently makes the intersection EMPTY, which is a draw that reports
#: ``Unsatisfiable`` rather than a cheap one.  Measured on
#: ``media-buy/get-products-response.json#``, whose root states
#: ``allOf: [{$ref: core/version-envelope.json}, {$ref: core/protocol-envelope.json}, ...]``:
#: one fixture per conjunct draws nothing at all.
#:
#: So such a reference is TRANSPARENT instead: :func:`referring_positions` reads THROUGH it
#: and keeps looking for own-instance positions below, which is the same reading
#: ``architecture.md`` already makes of the record's storage -- "a reader asking what the
#: document states reads through the storage".  The fixtures then land inside the
#: conjunct, at its own ``properties`` and ``items``, where they do not meet each other.
_OWN_INSTANCE = frozenset(
    {Position.PROP, Position.ELEM, Position.MAPV, Position.KEY, Position.DEF}
)

#: How deep the transparent walk follows a reference before it stops looking.  The bundle's
#: reference graph is a DAG with diamonds rather than a tree (``bundle._Where``), so the
#: guard that terminates the walk is the visited SET below and this is only a bound on an
#: unreasonable answer.
_FIXTURE_DEPTH = 12


#: "There is no fixture for this position", told apart from a fixture that IS JSON
#: ``null`` -- which a document can admit, so ``None`` cannot carry both answers.
#: :class:`_Draws` records the same defect one key space over, where ``[None]`` meant both
#: "the draw produced null" and "the draw failed".
NONE: Any = object()


#: **The two descending keywords a RESTRICTION does not travel through**, which is the one
#: thing :func:`locations` has to know and the whole of why it is a keyword set rather
#: than a position set.
#:
#: **AND :func:`locations` DOES NOT READ IT TODAY**, which is a defect this set is kept to
#: name rather than a reason to delete it (``adcp-client-python-d81a``'s prune pass): the
#: walk descends through an ALLOW-LIST -- :data:`_CONJOINS`, :data:`_CONDITIONAL` and the
#: child keywords it names inline -- so ``not`` and ``if`` are excluded by omission.  The
#: two readings agree today and nothing holds them together, so adding ``if`` to
#: :data:`_CONDITIONAL` would place a fixture under an inverting keyword and this set would
#: not stop it.
#:
#: ``not`` and ``if`` each hold their subschema at
#: ``Position.RULE``, and so do ``then``, ``else`` and ``dependencies`` -- so the position
#: cannot tell them apart and the keyword is what decides.
#:
#: Replacing a subschema by something NARROWER makes the enclosing node narrower at every
#: other descending keyword: a property, an element, a mapping value, a key, an ``allOf``
#: conjunct, an ``anyOf`` branch, a ``then`` and an ``else`` all pass a restriction
#: straight up.  Under these two it INVERTS: ``not S`` admits everything ``S`` refuses, so
#: narrowing ``S`` WIDENS the node, and ``if S then T`` lets every instance outside ``S``
#: through vacuously, so narrowing ``S`` widens the node too.  A fixture placed under
#: either is therefore not a restriction of the pair's node, the draw can produce an
#: instance the document REFUSES, and the saving would be bought with a false verdict.
#:
#: ``oneOf`` and ``anyOf`` are absent for a third reason and are handled where they arise
#: rather than here: a union is non-monotone in the other direction -- restricting one
#: branch can make an instance that used to match two branches match one, which a ``oneOf``
#: then ADMITS -- so a union node is a FRONTIER in its own right, replaced by an ``enum``
#: of values screened against the whole node, and never pinned branch by branch
#: underneath one (:meth:`Fixtures.narrowed`).
_INVERTS = frozenset({"not", "if"})

#: **The keyword whose subschema describes the SAME instance the node does
#: UNCONDITIONALLY, so the statements at it CONJOIN.**  draft-07 applies every ``allOf``
#: conjunct to the instance the enclosing node describes, so a value satisfying the node
#: satisfies all of them at once -- which is why :func:`locations` collects them together
#: and :meth:`Fixtures.value` draws from their conjunction rather than from any one of
#: them.  ``if`` is not one, and :data:`_INVERTS` says why.
_CONJOINS = frozenset({"allOf"})

#: **A consequent describes the same instance CONDITIONALLY, so it gets a SCOPE of its own
#: rather than joining the conjunction.**  Measured on
#: ``compliance/comply-test-controller-request.json#``, a 30-way discriminated dispatch:
#: read as unconditional conjuncts, the 30 consequents' statements about ``/params``
#: grouped into ONE demand of 8,158,816 bytes -- a value satisfying all thirty scenarios
#: at once, which no value does -- so the pin failed and the whole 8.17 MB node went to
#: the generator.  Scoped, each consequent is pinned on its own, and at most one of them
#: applies to any instance because the conditions are exclusive.
#:
#: The residual risk is named rather than hedged: two consequents whose conditions can
#: BOTH match are two pins that meet, and the draw then yields nothing.  That is a
#: ``strategy_error`` with ``hypothesis``'s own filtered-draw count -- a non-pass with a
#: name, never a green -- and the unconditional statements are conjoined into every
#: consequent's value so a consequent's pin cannot conflict with the node's own.
_CONDITIONAL = frozenset({"then", "else"})

#: **The keywords whose subschema describes a CHILD of the node's instance, and which of
#: them is REPLACED where several decide one location.**  A location's value is drawn from
#: the conjunction of every statement about it; only the OWNING position is replaced by
#: the pin, because the others then hold a constraint the pinned value already satisfies
#: and leaving them alone cannot make the node empty.
#:
#: * ``properties`` OWNS a named key.  Every ``patternProperties`` entry whose pattern
#:   matches that key also states something about it -- draft-07 applies all of them -- so
#:   those are conjoined and left standing.  A pattern entry is never the owner, because
#:   one entry can reach several keys and a single pin cannot answer for all of them.
#: * ``items`` in its SINGLE-SCHEMA form OWNS every element.  ``contains`` states
#:   something about one of them, so it is conjoined and left standing: with every element
#:   pinned to a value ``contains`` also admits, the keyword is satisfied rather than
#:   contradicted.  Measured on ``adagents.json#/oneOf/1/allOf/0/anyOf/1``, whose
#:   ``formats`` node is ``{contains, items, minItems, type}`` and 494,960 bytes: with
#:   ``contains`` read as a conflict the frontier was EMPTY and the whole subtree went to
#:   the generator untouched.
#: * ``additionalProperties`` in its schema form OWNS the keys no other keyword names,
#:   which is a location of its own and meets nothing.
#:
#: The rest are left to the draw.  A TUPLE-valued ``items`` decides one index that
#: ``additionalItems`` also reaches, and ``propertyNames`` decides a key and not a value --
#: both are §8's own named caveat, "two fixtures can still meet on one instance through
#: ``uniqueItems`` or a tuple-valued ``items``".
#:
#: **READ OFF THE TABLE'S OWNERSHIP COLUMN and not retyped here** (§3's monopoly, and
#: ``adcp-client-python-aeu`` is the red that said so): which keywords own a location is a
#: keyword decision, so it lives in the cell (:attr:`keywords.Cell.owns`) and this is
#: :func:`keywords.owns_a_location` reading it.  The three sentences above are the REASON
#: each one owns, which the cell carries too; what the table could not say before was the
#: answer itself -- ``items`` and ``contains`` agree on ``effect``, ``rendered`` and
#: ``descends`` and only one of them owns, which is §3's own test that the column is a
#: field.
#:
#: **AND THE MONOPOLY IS CLAIMED HERE AND NOT HELD: :func:`locations` RETYPES THE ANSWER**
#: (measured by ``adcp-client-python-d81a``'s prune pass).  The walk below names
#: ``properties``, ``items`` and ``additionalProperties`` as owners in its own source and
#: reads neither this set nor :data:`_CO_STATES`, so there are two owners of one derived
#: reading and the sentence above describes the intended one.  The two agree over this
#: bundle; nothing makes them agree over the next.  Kept, and not deleted as unread,
#: because deleting it is what would make the drift permanent.
_OWNS = keywords.owns_a_location()

#: The keywords :func:`locations` reads but never replaces: they state something about a
#: location another keyword owns, so they are conjoined into that location's value and
#: left exactly as they stand.  **Retyped in that walk too, for :data:`_OWNS`' reason.**
_CO_STATES = frozenset({"patternProperties", "contains"})


class Location(NamedTuple):
    """One frontier item: where it is, what is replaced there, and what decides it.

    ``pointers`` is in document order and relative to the node the walk started at, and
    they are the positions the pin REPLACES.  ``nodes`` is every statement the value has
    to satisfy, which is a superset: a keyword that co-states a location another keyword
    owns is conjoined and left standing (the keywords :data:`_CO_STATES` names, which
    :func:`locations` spells for itself -- see its docstring).

    ``kind`` says what the pin IS.

    * ``"const"`` -- one value every statement admits, which is the saving: a 287 KB
      property becomes a few KB of value.
    **AND THERE IS ONE KIND SINCE THIS ROW, WHICH IS ITS RESULT AND NOT A TIDYING.**  What
    stood beside it was ``"reduce"``: the UNCONDITIONAL statement about a location that a
    consequent or a union branch also decides, narrowed IN PLACE rather than pinned.
    :func:`locations` carries the three measurements that removed it -- the narrowing is a
    second answer to a question the scope's own pin has already answered, and no order of
    the two and no restriction of that position preserves satisfiability.  Such a position
    is left EXACTLY as the document states it.  The field stays because a reader of a
    frontier item is entitled to ask what the pin IS.
    """

    at: str
    pointers: tuple[str, ...]
    nodes: tuple[Mapping[str, Any], ...]
    kind: str


def locations(node: Any, *, depth: int = 32) -> tuple[Location, ...]:
    """The OUTERMOST frontier under ``node``: every instance location one level in.

    **§8's fixture rule, keyed on where a reference LANDS IN THE NODE BEING GRADED
    rather than on where a ``$ref`` string appears in the raw document** (the owner's
    correction, 2026-11-04, with the payload that measured it).  The rule
    :func:`referring_positions` carries reads the raw bundle document's own ``$ref``
    strings, and at a COMPOSED position that reading returns nothing: ``_base.applied_schema``
    conjoins what the enclosing nodes assert about the same instance -- "the conjunction is
    :data:`SAME_INSTANCE_FACTS` plus the enclosing node's own ``allOf``, spliced into the
    node's conjunct list" -- so the reference is in the GRADED NODE and at no pointer the
    document spells.

    Measured on ``media-buy/refine-proposals-response.json#/properties/results/items/oneOf/0``,
    the pair reported ungradeable at every bound including 3,600 s: the raw branch is 454
    bytes and holds NO ``$ref`` at all, so the raw reading finds nothing; the graded node
    is 683,849 bytes, of which 683,144 sit in one ``/allOf/0`` conjunct the document does
    not spell, and ``properties/proposals`` inside it is the whole of
    ``core/canonical-proposal.json``.  Validating a payload against that node costs 1 ms
    and generating one does not terminate -- so the cost is in GENERATION and the fix
    cannot lose a value the check was deciding.

    **What a frontier item is.**  The walk descends through what describes the same
    instance (:data:`_CONJOINS`) and stops at the first thing that describes a DIFFERENT
    one:

    * a **child location** -- a ``properties`` entry or a single-schema ``items`` --
      grouped by the location it decides, because several conjuncts can each state part of
      what one key or one element must satisfy and a pin per conjunct would be two
      documents answering one question with an empty intersection (§8's measured clause).
      The pin is ONE value drawn from their conjunction, placed at all of them.
    * a **union BRANCH**, descended into under a SCOPE of its own, because its interior
      describes the same instance as the conjuncts beside it: one location's statements
      are then one group whether they are stated unconditionally, inside a consequent or
      inside a branch, and one value answers for all of them.  A union NODE is not a
      location of its own -- a value one branch admits can meet a conjunct that refuses
      it, which is what the comment in the walk below measures.

    Nothing under ``not`` or ``if`` is a frontier item, and neither is a ``definitions``
    entry -- it has no instance location, which is §8's own reading of why such a
    declaration belongs to the entry's own pair.  Everything else is left to the draw.

    **AND THE OWNERSHIP ANSWER IS WRITTEN IN THIS FUNCTION, not read from the table that
    states it.**  :data:`_INVERTS`, :data:`_OWNS` and :data:`_CO_STATES` carry the REASONS
    and this walk carries a second copy of the ANSWER -- the keyword names below.  Each of
    those three says so at its own definition; none of them is read here, and the drift
    that makes possible is a defect and not a convention.
    """
    #: location token -> (pointers, nodes).  A dict keyed on the token and not a list, so
    #: the several conjuncts deciding one key arrive as ONE item.
    #: ``(instance location, conditional scope) -> (positions to replace, statements)``.
    found: dict[tuple[str, str], tuple[list[str], list[Mapping[str, Any]]]] = {}

    def take(key: tuple[str, str], pointer: str, sub: Any, *, owns: bool) -> None:
        if not isinstance(sub, Mapping):
            return
        pointers, nodes = found.setdefault(key, ([], []))
        if owns:
            pointers.append(pointer)
        nodes.append(sub)

    def walk(current: Any, rel: str, at: str, scope: str, left: int) -> None:
        if not isinstance(current, Mapping) or left <= 0:
            return
        #: **A UNION BRANCH IS A FRONTIER ITEM AND THE WALK KEEPS GOING**, which is the
        #: correction a 48 s measurement forced.  A union taken as a location of its OWN
        #: and pinned to a value derived from the union node alone produced
        #: ``{"allOf": [{"oneOf": [{"const": null}]}, {"type": "object", ...}]}`` on
        #: ``adagents.json#/oneOf/1/allOf/0/anyOf/1`` -- a value one branch admits, met by
        #: a conjunct at the same instance location that refuses it, so the draw reported
        #: ``Cannot generate test cases from empty strategy`` and the 1.16 MB node went to
        #: the generator untouched.  A union describes the node's OWN instance, so it is
        #: not a location of its own; what is reducible about it is each branch's
        #: interior, and that is what is substituted.
        #:
        #: **AND A BRANCH IS SCOPED EXACTLY AS A CONSEQUENT IS, WHICH IS THE WHOLE OF WHAT
        #: THIS LOOP DOES NOW.**  A branch reduced by a SEPARATE call -- which is what a
        #: ``Location`` of its own made it -- reads a frontier of its own, so the same
        #: instance location was pinned twice: once by the unconditional conjuncts here and
        #: once inside the branch, to two values, and the conjunction of the two is EMPTY.
        #: Measured on ``creative/sync-creatives-response.json#``'s ``("demand",
        #: ['creatives', 0, 'assignment_errors'])`` draw: ``/allOf/1/properties/creatives``
        #: pinned ``[{"assignment_errors": null}]`` while
        #: ``/allOf/0/oneOf/0/properties/creatives`` pinned ``[]``, and ``/status`` was
        #: ``"failed"`` unconditionally against ``"submitted"`` in a branch.  The node went
        #: 6,907,894 -> 11,268 bytes -- 613x -- and the reduced node admitted NOTHING
        #: (``Unsatisfiable``, 459 of 459 draws filtered out, 5.94 s), so
        #: :meth:`Fixtures._draw`'s fail-safe fell through to the UNREDUCED 6.9 MB draw and
        #: the pair reported ``over_budget`` at every bound to 300 s.  The saving was
        #: computed and then discarded.
        #:
        #: The machinery that answers it is already here and was written for ``if``/``then``:
        #: a SCOPE makes the branch's statement about a location arrive as its own group,
        #: the unconditional statements about that location are conjoined INTO it (``beside``
        #: below), so one value satisfies the branch and the conjuncts together -- and the
        #: unconditional position is not pinned at all, because its value and the branch's
        #: would both have to hold wherever that branch is the one that matches.  Scoped by
        #: the branch's own POINTER for the reason the consequent's comment states: a scope
        #: that collapsed two branches into one key would ask for a value satisfying both
        #: alternatives at once.
        for keyword in ("oneOf", "anyOf"):
            held = current.get(keyword)
            if not isinstance(held, list):
                continue
            for index, sub in enumerate(held):
                if isinstance(sub, Mapping) and sub:
                    suffix = f"/{keyword}/{index}"
                    walk(sub, rel + suffix, at, rel + suffix, left - 1)
        patterns = current.get("patternProperties")
        patterns = patterns if isinstance(patterns, Mapping) else {}
        properties = current.get("properties")
        if isinstance(properties, Mapping):
            for key, sub in properties.items():
                token = f"{at}/{bundle.escape_key(key)}"
                take(
                    (token, scope),
                    f"{rel}/properties/{bundle.escape_key(key)}",
                    sub,
                    owns=True,
                )
                for pattern, beside in patterns.items():
                    if _matches(pattern, key):
                        take((token, scope), "", beside, owns=False)
        items = current.get("items")
        #: ``uniqueItems`` with a floor of two is the one case a single element value
        #: cannot answer: every element pinned to one value makes a two-member array
        #: impossible, so the node would be EMPTY rather than narrower.  §8 names this
        #: case by keyword, and this is the guard it asks for.
        floor = current.get("minItems")
        unique = bool(current.get("uniqueItems")) and isinstance(floor, int) and floor > 1
        if isinstance(items, Mapping) and not unique:
            token = f"{at}/*"
            take((token, scope), f"{rel}/items", items, owns=True)
            contains = current.get("contains")
            if isinstance(contains, Mapping):
                take((token, scope), "", contains, owns=False)
        extra = current.get("additionalProperties")
        if isinstance(extra, Mapping) and extra:
            take((f"{at}/+", scope), f"{rel}/additionalProperties", extra, owns=True)
        for word, suffix, sub, _position in bundle.subschemas(current):
            if word in _CONJOINS:
                walk(sub, rel + suffix, at, scope, left - 1)
            elif word in _CONDITIONAL:
                #: **THE SCOPE IS THE CONSEQUENT'S WHOLE RELATIVE POINTER and never the
                #: keyword suffix alone.**  Measured: with ``scope + suffix`` every one of
                #: ``compliance/comply-test-controller-request.json#``'s thirty
                #: consequents was scoped ``/then``, so all thirty collapsed back into one
                #: key and the 8,158,816-byte demand was rebuilt -- 193.85 s to report
                #: that no value satisfies thirty scenarios at once.  The pointer is what
                #: makes one consequent one scope.
                walk(sub, rel + suffix, at, rel + suffix, left - 1)

    walk(node, "", "", "", depth)
    #: Which locations a CONSEQUENT or a union BRANCH decides, so the unconditional
    #: statement about one is narrowed in place instead of pinned: the two pins would both
    #: have to hold wherever the condition matches or that branch is the one that does.
    conditioned = {token for token, scope in found if scope}
    children: list[Location] = []
    for (token, scope), (pointers, nodes) in found.items():
        if not pointers:
            continue
        #: **AND THE UNCONDITIONAL STATEMENT ABOUT A SCOPED LOCATION IS LEFT EXACTLY AS THE
        #: DOCUMENT STATES IT -- NOT NARROWED IN PLACE, WHICH IS WHAT STOOD HERE.**  A
        #: narrowing is a second answer to a question the scope's own pin has already
        #: answered, and the two are drawn from conjunctions that cannot see each other: the
        #: scoped value satisfies the UNREDUCED statement beside it -- that statement is in
        #: the conjunction it was drawn from -- and a narrowing of that statement need not
        #: admit it.  The scope is then dead, and two readings make that fatal rather than
        #: merely wasteful:
        #:
        #: * a ``oneOf`` whose every branch is dead admits nothing;
        #: * a consequent whose ``if`` the rule's own pins FORCE to match is not escapable
        #:   either -- measured on ``media-buy/get-media-buys-response.json#``, where
        #:   ``/state`` was pinned ``"ready"`` and ``/allOf/0/if`` is ``state == "ready"``,
        #:   so ``/allOf/0/then``'s ``/configuration`` had to hold and said ``active:
        #:   true`` while the in-place narrowing of the same location said ``active:
        #:   false``.
        #:
        #: Measured on ``creative/sync-creatives-response.json#``'s ``("demand",
        #: ['creatives', 0, 'assignment_errors'])`` draw: ``/allOf/1/properties/creatives``
        #: was narrowed to ``items: {const: {"assignment_errors": null}}`` while
        #: ``/allOf/0/oneOf/0/properties/creatives`` was pinned to a one-element array the
        #: UNREDUCED statement admitted and the narrowed one did not, so the 15,345-byte
        #: node admitted nothing (``Unsatisfiable``, 459 of 459 draws filtered, 5.94 s) and
        #: :meth:`_Draws._draw`'s fail-safe paid the UNREDUCED 6.9 MB draw instead -- which
        #: is the whole-document draw this rule exists to avoid, at every bound to 300 s.
        #: Drawn against the narrowed statement, the same draw is **0.74 s on a
        #: 15,360-byte node and the pair passes**.
        #:
        #: **AN ``{"enum": [...]}`` OF THE SCOPES' OWN VALUES AT THE UNCONDITIONAL POSITION
        #: WAS TRIED AND IS REFUTED**, which is worth stating because it is the obvious
        #: alternative and its soundness argument is correct: every member is drawn from a
        #: conjunction containing that statement, so the enum is a RESTRICTION.  What it
        #: does not preserve is satisfiability.  Measured on the same draw: the enum at
        #: ``/status`` was ``["submitted"]`` -- the one value a branch had been pinned to --
        #: and ``oneOf/1`` states ``not: {anyOf: [..., {properties: {status: {const:
        #: "submitted"}}, required: ["status"]}]}``, so forcing that value killed the only
        #: branch left and the 11,377-byte node admitted nothing.  A restriction of a
        #: location shared by ALTERNATIVES can empty the node even where every member of it
        #: is admissible on its own.
        #:
        #: **AND SO WAS THE OTHER ORDER -- narrow first, then draw the scoped value against
        #: the narrowing, so the two agree by construction.**  It is the obvious repair and
        #: it fails symmetrically, because the narrowing is itself drawn with no knowledge of
        #: the scope: on the same draw the demand's ``/creatives`` narrowed to ``items:
        #: {const: {"assignment_errors": null}}``, ``oneOf/0``'s own ``items`` requires
        #: ``action`` and ``creative_id``, their intersection is empty, so the branch's pin
        #: answered :data:`NONE` and its 6.8 MB stood -- node 6,847,477 bytes of 6,907,894,
        #: cut again.  Neither order makes two independent draws agree; what does is not
        #: drawing twice.
        if not scope and token in conditioned:
            continue
        if scope:
            #: The unconditional statements are conjoined into the scoped value, so a
            #: consequent's or a branch's pin satisfies what the node itself says about the
            #: location and cannot conflict with it.  Where their intersection is empty the
            #: draw answers :data:`NONE` and nothing is pinned there, which is the right
            #: answer: that consequent or that branch is one the enclosing conjunction can
            #: never take, and it is left standing exactly as the document states it.
            beside = found.get((token, ""), ([], []))[1]
            children.append(
                Location(token, tuple(pointers), tuple(nodes) + tuple(beside), "const")
            )
        else:
            children.append(Location(token, tuple(pointers), tuple(nodes), "const"))
    return tuple(children)


@functools.lru_cache(maxsize=4096)
def _matches(pattern: str, key: str) -> bool:
    """Whether draft-07's ``patternProperties`` entry ``pattern`` reaches ``key``.

    ``re.search`` and not ``fullmatch``, which is draft-07's own reading: a
    ``patternProperties`` key is an unanchored ECMA-262 regular expression.  A pattern
    this engine cannot compile reaches nothing, which is the fail-safe direction -- it
    loses a co-statement and so loses a pin, rather than conjoining the wrong one.
    """
    try:
        return re.search(pattern, key) is not None
    except re.error:
        return False


def _admitting(node: Any) -> Any:
    """``node`` with every key that does not change what it ADMITS struck, recursively.

    :data:`keywords.ANNOTATIONS` by name and the ``x-`` namespace by prefix, which is §6's
    own two-part admission and the screen ``catalogue.Admitted`` applies for the same
    sentence -- "an annotation does not change what a node admits".  The set is declared
    once, in ``codegen/keywords.py``, as a reading of the keyword table; a second list here
    would be the hand-written one that derivation exists to have deleted.

    **A definitions SECTION is KEPT, and that is the one place this differs from
    ``catalogue.Admitted``.**  That class RESOLVES a ``$ref`` before keying, so the section
    it drops is already in the key at every referring site.  This one does not resolve:
    the nodes it keys are statements lifted out of one already-inlined record, and a local
    ``$ref`` into the record's own storage is still a ``$ref`` here.  Dropping the section
    while keeping the reference string would make two nodes that spell one pointer and
    store two different subtrees under it collide -- the memo would hand one the other's
    pin, which is a wrong value and not a coarse key.
    """
    if isinstance(node, list):
        return [_admitting(member) for member in node]
    if not isinstance(node, Mapping):
        return node
    return {
        word: _admitting(value)
        for word, value in node.items()
        if word not in keywords.ANNOTATIONS and not keywords.admitted_by_prefix(word)
    }


def _content_key(nodes: Sequence[Mapping[str, Any]], *, kind: bytes = b"") -> bytes | None:
    """A digest of what these statements ADMIT, for the pin memo, or ``None``.

    A digest and not the text, for the reason
    :func:`canonicalisation_shared_within_one_call` measures one layer down: the text of a
    subtree is held again by every ancestor's entry, and a memo keyed on text was "981 MiB,
    which is 28,370x the document it is a memo of".  A digest answers the one question the
    key decides -- whether these are the statements an entry was made for -- with the same
    equivalence classes.

    **WHAT THEY ADMIT AND NOT THEIR RAW TEXT, WHICH IS THE SAME RULE
    :func:`corpus_key` TAKES ONE LAYER UP** (``adcp-client-python-lzzj.8``, and
    ``docs/plan/final-state.md`` reading 1 is the sentence: "**A stored value, a key over a
    document's bytes, or any artifact that must be re-derived when the bundle moves makes
    an improvement to the schema cost exactly as much as a regression** -- and it makes the
    instrument answer for the bundle it was built against instead of for the compiler.").
    This key was ``json.dumps(list(nodes), sort_keys=True)`` -- the raw text, annotations
    included -- and the memo it addresses decides WHICH VALUE gets pinned at a fixture
    position.  So an annotation-only edit re-bucketed the memo, two statements that admit
    exactly the same instances stopped sharing one derivation, and a different value was
    drawn and pinned: **that is how two of the six pairs the patch was blamed for flipped
    verdict on a node that is byte-identical between the two bundles.**  Struck of what no
    instance can see (:func:`_admitting`), the bucket is the admitted set, two statements
    that admit alike share one pin, and a gained ``title`` moves nothing.

    It is sound in the direction a memo has to be sound in, and that is not an appeal to
    the strike being "only annotations": two statements with one admitted set admit the
    same values, so a value derived for one is a value the other admits, and
    :meth:`Fixtures.value` screens every pin against the conjunction it is placed into
    before it is kept.  A coarser bucket can therefore cost a screen, never a wrong pin.

    ``None`` where ``json`` declines the node, which is a node that simply gets no entry.
    """
    try:
        return hashlib.sha256(
            kind
            + b"\0"
            + json.dumps(
                _admitting(list(nodes)), sort_keys=True, separators=(",", ":")
            ).encode()
        ).digest()
    except (TypeError, ValueError):
        return None


class Referring(NamedTuple):
    """One position a fixture is substituted at, and the document it is derived FROM.

    ``pointer`` is relative to the node under grade; ``document`` and ``target`` name the
    referenced document and the pointer into it, which is the pair that grades it.
    """

    pointer: str
    document: str
    target: str


def referring_positions(
    read: Callable[[str], Any],
    document: str,
    pointer: str,
    documents: Collection[str],
) -> tuple[Referring, ...]:
    """Every FIXTURE position at or under ``document``'s ``pointer``, in document order.

    **Read off the RAW documents' own ``$ref`` strings and never off the record**, which is
    the one reading that answers.  ``bundle.record`` inlines a cross-document reference by
    copying, so by the time a node reaches this module there is no ``$ref`` left to say
    that a subtree came from somewhere else -- all 68,254 references the packaged records
    carry are local, and every one of them is either the document's own ``definitions`` or
    the record's storage.  §8's rule is about the DRAW and not about the record ("a fixture
    collapses it whether or not the record inlined the bytes"), so the reading has to come
    from the layer that still spells the reference: the bundle's own text.  ``read`` is the
    caller's reader for it (``bundle.read``), because this module reads no path.

    The pointers line up because the record inlines IN PLACE: ``architecture.md``'s
    "every pointer any reader SPELLS keeps the spelling it has today".  A raw ``$ref`` at
    ``/anyOf/0`` is the inlined target at ``/anyOf/0`` of the record, so a relative pointer
    taken here addresses the resolved node :func:`resolve` produced.

    A reference at an own-instance position (:data:`_OWN_INSTANCE`, or a whole ``anyOf``
    branch) is a fixture position and the walk STOPS there -- that is the sum the rule
    buys. Anywhere else it is transparent and the walk reads through it, which is the
    clause :data:`_OWN_INSTANCE` carries the measurement for.

    An ``anyOf`` branch is included because restricting one branch of a union cannot empty
    it while any branch survives, and because it is the case the rule is stated about: a
    root with 42 referenced branches is 42 fixtures, and ``core/async-response-data.json``
    is that root.
    """
    out: list[Referring] = []

    def node_at(home: str, at: str) -> Any:
        raw = read(home)
        inside = at.lstrip("#")
        return raw if not inside else bundle.node_at(raw, inside)

    def walk(node: Any, rel: str, own: bool, home: str, seen: frozenset, depth: int) -> None:
        if not isinstance(node, Mapping) or depth > _FIXTURE_DEPTH:
            return
        ref = node.get("$ref")
        if isinstance(ref, str):
            head, fragment = bundle.split_ref(ref)
            target = bundle.document_for(head, documents) if head else home
            if target is None:
                return
            at = "#" + fragment
            if own:
                out.append(Referring(rel, target, at))
                return
            if (target, at) in seen:
                return
            try:
                inner = node_at(target, at)
            except Exception:  # noqa: BLE001 -- a pointer the document does not hold
                return
            walk(inner, rel, own, target, seen | {(target, at)}, depth + 1)
            return
        for keyword, suffix, sub, position in bundle.subschemas(node):
            walk(
                sub,
                rel + suffix,
                position in _OWN_INSTANCE or keyword == "anyOf",
                home,
                seen,
                depth + 1,
            )

    try:
        start = node_at(document, pointer)
    except Exception:  # noqa: BLE001 -- a pointer the raw document does not hold
        return ()
    walk(start, "", False, document, frozenset({(document, pointer)}), 0)
    return tuple(out)


def fixtured(schema: Any, placements: Sequence[tuple[str, Any]]) -> tuple[Any, int]:
    """``schema`` with each ``(relative pointer, instance)`` pinned as ``{"const": ...}``.

    **A RESTRICTION and never a widening**, which is what makes the substitution sound in
    the one direction the accepts draw needs: ``{"const": v}`` admits a subset of what the
    referenced subtree admits, so every value the fixtured schema admits is a value the
    document admits.  :func:`_restricted` carries the same argument for the widening
    obligation's value classes, and :func:`check_accepts` validates the drawn instance
    against the UNFIXTURED node anyway, because "by construction" is a claim about this
    function and the claim is cheap to check.

    **COPY-ON-WRITE along the path and nothing else**, because the resolved schema is a DAG:
    :func:`resolve` deep-copies with a memo that preserves sharing, so one object stands at
    many pointers and mutating it in place would substitute at every one of them.  Each
    step rebuilds exactly the mapping or list it descends through, so a position nobody
    named keeps the object it had.

    Returns the schema and HOW MANY placements landed.  A pointer the resolved node does
    not hold is skipped: the raw document and the record agree about pointers everywhere
    this has been measured, and where they do not the fail-safe direction is to lose the
    saving rather than to place a value at a position nobody named.
    """
    return replaced(schema, [(pointer, {"const": v}) for pointer, v in placements])


def replaced(schema: Any, placements: Sequence[tuple[str, Any]]) -> tuple[Any, int]:
    """``schema`` with the SUBSCHEMA at each relative pointer replaced by the one given.

    :func:`fixtured`'s body, with the replacement a caller's rather than ``{"const": v}``,
    because the union rule substitutes an ``{"enum": [...]}`` over a whole union node
    where the reference rule substitutes one instance at a referring position
    (:meth:`Fixtures.reduced`).  Both are restrictions and the argument for each is made
    where it is built; this function only places what it is handed, and it is the ONE
    copy-on-write walk so a second spelling of it cannot drift.
    """
    placed = 0
    out = schema
    for pointer, replacement in placements:
        segments = [s for s in pointer.split("/") if s]

        def rebuilt(current: Any, i: int, _segments: list[str] = segments, _to=replacement) -> Any:
            if i == len(_segments):
                return _to
            word = _segments[i]
            if isinstance(current, list):
                index = int(word)
                return [
                    *current[:index],
                    rebuilt(current[index], i + 1),
                    *current[index + 1 :],
                ]
            return {**current, word: rebuilt(current[word], i + 1)}

        try:
            out = rebuilt(out, 0)
            placed += 1
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return out, placed


@dataclass
class Fixtures:
    """**WHERE §8's FIXTURE FOR A REFERENCED DOCUMENT COMES FROM, and why it is DERIVED.**

    §8: "the fixture is DERIVED from the referenced document, never hand-written: a
    hand-written one is a thousand files to maintain and a silent exemption the first time
    a document changes under it."  Two derivations, in this order, and the first answers
    for almost all of them:

    * **the accepts corpus's own held instance for that document's pair.**  That corpus is
      one instance per graded pair, drawn from the document by ``check_accepts``, keyed on
      the document's RAW BYTES and its raw reference closure's (``corpus_key``), and
      re-offered to the document on every read (``corpus_defect``).  So it is a derivation
      in the strict sense -- nothing is written down that the document does not decide --
      and it is already in the tree. **Measured: it answers 2,674 of the 2,753 pairs.**
    * **a fixtured draw over that document's own node, recursively**, for the rest.  The 79
      pairs the corpus holds nothing for are exactly the pairs the pole cannot finish, so
      the entry is missing precisely where it is needed: the referenced document's own
      draw is unaffordable for the same reason its referrer's is.  The recursion
      terminates because it is the sum the rule describes -- each document's fixtures are
      derived once, memoised, and the visited set cuts a cycle in the reference graph.

    A document neither answers for is reported rather than guessed: ``None``, the position
    is not substituted, and the pair draws exactly as it did before.  **The fail-safe
    direction is to lose the saving, never to place a value the document does not admit.**

    The three callables are the seam ``docs/plan/architecture.md`` §9 draws for the corpus
    and for the same reason -- "the store is the CALLER's, the key is the harness's" -- so
    this holds no path and reads no filesystem:

    * ``read(document)`` -- the RAW document, which is what still spells a ``$ref``;
    * ``node(document, pointer)`` -- the RECORD node a pair is graded against;
    * ``identity(document, pointer)`` -- the pair's static identity, for the corpus key.
    """

    read: Callable[[str], Any]
    node: Callable[[str, str], Any]
    identity: Callable[[str, str], Any]
    documents: Collection[str]
    corpus: Any = None
    custom_formats: Mapping[str, Any] = ()

    #: ``(document, pointer) -> the instance, or None``.  Memoised for the run, which is
    #: what turns the product into a sum.
    held: dict[tuple[str, str], Any] = field(default_factory=dict)
    #: ``digest of a frontier item's statements -> the subschema it is replaced by, or
    #: NONE``.  The node-side rule's memo, keyed on CONTENT and not on a pointer for the
    #: reason :func:`locations` measures: a location inside a pair's node sits at pointers
    #: ``applied_schema`` minted and the document does not spell, so there is no
    #: ``(document, pointer)`` to key on.  Content is the honest key and the stronger one
    #: -- two pairs holding one subtree at two pointers share one derivation.
    pins: dict[bytes, Any] = field(default_factory=dict)

    def positions(self, document: str, pointer: str) -> tuple[Referring, ...]:
        return referring_positions(self.read, document, pointer, self.documents)

    def substitute(self, schema: Any, document: str, pointer: str) -> tuple[Any, int]:
        """``schema`` with a fixture pinned at every referring position under ``pointer``."""
        placements = []
        for position in self.positions(document, pointer):
            instance = self.one(position.document, position.target)
            if instance is not NONE:
                placements.append((position.pointer, instance))
        return fixtured(schema, placements)

    def reduced(self, schema: Any, depth: int = 8) -> tuple[Any, int]:
        """``schema`` with every outermost instance location under it pinned to one value.

        **§8's fixture rule read off the NODE BEING GRADED**, which is the half
        :meth:`substitute` cannot reach.  That method asks the RAW document which positions
        refer, and at a composed position the answer is nothing: measured on
        ``media-buy/refine-proposals-response.json#/properties/results/items/oneOf/0``, the
        raw branch is 454 bytes with no ``$ref`` in it and the graded node is 683,849
        bytes, because ``applied_schema`` conjoins the enclosing node's statements about
        the same instance and ``core/canonical-proposal.json`` arrives inside that
        conjunct.  Having found nothing to place, the draw was handed the whole node.

        So the frontier is read off the node itself (:func:`locations`) and each item is
        pinned:

        * a **child location** -- what one ``properties`` entry or one ``items`` decides --
          is pinned to ONE value, drawn from the CONJUNCTION of every statement about that
          location and placed at all of them.  ``{"const": v}`` admits a subset of what
          each of those statements admits, so the result is a restriction, and the value is
          screened against the conjunction before it is kept.
        * a **location a SCOPE also decides** -- a consequent's or a union branch's own
          statement about the same instance location -- is pinned once per scope, each from
          the conjunction of that scope's statement WITH the unconditional ones, and the
          unconditional position itself is LEFT EXACTLY AS THE DOCUMENT STATES IT.  A union
          is not monotone branch by branch (narrowing one branch of a ``oneOf`` can make an
          instance that matched two match one, which the node then ADMITS) and the scopes
          are alternatives with no value in common, so there is no one value for that
          position, no restriction of it that cannot empty the node, and no ORDER of the
          two that makes them agree.  A statement left standing cannot contradict a value
          drawn from a conjunction that contains it, which is why that direction is the one
          that terminates; :func:`locations` carries all three measurements.

        **Every pin is DERIVED and never hand-written** (§8: "a hand-written one is a
        thousand files to maintain and a silent exemption the first time a document changes
        under it").  The value comes from that location's own statements by the same draw
        the location's own pair would pay, recursively reduced the same way, so the cost of
        a node is the SUM over its locations and not the product.

        An item no value survives for is left exactly as it stands: the fail-safe
        direction is to lose the saving, never to place a value the document does not
        admit.

        ``depth`` bounds how many times the reduction re-enters itself; it is a guard on an
        unreasonable answer and not the terminator, which is the content memo.
        """
        placements = []
        for item in locations(schema):
            answer = self._pin(item, depth)
            if answer is NONE:
                continue
            placements.extend((pointer, answer) for pointer in item.pointers)
        return replaced(schema, placements)

    def _pin(self, item: Location, depth: int) -> Any:
        """The subschema one frontier item is replaced by, or :data:`NONE`.

        **Memoised on the item's CONTENT and not on a pointer**, which is the key §8's
        "the key is the declaration" becomes here: a location inside a pair's node sits at
        pointers ``applied_schema`` minted and the document does not spell, so there is no
        ``(document, pointer)`` to key on.  Content is the honest key and the stronger one
        -- the three ``refine-proposals-response.json#/properties/results/items/oneOf/*``
        pairs hold the same commercial-terms subtree at three different pointers and share
        one derivation, which a pointer key cannot do.
        """
        if depth <= 0:
            return NONE
        #: The KIND is in the key, because a branch and a child location with identical
        #: content get different answers -- a reduced node and a ``{"const": v}`` -- and a
        #: key that could not tell them apart would hand one the other's.
        key = _content_key(item.nodes, kind=item.kind.encode())
        if key is not None and key in self.pins:
            return self.pins[key]
        answer = self._derived_pin(item, depth)
        if key is not None:
            self.pins[key] = answer
        return answer

    def _derived_pin(self, item: Location, depth: int) -> Any:
        """The subschema one frontier item is replaced by, or :data:`NONE`.

        One kind since this row (:class:`Location`), so this is the pin and not a
        dispatch: one value for the conjunction of the item's statements, as a
        ``{"const": v}``.  :data:`NONE` where no value survives, which is the fail-safe
        direction -- the position then stands as the document states it.
        """
        value = self.value(item.nodes, depth - 1)
        return NONE if value is NONE else {"const": value}

    def value(self, statements: Sequence[Mapping[str, Any]], depth: int) -> Any:
        """One instance the CONJUNCTION of ``statements`` admits, or :data:`NONE`.

        Several statements about one instance location are conjoined as the document
        conjoins them -- as an ``allOf`` -- and the draw is over that conjunction, which is
        what keeps §8's measured clause from biting: "a fixture per conjunct is two
        documents answering one question and the intersection is empty."  One value for the
        location, satisfying every statement about it, is the answer that cannot be empty
        by construction.

        The conjunction's own frontier is reduced first (:meth:`reduced`), so the draw is
        over a node whose children are already pinned.  **No budget of its own**, for
        :meth:`_derived`'s measured reason: ``signal.setitimer`` is process-global, so a
        nested :func:`within` would re-arm the caller's timer and clear it on the way out,
        leaving the enclosing grade unbounded.

        The value is screened against the conjunction before it is returned, because the
        restriction is this module's claim and the claim is cheap to check.
        """
        kept = [s for s in statements if isinstance(s, Mapping)]
        if not kept:
            return NONE
        conjunction: Any = kept[0] if len(kept) == 1 else {"allOf": list(kept)}
        #: **WHAT ANY STATEMENT ABOUT THIS LOCATION SAYS A VALID INSTANCE OF IT LOOKS LIKE,
        #: SCREENED AGAINST THE CONJUNCTION OF ALL OF THEM.**  The same rule
        #: :meth:`_stated` applies at a referring position, applied to a frontier item:
        #: where the document states an instance there is nothing to generate.  The screen
        #: is the conjunction and not the stating statement, because several statements
        #: decide one location and a member only one of them admits is not a pin -- which
        #: is the empty-intersection clause this method exists for, arriving by a new door.
        try:
            for statement in kept:
                for member in stated_instances(statement):
                    if conforms(conjunction, member) is True:
                        return member
        except OverBudget:
            raise
        except Exception:  # noqa: BLE001 -- an unusable statement states nothing
            pass
        narrowed, _ = self.reduced(conjunction, depth)
        try:
            instance = one_instance(narrowed, self.custom_formats)
        except OverBudget:
            raise
        except Exception:  # noqa: BLE001 -- an undrawable location has no pin
            if budget_expired():
                raise OverBudget("a fixture derivation was cut") from None
            return NONE
        if conforms(conjunction, instance) is not True:
            return NONE
        return instance

    def one(self, document: str, pointer: str, seen: frozenset = frozenset()) -> Any:
        """One instance ``document``'s node at ``pointer`` admits, or :data:`NONE`.

        **:data:`NONE` and never ``None``, which is the mistake :class:`_Draws` records
        one key space over**: a document can admit JSON ``null``, so ``None`` means both
        "the fixture is null" and "there is no fixture", and the first of those is a value
        the draw must be allowed to pin.
        """
        key = (document, pointer)
        if key in self.held:
            return self.held[key]
        if key in seen:
            return NONE  # a cycle in the reference graph is no fixture
        answer = self._replayed(key)
        if answer is NONE:
            answer = self._stated(key)
        if answer is NONE:
            answer = self._derived(key, seen)
        self.held[key] = answer
        return answer

    def _stated(self, key: tuple[str, str]) -> Any:
        """The referenced document's OWN ``examples``, which is the fixture with no draw.

        **§8's fixture rule and JSON Schema's own keyword are the same sentence** (the
        owner's decision, 2026-11-04).  The rule is that at a referring position the
        instrument needs "one instance that document admits", derived from the document and
        never hand-written -- and ``examples`` is the document's own statement of exactly
        that, maintained by whoever maintains the schema.  112 of this bundle's portable
        documents state one at their root, which is where a reference lands.

        Asked after :meth:`_replayed` and before :meth:`_derived`, so the committed floor
        still decides which witness is graded and this answers the positions it does not --
        and it answers them for nothing, where :meth:`_derived` pays a whole draw.
        Screened by the node it will stand for, which is :func:`stated_instances`' whole
        content.
        """
        document, pointer = key
        try:
            node = self.node(document, pointer)
        except Exception:  # noqa: BLE001 -- a pointer the record does not carry
            return NONE
        found = stated_instances(node)
        if not found:
            return NONE
        return found[0]

    def _replayed(self, key: tuple[str, str]) -> Any:
        if self.corpus is None:
            return NONE
        try:
            identity = self.identity(*key)
        except Exception:  # noqa: BLE001 -- a pair the caller cannot name has no entry
            return NONE
        entry = self.corpus.get(corpus_key(identity, custom_formats=self.custom_formats))
        if not isinstance(entry, list) or not entry:
            return NONE
        return entry[0]

    def _derived(self, key: tuple[str, str], seen: frozenset) -> Any:
        document, pointer = key
        try:
            node = self.node(document, pointer)
        except Exception:  # noqa: BLE001 -- a pointer the record does not carry
            return NONE
        try:
            root = self.node(document, "#")
            drawn_from = resolve(node, store={}, referrer=root)
        except Exception:  # noqa: BLE001 -- as check_pair: an unresolved node is used as is
            drawn_from = node
        placements = []
        for position in self.positions(document, pointer):
            instance = self.one(position.document, position.target, seen | {key})
            if instance is not NONE:
                placements.append((position.pointer, instance))
        substituted, _ = fixtured(drawn_from, placements)
        #: The union rule applies to a referenced document's own draw too, and it is the
        #: same call the pair makes: a referenced document whose cost is its OWN internal
        #: branches is exactly the case :meth:`substitute` leaves standing, and this is the
        #: position where that cost used to be paid in full.
        substituted, _ = self.reduced(substituted)
        #: **NO BUDGET OF ITS OWN, and that is a correction rather than an omission.**  A
        #: :func:`within` here looked right and silently removed the CALLER's bound:
        #: ``signal.setitimer`` is process-global, so a nested block re-arms the timer to
        #: its own interval and then clears it on the way out, leaving the enclosing grade
        #: with no timer at all.  Measured: one pair ran ten minutes against a 20 s budget.
        #: ``OverBudget`` is therefore not caught either -- a cut belongs to whoever set
        #: the budget, and a derivation that swallowed one would make the pair run past it.
        #: The caller's bound is the only bound, and a derivation that exceeds it cuts the
        #: pair, which is what the pair did before this rule existed.
        try:
            instance = one_instance(substituted, self.custom_formats)
        except Exception:  # noqa: BLE001 -- an undrawable node has no fixture
            if budget_expired():
                raise OverBudget("the fixture derivation was cut") from None
            return NONE
        #: **The DOCUMENT decides, before anything else reads the value.**  The
        #: substitution is a restriction, so this cannot fail by construction; it is
        #: checked because the construction is this module's claim and because an empty
        #: intersection is the one way the clause :data:`_OWN_INSTANCE` carries could be
        #: wrong at a position nobody has measured yet.
        if conforms(drawn_from, instance) is False:
            return NONE
        return instance


#: The identity of ``from_schema``'s own behaviour, in the key below.  The drawn stream is
#: a function of the library as much as of the schema, so a version bump MISSES every
#: entry and the population is re-drawn -- which is the honest direction: a held instance
#: from an older generator is a witness the generator in use would not have produced, and
#: the suite would then grade a stream nothing in the tree produces.
_DRAW_VERSION = f"hypothesis={hypothesis.__version__} hjs={hypothesis_jsonschema.__version__}"


def corpus_key(
    identity: Any,
    *,
    custom_formats: Mapping[str, Any] = (),
    position: Any = None,
) -> str:
    """The content address of the instances :func:`check_accepts` draws, under ``identity``.

    **``identity`` is what the CALLER says makes two draws the same question, and this
    function hashes it beside the two facts it owns**: the format strategies and the
    generator.  It is never derived from the schema the draw is handed, and the reason is
    the defect this signature exists to close.

    **THE EXAMPLE COUNT IS NOT IN THE KEY, AND REMOVING IT IS THIS FUNCTION'S WHOLE
    CURRENT CHANGE** (``adcp-client-python-82m.3``).  It was, and the consequence was
    measured: the count is the one input a lane raises deliberately, so every raise
    invalidated all 2,693 committed entries and paid a full cold draw of the population --
    and walking the count up through 1, 5 and 25 paid it three times over, for an artifact
    that was committed precisely so that nobody would ever redraw it.  Measured on this
    row before it was stopped: 2,635 entries drawn at ``examples=1`` and 2,407 at
    ``examples=5``, 8.5 MB of them, all of it answering questions the floor already held
    the beginning of.

    **An entry for N examples CONTAINS the answer for every n <= N**, which is why the
    count was never a property of the question.  ``check_accepts`` offers the instances in
    order, so the first n of a held list are exactly the list a draw of n would have been
    asked for -- the SAME witness, not a comparable one -- and
    :func:`corpus_defect` re-offers the n it serves to the document before any of them
    counts.  So one fill at the highest count anyone wants makes every lower setting free,
    and the committed floor stops being a single-count artifact.

    What the key must still move on is unchanged and is the property
    ``adcp-client-python-3be.22`` established: the DOCUMENT (through ``identity``), the
    format strategies, and the generator version.  A compiler edit moves nothing; a bundle
    bump or a generator bump moves everything.  Removing the count moves every key ONCE,
    which is the last time a count can move one, and the entries are RE-KEYED rather than
    redrawn -- the content is the instances and the instances did not change.

    **AND THE IDENTITY IS OVER WHAT THE DOCUMENT ADMITS, NEVER OVER ITS BYTES, WHICH IS
    THIS FUNCTION'S OTHER CURRENT CHANGE** (``adcp-client-python-lzzj.8``).  That is a
    statement about what a CALLER may hand in, so it is stated here and enforced where the
    identity is built (``catalogue.admitted_identities``, which carries the measurement).
    ``docs/plan/final-state.md`` reading 1 is the rule:

        "**BOTH CHECKS ARE A FUNCTION OF (class, document) AND OF NOTHING ELSE.** Point
        them at another bundle and they answer for that bundle, because there is nothing to
        carry over and nothing to expire. **A stored value, a key over a document's bytes,
        or any artifact that must be re-derived when the bundle moves makes an improvement
        to the schema cost exactly as much as a regression** -- and it makes the instrument
        answer for the bundle it was built against instead of for the compiler."

    The identity used to be a digest of a document's raw bytes and its raw reference
    closure's, which satisfied the paragraph below and nothing more: an
    ACCEPTANCE-PRESERVING rewrite of the bundle moved every key.  Measured over the
    published bundle against the patched one: 22,338 differences,
    ``patch.seen_by_a_validator`` zero -- nothing lost, nothing changed, every difference a
    gained ``$schema``/``title``/``description`` -- and all 1,054 identities moved, 854 of
    them by a TRAILING NEWLINE.  Over that same pair the admitted identity moves 0 of 1,054.

    Three things stay IN the key, and the test for each is whether it changes WHICH VALUE
    IS DRAWN: the format strategies and the generator version (this function's own two
    facts), and -- inside the identity -- the instances the node's document STATES and
    ADMITS, because ``check_accepts`` answers "the store, then the document's own
    ``examples``, then the draw" and ``examples`` is a dropped annotation that is also a
    source of witnesses.  The DIALECT is the fourth such fact and is deliberately NOT
    digested: the measured patch adds ``$schema: draft-07`` where none was stated, which
    changes no keyword's meaning, so carrying the string would move keys for an improvement
    -- and a document in ANOTHER dialect is a question about the whole bundle rather than
    about one key, asserted by
    ``tests/test_accepts_corpus.py::test_every_portable_document_states_one_dialect``.

    **THE SCHEMA IS NOT A STATIC FACT ABOUT THE DOCUMENT, BECAUSE THE RESOLVER IS OURS.**
    The schema ``check_accepts`` draws from is ``bundle.record``'s output -- this package's
    own inliner -- read at a pointer and inlined again by :func:`resolve`.  Keyed on that,
    the address moved with every change to how we inline, for the share of the bundle whose
    record differs from its raw document at all; the reading is ``bundle.record`` against
    ``bundle.read`` over ``bundle.portable``, and it is most of it.  So every held instance
    was redrawn on a change that altered no document, at the per-pair cold cost
    ``tests/corpus.py`` tabulates.  The document was static the whole time; only our
    rendering of it moved, and the key was tied to the rendering.

    **It was hashing the argument at the call site, which is the natural key right up to
    the point where the argument is OURS.**  The record is what ``from_schema`` is handed,
    so hashing it is hashing the input -- correct if the resolved document were a given,
    wrong because this package resolves it and this package changes.  So the identity comes
    from the caller, which is the half of the seam that can see upstream:
    ``catalogue.admitted_identities`` is one answer for a bundle document -- what that
    document ADMITS with every ``$ref`` resolved, and the instances it STATES and ADMITS --
    and a caller handing a literal schema is its own answer, since a literal is already
    static.

    **THE KEY WAS NEVER THE SAFETY NET AND MUST NOT BE MISTAKEN FOR ONE.**
    :func:`corpus_defect` re-offers every held instance to the DOCUMENT on every read, and
    its own docstring states the principle: a held corpus is a derived equality and never a
    stored answer.  So the key answers "is this the same question" and the document answers
    "is this value still admissible".  Two different inlinings of one document admit the
    same instances; a held instance that still conforms is still evidence, and the re-read
    proves that each time rather than assuming it.

    **It is a content address and NOT a claim that the draw is a pure function of its
    inputs**, which was measured rather than assumed: over two full passes of one pinned
    population a small share of pairs drew a different instance, and re-running one
    identical shard of one pass differed from itself -- the reading is the instances two
    passes hold for one key, and the share is read there.  The seed is not the cause
    (``_SETTINGS`` fixes ``derandomize``), nor ``PYTHONHASHSEED``, nor the recursion limit;
    what moves is process-global state inside ``hypothesis`` whose lifetime garbage
    collection governs.  Holding the witness makes the suite's evidence reproducible where
    the draw is not -- ``_SETTINGS``' own comment intends exactly that and does not achieve
    it.

    **WHAT A LOOSER KEY CAN FIND, and it is reported rather than guarded against.**  The
    draw is over the RESOLVED schema, so a resolution change could in principle alter what
    is DRAWABLE where the accepted set is identical -- a ``$ref`` the resolver used to fail
    on.  That is what the re-validation is for, and a rejection is a finding: the rate is
    read off :attr:`AcceptsResult.outcome` ``== "corpus_rejected"`` over the population, and
    a non-zero one says the looser key reached a pair whose question really did move.

    **``position`` IS THE SECOND HALF OF THE IDENTITY, and only §8's obligation has one.**
    The accepts draw is over the whole node a pair names, so the pair's identity names it
    completely.  :func:`check_widening` draws several times WITHIN one pair, each time from
    a schema it derived from a different place in that node -- a value class at one declared
    pointer and keyword (:func:`value_classes`), an intermediate node on the way to an
    instance location (:func:`_reached`), the node conjoined with a demand
    (:func:`_demanding`) -- and those draws are different questions about one document.  So
    the caller names WHICH derivation, and each of the three is a reading of the DECLARED
    POINTER and of nothing the compiler can move: ``_demanding``'s own docstring says the
    demand "is a reading of the POINTER and not of the document", and the other two are the
    document's own subschema reached along a stated pointer.  A position is therefore as
    static as the identity beside it, which is what makes the pair one key.

    **ABSENT FROM THE MATERIAL WHERE THERE IS NO POSITION, which is not a convenience.**
    ``check_accepts``' key is the address of 2,693 committed entries
    (``tests/accepts-corpus``), and a new material field would have moved every one of
    them -- a key change wearing a refactor, with
    ``test_every_graded_pair_has_a_committed_entry_under_the_current_key`` red on a bundle
    nobody bumped.  So the accepts key is unmoved BY CONSTRUCTION and not by inspection:
    the field appears only when a caller names a position, and
    ``test_the_accepts_key_does_not_move_when_a_position_is_available`` reads that back.

    The serialisation is ``json.dumps(..., sort_keys=True)``, the same canonical spelling
    ``canonicalisation_shared_within_one_call`` keys its within-call memo with -- and
    since ``adcp-client-python-82m.25.1`` that memo digests it too, for the reason this
    function always did: a key decides whether two things are one thing, and holding the
    text to decide it holds the text.
    """
    material: dict[str, Any] = {
        "identity": identity,
        "formats": sorted(custom_formats),
        "draw": _DRAW_VERSION,
    }
    if position is not None:
        material["position"] = position
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, default=repr).encode()
    ).hexdigest()


def corpus_defect(
    schema: dict, held: Any, examples: int, *, validator_cls: Any = None
) -> str:
    """Why ``held`` may NOT stand in for this pair's draw, or ``""`` when it may.

    **A held corpus is a derived equality and never a stored answer**, which is the shape
    ``codegen.dump_exemptions`` is built in and for the same reason: an entry nobody
    re-derives is an allowlist of payloads that silently stops covering the schema.  So
    every instance is re-offered to the DOCUMENT before it is allowed to count, and the
    count is checked against the obligation the caller asked for:

    * **fewer instances than ``examples``** -- including none at all, which is the one
      failure mode a cache of this shape can have.  §8's accepts draw is what PROVES a
      widening rather than believing it, so an empty or short entry that read as "the
      obligation passed" would be the cache grading something else.

      **EMPTY and no longer "short", which is the change that took the count out of the
      key** (:func:`corpus_key`).  Two readings moved and they moved in opposite
      directions:

      * an entry holding MORE than the obligation asks for was never a defect and is no
        longer treated as one.  The instances are offered in order, so the first
        ``examples`` of them are the list a draw of ``examples`` would have produced, and
        those are the ones this function checks and the ones ``check_accepts`` replays: a
        25-instance entry served as 5 is checked as 5.
      * an entry holding FEWER -- but at least one -- is not a wrong answer either.  It is
        a question nobody has yet asked at this depth, so ``check_accepts`` treats it as a
        MISS: it redraws to ``examples`` and holds the longer list.  Reporting it here
        instead would make raising the example count turn every pair of the population
        ``corpus_rejected`` at once, which is a red suite standing in for a fill that is
        owed.  **A redraw and not "draw the difference"**, because the draw is one
        ``hypothesis`` run over one strategy and there is no affordance for resuming it at
        instance n; the entry it produces then covers every lower count for ever, so the
        redraw is paid once.

      ZERO instances stays a defect, and that is the clause this one keeps: a store
      answering with an empty LIST rather than with ``None`` is broken, and a pair that
      graded no instance has not passed.
    * **an instance the document REFUSES**.  The key already makes this unreachable --
      it hashes the schema the instance was drawn from -- so reaching it means the store
      answered for a key it was not asked about, and that is the one way a stale entry
      could grade a model against the wrong document.  ``is False`` and not ``is not
      True``: a document ``jsonschema`` cannot build a validator from states nothing
      about any instance, and the accepts check's own dump half already reads that
      answer the same way.

    Both are reported by :attr:`AcceptsResult.outcome` as ``corpus_rejected``, which
    :attr:`PairReport.outcome` turns into ``accepts:corpus_rejected``: a verdict on the
    pair, with the instance count at zero, so the pair reddens twice over rather than
    passing on evidence it does not have.
    """
    if not isinstance(held, list) or not held:
        n = len(held) if isinstance(held, list) else "a non-list"
        return (
            f"the held corpus carries {n} instances where the obligation is {examples}; "
            "an entry that cannot cover the draw is not evidence"
        )
    cls = validator_cls or validator_for(schema)
    for i, instance in enumerate(held[:examples]):
        if conforms(schema, instance, validator_cls=cls) is False:
            broke = violated_keywords(schema, instance, validator_cls=cls)
            return (
                f"the document refuses held instance {i} on {', '.join(broke)}"
                f": {_dump(instance)}"
            )
    return ""


@functools.cache
def _malloc_trim() -> Any:
    """``malloc_trim`` off the C library, or ``None`` where there is no such symbol.

    ``functools.cache`` because the answer is a property of the LIBRARY this interpreter
    is linked against and cannot change under a running process -- the one shape of cache
    whose key is not a subject of ``adcp-client-python-82m.25.1`` at all.

    ``None`` on anything other than glibc, and the caller then does nothing: the trim is a
    RETURN of pages the process has already freed, so an allocator that has no such call
    is an allocator with nothing to return and never a failure.
    """
    try:
        name = ctypes.util.find_library("c") or "libc.so.6"
        return ctypes.CDLL(name).malloc_trim
    except (OSError, AttributeError):
        return None


def _release_freed_pages() -> None:
    """Give the kernel back what Python has already freed.

    **Measured, and it is why "then drop them" needs a second sentence on this
    allocator** (``adcp-client-python-82m.25.1``).  One cold draw --
    ``adagents.json#/oneOf/1/allOf/0/anyOf/1``, cut at 90 s -- takes RSS from 0.45 GB to
    0.70 GB and leaves it there once the memo is dropped, while ``tracemalloc``'s traced
    total comes back to the baseline: Python retains nothing and glibc retains the
    arenas.  This call reads 0.50 GB.

    It bounds nothing.  No entry is evicted, no draw is cut and no pair is skipped; the
    only thing that changes is which process holds pages nobody has a reference to.  That
    distinction is the whole of why a trim is admissible where a worker cap is not: a cap
    changes what is graded and this changes what is resident.
    """
    trim = _malloc_trim()
    if trim is not None:
        trim(0)


@contextmanager
def canonicalisation_shared_within_one_call() -> Iterator[dict[bytes, Any]]:
    """Share ``canonicalish`` results for the duration of ONE check, then drop them.

    **THIS IS A DIVERGENCE FROM SECTION 6's LETTER AND IT IS MEASURED.**  Section 6
    says ``_CANON_MEMO`` is "DELETED, not bounded", because "a repetition that
    resolution removes needs no cache at all".  The first half is right and is done:
    there is no process-global dict here, nothing is retained between pairs, and
    nothing is patched at import time.  **The second half is refuted by the
    measurement.**  The repetition the memo covered is not only across step sites --
    ``merged`` re-enters ``canonicalish`` for every subschema it sorts
    (``_canonicalise.py:631``), so ONE ``from_schema`` call on ONE already-resolved
    document re-canonicalises the same subtrees. Resolution cannot remove that: the
    document arrives with zero ``$ref`` and the repetition is inside the library's
    own recursion.

    Measured on ``core/macro-declaration.json#``, 18,301 bytes, one pair, single
    process, no profiler:

    ======================================  ==========  =============
    ``from_schema`` on that one document    seconds     memo entries
    ======================================  ==========  =============
    sharing within the call                     43.58            504
    no sharing at all                         >600.0  (stopped)     -
    ======================================  ==========  =============

    So deleting the sharing outright does not make the suite cheaper, it makes one
    pair cost more than the whole population does with it.

    **What section 6's complaint actually names, and what this keeps out.**  The
    defect was "an unbounded process-global dict ... grows by roughly 340 entries per
    pair", retained across every pair of the population and multiplied by ten
    workers, with a measured hit rate and no measured size.  A memo whose lifetime is
    one call has none of those properties: its contents are one document's
    subschemas, 504 at the measured worst, it is discarded on exit including on an
    exception, and that size is the figure above rather than an unknown.  The name
    says the lifetime, so a later reader cannot widen it without renaming it.

    **THE ENTRY IS A SERIALISED COPY AND NOT THE OBJECT, because the way OUT of this
    memo was the second largest cost in the whole check.**  An entry must be handed
    back as an independent value -- the library rewrites the nodes it is given -- and
    ``copy.deepcopy`` is the wrong instrument for that here.  ``canonicalish`` rebuilds
    its argument before recursing, so its result carries NO internal aliasing: measured
    over the 300 largest results of three pairs, 275,143 / 808,576 / 851,328 structural
    ``dict``/``list`` nodes at 275,143 / 808,576 / 851,328 distinct ``id``s -- an aliasing
    factor of 1.000 in every case.  ``deepcopy``'s whole extra machinery over a plain
    rebuild is the identity memo that preserves aliasing there is none of, and it shows:
    110,496,108 ``id()`` calls and 16,194,960 ``_keep_alive`` calls on one 120 s pair.

    So the entry holds the result's JSON text and a hit is ``json.loads``, which is C and
    allocates the same tree:

    ======================================  ==============  ================  ==========
    300 largest results of                  ``deepcopy``    ``json.loads``    speed-up
    ======================================  ==============  ================  ==========
    ``governance/check-governance-request``        247.6 ms           80.3 ms       3.1x
    ``core/creative-representation-set``           993.7 ms          291.7 ms       3.4x
    ``core/mcp-webhook-payload``                  1076.0 ms          370.7 ms       2.9x
    ======================================  ==============  ================  ==========

    **The serialisation is CHECKED rather than assumed**, which is what makes it a copy
    and not an approximation of one: the text is read back and compared to the result
    before the entry is kept, so a value the round trip would alter -- a non-string key, a
    tuple, anything ``json`` declines -- is held as the object and deep-copied as before.
    Measured over 900 results of those three pairs: 0 that ``json`` declined and 0 that
    came back unequal, so the fallback is a guarantee and not a cost.

    The MISS hands back the result itself and holds only the text, so a miss now copies
    once where it copied twice.

    **AN ENTRY COUNT IS NOT A SIZE, AND THE PARAGRAPHS ABOVE SIZED THIS MEMO BY COUNTING
    ENTRIES** (``adcp-client-python-82m.25.1``).  "504 at the measured worst" is a COUNT,
    taken on an 18,301-byte document, and the two halves of an entry are each a whole
    subtree's TEXT -- the key is ``json.dumps`` of the subschema and the value is
    ``json.dumps`` of its canonical form.  ``canonicalish`` recurses, so a parent's entry
    holds every descendant's text again and the memo's BYTES grow as the text times the
    depth where its entry count grows as the distinct subschemas.  Measured on
    ``adagents.json#/oneOf/1/allOf/0/anyOf/1``, one pair, cut at 60 s with the draw still
    running: **2,793 entries holding 437 MiB of keys and 544 MiB of values**, from a
    36,283-byte document -- 981 MiB, which is 28,370x the document it is a memo of and
    the whole of that pair's 2.15 GB peak.  The count was in range; the size was four
    orders of magnitude outside it.

    So the two halves are held as what the memo needs them for rather than as text, and
    neither change can move an answer:

    * **THE KEY IS A DIGEST OF THE TEXT AND NOT THE TEXT.**  The key decides one
      question -- whether this subschema is the one an entry was made for -- and a digest
      of the canonical text answers exactly it, with the same equivalence classes.  2,793
      keys are 89 KB where the text was 437 MiB.
    * **THE VALUE IS THE TEXT COMPRESSED.**  The value is handed back through
      ``json.loads``, so what it has to be is the bytes that parse to the result; schema
      text is repetitive and ``zlib`` at level 1 is the cheap end of the trade.  The
      round trip is still CHECKED on the uncompressed text before the entry is kept, so
      :func:`_round_trips`' guarantee is untouched and the object fallback is still the
      object.

    **AND THE PAGES THE MEMO OCCUPIED ARE RETURNED WHEN IT IS DROPPED**, which is the
    other half of what "then drop them" has to mean on this allocator.  Measured on the
    same pair: Python's own traced total comes back to the baseline when the memo goes --
    nothing is retained, which is what the name promises -- and RSS does not, because
    glibc holds the freed arenas. 0.45 GB baseline, 0.70 GB after the pair, **0.50 GB
    after ``malloc_trim``**.  Over the 77 pairs of this bundle that DRAW rather than
    replay, that un-returned remainder is what makes a worker's peak RSS look like a
    function of how many documents it has graded when it is a function of how many cold
    draws it has been given: four workers reached 28.8 / 28.3 / 17.6 / 9.9 GB on one
    domain.  It is not a cap and it is not a budget -- nothing is bounded, evicted or
    skipped; the process returns memory it has already freed.
    """
    memo: dict[bytes, tuple[bytes | None, Any]] = {}
    uncached = _hjs_canon.canonicalish

    def shared(schema: Any) -> Any:
        try:
            text = json.dumps(schema, sort_keys=True, default=repr)
        except (TypeError, ValueError):
            return uncached(schema)
        key = hashlib.blake2b(text.encode(), digest_size=32).digest()
        entry = memo.get(key)
        if entry is None:
            result = uncached(schema)
            blob = _round_trips(result)
            memo[key] = (
                None if blob is None else zlib.compress(blob.encode(), 1),
                None if blob is not None else result,
            )
            return result
        packed, held = entry
        if packed is None:
            return copy.deepcopy(held)
        return json.loads(zlib.decompress(packed))

    _hjs_canon.canonicalish = shared
    try:
        yield memo
    finally:
        _hjs_canon.canonicalish = uncached
        memo.clear()
        _release_freed_pages()


def _round_trips(value: Any) -> str | None:
    """``value`` as JSON text if reading that text back yields ``value``, else ``None``.

    The copy clause of :func:`canonicalisation_shared_within_one_call`, stated as a
    predicate so the fallback is readable: ``None`` means "this value is not a thing JSON
    text can stand in for", and the one caller then holds the object and deep-copies it.
    ``==`` and not a type walk, because what the caller needs is that the value handed
    back equals the one ``canonicalish`` produced, which is exactly what ``==`` says.
    """
    try:
        blob = json.dumps(value)
    except (TypeError, ValueError):
        return None
    return blob if json.loads(blob) == value else None


@contextmanager
def validator_classes_shared_within_one_call() -> Iterator[Any]:
    """Unbound ``hypothesis_jsonschema``'s validator-class cache for ONE check.

    **THE LARGEST SINGLE COST IN THE CHECK, and it is a cache that is too small rather
    than a computation that is needed.**  ``merged`` ends by calling
    ``_get_validator_class`` on every schema it produces (``_canonicalise.py:853``), which
    validates that merged schema against its own METASCHEMA -- a full
    ``jsonschema.check_schema`` walk, measured at 41.6 ms each.  The library caches the
    answer under ``lru_cache(maxsize=128)``, and 128 does not hold one document's merged
    subschemas, so the cache EVICTS entries the same call asks for again.  Measured per
    pair, single process, instrumented rather than profiled:

    ==========================================  =======  ==========  ======  ==========
    pair                                          calls    distinct  misses  re-walked
    ==========================================  =======  ==========  ======  ==========
    ``core/creative-representation-set#``         8,181         600   1,069        44%
    ``governance/check-governance-request#``     47,697         926   3,527        74%
    ``core/mcp-webhook-payload#``                29,401       1,604   2,082        23%
    ==========================================  =======  ==========  ======  ==========

    "re-walked" is the share of metaschema walks that re-derive an answer the SAME call
    already had and the bound threw away.  That share of 74.1% / 14.8% / 40.4% of those
    pairs' budgets is what this removes, and it removes nothing else: the cache is the
    library's own function under its own key, rebuilt with no bound and put back on exit.

    **The lifetime is the same lifetime the canonicalisation sharing has, and for the same
    reason.**  What section 6 forbids is a process-global store that grows across pairs and
    workers; this one holds one document's distinct merged subschemas -- 1,604 at the
    measured worst -- and is dropped on exit including on an exception, which the restored
    bounded cache then proves by holding its own 128 again.
    """
    module = _hjs_canon.__dict__
    #: The private name as the module spells it.  Module scope does not mangle, so this is
    #: the global ``_get_validator_class`` resolves at call time -- rebinding it here is
    #: what reaches the library's own call site without touching the library's source.
    name = "__get_validator_class"
    bounded = module[name]
    unbounded = functools.lru_cache(maxsize=None)(bounded.__wrapped__)
    module[name] = unbounded
    try:
        yield unbounded
    finally:
        module[name] = bounded


@contextmanager
def a_combinator_is_covered_and_never_enumerated() -> Iterator[list[tuple[int, int, int]]]:
    """Build a combinator's strategy over a COVER of its branches, never over their POWER SET.

    **§8's own residue clause, made true of the library that does the drawing**: "a
    combinator root is not graded by drawing the power set of its branches ... that is
    2^n, not a product, and it is why no constant factor reaches it."  The rule was
    written and the library does not honour it.

    **WHERE IT SITS, BY STACK AND NOT BY INFERENCE.**  ``hypothesis_jsonschema``'s
    ``merged_as_strategies`` is handed every statement that has to hold about ONE instance
    -- for a node with an ``allOf`` that is the node's own keywords plus every conjunct --
    and it looks for the largest subsets it can intersect by enumerating
    ``itertools.combinations(inputs, n)`` for ``n`` from ``len(inputs)`` down to 1.  That
    is the power set, and ``merged`` runs on each group.  The first group is the whole set,
    and when it intersects the loop stops there -- ``combined`` then supersets every later
    group -- so the cost is 2^n only when the WHOLE conjunction does not merge, which is
    exactly the shape §8 names.

    Measured on the two pairs this leaves cut, each with its §8 substitution already
    applied, stack-sampled at 4 Hz under :func:`within`:

    ====================================================  =======  =======  =============
    node                                                   bytes    inputs  60 s sample
    ====================================================  =======  =======  =============
    ``protocol/get-adcp-capabilities-response.json#``       50,256       19  ``merged`` under ``merged_as_strategies``, 220/240
    ``compliance/comply-test-controller-request.json#``     14,871       32  ``merged`` under ``merged_as_strategies``, 232/240
    ====================================================  =======  =======  =============

    2^19 and 2^32 groups.  ``canonicalish`` had already tried the one whole-conjunction
    merge (``_canonicalise.py:593``) and it returned ``None``, which is why the ``allOf``
    survived to here.  **Neither is a byte problem**: the first is 620,066 bytes reduced to
    50,256 and the second 8,172,302 reduced to 14,871 -- three orders of magnitude -- and
    both are still cut, which is the measurement that rules out every constant factor.

    **WHAT THIS REPLACES THE ENUMERATION BY, and why it is the same answer.**  The
    library's contract is not "the largest subsets"; it is a COVER: ``st.one_of`` over
    groups whose union is every input, each group drawn from its own intersection and then
    FILTERED by every input's validator.  A cover is what makes it sound -- an
    intersection of SOME of the statements admits a superset of what all of them admit,
    and the filter removes the difference -- and the power set is only how the library
    searches for one.

    So the search is replaced and the contract is not:

    * **the whole set first, exactly as the library tries it.**  Where the conjunction
      merges, this call returns the library's own answer and nothing has changed.  That is
      the path almost every pair takes.
    * **otherwise one greedy pass**: take the first input that is not yet covered as an
      accumulator, intersect every other uncovered input into it that will intersect,
      re-scanning while any did, and emit the accumulator as a group.  Repeat on what is
      left.  Every input lands in exactly one group, so the union is the whole set and the
      cover condition holds by construction.
    * **the filter is the library's, kept verbatim** -- ``all(v(obj) for v in
      validators)`` over a validator per INPUT.  This function does not weaken what a
      drawn value has to satisfy; it only changes which intersections are offered to the
      generator.  That is what makes this a statement about GENERATION and about nothing
      else, which is the same clause :meth:`Fixtures.reduced` is held to.

    The greedy pass is ``O(n^2)`` intersections against ``O(2^n)``: 158 for the first node
    above and 526 for the second, 19 inputs covered by 15 groups and 32 by 30.  Both then
    draw a value the UNSUBSTITUTED node admits, in 0.86 s and 0.32 s.

    **A cover is not a partition of the admissible space and no value is lost by taking
    one.**  Each group's strategy is filtered by every input, so each one draws from
    exactly the conjunction's admissible set; what differs between two covers is the
    DISTRIBUTION the generator sees, never the set.  A greedy cover can be finer than the
    largest-first one -- more groups, each less constrained, so more of the work falls to
    the filter -- and where that filters everything out the draw reports ``Unsatisfiable``
    with ``hypothesis``'s own filtered-draw count, which :func:`_why` keeps and
    :func:`check_accepts` reports as ``strategy_error``.  A non-pass with a name, never a
    green.

    **The lifetime is ONE CHECK, which is the lifetime its two siblings have and for the
    same reason**: nothing is patched at import time, so a caller of this module that did
    not ask for the rule gets the library exactly as it ships.  The yielded list records
    ``(inputs, groups, intersections)`` per call for a caller that wants to measure it.
    """
    cover: list[tuple[int, int, int]] = []
    enumerated = _hjs_from.merged_as_strategies
    #: The library's own per-schema entry point, under the name the module spells.  Module
    #: scope does not mangle, so this is the global its ``allOf``/``anyOf``/``oneOf`` arms
    #: and its ``patternProperties`` draw already resolve at call time.
    one = _hjs_from.__dict__["__from_schema"]

    def covered(
        schemas: list[Any], *, alphabet: Any, custom_formats: Any
    ) -> st.SearchStrategy:
        assert schemas, "internal error: must pass at least one schema to merge"
        if len(schemas) == 1:
            return one(schemas[0], alphabet=alphabet, custom_formats=custom_formats)
        #: Keyed on the canonical encoding, which is the library's own de-duplication of
        #: its inputs: two conjuncts spelling one statement are one input.
        inputs = {_hjs_canon.encode_canonical_json(s): s for s in schemas}
        intersections = 1
        whole = _hjs_canon.merged(list(inputs.values()))
        if whole is not None and whole != _hjs_canon.FALSEY:
            groups = [whole]
        else:
            groups = []
            left = list(inputs)
            while left:
                accumulated = inputs[left.pop(0)]
                again = True
                while again:
                    again = False
                    for key in list(left):
                        intersections += 1
                        narrower = _hjs_canon.merged([accumulated, inputs[key]])
                        if narrower is not None and narrower != _hjs_canon.FALSEY:
                            accumulated = narrower
                            left.remove(key)
                            again = True
                groups.append(accumulated)
        cover.append((len(inputs), len(groups), intersections))
        #: One validator per INPUT and not per group: what a drawn value has to satisfy is
        #: every statement, which is the library's filter unchanged.
        validators = tuple(_hjs_canon.make_validator(s).is_valid for s in schemas)
        return st.one_of(
            [
                one(s, alphabet=alphabet, custom_formats=custom_formats).filter(
                    lambda obj, _v=validators: all(valid(obj) for valid in _v)
                )
                for s in groups
                if s != _hjs_canon.FALSEY
            ]
        )

    _hjs_from.merged_as_strategies = covered
    try:
        yield cover
    finally:
        _hjs_from.merged_as_strategies = enumerated


def format_pattern_positions(schema: Any) -> list[tuple[str, dict]]:
    """Every position where a ``format`` and a ``pattern`` meet, node and pointer.

    **The shape ``hypothesis_jsonschema`` has no generator for**, and the reason is in
    its own source: ``string_schema`` takes the FORMAT's strategy and then applies the
    pattern as a ``.filter()``, with the comment *"This isn't really supported, but
    we'll do our best with a filter"*.  Where the pattern restricts the value beyond
    what the format strategy happens to emit, every draw is filtered out and
    ``hypothesis`` raises ``Unsatisfiable`` over the WHOLE schema, naming no node.

    It is not gated on the format being ASSERTED, and that is deliberate: the filter
    runs whether or not a checker is installed, so the drawing problem is the same.

    **This is the CO-OCCURRENCE census and not the undrawable population**, which is
    the distinction :func:`undrawable_formats` exists to draw: over the 3.2 bundle 73
    positions in 47 of 1,054 documents state the two keywords together, in 8 distinct
    ``(format, pattern)`` pairs, and 72 of the 73 DRAW.
    """
    return [
        (pointer or "/", node)
        for pointer, node in _nodes(schema)
        if isinstance(node.get("format"), str) and isinstance(node.get("pattern"), str)
    ]


def _drawing_this_node(instance: Any) -> None:
    """The body :func:`undrawable_formats` draws into: the draw IS the measurement.

    Named rather than a lambda because ``hypothesis`` puts this function's name in
    ``Unsatisfiable``'s own sentence, which :func:`_why` carries into the report.
    """


def undrawable_formats(
    schema: Any, *, custom_formats: Mapping[str, Any] = (), examples: int = 25
) -> tuple[str, ...]:
    """Of the positions :func:`format_pattern_positions` names, the ones a draw cannot reach.

    **Co-occurrence is not the undrawable shape, and the measurement is the whole
    difference.** 72 of the bundle's 73 format-beside-pattern positions draw, because
    ``hypothesis_jsonschema``'s ``uri`` strategy emits ``https://A.COM`` and that
    matches every one of the bundle's patterns that pins the scheme or the general host
    shape -- 7 of its 8 distinct pairs.  The eighth pins a LITERAL host,
    ``^https://github\\.com/`` at
    ``core/reference-renderer.json#/properties/provenance/properties/source_repository``,
    and no generic generator reaches a literal host: 459 of 459 draws are filtered, at
    10, 25 and 50 examples alike.

    So a cause naming every co-occurrence would admit a ``strategy_error`` from ANY
    cause, as long as the document states the two keywords somewhere.  This draws each
    node ALONE and keeps the ones that failed, with hypothesis's own reason per
    position -- which is what makes :attr:`PairReport.no_instrument` conditional on a
    measurement of the shape rather than on two keywords meeting.

    **Derandomized, so the answer is a function of (node, library version)** and P7's
    determinism holds over it.

    KNOWN CEILING: a node undrawable only IN CONTEXT -- a conjunct narrowing the
    pattern beside it -- draws here and is not named, so its pair reddens rather than
    being admitted.  That is the safe direction and it is visible: an exit this check
    cannot explain is a failure and not a tolerance.  The upgrade path is to draw the
    node as the generator sees it, which needs the merged node the library builds
    internally.
    """
    out: list[str] = []
    for pointer, node in format_pattern_positions(schema):
        try:
            run = given(instance=strategy(node, dict(custom_formats)))(_drawing_this_node)
            settings(max_examples=examples, phases=[Phase.generate], **_SETTINGS)(run)()
        except Exception as e:  # any failure to draw names the position
            out.append(
                f"{pointer}: format {node['format']!r} beside pattern"
                f" {node['pattern']!r} [{_why(e)}]"
            )
    return tuple(out)


def validator_for(schema: dict) -> Any:
    """The validator the document's own ``$schema`` names.

    One function so the three places below cannot come to validate with
    different vocabularies, and so ``format`` is asserted in all of them: see
    ``_validating``.
    """
    return jsonschema.validators.validator_for(schema, jsonschema.Draft7Validator)


def _validating(cls: Any, schema: dict) -> Any:
    """A validator instance that ASSERTS ``format``, with the draft's own checker.

    ``jsonschema`` treats ``format`` as a pure annotation unless it is handed a
    ``FormatChecker``, and the consequence is not a missing nicety: the whole
    accepted set of a formatted node went ungraded, so a model carrying a
    format-derived Python type was narrower than its own document and no check
    reported it.  The accepts check could not on its own, because
    ``hypothesis_jsonschema`` HONOURS a format it knows when generating -- it
    produced an offset in 200 of 200 ``date-time`` instances -- so every drawn
    instance landed inside the narrow type and the draw was green on a model that
    refused every other shape the format admits.

    The checker is ``cls.FORMAT_CHECKER``, the one the declared draft defines,
    rather than ``jsonschema.FormatChecker()``.  That is the faithful reading:
    the global registry carries every checker any draft defines, so it would
    assert ``uuid`` against a draft-07 document, which draft-07 does not define
    as a format -- the SDK inventing a constraint.  Which formats the draft's own
    checker can actually decide depends on what is installed, and ``pyproject``
    names the two packages that make this bundle's own formats decidable
    (``rfc3339-validator``, ``rfc3987``).  The emitter gates its type selection
    on the same set, so the two halves cannot disagree about which formats are
    asserted.
    """
    return cls(schema, format_checker=cls.FORMAT_CHECKER)


def conforms(schema: dict, instance: Any, *, validator_cls=None) -> bool | None:
    """True / False, or None when the document is not usable as a validator."""
    cls = validator_cls or validator_for(schema)
    try:
        _validating(cls, schema).validate(instance)
        return True
    except jsonschema.ValidationError:
        return False
    except Exception:
        return None


def violated_keywords(schema: dict, instance: Any, *, validator_cls=None) -> list[str]:
    """Which keywords the ORIGINAL document rejects this instance on.

    The step's own keyword is NOT a safe label for a refuses-check failure.  Two
    reasons, both measured here: ``canonicalish`` DERIVES constraints while
    resolving (``uniqueItems: true`` over a 2-member enum became ``maxItems: 2``,
    so a "maxItems" step produced an instance the document refuses on
    ``uniqueItems``), and a step drops sibling keywords it would otherwise
    contradict.  Asking the validator which keyword bit makes the attribution
    exact instead of assumed.
    """
    cls = validator_cls or validator_for(schema)
    out: list[str] = []
    for err in _validating(cls, schema).iter_errors(instance):
        for e in [err, *err.context] if err.context else [err]:
            if isinstance(e.validator, str):
                out.append(e.validator)
    return sorted(set(out))


#: The verifier's descent, by how each keyword holds its subschema.  A keyword is here
#: only if a document of record can spell it.
#:
#: **Five keywords left at ``adcp-client-python-10l.52``, each measured 0 over all 1,054
#: portable documents and all 1,628 graded pairs.**  Four of them no input of this
#: pipeline can produce at all: ``unevaluatedProperties``, ``unevaluatedItems`` and
#: ``dependentSchemas`` are draft 2019-09 vocabulary and every one of the 1,054 portable
#: documents declares draft-07; ``prefixItems`` is 2020-12's, and section 5's ``items``
#: row refuses a list-valued ``items`` ("that is tuple validation"), so no emitted class
#: carries one.  The fifth, ``additionalItems``, IS draft-07 vocabulary and bundle 3.2
#: simply states none -- so this is the one entry a later bundle version can make live
#: again, and the cost of its absence is that a subschema held under it would not be
#: walked.
#:
#: **Those five were the WHOLE of the drift from the one descent table**, which is the
#: measurement that says the removal was exactly a removal: with them gone,
#: ``set(_DESCEND_ONE) | set(_DESCEND_MAP) | set(_DESCEND_LIST)`` equalled
#: ``set(keywords.descends_at(Position.ROOT))`` in both directions.
#:
#: **And the three tuples are gone with them** (``adcp-client-python-3be.8``).  The
#: comment here used to admit the restatement -- "still §11's repetition and is not fixed
#: here" -- and hold the agreement by that one-time measurement, which is the shape that
#: goes stale: the equality was true of the tuples as written and nothing re-asked it.
#:
#: There is no seam to cross for the fix.  §9 names ``codegen.bundle`` in the verifier's
#: import set "for the record and the document set", and its own sentence for this very
#: walk is that the record is read "by the verifier's own walk ... over the descent column
#: of the table" -- so descending by the column is what §9 ASKS for, and what it forbids is
#: reading ``codegen.schema`` / ``codegen.lower``, which this does not.  The SET comes from
#: the column; the three-way split is draft-07's GRAMMAR of how each keyword spells what it
#: holds, and ``bundle`` already derives that from the child position with one name written
#: (:data:`bundle.HELD_BY_NAME`, :data:`bundle.HELD_IN_A_LIST`).  Re-deriving it here would
#: be a second reading of one grammar and would carry that name twice, which is
#: ``bundle.constrained_to_object``'s stated ground for deriving rather than restating:
#: "two spellings of 'which hop keeps the instance' is precisely how that divergence would
#: arrive, and it would arrive silently."
#:
#: ``_DESCEND_ONE`` is the column's REMAINDER and is a reading rather than a list, so a
#: keyword joining the column with a new spelling lands here and is walked, where before it
#: had to be written into one of three tuples to be walked at all.
#: ``tests/test_keywords.py`` holds all three equalities.
_DESCEND_MAP = bundle.HELD_BY_NAME
_DESCEND_LIST = bundle.HELD_IN_A_LIST
_DESCEND_ONE = frozenset(bundle.DESCENDS) - _DESCEND_MAP - _DESCEND_LIST


#: ``bundle.escape_key``, not a second copy: a pointer segment is spelled by four
#: readers and the two halves have to agree about a key carrying a ``/``.
#:
#: **It was ``compiler.escape_key``, and that import is what kept ``codegen.compiler``
#: in §9's permitted set.**  §11 puts a pointer speller in the SOURCE layer, so §14
#: step 5 moved the pair to ``codegen/bundle.py`` -- a module §9 permits by name, "for
#: the record and the document set" -- and the verifier now imports no module of the
#: walk at all.
_esc = bundle.escape_key


def at(doc: Any, pointer: str) -> Any:
    """Dereference a JSON Pointer against a document.

    ``bundle.node_at`` is the one reading, beside ``escape_key``'s inverse; this is
    the verifier's name for it.
    """
    return bundle.node_at(doc, pointer)


def _nodes(schema: Any, pointer: str = "") -> list[tuple[str, dict]]:
    """Every dict node of the document, with its pointer, by the same descent."""
    out: list[tuple[str, dict]] = []
    if isinstance(schema, list):
        for i, v in enumerate(schema):
            out += _nodes(v, f"{pointer}/{i}")
        return out
    if not isinstance(schema, dict):
        return out
    out.append((pointer or "/", schema))
    for k, v in schema.items():
        if k in _DESCEND_MAP and isinstance(v, dict):
            for kk, vv in v.items():
                out += _nodes(vv, f"{pointer}/{k}/{_esc(kk)}")
        elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
            out += _nodes(v, f"{pointer}/{k}")
        elif k in _DESCEND_LIST and isinstance(v, list):
            out += _nodes(v, f"{pointer}/{k}")
    return out


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #
@dataclass
class FormatStrategyVerdict:
    """Whether a supplied format strategy produces values the format itself admits.

    ``unchecked`` is a distinct outcome from ``pass`` and that distinction is the
    reason this type exists: a validator with no checker for a format answers True
    for every input, garbage included, so grading a strategy against one says
    nothing at all. Reporting that as a pass is the vacuous pass.
    """

    fmt: str = ""
    checked: bool = False  # the validator has a checker for this format
    examples: int = 0
    accepted: int = 0  # produced values the checker admits
    rejected: str = ""  # first produced value the checker REFUSES, if any
    counterexample_refused: bool | None = None  # the second answer
    detail: str = ""

    @property
    def outcome(self) -> str:
        if self.detail:
            return "error"
        if not self.checked:
            return "unchecked"  # nothing graded the strategy; NOT a pass
        if not self.examples:
            return "no_examples"
        if self.rejected:
            return "generates_invalid"  # every site using it would pass vacuously
        if self.counterexample_refused is not True:
            return "checker_accepts_anything"
        return "pass"


@dataclass
class AcceptsResult:
    examples: int = 0
    #: pass | model_refused_valid | model_dropped_a_fact | strategy_error | model_error
    #: | corpus_rejected
    outcome: str = "unrun"
    detail: str = ""
    counterexample: str = ""
    #: How many of :attr:`examples` were dumped back out and still admitted by the
    #: DOCUMENT.  The denominator ``check_pair`` reads to tell a pair whose class
    #: round-tripped every instance from one the generator never reached.
    round_tripped: int = 0

    #: The exempt positions this pair's dump actually NEEDED,
    #: ``"<document>#<pointer>/<keyword>"`` each, from ``codegen.dump_exemptions``.
    #:
    #: **REPORTED and not silent, which is the precedent every other excused fact in
    #: this module follows** -- :attr:`replayed` and ``WideningResult.unproved`` both
    #: put the qualification on the result where a reader of the pair meets it.  An
    #: exemption the harness does not report is one nobody reading a green pair can
    #: see, and this is the only check that reads what a class DID with a value.  So a
    #: non-empty list beside ``outcome == "pass"`` is a CONDITIONAL pass.
    #:
    #: **"Needed" and not "in force", and the difference was measured.**  An entry
    #: applies to every pair whose node CONTAINS the position, which it must -- an
    #: ancestor pair's dump carries the nested node, which is exactly why
    #: ``core/attestation-capabilities.json#`` is refused for a position inside
    #: ``core/attestation-issuer.json``.  But 8 pairs contain one of the four
    #: positions and only 3 are refused without it: the other 5 are ancestors whose
    #: drawn instance never reached the node.  Reporting all 8 would make this field
    #: mean "an exemption lies somewhere inside me", which is not a fact about the
    #: pair's verdict, and would make a conditional pass unreadable among pairs that
    #: pass on their own merits.  So the dump is re-validated against the UNSTRUCK
    #: node and the label is recorded only where that refuses it.
    dump_exempt: list[str] = field(default_factory=list)

    #: How many of :attr:`examples` came from a held corpus instead of a draw, and the key
    #: they were held under.  **REPORTED for ``dump_exempt``'s reason**: the instances are
    #: the same instances either way -- re-offered to the document before they count
    #: (:func:`corpus_defect`) -- but a reader of a green pair is entitled to know which run
    #: paid for its evidence, and a census that cannot tell the two apart cannot measure a
    #: cold run against a warm one.  ``replayed == 0`` with ``examples > 0`` is a pair that
    #: drew; ``replayed == examples`` is a pair that did not.
    replayed: int = 0
    corpus_key: str = ""

    #: How many of :attr:`examples` came from the node's OWN ``examples`` keyword -- the
    #: document's own statement of a valid instance of itself, screened by the document
    #: before it counts (:func:`stated_instances`).  **A THIRD STATE BESIDE DRAWN AND
    #: REPLAYED, and §8 already requires it to be visible**: "a store that answers and a
    #: borrow that answers are different facts about coverage, and conflating them hides
    #: which one is doing the work."  ``stated == examples`` is a pair whose evidence is
    #: the schema author's, which is the strongest of the three and the only one that
    #: costs nothing.
    stated: int = 0

    #: Why §8's SUBSTITUTED node was abandoned and the pair redrawn from its own node, or
    #: ``""`` where the substitution answered.  ``hypothesis``'s own sentence, which
    #: carries the filtered-draw count.
    #:
    #: **§8 requires this to be loud: "A reduction reports emptiness as a failure, loudly,
    #: and a pair whose reduction came back empty is a defect report and not a slow
    #: pair."**  A substitution is this module's own derivation, so a substitution that
    #: admits nothing is a defect HERE and never a fact about the document -- and the whole
    #: hazard is that the fallback hides it: the pair goes green on its unreduced draw,
    #: pays the time the rule exists to remove, and reads as a pair that is inherently
    #: large.  A non-empty value beside ``outcome == "pass"`` is therefore a pass with a
    #: defect report attached, exactly as a non-empty :attr:`dump_exempt` is a conditional
    #: one; ``tests/test_emit.py`` ranges over the population and names them.
    abandoned: str = ""


def stated_instances(node: Any, *, validator_cls: Any = None) -> list[Any]:
    """The members of ``node``'s own ``examples`` that ``node`` ADMITS, in document order.

    **JSON Schema's own keyword for "here is a valid instance of this schema"**, which
    this bundle states 4,280 times over the 1,625 documents of its directory -- 167 of
    them inside the 1,054 PORTABLE documents the harness grades, 112 of those at a
    document root.  §8's fixture rule says a fixture is DERIVED and never hand-written
    because "a hand-written one is a thousand files to maintain and a silent exemption the
    first time a document changes under it"; an ``examples`` member is neither.  It is
    maintained with the schema, by the people who own the schema, and it is a derivation
    in the strict sense this module already uses -- nothing is written down here that the
    document does not state.

    **THE SCREEN IS THE WHOLE OF IT, and it is not a formality: measured over the graded
    population, 115 pairs' own node carries ``examples`` and the node REFUSES every member
    of 64 of them.**  The cause is one convention, visible in the first member of every one
    of the 64: the bundle's root ``examples`` hold ``{"description": ..., "data": <the
    instance>}`` rather than the instance, and a root that requires its own keys refuses
    that wrapper. 196 of the bundle's members take that shape.

    **The wrapper is NOT unwrapped here, and that is a decision rather than an
    omission.** draft-07 says a member of ``examples`` IS an instance; reading a ``data``
    key out of one would make this function interpret a convention the specification does
    not have, and the first document to spell the wrapper differently would get a silently
    wrong instance. An ``examples`` member its own node refuses is an upstream defect, it
    is reported as one, and the repair is a patch that is also the pull request (§1).

    ``[]`` for a node with no ``examples``, a non-list ``examples``, or one whose every
    member the node refuses -- all three mean "there is no stated instance here", and the
    caller then does exactly what it did before this rule existed.
    """
    if not isinstance(node, Mapping):
        return []
    held = node.get("examples")
    if not isinstance(held, list) or not held:
        return []
    try:
        cls = validator_cls or validator_for(node)
    except Exception:  # noqa: BLE001 -- a node with no validator states no instance
        return []
    return [m for m in held if conforms(node, m, validator_cls=cls) is True]


@dataclass
class LivenessResult:
    """One payload the DOCUMENT refuses, offered to the entry point under test."""

    #: Which perturbation produced the payload, naming the fact it broke
    #: (``"drops the required key 'x'"``), or ``""`` when none was found.
    how: str = ""
    #: Which keywords the document refused the payload on -- asked of the document
    #: rather than assumed from the perturbation, because a perturbation can break
    #: more than it aimed at.
    violated: tuple[str, ...] = ()
    detail: str = ""
    #: pass | schema_half_not_connected | model_error | no_payload
    outcome: str = "unrun"


# --------------------------------------------------------------------------- #
# the two directions
# --------------------------------------------------------------------------- #
_SETTINGS = {
    "deadline": None,
    "database": None,
    # **What this buys and what it does NOT, measured rather than assumed.**  It fixes the
    # SEED, so the same strategy yields the same stream; it does not make the drawn
    # instance a function of the schema.  Over two full passes of the same 1,664 pairs at
    # the same pinned inputs, 23 (1.4%) drew a different instance, and one identical
    # 208-pair shard re-run differed from itself on 3 -- not on the seed, not on
    # ``PYTHONHASHSEED`` and not on the recursion limit, but on process-global state inside
    # ``hypothesis`` whose lifetime garbage collection governs.  ``corpus_key`` and the
    # store behind it are what make the witness reproducible; this makes it cheap to
    # reproduce once held.
    # one seed per call; see above for what that does and does not fix
    "derandomize": True,
    "suppress_health_check": list(HealthCheck),
}


def check_format_strategy(
    fmt: str,
    strategy: st.SearchStrategy,
    *,
    counterexample: Any,
    examples: int = 50,
    format_checker: Any = None,
) -> FormatStrategyVerdict:
    """Grade a ``custom_formats`` entry before it is trusted to generate.

    ``missing_formats`` says which formats have no strategy. It cannot say whether
    a strategy that EXISTS is right, and a wrong one is the more dangerous of the
    two: a strategy emitting values the format refuses makes every site using that
    format pass vacuously, and a vacuous pass is reported by nothing. So both
    answers are required of every entry --

      * the values it produces are admitted by the format;
      * a deliberately malformed value of the same shape is REFUSED.

    The second answer is not redundant. Without it, a validator that has no checker
    for the format (``conforms`` then answers True for every input) is
    indistinguishable from one that genuinely admits what was generated. That case
    is reported as ``unchecked``, which is not a pass: a format nothing checks
    cannot be graded by checking it, and the caller is owed that fact rather than a
    green mark.
    """
    fc = format_checker if format_checker is not None else jsonschema.FormatChecker()
    v = FormatStrategyVerdict(fmt=fmt, checked=fmt in fc.checkers)
    if not v.checked:
        return v

    def body(value: Any) -> None:
        v.examples += 1
        if fc.conforms(value, fmt):
            v.accepted += 1
        elif not v.rejected:
            v.rejected = repr(value)[:200]

    try:
        run = given(value=strategy)(body)
        run = settings(max_examples=examples, phases=[Phase.explicit, Phase.generate], **_SETTINGS)(
            run
        )
        run()
        v.counterexample_refused = not fc.conforms(counterexample, fmt)
    except Exception as e:
        v.detail = f"{type(e).__name__}: {e}"[:300]
    return v


class _DumpRefused(Exception):
    """The class constructed a value whose DUMP its own document refuses.

    Raised from inside the accepts check's body and caught BY NAME, so the verdict
    is ``model_dropped_a_fact`` and not the ``model_error`` any other exception from
    the body reads as.  The instance that showed it is reported verbatim: there is
    no shrink phase to simplify it, and at the default ``examples=1`` there is one
    generated instance for a shrink to have worked on anyway.
    """


def _wire_dump(value: Any) -> Any:
    """What ``value`` looks like on the wire, by pydantic's own reading.

    ``mode="json"`` so a ``datetime`` and a URL come back as the strings their
    documents declare; ``by_alias`` because a document's key is the alias wherever
    the two differ; and ``exclude_unset`` because a key the payload never carried
    is not a fact the document stated about it -- dumping the model's rendering of
    absence instead would charge the class for a ``null`` the instance never had.

    A scalar root is an ``Annotated`` ALIAS and not a class (D2), so there is no
    ``model_dump`` to call and the adapter for the value's own type is the dump:
    it is the same conversion pydantic would apply to that field inside a class.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_unset=True)
    return TypeAdapter(type(value)).dump_python(value, mode="json")


#: A key no document in any bundle declares, used to probe a closed object.
_ALIEN_KEY = "__adcp_harness_not_a_property__"

#: Values spanning the JSON types, tried in order as a whole-instance replacement.
#: One of them has a different JSON type from any instance, so a document that
#: states a root ``type`` at all refuses at least one.
_ALIEN_VALUES: tuple[Any, ...] = (None, "__adcp_harness__", -1, [], {}, True)


#: How many ``allOf`` levels :func:`own_facts` folds before it stops.  A composed class
#: is one class over its whole conjunct list at any depth
#: (``lower.composition.lower_composition``'s worklist), so the fold has to reach the same depth;
#: the bound is here because a fold with no base case is a crash and section 9 says a
#: crash is not an outcome.
_OWN_DEPTH = 8


def own_facts(schema: Any, depth: int = 0) -> dict[str, Any]:
    """Every keyword the node at this pointer states ABOUT ITSELF, conjuncts folded in.

    **The input half of :func:`refused_witnesses`, and it is not :func:`_composed`.**
    That function is the document-side reading of a node's VALUE SET and folds the facts
    section 2's intersection rule orders -- ``FOLDED_FACTS``, which is
    ``keywords.rendered_at(ROOT)`` and therefore carries no ``min``/``maxProperties``, no
    ``dependencies`` and no conditional.  What a refuses-check needs is the opposite
    reading: not "what does the composed node admit" but "which keywords are there to take
    a boundary FROM", and a keyword no intersection rule can order still names a boundary.
    ``core/positive-postal-area-support.json`` is the measurement: its ``minProperties``
    sits in a conjunct, ``_composed`` does not carry it to the root, and the witness that
    found the P0 -- ``{}`` -- is derived from that keyword and from no other.

    Gap-fill and never override, in document order, which is the safe direction here: the
    node's own statement is the one the walk reads first, and a conjunct's fills a keyword
    nobody else states.  Every candidate built from this is SCREENED by the whole document
    anyway (:func:`refused_witnesses`), so a fold that reads one keyword from the wrong
    view produces a candidate the document admits and the candidate is dropped.

    **``required`` is the one exception and it composes by UNION**, which is
    :func:`_composed`'s own rule for it: it is a set of names and every conjunct
    contributes its own, so a gap-fill would read one view's names and drop the rest --
    and ``required`` is the keyword this function's commonest witness comes from.

    **``properties`` is deliberately NOT merged here.**  A key two views declare is one
    key whose declarations compose, and composing them needs the pointer each view's
    ``$ref`` is read against -- ``core/positive-postal-area-support.json`` declares
    ``us_zip`` in both views and the RECORD shares each declaration into its own
    ``definitions`` entry, so the merge is of two pointers and not of two declarations.
    That reading belongs to a caller that has the root in hand; nothing in
    :func:`refused_witnesses` reads ``properties`` at all.

    **AND A CONJUNCT'S ``if``/``then``/``else`` IS NOT FOLDED EITHER, BECAUSE THE FOLD WAS
    MEASURED TO DROP ONE AND TO FABRICATE ANOTHER** (``adcp-client-python-x63t`` cause 3,
    ``adcp-client-python-wvod``).  The gap-fill above is "the safe direction" for a keyword
    that stands alone; a conditional does not.  Two things go wrong and both are measured
    at ``protocol/sync-agent-notification-configs-request.json
    #/properties/notification_configs/items``, where conjunct 0 (the ``$ref``'d document's
    own) and conjunct 1 each state one:

    * ``setdefault`` keeps conjunct 0's ``if`` and SILENTLY DISCARDS conjunct 1's
      ``{"required": ["authentication"]}`` -- which is the whole of the fact
      ``adcp-client-python-wvod`` is about, so the keyword never reached the derivation at
      all;
    * and the three keys are folded INDEPENDENTLY, so one conjunct's ``if`` can be paired
      with another's ``then`` -- a conditional no document states, derived by this
      function and attributable to nothing.

    A conditional is a TRIPLE whose members mean nothing apart, and two conjuncts' triples
    are two independent constraints on one instance rather than one constraint with gaps.
    :func:`conditionals` is the reader for the composed answer and returns them unmerged;
    the node's OWN triple stays in this mapping because the node does state it about
    itself, and nothing reads it from here.
    """
    if not isinstance(schema, dict) or depth > _OWN_DEPTH:
        return {}
    out = {k: v for k, v in schema.items() if k != "allOf"}
    conjuncts = schema.get("allOf")
    if not isinstance(conjuncts, list):
        return out
    for conjunct in conjuncts:
        folded = own_facts(conjunct, depth + 1)
        for keyword, value in folded.items():
            if keyword in CONDITIONAL:
                continue
            if keyword == "required" and isinstance(value, list):
                have = out["required"] if isinstance(out.get("required"), list) else []
                out["required"] = [*have, *(k for k in value if k not in have)]
                continue
            out.setdefault(keyword, value)
    return out


#: draft-07's conditional, read off the TABLE and never spelled here
#: (:func:`codegen.keywords.conditional`).  Two readers need the same answer to "is this
#: keyword part of a conditional" -- :func:`own_facts` declines to fold one and
#: :func:`conditionals` collects them whole -- and §3 makes the table the one place a
#: keyword decision lives, so this is a derived VIEW for :data:`_OWNS`' reason and not a
#: second declaration.
CONDITIONAL: frozenset[str] = frozenset(keywords.conditional())


def conditionals(schema: Any, depth: int = 0) -> tuple[dict[str, Any], ...]:
    """Every ``if``/``then``/``else`` TRIPLE this node states, conjuncts included, UNMERGED.

    **The composed reading :func:`own_facts` declines to make**, and the reason it is a
    tuple of triples rather than one mapping is the measurement on
    ``adcp-client-python-wvod``'s three sites: each is an ``allOf`` of a ``$ref`` to a
    named document that states its own conditional, plus a conjunct stating a second one.
    Those are two constraints on the same instance -- draft-07 applies every ``allOf``
    member to the whole instance -- so an instance must satisfy both, and a reading that
    keeps one has dropped a fact the document states.  A reading that keeps one's ``if``
    beside the other's ``then`` has invented a fact the document does not state.

    In document order, the node's own first and then each conjunct's, depth-first, bounded
    by :data:`_OWN_DEPTH` for the reason that constant already carries: a composed class is
    one class over its whole conjunct list at any depth, so the collection has to reach the
    same depth, and a walk with no base case is a crash rather than an outcome.

    A triple with no ``if`` is not one: draft-07 gives ``then`` and ``else`` no effect
    without it, so a node stating only ``then`` states no conditional and contributes
    nothing here.
    """
    if not isinstance(schema, dict) or depth > _OWN_DEPTH:
        return ()
    out: list[dict[str, Any]] = []
    #: The keys in the table's own order, which is why :func:`keywords.conditional`
    #: returns a tuple: a triple whose key order came from a set would differ between two
    #: readings of one document, and this mapping is what a reader of a failure sees.
    if "if" in schema:
        out.append({k: schema[k] for k in keywords.conditional() if k in schema})
    conjuncts = schema.get("allOf")
    if isinstance(conjuncts, list):
        for conjunct in conjuncts:
            out.extend(conditionals(conjunct, depth + 1))
    return tuple(out)


def _far_side(facts: Mapping[str, Any], instance: Any) -> Iterator[tuple[Any, str, str]]:
    """One value on the FAR side of each boundary ``facts`` states, from ``instance``.

    :func:`refused_witnesses`' derivation, extracted from its screen so that a second
    caller can reach it: the conditional arm needs candidates violating a SUBSCHEMA -- the
    ``then`` or the ``else`` -- while screening each against the whole document, and a
    derivation that screened as it went could only ever answer about the node it was handed.

    So this yields and never decides: a candidate here is a value some keyword of ``facts``
    says is outside its boundary, with no claim that the DOCUMENT refuses it.  The claim is
    the caller's and it is made by ``conforms``.  That split is what keeps the derivations
    simple -- a keyword whose far side cannot be built, or whose far side a sibling keyword
    widens back in, contributes nothing and costs no verdict.

    ``facts`` and not a schema, because the caller chooses the fold: the node's own is
    :func:`own_facts`, and an arm's is :func:`own_facts` of the arm.
    """

    def whole(value: Any) -> int | float | None:
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    # ---- the object's KEY SET: required, the property counts, a closed object ----
    if isinstance(instance, dict):
        for key in facts.get("required") or []:
            if isinstance(key, str) and key in instance:
                yield ({k: v for k, v in instance.items() if k != key}, "required",
                       f"drops the required key {key!r}")
        low = whole(facts.get("minProperties"))
        if low is not None:
            short = dict(list(instance.items())[: max(int(low) - 1, 0)])
            yield (short, "minProperties",
                   f"{len(short)} keys, one short of minProperties {low}")
        high = whole(facts.get("maxProperties"))
        if high is not None:
            over = dict(instance)
            while len(over) <= int(high):
                over[f"{_ALIEN_KEY}{len(over)}"] = 1
            yield over, "maxProperties", f"{len(over)} keys, one past maxProperties {high}"
        for keyword in ("additionalProperties", "propertyNames", "patternProperties"):
            # **``true`` IS THE IDENTITY AND STATES NO BOUNDARY, so it yields no witness**
            # (``adcp-client-python-szfx``).  The value below is screened by the whole
            # document, so an identity keyword still produced a candidate wherever some
            # OTHER keyword refused the undeclared key -- and the candidate then carried
            # this keyword's name, which is the name ``check_refuses`` compares against the
            # declared set.  Two pairs were reported undeclared on a keyword that refused
            # nothing: ``core/creative-assets.json#``, whose ``patternProperties`` is
            # DECLARED and whose ``additionalProperties`` is ``true``, and
            # ``core/catalog-item-availability-error.json#``, where ``core/error.json``
            # states ``true`` and the refusal is a conditional arm's
            # ``additionalProperties: false`` one level in.  This module already reads the
            # keyword that way where the answer is an accepted SET (:func:`_silent_about_extras`:
            # "the two spellings accept and refuse identical instances"); a boundary
            # derivation is the same reading, and the keyword that does refuse keeps the
            # witness instead.
            if keyword in facts and facts[keyword] is not True:
                yield ({**instance, _ALIEN_KEY: 1}, keyword,
                       f"adds the undeclared key {_ALIEN_KEY!r}")
        depends = facts.get("dependencies")
        if isinstance(depends, dict):
            for trigger, needs in depends.items():
                if not isinstance(needs, list):
                    continue
                dropped = {k: v for k, v in instance.items() if k not in needs}
                yield ({**dropped, trigger: instance.get(trigger, 1)}, "dependencies",
                       f"keeps {trigger!r} and drops what it depends on")
    # ---- the string's LENGTH and its PATTERN ----
    if isinstance(instance, str):
        low = whole(facts.get("minLength"))
        if low is not None:
            yield (instance[: max(int(low) - 1, 0)], "minLength",
                   f"one character short of minLength {low}")
        high = whole(facts.get("maxLength"))
        if high is not None:
            # EXACTLY one past the bound, built by padding the accepted instance and
            # truncating: the witness §8 names is "both sides of each bound and the bound
            # itself", so the far side is the bound plus one and not an arbitrarily longer
            # string -- a reader of a failure has to see which boundary was crossed.
            yield ((instance + "x" * (int(high) + 1))[: int(high) + 1], "maxLength",
                   f"one character past maxLength {high}")
        if "pattern" in facts:
            yield _ALIEN_KEY, "pattern", "a string the pattern does not match"
    # ---- the number's BOUNDS ----
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        for keyword, step in (("minimum", -1), ("maximum", 1)):
            bound = whole(facts.get(keyword))
            if bound is not None:
                yield bound + step, keyword, f"one past {keyword} {bound}"
        for keyword in ("exclusiveMinimum", "exclusiveMaximum"):
            bound = whole(facts.get(keyword))
            if bound is not None:
                yield bound, keyword, f"the excluded bound {bound} itself"
        factor = whole(facts.get("multipleOf"))
        if factor:
            yield (factor + factor / 2 if isinstance(factor, float) else factor * 2 + 1,
                   "multipleOf", f"not a multiple of {factor}")
    # ---- the array's LENGTH and its DISTINCTNESS ----
    if isinstance(instance, list):
        low = whole(facts.get("minItems"))
        if low is not None:
            yield (instance[: max(int(low) - 1, 0)], "minItems",
                   f"one element short of minItems {low}")
        high = whole(facts.get("maxItems"))
        if high is not None:
            filler = instance[0] if instance else None
            yield ([*instance, *([filler] * (int(high) + 1 - len(instance)))], "maxItems",
                   f"one element past maxItems {high}")
        if facts.get("uniqueItems") is True and instance:
            yield [*instance, instance[0]], "uniqueItems", "repeats an element"
        if "contains" in facts:
            yield [], "contains", "an empty array, which contains nothing"
    # ---- the VOCABULARY, and the JSON type itself ----
    if "const" in facts:
        for alien in _ALIEN_VALUES:
            yield alien, "const", f"{alien!r}, which is not the pinned value"
    members = facts.get("enum")
    if isinstance(members, list):
        for alien in (_ALIEN_KEY, *_ALIEN_VALUES):
            if alien not in members:
                yield alien, "enum", f"{alien!r}, which no enum member is"
    if "type" in facts:
        for alien in _ALIEN_VALUES:
            if type(alien) is not type(instance):
                yield alien, "type", f"replaces the instance with {alien!r}"


#: How deep a conditional's ARM is descended by :func:`_violating`.
#:
#: **A BOUND AND NOT A REACH, and the reason is the instrument §8 deleted.**  That one
#: mutated one keyword at every one of 27,791 sites and spent the suite's whole wall clock
#: proving a property of ``jsonschema``; this descends an arm's ``properties`` for the keys
#: the instance already carries, which is finite and small, and the bound is what keeps a
#: document that nests conditionals from turning the reduction back into that sweep.
#: ``adcp-client-python-wvod``'s three sites are reached at depth 1 -- the arm states
#: ``properties.authentication.required`` -- so the bound is above the measured shape and
#: not tuned to it.
_ARM_DEPTH = 4


def _arm_of(
    triple: Mapping[str, Any], instance: Any, *, validator_cls: Any = None
) -> tuple[str, Any]:
    """WHICH of a conditional's two arms is in force for ``instance``, and the arm.

    **The document's answer and not a guess.**  draft-07 applies ``then`` where the
    instance satisfies ``if`` and ``else`` where it does not, so the accepted instance
    decides which of the two is in force -- and only that one is a boundary a witness can
    be taken from.  The other arm says nothing about this instance at all.

    A condition the validator cannot answer (``conforms`` -> ``None``) selects ``else``,
    which is fail-safe in the direction that matters: every candidate derived from an arm
    is screened against the whole document, so a wrong arm contributes no witness rather
    than an assertion the document does not make.

    One function because two readers need the same answer and must not differ:
    :func:`refused_witnesses` takes the witnesses, and :func:`unreached_conditionals`
    reports the conditionals that yielded none.  Stated twice, the artifact could report a
    boundary as unreached while the derivation had in fact read the other arm.
    """
    condition = triple.get("if")
    satisfied = conforms(condition, instance, validator_cls=validator_cls) is True
    which = "then" if satisfied else "else"
    return which, triple.get(which)


def unreached_conditionals(
    schema: dict, instance: Any, *, validator_cls: Any = None
) -> tuple[str, ...]:
    """Every conditional of this node that the reduction could put NO value to, with why.

    **The reduction's reach is not its population, and this is the difference measured
    rather than described.**  :func:`check_refuses` is asked about every pair of the graded
    population, but a conditional's boundary lies inside the region its ``if`` selects, and
    the reduction has ONE accepted instance -- ``check_accepts``' draw at ``examples=1``.
    Where that instance is outside the ``if``'s region and the node states no ``else``,
    there is no arm in force and no boundary to perturb: the class is never asked about
    that conditional at all.

    Measured on ``adcp-client-python-wvod``'s own three sites, which is why this exists:
    two of them drew an instance carrying ``authentication``, so the
    ``{"if": {"required": ["authentication"]}}`` arm was in force and both reported the
    undeclared widening.  The third --
    ``account/sync-accounts-request.json#/properties/accounts/items/properties/notification_configs/items``
    -- drew ``{event_types, subscriber_id, url}``, satisfied neither of its two ``if``s,
    and reported ``pass`` on the witnesses it DID offer.  A ``pass`` there would say the
    class refuses what its document refuses, about a document fact the class was never
    offered a value for; this is what makes the cell ``absent`` instead.

    Two reasons a conditional is unreached and both are reported, because they ask for
    different work: the ARM IS ABSENT (a wider draw reaches it) and the arm states nothing
    this reduction can perturb (:func:`_violating` is what would have to grow -- an
    ``items`` narrowing, or ``adcp-client-python-3bb``'s conditional nested in an arm).
    """
    cls = validator_cls or validator_for(schema)
    out: list[str] = []
    for triple in conditionals(schema):
        which, arm = _arm_of(triple, instance, validator_cls=cls)
        condition = json.dumps(triple.get("if"), sort_keys=True, default=str)[:120]
        if not isinstance(arm, dict):
            out.append(
                f"the instance is outside the region {condition} selects and the node "
                f"states no {which}, so no arm is in force and no value was offered"
            )
            continue
        if not any(True for _ in _violating(arm, instance)):
            out.append(
                f"the {which} of {condition} states nothing this reduction can perturb "
                "from the accepted instance, so no value was offered"
            )
    return tuple(out)


def _violating(arm: Any, instance: Any, depth: int = 0) -> Iterator[tuple[Any, str, str]]:
    """Values that break ``arm`` while keeping ``instance``'s shape, as far as an arm goes.

    **The half of the conditional a refuses-check needs.**  A node stating
    ``{"if": C, "then": T}`` refuses every value that satisfies ``C`` and breaks ``T``, so
    the witness is the accepted instance perturbed to break ``T`` and nothing else -- and
    whether the perturbation also broke ``C`` is the document's question, answered by the
    screen in :func:`refused_witnesses` rather than by this derivation.

    Two descents, and the second is what ``adcp-client-python-wvod`` needs:

    * the arm's OWN keywords, through :func:`_far_side`, which covers an arm stating
      ``required`` or a ``const`` or a count on the whole instance;
    * the arm's ``properties``, for the keys the instance ALREADY CARRIES, rebuilt as the
      instance with that one key replaced.  wvod's three sites state
      ``{"then": {"properties": {"authentication": {"required": ["credentials"]}}}}``, and
      the witness is the instance with ``credentials`` dropped from ``authentication`` --
      which is the payload that row exhibits, derived rather than written down.

    **Only keys the instance carries, which is what keeps this a REDUCTION.**  Inventing a
    key the instance does not have would be building a value rather than perturbing one,
    and §8's whole cost argument is that this function draws nothing.

    **``items`` is NOT descended and that is a stated limit, not an oversight.**  An arm
    narrowing an array's members would need one witness per element and a reader of a
    failure would need to be told which one; nothing in the measured population
    (``adcp-client-python-wvod``, 13 sites) takes that shape, and a conditional nested
    inside another conditional's ARM is ``adcp-client-python-3bb``'s row and not this one.
    Both are reported as unreached rather than as green: a witness this cannot build
    contributes no verdict, so the pair reads ``pass`` only on the witnesses that WERE
    offered and the row above says which.
    """
    if not isinstance(arm, dict) or depth > _ARM_DEPTH:
        return
    facts = own_facts(arm)
    yield from _far_side(facts, instance)
    declared = facts.get("properties")
    if not isinstance(declared, dict) or not isinstance(instance, dict):
        return
    for key, declaration in declared.items():
        if key not in instance:
            continue
        for candidate, keyword, how in _violating(declaration, instance[key], depth + 1):
            yield {**instance, key: candidate}, keyword, f"at {key!r}, {how}"


def refused_witnesses(
    schema: dict, instance: Any, *, validator_cls: Any = None
) -> tuple[tuple[Any, str, str], ...]:
    """Every value this node's own keywords say the document REFUSES, from one it ADMITS.

    **Section 8's witness derivation, taken on the FAR side of each boundary.**  The draw
    "COVERS the node's admissible space by constraint class; it does not sample it. ...
    For each keyword the node states, the draw takes the classes that keyword
    distinguishes: every member of an ``enum``, both sides of each bound and the bound
    itself."  :data:`codegen.keywords` names the keywords; this takes the OUTSIDE class of
    each one -- the string one shorter than ``minLength``, the object one key short of
    ``minProperties``, the number just past ``maximum``, the value no ``enum`` member is --
    because that is the half ``check_accepts`` never offers and therefore the half no
    instrument has ever graded.  ``adcp-client-python-6oe`` is what that blindness cost: a
    class wider than its document in the one direction the whole existing instrument
    cannot see, reported by nothing for as long as it existed.

    **EVERY CANDIDATE IS SCREENED BY THE DOCUMENT**, exactly as :func:`refusing_payload`
    screens its three: ``conforms`` has to answer ``False`` before a candidate is yielded,
    so a derivation that misreads a keyword yields nothing rather than an assertion the
    document does not make.  That is what lets the derivations below be simple: a keyword
    whose far side this cannot build, or whose far side the document admits anyway because
    a sibling keyword widens it, contributes no witness and costs no verdict.

    **It is a REDUCTION of the instance and never a draw**, which is the whole of why this
    is affordable: ``check_accepts``' cost is ``hypothesis_jsonschema.from_schema``
    (151.24 s of a 151.51 s pair, ``tests/corpus.py``), and this calls it never.  One
    accepted instance -- the one the accepts check already has in hand, which is why
    ``check_pair`` passes ``accepted[0]`` to :func:`check_liveness` for its own payload --
    is perturbed once per keyword, and each perturbation is one ``conforms``.

    Returns ``(the candidate, the keyword it came from, how)``.  The keyword is the one
    this function AIMED at; which keywords the document actually refused on is
    :func:`violated_keywords`' answer and the caller reports that beside it, for the reason
    that function's own docstring gives.

    **AND A CONDITIONAL IS ONE OF THE KEYWORDS, which it was not until
    ``adcp-client-python-x63t``.**  That row measured the hole from the far side: over
    ``adcp-client-python-wvod``'s three nodes this function aimed at
    ``['additionalProperties', 'required', 'type']``, no witness aimed at
    ``if``/``then``/``else``, and "the payload the document refuses is among the witnesses:
    False" -- so even wired onto the graded path the instrument could not have found those
    three.  :func:`conditionals` collects the triples a node states, :func:`_arm_of` says
    which arm an instance puts in force, and :func:`_violating` takes the far side of THAT
    arm; the conditionals no value was offered for are
    :func:`unreached_conditionals`' answer, which ``check_refuses`` reports beside this so
    a ``pass`` cannot stand for a boundary nobody crossed.
    """
    cls = validator_cls or validator_for(schema)
    out: list[tuple[Any, str, str]] = []

    def take(candidate: Any, keyword: str, how: str) -> None:
        if conforms(schema, candidate, validator_cls=cls) is False:
            out.append((candidate, keyword, how))

    for candidate, keyword, how in _far_side(own_facts(schema), instance):
        take(candidate, keyword, how)
    #: **THE CONDITIONAL ARM, and it is LAST so no existing witness changes its label.**
    #: The dedup below keeps the FIRST keyword that aimed at a candidate, so an arm placed
    #: before the keyword derivations would relabel witnesses the 15-pair gate already
    #: reads -- which is a change to what this function says about pairs nobody asked about.
    for triple in conditionals(schema):
        which, arm = _arm_of(triple, instance, validator_cls=cls)
        for candidate, keyword, how in _violating(arm, instance):
            #: **ATTRIBUTED TO ``if`` AND NOT TO THE ARM'S OWN KEYWORD**, because that is
            #: the keyword §2's declaration carries: ``core/agent-notification-config.json``
            #: declares its own root conditional as ``Approximation(pointer='#',
            #: keyword='if', kind='WIDENED', rung='KEYWORD')``, so a module that declares
            #: this widening declares it under ``if`` and ``check_refuses``' comparison
            #: against ``declared`` has to be made on the same name.  The arm's own keyword
            #: travels in ``how``, where a reader of a failure needs it.
            take(candidate, "if", f"satisfies the if, and the {which} refuses it: {how}")
    #: Deduplicated by the candidate's JSON text, keeping the FIRST keyword that aimed at
    #: it: two keywords can name one value (a ``const`` and the ``type`` beside it), and
    #: offering it twice would report one disagreement twice.
    seen: set[str] = set()
    unique: list[tuple[Any, str, str]] = []
    for candidate, keyword, how in out:
        text = json.dumps(candidate, sort_keys=True, default=str)
        if text in seen:
            continue
        seen.add(text)
        unique.append((candidate, keyword, how))
    return tuple(unique)


#: How long a witness :func:`admitted_witnesses` grows a string leaf to.
#:
#: **THE INSTRUMENT'S OWN BUDGET AND NEVER A TYPE'S BOUND, which is the whole of why this
#: is one number rather than a table.**  A position whose document states no ``maxLength``
#: admits a string of ANY length, so no finite witness is the boundary -- there is no
#: boundary to take, which is exactly what makes the position invisible to
#: :func:`refused_witnesses`' derivation (it takes the far side of a bound, and here there
#: is none).  What a witness can say is "the document admits a string this long and the
#: class does not", and how long is then the instrument's choice.
#:
#: **A per-``format`` table of witnesses was the alternative and it is refused.**  Pydantic
#: caps its URL types at 2083 characters; a witness written as "2084 characters" would be
#: the SDK's own reading of pydantic's internals committed to a file, and would say nothing
#: the day pydantic moved the cap or a second narrow type arrived with a different one.
#: 2083 appears nowhere here.  One power of two above it, chosen so a single witness per
#: leaf answers for any cap below it, is a budget: it is read once, it is reported with the
#: result, and it is wrong in the safe direction -- too SHORT a budget loses a finding and
#: cannot manufacture one, because every candidate is screened by the document.
WITNESS_LENGTH = 4096

#: How many string leaves of one instance :func:`admitted_witnesses` reaches.
#:
#: A BUDGET, and :attr:`AdmitsResult.capped` reports it as one so a ``pass`` over a capped
#: instance is not read as a pass over the whole of it.  Measured over the graded
#: population: 18 of 2,582 instances carry more leaves than this.
WITNESS_LEAVES = 60


def _string_leaves(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[tuple[Any, ...], str]]:
    """Every STRING leaf of an instance, with its instance location.

    The location is a path of keys and indices into the instance and never a JSON pointer:
    what the caller does with it is :func:`_placed`, which rebuilds the instance with one
    leaf replaced, and a pointer would have to be parsed back into exactly this.
    """
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, inner in value.items():
            yield from _string_leaves(inner, (*path, key))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _string_leaves(inner, (*path, index))


def _at_leaf(value: Any, path: Sequence[Any], new: Any) -> Any:
    """``value`` with ``new`` at ``path``, COPIED and never mutated in place.

    Mutation would hand the next candidate an instance the previous one had already
    changed, so one refused witness would pollute every witness after it and a failure
    would name a value no derivation produced.
    """
    if not path:
        return new
    head, rest = path[0], path[1:]
    if isinstance(value, dict):
        return {**value, head: _at_leaf(value[head], rest, new)}
    copy = list(value)
    copy[head] = _at_leaf(copy[head], rest, new)
    return copy


def stated_patterns(node: Any, depth: int = 0) -> tuple[str, ...]:
    """Every ``pattern`` this node states anywhere under it, deduplicated, document order.

    **The input half of :func:`admitted_witnesses`' third derivation, and it is a WALK
    rather than a frontier read** (:func:`locations`) because what it needs is not where
    the pattern sits but which patterns exist to draw from: a candidate drawn from a
    pattern is offered at a leaf the pattern already matches and screened by the whole
    document, so a pattern read from the wrong depth yields nothing rather than a claim.

    Bounded for :data:`_OWN_DEPTH`'s reason -- a graded node reaches 683,849 bytes and a
    walk with no base case is a crash rather than an outcome.
    """
    out: list[str] = []

    def walk(inner: Any, at: int) -> None:
        if at > _OWN_DEPTH:
            return
        if isinstance(inner, dict):
            pattern = inner.get("pattern")
            if isinstance(pattern, str) and pattern not in out:
                out.append(pattern)
            for value in inner.values():
                walk(value, at + 1)
        elif isinstance(inner, list):
            for value in inner:
                walk(value, at + 1)

    walk(node, depth)
    return tuple(out)


@functools.lru_cache(maxsize=4096)
def matching_a_pattern(pattern: str, examples: int = 2) -> tuple[str, ...]:
    """Strings the pattern matches, DRAWN from the pattern rather than written.

    **The one derivation in this module whose source is a KEYWORD and not an instance**,
    and ``adcp-client-python-rwng`` is why it has to exist: an instance-derived witness is
    a perturbation of a value the generator already produced, so where that value is
    already inside the narrow type and stays inside it under perturbation, no instance
    witness reaches the narrowing.  Measured at ``core/https-url.json#``, whose document is
    ``{"type": "string", "format": "uri", "pattern": "^https://"}``: the held value is
    ``'https://A.COM'``, the trailing-newline witness is ``'https://A.COM\\n'``, and
    pydantic NORMALISES and admits it.  Drawn from the pattern instead, the value is
    ``'https://'`` -- a string the pattern matches, the document admits and the alias
    refuses with ``url_parsing``, "empty host".  So the two derivations are complements:
    the family sized by instance witnesses alone was a LOWER bound.

    Cached on the pattern, because the graded population states each pattern at many
    positions and a draw per position would pay ``from_regex`` thousands of times for an
    answer that is a function of the pattern alone.

    A pattern ``from_regex`` cannot build contributes NO witness and raises nothing: the
    screen is what makes a candidate a claim, so a derivation that produces nothing costs
    a verdict nobody is entitled to rather than an error.
    """
    out: list[str] = []

    @settings(
        max_examples=examples,
        phases=[Phase.generate],
        **_SETTINGS,
    )
    @given(st.from_regex(pattern))
    def draw(value: str) -> None:
        out.append(value)

    try:
        draw()
    except Exception:  # noqa: BLE001 -- a pattern nothing can draw states no witness
        return ()
    return tuple(dict.fromkeys(out))


def admitted_witnesses(
    schema: dict,
    instance: Any,
    *,
    validator_cls: Any = None,
    length: int = WITNESS_LENGTH,
    leaves: int = WITNESS_LEAVES,
) -> Iterator[tuple[Any, str, str]]:
    """Every value this document ADMITS that the DRAW will not produce, from one it admits.

    **:func:`refused_witnesses` in the other direction, and it exists because reading 1's
    first check cannot fail at a formatted position without it**
    (``adcp-client-python-87ll``).  ``docs/plan/final-state.md`` reading 1 check 1 is "draw
    a value from the document; the class must admit it", and :func:`_validating`'s own
    docstring already says why the draw cannot decide it: *"hypothesis_jsonschema HONOURS a
    format it knows when generating -- it produced an offset in 200 of 200 date-time
    instances -- so every drawn instance landed inside the narrow type and the draw was
    green on a model that refused every other shape the format admits."*  A class carrying
    a pydantic type substituted for a document's ``format`` is NARROWER than its document,
    and at 404 pairs of 2,587 the check passed without ever offering the document's own
    wider value.  A check that cannot fail at 404 positions reports the generator and not
    the class.

    **NOTHING HERE IS LISTED PER ``format``, and that is the one rule this derivation has
    to keep.**  A table of hand-written witnesses -- "for date-time, try a trailing
    newline; for uri, try 2084 characters" -- would be a frozen census of pydantic's
    internals in a file, stale the first time either side moved, and this epic has repaired
    four of those in two days.  So: the LEAF comes from an instance the document has
    already admitted, the perturbation is one universal string operation, the length is
    :data:`WITNESS_LENGTH` (the instrument's budget), the pattern is the document's own
    keyword, and **the claim that the document admits the result is the DOCUMENT's**.

    Three derivations, each at every string leaf of ``instance``:

    * **a trailing newline** -- ``leaf.rstrip("\\n") + "\\n"``.  One character, the same
      universal perturbation :func:`_far_side` makes with ``"x"``.  It reaches the 164
      ``date-time`` pairs, where ``rfc3339-validator``'s regex is ``$``-anchored and
      Python's ``$`` matches before a trailing newline -- the same defect
      ``test_a_root_scalar_alias_is_compiled_with_the_same_engine_as_a_class`` exists for,
      which the project fixed in the CLASS (``regex_engine="python-re"``) rather than
      calling the document's own admission an instrument defect.
    * **an unbounded length** -- the leaf grown with its OWN last character to
      :data:`WITNESS_LENGTH`.  The filler is the instance's and not a letter chosen here,
      and a leaf whose format refuses the repetition is screened out and contributes
      nothing.  It reaches the 188 ``url_too_long`` pairs.
    * **a value drawn from a ``pattern`` the document states** (:func:`matching_a_pattern`),
      offered at a leaf that pattern already matches.  ``adcp-client-python-rwng``'s route,
      and it reaches 87 pairs no instance-derived witness does.

    **THE SCREEN IS THE WHOLE OF IT** -- :func:`conforms` against ``schema`` has to answer
    ``True`` before a candidate is yielded, which is :func:`refused_witnesses`' rule with
    the sign flipped and buys the same thing: the derivations may be simple and wrong in
    the safe direction, because a candidate the document does not admit says nothing about
    the class and is never offered to it.  So this cannot manufacture a failure; it can
    only miss one.

    Yields ``(the candidate, the kind of witness, how it was derived)``.
    """
    cls = validator_cls or validator_for(schema)
    patterns = stated_patterns(schema)
    for path, old in itertools.islice(_string_leaves(instance), leaves):
        if not old:
            continue
        candidates: list[tuple[Any, str, str]] = []
        newline = old.rstrip("\n") + "\n"
        if newline != old:
            candidates.append(
                (newline, "trailing_newline", "the leaf's own value with a trailing newline")
            )
        if len(old) < length:
            candidates.append(
                (
                    old + old[-1] * (length - len(old)),
                    "unbounded_length",
                    f"the leaf's own value grown to {length} characters on {old[-1]!r}",
                )
            )
        for pattern in patterns:
            try:
                governs = re.search(pattern, old) is not None
            except re.error:  # a pattern Python cannot compile governs nothing here
                continue
            if not governs:
                continue
            for drawn in matching_a_pattern(pattern):
                for value, how in (
                    (drawn, f"drawn from the pattern {pattern!r}"),
                    (
                        drawn.rstrip("\n") + "\n",
                        f"drawn from the pattern {pattern!r}, with a trailing newline",
                    ),
                ):
                    if value != old:
                        candidates.append((value, "pattern_derived", how))
        for value, kind, how in candidates:
            whole = _at_leaf(instance, path, value)
            if conforms(schema, whole, validator_cls=cls) is not True:
                continue
            yield whole, kind, f"{how} at {_location(path)}"


def _location(path: Sequence[Any]) -> str:
    """One instance location, spelled as a path and named ``the instance itself`` at the root."""
    return "/".join(str(step) for step in path) or "the instance itself"


def _refusal_cause(e: BaseException) -> str:
    """What the class refused ON, read off pydantic's own error ``type``.

    :func:`violated_keywords`' rule applied to the class's side of a disagreement: the
    name a reader categorises by has to be the one the engine NAMES, because a category
    read out of prose moves the next time the prose does -- and these messages are
    pydantic's, which the project does not own.  ``check_accepts`` reads the same field for
    ``model_refused_valid``.

    The exception's CLASS NAME where there is no such field, which is the honest answer for
    a class that raised something a consumer cannot catch as a validation error.
    """
    errors = getattr(e, "errors", None)
    if not callable(errors):
        return type(e).__name__
    found = errors()
    if not found or not isinstance(found[0], Mapping) or "type" not in found[0]:
        return type(e).__name__
    return f"{found[0]['type']} at {found[0].get('loc', ())}"


@dataclass
class AdmitsResult:
    """What the class did with the values its DOCUMENT admits and the DRAW cannot produce.

    Reading 1's first check over :func:`admitted_witnesses`, reported as its own result
    rather than merged into :class:`AcceptsResult`, for the reason :data:`CHECKS` gives for
    appending a column: ``accepts`` has always meant "the instance this run drew", its
    census is read across runs, and folding a second witness class into it would renumber
    that census while saying nothing new about the instances it ranges over.
    """

    #: ``(the witness as JSON, its kind, how it was derived, the class's own CAUSE, the
    #: class's message)``, one row per witness the class REFUSED.  Capped by ``keep``;
    #: :attr:`refused` is the count.
    #:
    #: **The CAUSE is its own field and is pydantic's own error ``type``**, which is what
    #: makes the table self-categorising: a reader asking "how many of these are the URL
    #: length cap and how many the datetime parser" greps ``url_too_long`` in the note
    #: instead of re-deriving the whole census, and the note field is truncated to 400
    #: characters so a cause read out of the MESSAGE is a cause that disappears behind a
    #: 4,096-character witness.  Measured: on the first table written with this column, 345
    #: of 444 rows had their error type cut off.
    rows: tuple[tuple[str, str, str, str, str], ...] = ()
    #: Every distinct cause this pair's refusals carry, sorted -- the pair's own category,
    #: read off pydantic and never off a sentence.
    causes: tuple[str, ...] = ()
    #: How many witnesses the class refused, which is ``len(rows)`` until the cap bites.
    refused: int = 0
    #: How many witnesses the DOCUMENT admitted and the class was therefore asked about.
    #: Zero with ``no_witness``: every candidate the derivation made, the document refused.
    offered: int = 0
    #: Whether the instance carried more string leaves than :data:`WITNESS_LEAVES`, so a
    #: ``pass`` here is a pass over the leaves reached and not over the whole instance.
    capped: bool = False
    #: pass | model_refused_admitted | no_witness | unrun
    outcome: str = "unrun"
    detail: str = ""


def check_admits(
    schema: dict,
    accept: Callable[[Any], Any],
    instance: Any,
    *,
    validator_cls: Any = None,
    keep: int = 3,
    length: int = WITNESS_LENGTH,
    leaves: int = WITNESS_LEAVES,
) -> AdmitsResult:
    """Reading 1 check 1, over a witness the DOCUMENT states and the DRAW cannot reach.

    ``docs/plan/final-state.md`` reading 1: "every class accepts every value its document
    admits".  :func:`check_accepts` puts that to the instances a run DREW, and
    :func:`admitted_witnesses` says why that is not the reading at a formatted position --
    the generator honours the format, so every drawn instance lands inside the narrow type
    and the check passes without the document's own wider value ever being offered.

    **``accept`` and not the constructor, which is the opposite of
    :func:`check_refuses`' rule and for the same reason.**  That check must bypass the
    schema half, because a value the DOCUMENT refuses offered to ``strict_validate``
    measures ``jsonschema``.  Here the value is one the document ADMITS -- screened, by the
    document, before it is offered -- so the schema half answers "yes" and the constructor
    runs; this is the entry point reading 1 check 1 names, and asking the constructor
    directly would grade a path no consumer takes.

    **THE DUMP IS NOT RUN HERE, and that is a boundary rather than an omission.**  Reading
    1's second check is the round trip, and :func:`check_accepts`'s ``body`` already puts
    every graded instance through it.  A witness carried through the dump as well would
    report ``model_dropped_a_fact`` for a value whose own acceptance is the finding, so one
    cause would arrive wearing two names and the re-grade could not be attributed.  The
    dump over these witnesses is its own reading and is filed as one.

    **EARLY, at ``keep`` refusals, because the verdict needs one.**  A pair narrower than
    its document is narrower at every leaf carrying the same format -- 27 witnesses in one
    document, measured -- and the verdict, the cause and the value are all carried by the
    first few.  The cap is on the ROWS and not on the derivation, so ``offered`` still
    counts every witness the document admitted up to that point.

    ``no_witness`` where the document admitted none of the candidates, which is a fact
    about the DOCUMENT (no string leaf, or every perturbation of every leaf refused) and
    reads ``absent`` in the table rather than ``pass``.  ``unrun`` where the accepts check
    produced no instance to perturb, which is a fact about the DRAW.
    """
    res = AdmitsResult()
    cls = validator_cls or validator_for(schema)
    res.capped = sum(1 for _ in itertools.islice(_string_leaves(instance), leaves + 1)) > leaves
    rows: list[tuple[str, str, str, str, str]] = []
    causes: list[str] = []
    for witness, kind, how in admitted_witnesses(
        schema, instance, validator_cls=cls, length=length, leaves=leaves
    ):
        res.offered += 1
        try:
            accept(witness)
        except Exception as e:  # noqa: BLE001 -- any refusal is the finding
            res.refused += 1
            #: **The CAUSE is pydantic's own error ``type`` and never a substring of the
            #: message**, which is :func:`violated_keywords`' rule in the other direction:
            #: the keyword a reader categorises by is the one the engine NAMES, and a
            #: category read out of prose moves when the prose does.  ``check_accepts``
            #: reads the same field for ``model_refused_valid``.  A non-``ValidationError``
            #: carries its class name, which is the honest answer for a class that raised
            #: something a consumer cannot catch.
            cause = _refusal_cause(e)
            if cause not in causes:
                causes.append(cause)
            if len(rows) < keep:
                rows.append((_dump(witness), kind, how, cause, f"{e}"[:200]))
            if len(rows) >= keep:
                break
    res.rows = tuple(rows)
    res.causes = tuple(sorted(causes))
    if not res.offered:
        res.outcome = "no_witness"
        res.detail = (
            "the document admits none of the candidates this derivation makes from the "
            "accepted instance, so the class was never asked"
        )
        return res
    if res.refused:
        res.outcome = "model_refused_admitted"
        res.detail = (
            f"the class is NARROWER than its document: it refused {res.refused} of "
            f"{res.offered} values the document admits, on {', '.join(res.causes)}"
        )
        return res
    res.outcome = "pass"
    return res


def _constructor(model: Any) -> Callable[[Any], Any]:
    """``model``'s CONSTRUCTOR, for a class and for D2's root-scalar ALIAS alike.

    :func:`check_refuses` takes "the constructor and not the entry point", and its whole
    distinction from :func:`check_liveness` is that the value reaches pydantic with the
    document taking no part -- so what this returns must be ``model_validate`` and never
    ``pair.accept``.

    **Two spellings because D2 emits two kinds of pair.**  A class carries
    ``model_validate``; a root scalar is an ``Annotated`` ALIAS and not a class, so there
    is no method to call and ``TypeAdapter`` is the constructor for it -- the same reading
    ``_wire_dump`` already makes one direction out, and the same one
    ``tests/test_refuses_check.py`` makes over its own population.

    The adapter is built here and not cached: one pair builds one, ``check_refuses`` is a
    reduction and not a draw, and a cache keyed on a type that pydantic rebuilds would be
    a second answer to "what is this model" for the sake of microseconds.
    """
    validate = getattr(model, "model_validate", None)
    if callable(validate):
        return validate
    return TypeAdapter(model).validate_python


@dataclass
class RefusesResult:
    """What the refuses-check found about one pair: the witnesses and the disagreements."""

    #: ``(the candidate as JSON, the keyword aimed at, the keywords the document refused
    #: on, whether the CONSTRUCTOR admitted it)``, one row per witness offered.
    rows: tuple[tuple[str, str, tuple[str, ...], bool], ...] = ()
    #: The rows the constructor ADMITTED -- the model wider than its document -- and for
    #: which the module declares nothing.  Section 2 permits the first and not the second.
    undeclared: tuple[tuple[str, str, tuple[str, ...], bool], ...] = ()
    #: The keywords the module DECLARES an approximation for at or under this pointer.
    declared: tuple[str, ...] = ()
    #: The conditionals of this node no value was offered for, with the reason each
    #: (:func:`unreached_conditionals`).  **Non-empty beside a ``pass`` makes the pass a
    #: PARTIAL one**, which is what the verdict reads: the class refused every witness it
    #: was offered, and a boundary the document states was not among them.
    unreached: tuple[str, ...] = ()
    #: How many ``if``/``then``/``else`` TRIPLES this node states, conjuncts included
    #: (:func:`conditionals`).  The denominator :attr:`unreached` is a count against, so a
    #: reader of "2 unreached" knows whether that is two of two or two of nine.
    conditional_sites: int = 0
    #: pass | widened_undeclared | model_error | no_witness
    outcome: str = "unrun"
    detail: str = ""


def check_refuses(
    schema: dict,
    construct: Callable[[Any], Any],
    instance: Any,
    *,
    declared: Collection[str] = (),
    validator_cls: Any = None,
) -> RefusesResult:
    """**The other half of section 8's method**: every value the document REFUSES, offered
    to the class, which must refuse it or carry a declaration saying it does not.

    Section 8 states the obligation as "the class admits every value its document admits
    and refuses every value it refuses", and ``docs/plan/final-state.md`` reading 1 is the
    same sentence about the artifact.  :func:`check_accepts` is the first half; this is the
    second, over the witnesses :func:`refused_witnesses` derives from the node's own
    keywords.  ``adcp-client-python-6oe`` is what its absence cost: a class admitting ``{}``
    where its document refuses it, undeclared, which a cell proof found in 1.4 s and no
    pair-scoped site had ever reported.

    **AND ONE FORM OF THIS CHECK WAS BUILT, MEASURED WORTHLESS AND DELETED.  THIS IS NOT
    THAT FORM, AND THE DIFFERENCE IS THE WHOLE DESIGN.**  This module's own docstring
    records the refutation: the deleted check "mutated ONE KEYWORD at a time, drew an
    instance the mutated schema accepts, and passed it to the caller's ``accept`` -- which
    validates against THE DOCUMENT before constructing.  So a step site asserted that
    ``jsonschema`` rejects a payload violating the schema it was handed, and the generated
    class took no part in the outcome: on ``core/pagination-request.json`` a model with
    ``Any`` on every field accepted, refused 75 of 75 instances and recorded no wrong
    acceptance, exactly as a faithful one did."  27,791 such sites were the suite's entire
    wall clock, spent on a property of a third-party validator.

    Three things keep this out of that trap, and each is GATED in
    ``tests/test_refuses_check.py`` rather than asserted here:

    * **the value is offered to the CLASS and to nothing else.**  ``construct`` is
      ``model_validate``, never ``pair.accept`` -- see the paragraph below, which is the
      one rule this signature exists to enforce;
    * **the refutation is the gate.**
      ``test_a_model_with_any_on_every_field_fails_this_check`` runs the discarded
      instrument's own counterexample against this one, and a model with ``Any`` on every
      field must FAIL.  A green there means this has been rebuilt as the thing that
      measured ``jsonschema``;
    * **nothing is drawn and nothing is MUTATED.**  The witness comes off the unmodified
      document and is screened by ``conforms(schema, candidate) is False``, so the document
      refuses it as written rather than as a mutation left it.

    **``construct`` IS THE CONSTRUCTOR AND NOT THE ENTRY POINT, and that is the whole
    distinction from :func:`check_liveness` and the whole distinction from the deleted
    check above.**  That function offers ONE refused payload to
    ``pair.accept``, whose schema half answers first, and its own docstring is emphatic
    that the result "is a LIVENESS check on the wiring and it is not a measurement of the
    class" -- an acceptance there means the schema half is missing.  This function asks the
    other question, the one reading 1 is actually about: ``model_validate`` builds this
    payload, so what does a consumer who constructs rather than validates get?  D4 says
    the constructor MAY be looser; reading 2 says every place it is must be declared at
    its own pointer.  So an admission here is not a verdict on its own -- it is one exactly
    where the module declares nothing.

    ``declared`` is the keywords the module declares an approximation for at or under this
    pointer (``harness.declarations_of`` read through ``render.declared_at``'s containment
    rule).  A candidate the constructor admits is ``pass`` where a declaration names its
    keyword and ``widened_undeclared`` where none does -- which is section 2's rule read as
    a check rather than as prose, and is what keeps the declared set from being an
    allowlist in this direction too.

    ``no_witness`` is a real answer and not a failure: a document that refuses nothing this
    reduction can build -- an open typeless object, which draft-07 admits every instance of
    -- has nothing for the class to refuse, and the pair is neither graded nor failed.
    """
    res = RefusesResult(declared=tuple(sorted(set(declared))))
    cls = validator_cls or validator_for(schema)
    #: **THE REACH, RECORDED BEFORE THE VERDICT**, because the two are different facts and
    #: a reader of a ``pass`` needs both: the witnesses say what the class was asked, and
    #: this says which of the node's own boundaries it was NOT asked about.  Computed even
    #: where there is no witness at all, so ``no_witness`` beside a node that states three
    #: conditionals reads as the unreached boundaries it is rather than as an empty node.
    res.conditional_sites = len(conditionals(schema))
    res.unreached = unreached_conditionals(schema, instance, validator_cls=cls)
    witnesses = refused_witnesses(schema, instance, validator_cls=cls)
    if not witnesses:
        res.outcome = "no_witness"
        return res
    rows: list[tuple[str, str, tuple[str, ...], bool]] = []
    for candidate, keyword, _how in witnesses:
        try:
            construct(candidate)
            admitted = True
        except ValidationError:
            admitted = False
        except Exception as error:  # not a refusal a consumer could catch
            res.outcome = "model_error"
            res.detail = f"{type(error).__name__}: {error}"[:300]
            return res
        rows.append(
            (
                json.dumps(candidate, sort_keys=True, default=str),
                keyword,
                tuple(violated_keywords(schema, candidate, validator_cls=cls)),
                admitted,
            )
        )
    res.rows = tuple(rows)
    res.undeclared = tuple(
        row for row in rows if row[3] and row[1] not in res.declared
    )
    res.outcome = "widened_undeclared" if res.undeclared else "pass"
    return res


def refusing_payload(
    schema: dict, instance: Any, *, validator_cls: Any = None
) -> tuple[Any, str] | None:
    """One payload the DOCUMENT refuses, derived from one it ACCEPTS.

    Section 6 asks for one payload the schema refuses per class, routed through the
    entry point once.  It is DERIVED from the accepted instance
    rather than drawn, which is the whole saving: a draw from a mutated document
    costs ``from_schema`` another canonicalisation of the whole document, and the
    27,791 of those is what this rebuild removes.

    Three perturbations, tried in this order, and the order is the point:

    1. **drop a key the root ``required`` names.**  A missing required key is the
       plainest thing a document refuses, so it is the cheapest proof that the
       schema half ran at all.
    2. **replace the whole instance with a value of another JSON type.**  Reaches a
       root that demands no key, and a scalar root, which the first cannot.
    3. **add a property no document declares.**  Last, so it is reached only by a
       root that admits every scalar -- an open object.

    **Every candidate is screened by the DOCUMENT**, which is what keeps this from
    asserting a refusal the document does not make: ``conforms`` has to answer
    ``False`` before a payload is offered to anything.  Where no candidate is
    refused the document admits all three shapes, there is no invalid payload to
    find, and ``None`` says so rather than a perturbation being forced through.
    """
    cls = validator_cls or validator_for(schema)

    def refused(candidate: Any) -> bool:
        return conforms(schema, candidate, validator_cls=cls) is False

    if isinstance(instance, dict):
        for key in schema.get("required", []) if isinstance(schema.get("required"), list) else []:
            if key in instance:
                candidate = {k: v for k, v in instance.items() if k != key}
                if refused(candidate):
                    return candidate, f"drops the required key {key!r}"
    for alien in _ALIEN_VALUES:
        if type(alien) is not type(instance) and refused(alien):
            return alien, f"replaces the instance with {alien!r}"
    if isinstance(instance, dict):
        candidate = {**instance, _ALIEN_KEY: 1}
        if refused(candidate):
            return candidate, f"adds the property {_ALIEN_KEY!r}"
    return None


def check_liveness(
    schema: dict,
    accept: Callable[[Any], Any],
    instance: Any,
    *,
    validator_cls: Any = None,
) -> LivenessResult:
    """Offer one payload the document refuses to the entry point, ONCE per class.

    **This is a LIVENESS check on the wiring and it is not a measurement of the
    class.**  Section 6 is explicit about why, and about why it used to be read the
    other way: pydantic is DELIBERATELY less strict than the schema.  D4 gives the
    schema the acceptance decision and pydantic the construction, so a model holds
    the document's types and emits the document's schema rather than reimplementing
    every JSON Schema keyword -- which is the whole reason ``strict_validate``
    exists.  So a payload the schema refuses says nothing about the generated code
    on EITHER route: ``model_validate`` may accept it by design, and ``accept``
    refuses it because the document answered.

    What one refusal through ``accept`` does prove is that this class's schema half
    is CONNECTED and that the ref it names resolves to the document it names.  That
    is worth asserting once per class, and it is what the 27,791-site sweep was
    already asserting -- 27,791 times, at the cost of the suite's entire wall clock.

    An ACCEPTANCE is therefore ``schema_half_not_connected``: the document refuses
    this payload and the entry point did not, so either the schema half is not
    running or ``__adcp_schema__`` does not resolve to this document.

    **That verdict is a statement about the WIRING and never about pydantic's
    strictness, and the distinction is load-bearing enough to say twice.**  Pass this
    a bare ``model_validate`` and it will report ``schema_half_not_connected`` on a
    perfectly correct class, because a correct class MAY accept a schema-invalid
    payload -- that is D4, and section 6 says so in as many words.  So ``accept`` is
    the entry point the caller ships, the one whose schema half answers first; the
    only thing an acceptance can mean through THAT is that the half is missing.
    ``check_pair`` passes ``pair.accept`` and there is no other production call site.

    **A refusal means pydantic's ``ValidationError`` and nothing else**, and that is
    measured rather than chosen: over 838 graded pairs, 0 refused this payload with
    any other exception, so admitting a foreign exception as a refusal would cost
    nothing today and would hide the one thing it could ever hide -- an entry point
    raising something the caller cannot catch, which is how the specification's own
    probe came to read a pair nothing graded as green.  So a foreign exception is
    ``model_error`` with its type in ``detail``, which is a verdict and not a pass.
    """
    res = LivenessResult()
    cls = validator_cls or validator_for(schema)
    found = refusing_payload(schema, instance, validator_cls=cls)
    if found is None:
        res.outcome = "no_payload"
        return res
    payload, how = found
    res.how = how
    res.violated = tuple(violated_keywords(schema, payload, validator_cls=cls))
    try:
        accept(payload)
    except ValidationError:
        res.outcome = "pass"
    except Exception as e:  # not a refusal this caller could catch
        res.outcome = "model_error"
        res.detail = f"{type(e).__name__}: {e}"[:300]
    else:
        res.outcome = "schema_half_not_connected"
    return res


def check_accepts(
    schema: dict,
    accept: Callable[[Any], Any],
    *,
    examples: int = 25,
    custom_formats: Mapping[str, Any] = (),
    dump: Callable[[Any], Any] | None = None,
    seen: list[Any] | None = None,
    ref: SchemaRef | None = None,
    corpus: Any = None,
    identity: Any = None,
    draw_from: dict | Callable[[], dict | None] | None = None,
) -> AcceptsResult:
    """The accepts check: every instance the schema admits, ``accept`` admits --
    and what it constructed, DUMPED back out, is an instance the schema admits too.

    This is where a model NARROWER than its document fails, and the annotations
    are load-bearing here even behind a schema check: the schema half passes an
    instance it admits, and then the constructor runs on it.  A ``maxLength``
    the annotation invented, or a required field the model does not declare, is
    refused at construction and reported.

    **The dump is the half that reads what the class DID with the value**, and the
    accepts check alone cannot: a class that takes an instance and loses a key, or
    renames one, or coerces it to a shape the document refuses, accepts every
    instance there is.  So the constructed value goes back out through ``dump`` and
    the DOCUMENT decides again, which costs one validation and no draw.  ``dump``
    defaults to the pydantic reading of "what this value looks like on the wire" --
    ``mode="json"``, by alias, and only the fields the payload actually set, because
    a field the instance never carried is not a fact the document stated about it.

    A pair whose ``dump`` raises is a ``model_error`` like any other construction
    failure; a dump the document refuses is ``model_dropped_a_fact``, named for what
    it is rather than for the check that caught it.

    **``ref`` names the node, and it buys exactly one thing: the dump is validated
    against the document with ``codegen.dump_exemptions``' struck keywords removed.**
    Four positions state a keyword no correct class can satisfy -- a ``pattern`` that
    forbids what RFC 3986 normalization produces, and a ``minProperties`` over keys
    D8 drops -- and D5 and D8 both stay as written, so the positions are exempt and
    the defect is upstream (``adcontextprotocol/adcp#8398``).

    **THE STRIKE TOUCHES THIS VALIDATION AND NOTHING ELSE, and that is what keeps it
    from being a relaxation of the accepts half.** The instance is DRAWN from
    ``schema`` and the constructor still runs on it, so a model narrower than its
    document still fails here exactly as before; a keyword struck for the dump is
    still in force for every instance going IN. Without a ``ref`` nothing is struck,
    which loses an exemption and cannot invent one.

    **``Phase.shrink`` is NOT in the phase list, and that is a measured decision
    rather than an omission.**  Hypothesis caps a shrink at its own
    ``MAX_SHRINKING_SECONDS``, 300 s, so each FAILING pair could cost five minutes
    of a worker's wall clock -- measured here: one failing pair held a core at 99%
    for over ten minutes across two of its checks, against 0.1-0.4 s for a passing
    one.  What a shrink buys is a smaller counterexample, and at the default
    ``examples=1`` there is exactly ONE generated instance, so shrinking it cannot
    reach a different failure -- it can only simplify the one already reported in
    ``counterexample``.  ``Phase.target`` is out with it because no call site
    supplies a ``target()``, so it had nothing to steer.

    **``corpus`` makes the draw DELTA-BASED, and it is the caller's OBJECT and not a path.**
    ``from_schema`` is the overwhelming majority of this check's cost over the graded
    population and the suite regenerates the same instances every run from inputs every one
    of which is in git, so the instances are held content-addressed by :func:`corpus_key`
    and replayed.  The object is anything with ``get(key)`` answering a held list or
    ``None`` and ``put(key, instances)`` holding one; **this module computes the key and
    reads no path, no filesystem and nothing of the vocabulary it is pointed at**, which is
    ``docs/plan/architecture.md`` §9's import rule and the reason this harness can grade
    output that does not exist yet.  Where the store lives is the caller's business, and
    ``tests/corpus.py`` is one answer.

    Three branches, and each is reported rather than silent:

    * **a hit** -- the instances are re-offered to the DOCUMENT
      (:func:`corpus_defect`) and then run through the SAME ``body`` a draw runs through,
      so ``accept``, ``dump``, the exemption reading and every counter are the ones a
      drawing run produced.  The instance reaching the class is the identical instance;
      only ``from_schema`` is skipped.  :attr:`AcceptsResult.replayed` says so.
    * **a held entry that cannot stand in** -- ``corpus_rejected``, with ZERO instances
      graded, so :attr:`PairReport.outcome` reddens the pair twice over.  Never a silent
      re-draw: a store answering with the wrong count, or with an instance the document
      refuses, is broken, and a fallback would hide it for as long as it kept happening.
    * **a miss** -- the draw runs exactly as it always did and the instances are offered
      to the store afterwards, and only where the draw produced the whole obligation, so a
      short or errored draw is never held.  A miss therefore COSTS and cannot pass:
      adding a document adds one key, changing one changes that key and every dependent's
      with it (``identity`` carries the closure, so their identities moved too), and an
      absent corpus is one full cold run.

    **``draw_from`` IS WHERE THE INSTANCES COME FROM; ``schema`` STAYS WHAT DECIDES.**
    A CALLABLE is forced only on a corpus MISS, which is the only branch that draws; §8's
    substitution costs a derivation per instance location and a replayed pair must not pay
    for a draw it does not make.
    §8's fixture rule substitutes an instance of a referenced document at the referring
    position (:class:`Fixtures`), and that is a statement about the DRAW: the fixtured node
    is a RESTRICTION of this one, so every instance it yields is an instance ``schema``
    admits, and ``schema`` is still what the dump is validated against and what
    :func:`corpus_defect` re-offers a held instance to.  Validating the dump against the
    restriction instead would report ``model_dropped_a_fact`` wherever the class returned
    a value the referenced document admits and the one pinned fixture is not -- a defect
    manufactured by the instrument.  ``None`` means "draw from ``schema``", which is what
    every caller did before the rule and what a caller with no fixtures still does.

    **``identity`` is REQUIRED with a ``corpus`` and there is no fallback, because the
    fallback was the defect.**  :func:`corpus_key` says why ``schema`` cannot stand in for
    it: the schema here is ``bundle.record``'s rendering of a document, so keying on it
    redrew the bundle whenever the inliner moved and no document had.  Defaulting to the
    schema would leave that door open for any caller who forgot the argument -- silently,
    and visible only as a cold run nobody ordered -- so a store with no identity beside it
    raises instead.  A caller with no static identity to offer passes ``corpus=None`` and
    draws, which costs time and grades the same thing.
    """
    if corpus is not None and identity is None:
        raise ValueError(
            "a corpus needs the draw's STATIC identity: the schema handed here is "
            "bundle.record's rendering of a document, so keying on it misses every "
            "entry whenever the inliner moves.  Pass identity= (see "
            "catalogue.admitted_identities) or corpus=None."
        )
    res = AcceptsResult()
    cf = dict(custom_formats)
    #: The instances this check drew, in order, HANDED BACK to the caller when it
    #: supplies a list.  ``check_pair`` reads the first one and derives the refused
    #: payload from it, which is what keeps the liveness check from costing a second
    #: draw -- the one saving in this module that is a reuse rather than a deletion.
    seen = [] if seen is None else seen
    validator_cls = validator_for(schema)
    #: The schema the DUMP answers to: the node with the exempt keywords struck, or
    #: the node itself.  Computed once per call rather than per instance, and by
    #: IDENTITY when nothing is exempt, so the pairs with no entry are untouched.
    dump_schema = (
        schema if ref is None else dump_exemptions.struck(schema, ref.document, ref.pointer)
    )
    dump_validator_cls = validator_cls if dump_schema is schema else validator_for(dump_schema)

    def body(instance: Any) -> None:
        res.examples += 1
        seen.append(instance)
        built = accept(instance)
        back = dump(built) if dump is not None else _wire_dump(built)
        if dump_schema is not schema and conforms(schema, back, validator_cls=validator_cls) is (
            False
        ):
            # The strike MATTERED for this instance: the unstruck node refuses this
            # dump and the struck one is about to be asked.  Recorded here rather than
            # once per call, so the field says what this pair needed and not what lies
            # inside it -- see ``AcceptsResult.dump_exempt``.
            assert ref is not None  # dump_schema differs only when a ref was supplied
            res.dump_exempt = dump_exemptions.labels(ref.document, ref.pointer)
        if conforms(dump_schema, back, validator_cls=dump_validator_cls) is False:
            # The CAUSE goes first, because ``detail`` is truncated and a reason at
            # the end of a megabyte of dumped instance is a reason nothing can read.
            broke = violated_keywords(dump_schema, back, validator_cls=dump_validator_cls)
            raise _DumpRefused(
                f"the document refuses the dump on {', '.join(broke)}"
                f"; dumped {_dump(back)} from {_dump(instance)}"
            )
        res.round_tripped += 1

    #: The held instances, or ``None`` for a miss and for a caller that supplied no store.
    #: Both answer "draw", and they are not the same thing to a reader: a miss is a key
    #: this corpus has never been asked for, which is what a new or changed record
    #: produces.
    held = None
    if corpus is not None:
        res.corpus_key = corpus_key(identity, custom_formats=cf)
        held = corpus.get(res.corpus_key)
    if held is not None:
        defect = corpus_defect(schema, held, examples, validator_cls=validator_cls)
        if defect:
            res.outcome = "corpus_rejected"
            res.detail = f"{defect} (key {res.corpus_key[:16]})"[:400]
            return res
    #: **An entry SHORT of the obligation is a miss and not a hit**, which is the other
    #: half of taking the count out of the key (:func:`corpus_defect`).  The entry is not
    #: wrong -- its instances are this document's and are checked above -- it simply does
    #: not reach this far, so the draw runs and the write below replaces it with the longer
    #: list.  Paid once: the new entry answers every count at or below it for ever.
    if isinstance(held, list) and len(held) < examples:
        held = None

    #: **THE STORE, THEN THE DOCUMENT'S OWN ``examples``, THEN THE DRAW** (the owner's
    #: decision, 2026-11-04).  ``examples`` is JSON Schema's own keyword for "here is a
    #: valid instance of this schema", so where the node states one there is nothing to
    #: generate: the schema author has already answered the question this check asks.  It
    #: is better evidence as well as cheaper -- a realistic payload rather than a
    #: generated one -- and it is maintained with the schema by the people who own it,
    #: which is why it is not the hand-written fixture §8 forbids.
    #:
    #: **AFTER the store and not before it**, which is :class:`Layered`'s own reading one
    #: key space over: which source answers decides WHICH witness the suite grades, and
    #: the committed floor is the witness every lane and every fresh checkout agrees on.
    #: A node whose ``examples`` changed upstream would otherwise silently re-point every
    #: verdict that depends on it; this way the floor keeps deciding and ``examples``
    #: answers exactly the pairs the floor does not.
    #:
    #: **SCREENED BY THE NODE, and the screen is load-bearing**: 64 of the 115 pairs whose
    #: node carries ``examples`` have none the node admits, because the bundle's root
    #: ``examples`` hold a ``{"description", "data"}`` wrapper rather than an instance.
    #: :func:`stated_instances` carries that measurement and says why the wrapper is not
    #: unwrapped.
    stated = None
    if held is None:
        found = stated_instances(schema, validator_cls=validator_cls)
        if len(found) >= examples:
            stated = found

    try:
        if held is None and stated is not None:
            #: Through the SAME ``body`` a draw and a replay run through, so ``accept``,
            #: the dump, the exemption reading and every counter are the ones a drawing
            #: run produced; only ``from_schema`` is skipped.  :attr:`AcceptsResult.stated`
            #: is what tells a reader which of the three answered.
            for instance in stated[:examples]:
                res.stated += 1
                body(instance)
        elif held is None:
            with (
                canonicalisation_shared_within_one_call(),
                validator_classes_shared_within_one_call(),
                #: **§8's residue clause, and it has to be live during the DRAW and not
                #: only during the build**: the library reaches ``merged_as_strategies``
                #: from inside an ``@st.composite`` object draw as well as from its
                #: ``allOf`` arm, so a patch that ended with the strategy object would miss
                #: the nested call.  :func:`a_combinator_is_covered_and_never_enumerated`
                #: carries the rule, the stacks and the measurement.
                a_combinator_is_covered_and_never_enumerated(),
            ):
                #: **A CALLABLE IS CALLED HERE AND NOWHERE ELSE, which is what keeps
                #: §8's substitution off the replayed path.**  The substitution derives
                #: a value per instance location of the node (:meth:`Fixtures.reduced`),
                #: and the 2,674 pairs the committed floor answers would each pay that
                #: derivation for a draw that never happens -- so the caller hands a
                #: thunk and it is forced on the MISS, which is the only branch that
                #: draws.  A mapping still means what it meant.
                drawing = draw_from() if callable(draw_from) else draw_from
                #: **THE DOCUMENT SCREENS EVERY INSTANCE A SUBSTITUTION PRODUCED, which is
                #: what makes §8's substitution a statement about GENERATION and nothing
                #: else.**  The owner's measurement is the whole argument: on
                #: ``media-buy/refine-proposals-response.json#/properties/results/items/oneOf/0``,
                #: validating a payload against the 683,849-byte node costs 1 ms and
                #: generating one does not terminate -- so the cost is in generation,
                #: never in the check, and a screen on the way out costs nothing and
                #: removes every soundness question the substitution could raise.
                #:
                #: With it, a pair cannot be graded on a value its own node refuses
                #: whatever the substitution did: ``oneOf`` is not monotone branch by
                #: branch, a ``properties`` pin can meet another statement about the same
                #: key through a keyword the frontier guards did not foresee, and neither
                #: can now reach a verdict.
                #:
                #: ``schema`` and not ``dump_schema``: the exemptions are the DUMP's and
                #: an instance going IN is decided by the node as the document writes it.
                drawn_from_schema = drawing is None or drawing is schema

                def drawn(node: Any, *, substituted: bool) -> None:
                    payloads = strategy(node, cf)
                    if substituted:
                        payloads = payloads.filter(
                            lambda value: conforms(schema, value, validator_cls=validator_cls)
                            is True
                        )
                    run = given(instance=payloads)(body)
                    run = settings(
                        max_examples=examples,
                        phases=[Phase.explicit, Phase.generate],
                        **_SETTINGS,
                    )(run)
                    run()

                if drawn_from_schema:
                    drawn(schema, substituted=False)
                else:
                    #: **A SUBSTITUTION THAT ADMITS NOTHING IS ABANDONED, AND THE
                    #: ABANDONMENT IS REPORTED.**  §8: *"AND A REDUCTION THAT YIELDS AN
                    #: EMPTY NODE IS A DEFECT, NEVER A LOST SAVING. ... A reduction reports
                    #: emptiness as a failure, loudly, and a pair whose reduction came back
                    #: empty is a defect report and not a slow pair."*
                    #:
                    #: **AND THE SCREEN IS OVER THE WHOLE NODE, which is the half neither
                    #: fail-safe above can reach.**  :meth:`Fixtures._pin`'s fail-safe is
                    #: per-LOCATION -- "an item no value survives for is left exactly as it
                    #: stands" -- and :meth:`Fixtures.substitute` has none at all, so both
                    #: pin instance locations INDEPENDENTLY and a document whose ``anyOf``
                    #: or ``if`` RELATES two locations has no such independent value.  §8
                    #: states the consequence one line earlier: *"two pins on one location
                    #: do not narrow the node -- they empty it."*
                    #:
                    #: **MEASURED, and it is a wrong verdict rather than a slow draw.**
                    #: ``core/postal-country-system.json`` states a cross-field ``anyOf``
                    #: pairing a ``country`` with the postal systems that country admits.
                    #: Where ``country`` is inline only ``system`` is pinned and the
                    #: generator draws a country that agrees with it; where ``country`` is
                    #: a ``$ref``, both are pinned independently -- ``country="AA"`` with
                    #: ``system="cep"`` -- and no branch of the ``anyOf`` admits that pair.
                    #: The ``.filter()`` above then turns the empty node into
                    #: ``Unsatisfiable: 459 of 459 test cases failed a .filter()``, which
                    #: this check used to report as ``strategy_error``: a RED PAIR
                    #: manufactured by the instrument, over a node whose own draw passes.
                    #: Five pairs of the patched bundle and 33 more the committed floor was
                    #: masking (``adcp-client-python-lzzj.1``).
                    #:
                    #: **The retry is the UNREDUCED draw and nothing cleverer**, because
                    #: that is the fail-safe direction this module already takes everywhere
                    #: else: lose the saving, never place a value the document does not
                    #: admit.  It costs what the pair cost before the rule existed -- 0.0
                    #: to 0.2 s for four of those five, measured -- and a pair that cannot
                    #: draw unreduced either is then reported on its own node, which is the
                    #: verdict it is entitled to.
                    #:
                    #: **The counters are wound back with it**, so a partial substituted
                    #: draw cannot leave instances in ``seen`` that the retry then counts
                    #: twice, and ``dump_exempt`` cannot report an exemption the graded draw
                    #: never needed.
                    standing = (len(seen), res.examples, res.round_tripped, list(res.dump_exempt))
                    try:
                        drawn(drawing, substituted=True)
                    except (
                        HypothesisRefResolutionError,
                        HypothesisException,
                        RecursionError,
                    ) as e:
                        #: The CLOCK first, for the reason the handler below reads it: a
                        #: cut arrives wearing hypothesis's own exception, and retrying a
                        #: draw the budget has already stopped would charge this pair the
                        #: whole budget twice.
                        if budget_expired():
                            raise
                        res.abandoned = _why(e)
                        del seen[standing[0]:]
                        res.examples, res.round_tripped = standing[1], standing[2]
                        res.dump_exempt = standing[3]
                        drawn(schema, substituted=False)
        else:
            #: The FIRST ``examples`` of the held list and not all of it, which is the n <=
            #: N reading :func:`corpus_key` argues for: the instances are offered in order,
            #: so these are the ones a draw of ``examples`` would have produced, and
            #: :func:`corpus_defect` has already re-offered exactly these to the document.
            for instance in held[:examples]:
                res.replayed += 1
                body(instance)
        res.outcome = "pass"
    except _DumpRefused as e:
        res.outcome = "model_dropped_a_fact"
        res.detail = str(e)[:400]
        res.counterexample = _dump(seen[-1]) if seen else ""
    except ValidationError as e:
        err = e.errors()[0]
        res.outcome = "model_refused_valid"
        res.detail = f"{err['type']} at {err['loc']}: {err['msg']}"
        res.counterexample = _dump(seen[-1]) if seen else ""
    except (HypothesisRefResolutionError, HypothesisException, RecursionError) as e:
        #: The CLOCK first, because ``hypothesis`` swallows the cut and raises its own
        #: ``FlakyStrategyDefinition`` in its place; :func:`budget_expired` measures it.
        if budget_expired():
            raise OverBudget(f"the grade was cut and {type(e).__name__} arrived after") from e
        res.outcome = "strategy_error"
        #: ``_why`` and not the raw message: hypothesis's advice to whoever wrote the
        #: test was pushing the filtered-draw count past the truncation, and the cut
        #: belongs HERE rather than in the reader -- :attr:`PairReport.no_instrument`
        #: re-split the same sentence for want of this line, which is one rule in two
        #: places and the one that goes stale.
        res.detail = _why(e)
    except Exception as e:  # a model that raises something other than ValidationError
        if budget_expired():
            raise OverBudget(f"the grade was cut and {type(e).__name__} arrived after") from e
        res.outcome = "model_error"
        res.detail = f"{type(e).__name__}: {e}"[:400]
        res.counterexample = _dump(seen[-1]) if seen else ""
    #: Held only where the draw produced the WHOLE obligation, so a draw that errored
    #: part-way leaves no entry and the next run draws again.  **After the handlers and
    #: not inside the ``try``, which is what makes a FAILING pair cheap too**: an instance
    #: that reddens the pair is the one a reader most wants back, and holding it keeps the
    #: counterexample reproducible rather than re-derived.  ``strategy_error`` is excluded
    #: because what it reports is that the generator produced nothing for this schema, and
    #: an entry would then claim a draw happened.
    #:
    #: The count is :attr:`AcceptsResult.examples` and not ``len(seen)``, because ``seen``
    #: is the CALLER's list and a caller may hand one that already holds something: what
    #: this call drew is what ``body`` counted.
    #: **A STATED INSTANCE IS NOT HELD, because it is already committed -- in the
    #: document, in git, in the artifact every lane and CI reads.**  The floor exists so
    #: that "every lane, every fresh checkout and CI grade the same one" (:class:`Layered`),
    #: and an ``examples`` member satisfies that on its own: it moves only when the schema
    #: moves, and when it does, this check re-screens it and reports an upstream defect
    #: with the document's name.  Copying it into a store would make one fact two, give it
    #: a second maintenance point, and let the copy outlive the statement it came from --
    #: which is exactly the drift §8's "never hand-written" clause is about.
    if corpus is not None and held is None and not res.stated and res.outcome != (
        "strategy_error"
    ):
        #: **The whole draw and never a truncation, and NEVER SHORTER THAN WHAT IS ALREADY
        #: HELD.**  With the count out of the key one entry answers every setting, so a run
        #: at a LOW count must not overwrite a long entry with a short one -- that would
        #: make the floor's reach a function of whichever setting ran last, and the next run
        #: at the high count would draw again.  The store is asked what it holds and the
        #: longer list wins; a tie keeps what is held, so a run that adds nothing writes
        #: nothing.
        #:
        #: ``res.examples`` and not ``examples``: a draw SATURATES where the node's
        #: admissible set is smaller than the count -- an eight-member enum yields 8
        #: instances however many are asked for -- and the old equality held no entry at
        #: all for such a node, so every run redrew it.  What the draw produced is what
        #: there is to hold, and :func:`corpus_defect` reports it short only against a
        #: request it cannot cover.
        standing = corpus.get(res.corpus_key)
        drawn = seen[-res.examples:] if res.examples else []
        if drawn and len(drawn) > len(standing or []):
            corpus.put(res.corpus_key, drawn)
    return res


# --------------------------------------------------------------------------- #
# section 8's accepts OBLIGATION: a widening is PROVED, not believed
# --------------------------------------------------------------------------- #
def records_a_cut(entry: Any) -> bool:
    """Whether a held widening answer records a BUDGET CUT rather than a value.

    **The clause the widening store was missing, and the one reading two callers share**
    (``adcp-client-python-pjc``).  :meth:`_Draws.one` asks it before it holds anything, so
    a cut cannot enter the store; ``tests/test_widening_corpus.py`` asks it of every entry
    the floor and the cache already hold, so a cut cannot be promoted into the repository
    by ``--write-corpus`` either.  One predicate and not two, because a store clause and a
    gate that disagreed about what a cut looks like would be a gate that passes the entries
    its own clause declines.

    **Why a declaration backed by a cut is the worst entry this store can hold.**
    ``docs/plan/final-state.md`` reading 2 is that every widening is "proved by a value",
    and :func:`within`'s docstring already says what a budgeted pair is: "a statement about
    the INSTRUMENT".  A cut held here makes the instrument's own statement the evidence --
    :class:`Layered` serves it like any other entry, :func:`check_widening` reports
    ``unproved_widening`` with "a key the patternProperties admits could not be drawn:
    OverBudget: ...", and at the point of use that verdict is indistinguishable from a
    measurement of the document.  Measured on
    ``trusted-match/offer.json#``: with the cut entry in place the pair graded in 8.8 s;
    with it removed the same pair did not finish in 600 s.  The entry was not making the
    grade cheap, it was making an unbounded draw LOOK graded.

    **Read off the REASON and not off a list of keys**, because the subject is an artifact
    on disk and a hash is not readable: a held failure's reason is :func:`_why`'s
    ``f"{type(e).__name__}: ..."``, so the entry carries the name of the exception that
    ended the draw and that name is the whole question.  The needle is
    :class:`OverBudget`'s own ``__name__`` rather than a literal, so a rename moves both
    the clause and the gate; it is sought anywhere in the sentence rather than only at the
    front, which catches a cut a library wrapped on the way out and the one entry in the
    shared cache spelled ``_OverBudget:`` by a lane that had renamed the class.

    A one-element entry is a VALUE whatever the value is (:class:`_Draws` -- a document can
    admit ``null``), so only the two-element failure form can record a cut.
    """
    if not (isinstance(entry, list) and len(entry) == 2 and entry[0] is None):
        return False
    return isinstance(entry[1], str) and OverBudget.__name__ in entry[1]


@dataclass
class _Draws:
    """**WHERE §8's OBLIGATION HOLDS THE INSTANCES IT DRAWS**, and what it paid for them.

    ``check_accepts`` draws ONCE per pair and :func:`corpus_key` holds it;
    :func:`check_widening` draws several times per pair, from schemas it derives out of the
    pair's own node, and held NONE of them.  This is the same relocation
    ``tests/corpus.py`` describes for the accepts draw, applied to the three sites §8's
    obligation draws at -- and it is the relocation and not a second instrument: the key is
    :func:`corpus_key`'s, with the derivation named in its ``position``.

    **MEASURED, AND THE SITE THAT COSTS IS NOT ONLY THE ONE THE ROW WAS FILED ABOUT.**  The
    population is read first, because every number below is about a small part of it: of
    2,793 graded pairs, **87 carry a declaration at all, and 53 carry one this check can
    put to a draw** -- the other 34 declare only UNDERDETERMINED facts, which the loop
    below subtracts before anything is drawn.  So the obligation's whole cost sits on 53
    pairs, and over those pairs it sits on draws, not on grading:

    ===================================================  ==========  ==============
    ``check_widening`` on one pair, nothing held           node MB         seconds
    ===================================================  ==========  ==============
    ``compliance/comply-test-controller-request.json#``          8.2  >900, cut off
    ``core/async-response-data.json#/anyOf/34``                 6.9  >600, cut off
    ``core/async-response-data.json#/anyOf/27``                14.1  >600, cut off
    ``core/async-response-data.json#/anyOf/28``                 4.7           246.7
    ``core/creative-representation.json#``                      4.6            11.9
    ===================================================  ==========  ==============

    Over the 52 of those 53 pairs one pass completed, **1,606 s of widening wall clock of
    which 1,605 s is inside the draw** -- 108 draws, with one pair cut off at 600 s and
    nothing graded costing more than a second.  Where the time goes:

    * ``_reached``, 1,441 s of it over 17 draws, worst 600 s on a 6,832,209-byte node.
    * the value class, 164 s over 71 draws of multi-megabyte RESTRICTIONS of a node.
    * ``_bases``' demand, which the completed pass reached for 24 declarations over 14
      pairs and which is the one site a deadline could not time: ``>900 s`` on an
      8,145,255-byte conjunction, twice, on two pairs of one document.
    * :func:`_mapping_key`, 0.16 s over 20 draws of 50-byte key schemas.  Not held: the
      store's own file read costs more than the draw.

    **WHICH SITE A PAIR PAYS IS DECIDED BY ITS ACCEPTS INSTANCE**, which is why holding one
    and not the other would have moved the pole rather than removed it.  A pair whose
    accepts draw produced an instance has a base to place into, so ``_reached`` fills the
    gaps in it and ``_bases``' last candidate is never asked for -- that is both
    ``async-response-data`` pairs above, each with its accepts draw already replayed from
    the committed floor.  A pair whose accepts draw produced NOTHING hands ``_reached`` a
    ``None`` it returns unchanged, every borrowed candidate fails, and ``_bases`` draws the
    demand -- over the node CONJOINED with it, which is strictly larger than the document.
    That is both ``comply-test-controller-request`` pairs.

    **AND A STORE DOES NOT REACH EVERY POSITION, which is stated because the reading says
    so.**  A draw that never returns is never held, so the positions above that no deadline
    could time are positions a store cannot answer for until something draws them once.
    What a store removes is the repetition -- the same position paid again per value class,
    per pair of a document, and per run -- which is the whole of what was measured twice
    over on one node.  Whether the whole-node draw should be replaced by a construction
    from the document is a separate question and a separate decision.

    **THE KEY IS THE PAIR'S IDENTITY AND THE POSITION, and never the derived schema.**
    :func:`corpus_key` carries the argument -- the schema these draws are handed is
    ``bundle.record``'s rendering conjoined, restricted or walked by this module, so an
    address taken from it moves whenever the compiler does.  Each position is a reading of
    the DECLARED POINTER instead, which the bundle fixes.

    **AND NOTHING HERE DECIDES WHETHER A HELD VALUE MAY BE USED**, which is why this needs
    no ``corpus_defect`` of its own: every candidate base this holds is placed, and
    :func:`check_widening` then offers the placed payload TO THE DOCUMENT before the entry
    point is shown anything (``conforms(schema, attempt)``).  A stale base makes that
    refuse, the declaration is reported ``unproved`` or refused, and the pair reddens -- the
    same derived equality ``corpus_defect`` performs for the accepts draw, already in the
    code that consumes these values.  There is deliberately no fall-through to a fresh draw
    on a held base the document refuses: that is the silent repair ``corpus.Layered``'s
    docstring refuses for the same reason.

    **A FAILED DRAW IS HELD TOO, with its reason beside it.**  An undrawable position is
    reported ``unproved``, and the ``Unsatisfiable`` that says so is itself expensive -- it
    is the whole generation budget spent on filtered cases.  So :meth:`one` answers
    ``[value]`` or ``[None, reason]``: the two states :func:`_bases`' ``memo`` already had,
    plus the sentence, because a replayed run that reported a thinner reason than a drawn
    one would make the store visible in the verdict.  Only an ``Exception`` is held -- a
    ``MemoryError`` or an interrupt is a fact about the machine and not about the position.

    **THE TWO STATES ARE TOLD APART BY LENGTH AND NEVER BY THE VALUE**, which fixes
    something the one-slot memo had wrong: a document can admit ``null``, so ``[None]``
    meant both "the draw produced JSON null" and "the draw failed".  One element is an
    answer whatever it is; two is a failure carrying its reason.

    **A STALE HELD FAILURE REDDENS, which is the direction that is safe.**  An entry saying
    "this position cannot be drawn" keeps the declaration ``unproved``, and ``unproved`` is
    as much a failure as a narrowing (:class:`WideningResult`) -- so the worst a held
    failure can do is report work owed, never a pass nobody earned.  A generator bump moves
    the key (``_DRAW_VERSION``) and the position is redrawn.

    **AND A DRAW THAT WAS CUT IS NOT A FAILED DRAW, which is the clause the accepts store
    has had all along and this one did not** (``adcp-client-python-pjc``).
    ``check_accepts`` declines to hold a ``strategy_error`` "because what it reports is
    that the generator produced nothing for this schema, and an entry would then claim a
    draw happened".  A budget cut reports strictly less than that -- it reports that THIS
    PROCESS stopped asking -- and the paragraph above is exactly what let one in: a cut
    arrived at :meth:`_draw`'s handler like any other failure, was spelled with
    :func:`_why`, and was held as "this position cannot be drawn".  :func:`records_a_cut`
    is the clause, and ``tests/test_widening_corpus.py`` reads it over both stores.
    """

    #: The caller's store, or ``None`` to draw exactly as this check always did.
    corpus: Any = None
    #: **§8's SUBSTITUTION, for the schemas this obligation DERIVES**, or ``None`` to draw
    #: the derived schema whole.  The obligation's draws are built out of the pair's node
    #: -- a value class, an intermediate node, the node conjoined with a demand -- so they
    #: inherit the node's size, and the substitution that makes the accepts draw
    #: affordable has to reach them or reading 2 stays blocked wherever reading 1 was.
    #:
    #: Measured: with the accepts draw substituted,
    #: ``creative/sync-creatives-response.json#`` and both
    #: ``media-buy/get-media-buys-response.json`` pairs stopped being cut in
    #: ``check_accepts`` and started being cut HERE -- same library call,
    #: ``merged_as_strategies``, one check further on.
    fixtures: "Fixtures | None" = None
    #: The pair's STATIC identity, :attr:`Pair.identity`.  Required beside a ``corpus``.
    identity: Any = None
    #: How many draws were PAID, and how many a held value answered.  Reported on
    #: :class:`WideningResult` for ``AcceptsResult.replayed``'s reason: the instances are
    #: the same instances either way, and a reader of a green pair is entitled to know
    #: which run paid for its evidence.
    drawn: int = 0
    replayed: int = 0
    #: How many answers came from a draw ANOTHER check of this pair already paid for
    #: (:meth:`one`'s ``borrowed``).  Counted apart from ``drawn`` and from ``replayed``
    #: because it is a third thing: not this check's draw, and not a held entry either --
    #: the first run that borrows one also HOLDS it, so the next run reports it replayed.
    borrowed: int = 0

    def one(
        self,
        schema: Any,
        position: Any,
        custom_formats: Mapping[str, Any],
        borrowed: Sequence[Any] = (),
    ) -> list[Any]:
        """``[one instance of schema]``, or ``[None, why not]`` -- held under ``position``.

        **``borrowed`` are values a draw of THIS PAIR has already produced**, offered to
        ``schema`` in order, and the first one it admits is the answer.  Asked after the
        store and before the draw, so a held entry still decides which witness is graded
        and nothing about a warm run changes.

        **Why it exists, measured.**  :func:`check_widening`'s value class for a
        same-instance keyword is the node AS IT STANDS conjoined with its host, and at a
        pointer whose segments are all same-instance hops the host is the pair's own node
        -- so the class is the document, and drawing it is a whole-document draw the
        ACCEPTS check has already paid for and committed.  On ``adagents.json#`` the
        subject is **2,490,001 bytes of resolved document for a 384-byte conjunct**, and a
        process drawing it reached 2.9 GB of RSS without finishing inside 600 s while the
        accepts floor held an instance of exactly that node.  90 of the bundle's 103
        provable declarations sit at such a pointer.

        **It is not a weaker value and the schema is what says so.**  The candidate is
        offered to the SAME schema a draw would have been asked for, so it is admitted on
        the same terms -- the one difference is which of this pair's draws produced it, and
        :func:`check_widening` then validates it against the document's node and against
        the whole document before the entry point is shown anything, exactly as it does a
        drawn one.  Nothing is hand-written: a borrowed value is ``check_accepts``' own
        output, which is the rule the accepts corpus already follows.  For a class that
        PINS a value -- an ``enum`` member, a ``format`` shape, a bound -- a borrowed
        candidate almost never conforms and the draw happens; the saving is exactly where
        the class is the node, which is where the cost is.

        This is :func:`_bases`' own sentence one level down -- "the base instance is a FREE
        CHOICE among the ones the accepts check already drew" -- applied to the value.
        """
        if self.corpus is None or self.identity is None:
            answer = self._borrowed(schema, borrowed)
            return self._draw(schema, custom_formats) if answer is None else answer
        key = corpus_key(self.identity, custom_formats=custom_formats, position=position)
        held = self.corpus.get(key)
        if isinstance(held, list) and held:
            self.replayed += 1
            return held
        answer = self._borrowed(schema, borrowed)
        if answer is not None:
            self.corpus.put(key, answer)
            return answer
        answer = self._draw(schema, custom_formats)
        #: **A cut is not an answer, so nothing holds it** -- ``check_accepts``' own
        #: ``res.outcome != "strategy_error"`` clause, for this key space.
        #: :func:`records_a_cut` carries the reasoning and the measurement.  The answer is
        #: still RETURNED, because this call's caller asked a question and the cut is the
        #: honest answer to it for this run; what must not happen is the next run reading
        #: it back as evidence.
        if not records_a_cut(answer):
            self.corpus.put(key, answer)
        return answer

    def _borrowed(self, schema: Any, candidates: Sequence[Any]) -> list[Any] | None:
        """The first of ``candidates`` the schema admits, or ``None``.

        ``conforms`` and not a second validator: a schema it cannot build a validator for
        answers ``None``, which is neither admitted nor refused, so such a schema borrows
        nothing and the draw decides.
        """
        if not candidates:
            return None
        try:
            validator_cls = validator_for(schema)
        except Exception:  # noqa: BLE001 -- a schema with no validator borrows nothing
            return None
        for candidate in candidates:
            if conforms(schema, candidate, validator_cls=validator_cls) is True:
                self.borrowed += 1
                return [candidate]
        return None

    def _draw(self, schema: Any, custom_formats: Mapping[str, Any]) -> list[Any]:
        #: **WHAT THE DERIVED SCHEMA ITSELF STATES, ASKED BEFORE ANYTHING IS GENERATED.**
        #: :func:`check_widening`'s value classes are RESTRICTIONS of the node
        #: (:func:`_restricted`), so a node carrying ``examples`` carries it into every
        #: class derived from it -- and :func:`stated_instances` screens the member against
        #: the restriction, so a member the class refuses is simply not an answer and the
        #: draw runs as before.  Counted as a borrow and not as a draw, because that is
        #: what it is: a value this module did not generate.
        stated = stated_instances(schema)
        if stated:
            self.borrowed += 1
            return [stated[0]]
        self.drawn += 1
        #: **The DERIVED schema is reduced before it is drawn from, and the value is
        #: screened against the SCHEMA AS DERIVED.**  Same rule, same seam: the reduction
        #: is a restriction, so a value it yields is a value this position admits, and the
        #: screen makes that a check rather than a claim.  A reduction that places nothing,
        #: raises, or yields a value this schema refuses loses the saving and the draw runs
        #: exactly as it did before -- which is the fail-safe direction §8 requires.
        if self.fixtures is not None:
            try:
                narrowed, placed = self.fixtures.reduced(schema)
            except OverBudget:
                raise
            except Exception:  # noqa: BLE001 -- a derivation that raises loses the saving
                narrowed, placed = schema, 0
            if placed:
                try:
                    value = one_instance(narrowed, custom_formats)
                except OverBudget:
                    raise
                except Exception:  # noqa: BLE001 -- fall through to the unreduced draw
                    value = NONE
                if value is not NONE and conforms(schema, value) is True:
                    return [value]
        try:
            return [one_instance(schema, custom_formats)]
        except Exception as e:  # an undrawable position is unproved
            #: A cut that ``hypothesis`` swallowed and replaced with its own exception is
            #: not an undrawable position; :func:`budget_expired` says which this is.
            if budget_expired():
                raise OverBudget(
                    f"the widening draw was cut and {type(e).__name__} arrived after"
                ) from e
            return [None, _why(e)]


#: **Every shape the format's own checker admits**, for the three formats section 5's
#: ``format`` row lets SELECT A PYTHON TYPE -- and those are the three a narrowing can
#: come from, because a selected type brings its own constraints with it where a format
#: riding as ``json_schema_extra`` brings none.  ``codegen.lower.scalars.FORMAT_TYPES`` is
#: the declaration of which three; this is the shapes, and the two are asserted against
#: each other in ``tests/test_approximation.py`` so a fourth selected format arrives here
#: with its shapes or reddens.
#:
#: Section 8: "for a ``format`` every shape the format's own checker admits rather than the
#: shape a generator finds most likely".  A generator finds the LIKELY shape, which for
#: ``uri`` is a short ``http://`` and for ``date-time`` is a UTC ``Z`` -- so a draw of the
#: likely shape alone is green against a type that refuses every other admissible shape,
#: and these are the shapes that make the draw say so.
#:
#: Each value is admitted by RFC 3986 / RFC 3339 as the draft's own checker reads it, and
#: ``tests/test_approximation.py`` asserts that of every one of them against the checker
#: rather than taking this comment's word for it.
FORMAT_SHAPES: Mapping[str, tuple[tuple[str, Any], ...]] = {
    "uri": (
        ("an https URL", "https://example.com/a"),
        ("a plain http URL", "http://example.com/a"),
        ("a URN", "urn:ietf:rfc:3986"),
        ("a file URL", "file:///tmp/a"),
        ("a mailto URI", "mailto:a@example.com"),
        # 2,220 characters, which is what row .10's live narrowing is measured on: the
        # document states no length and ``HttpUrl`` renders ``maxLength: 2083``.
        ("a URL longer than 2,083 characters", "https://example.com/" + "a" * 2200),
        ("a URL with a port and a query", "https://example.com:8443/a?b=c#d"),
    ),
    "date-time": (
        ("a UTC timestamp", "2026-10-26T12:00:00Z"),
        ("an offset timestamp", "2026-10-26T12:00:00+02:00"),
        ("a negative-offset timestamp", "2026-10-26T12:00:00-05:00"),
        ("a fractional-second timestamp", "2026-10-26T12:00:00.123456Z"),
    ),
    "date": (
        ("a date", "2026-10-26"),
        ("a leap day", "2024-02-29"),
        ("the first day of an era", "0001-01-01"),
    ),
}

#: The keywords whose classes are enumerated from the node, each with how.  A keyword NOT
#: here has no derivation and :func:`value_classes` says so rather than passing -- the
#: vacuous-pass rule this module applies to ``FormatStrategyVerdict.unchecked`` and to
#: ``PairReport.no_instrument`` alike: a check that cannot reach its subject reports that,
#: it does not report a pass.
#:
#: Section 8 names three families and all three are here: "every member of an ``enum``,
#: both sides of each bound and the bound itself, and for a ``format`` every shape the
#: format's own checker admits".  A ``const`` is a one-member ``enum``; a ``pattern``, a
#: ``type`` and the structural keywords have one class, which is the node as it stands.
#: **The bound arm reads :data:`keywords.RANGES`** and no longer lists the eight
#: (``adcp-client-python-3be.8``): each ordering keyword maps to its own range, which is the
#: pair this arm needs because it pins a draw INSIDE the range -- "both sides of each bound
#: and the bound itself, less the side the node's OTHER bound forbids".
#:
#: The INCLUSIVE ranges only, which is the declaration's ``EXCLUSIVE`` column and the one
#: place a reader of a bound needs it: an exclusive bound admits no instance AT the bound,
#: so "the bound exactly" is a value class the document does not have.  ``exclusiveMinimum``
#: and ``exclusiveMaximum`` take the one-class arm below, with ``pattern`` and
#: ``multipleOf``, for the reason stated there.
_BOUNDS: Mapping[str, tuple[str, str]] = {
    keyword: (low, high)
    for low, high in keywords.RANGES
    if low not in keywords.EXCLUSIVE
    for keyword in (low, high)
}


#: **The three structural arms of :func:`value_classes`, read off the DESCENT COLUMN
#: rather than named** (``adcp-client-python-3be.8``).  What a structural keyword's one
#: value class has to RESTRICT is decided by where the keyword holds its subschema, which
#: is exactly the column's answer:
#:
#: * a subschema at MAPV or KEY constrains the object's KEYS or its extra values, so the
#:   class is a one-key object (``minProperties: 1``);
#: * a subschema at ELEM constrains the array's members, so the class is a one-member
#:   list (``minItems: 1``);
#: * a subschema at CONJ, BRANCH or RULE applies to the SAME instance -- a conjunct, a
#:   branch, a conditional -- so there is nothing to restrict and the class is the node
#:   as it stands.
#:
#: PROP is the fourth answer and it is :func:`value_classes`'s own arm, one class per
#: declared property, because the names are the node's and not the column's.
#:
#: ``$ref`` and ``dependencies`` are the **two written names**, and each is written
#: because the column gives it no descent to read: ``$ref``'s target is another document's
#: and §5's row sends it to the TOP rung for exactly that reason, and this bundle's 27
#: ``dependencies`` all hold a LIST of names rather than a schema (``tests/test_keywords.py``
#: records the measurement), so neither holds a subschema at a position of its own. Both
#: constrain the same instance, which is the arm they take.
_A_KEY = frozenset(
    k for k, p in bundle.DESCENDS.items() if p in (Position.MAPV, Position.KEY)
)
_A_MEMBER = frozenset(k for k, p in bundle.DESCENDS.items() if p is Position.ELEM)
_SAME_INSTANCE = frozenset(
    {k for k, p in bundle.DESCENDS.items() if p in (Position.CONJ, Position.BRANCH, Position.RULE)}
    | {"$ref", "dependencies"}
)


def _restricted(node: Mapping[str, Any], **pins: Any) -> dict:
    """``node`` with the keywords in ``pins`` replaced -- a RESTRICTION of it.

    Every value class is a sub-schema of the node and the class's value is a draw from
    that sub-schema, which is what makes "a value the document admits" true by
    construction rather than by assertion: a restriction admits a subset of what the node
    admits.  :func:`check_widening` validates each drawn value against the node anyway,
    because "by construction" is a claim about this function and the claim is cheap to
    check.
    """
    return {**node, **pins}


def value_classes(keyword: str, node: Mapping[str, Any]) -> tuple[tuple[str, dict], ...]:
    """**The classes ``keyword`` distinguishes at ``node``**, as labelled sub-schemas.

    Section 8: "The draw COVERS the node's admissible space by constraint class; it does
    not sample it.  'Never tighter' is a claim about every value the document admits, and a
    sampling draw reports only the values it drew -- so it can run green forever against a
    type that refuses a whole class of admissible value."

    Empty means NO DERIVATION, which :func:`check_widening` reports as
    ``no_value_classes`` and never as a pass.  A keyword whose classes cannot be
    enumerated is a widening nothing proves, and section 9's rule about a check that
    cannot reach its subject applies: "A check is exhaustive over the set of nodes it
    claims, or it does not exist."
    """
    if keyword == "enum" and isinstance(node.get("enum"), list):
        return tuple(
            (f"enum member {member!r}", _restricted(node, enum=[member]))
            for member in node["enum"]
        )
    if keyword == "const":
        return (("the pinned const", dict(node)),)
    if keyword == "type":
        words = node["type"] if isinstance(node.get("type"), list) else [node.get("type")]
        return tuple((f"type {w!r}", _restricted(node, type=w)) for w in words if w)
    if keyword == "format" and node.get("format") in FORMAT_SHAPES:
        return tuple(
            (f"{label} ({node['format']})", _restricted(node, const=value))
            for label, value in FORMAT_SHAPES[node["format"]]
        )
    if keyword in _BOUNDS and isinstance(node.get(keyword), (int, float)):
        low, high = _BOUNDS[keyword]
        bound = node[keyword]
        # Which way "one step inside" points is the declaration's bit and not the
        # keyword's SPELLING: a floor's inside is above it and a ceiling's below.
        inside = bound + 1 if keywords.pins_a_floor(keyword) else bound - 1
        floor, ceiling = node.get(low), node.get(high)
        out = [(f"{keyword} exactly ({bound})", _restricted(node, **{low: bound, high: bound}))]
        # **Both sides and the bound itself**, less the side the node's OTHER bound
        # forbids: a ``minLength: 1, maxLength: 1`` node admits exactly one length, and a
        # class for length 2 would be a value the DOCUMENT refuses -- which section 8 says
        # nothing about, because the schema half refuses it first.
        if (floor is None or inside >= floor) and (ceiling is None or inside <= ceiling):
            out.append(
                (f"{keyword} one step inside ({inside})", _restricted(node, **{low: inside, high: inside}))
            )
        return tuple(out)
    if keyword == "uniqueItems" and node.get("uniqueItems") is True:
        # What the keyword DISTINGUISHES is a list of two or more members, since a list of
        # one cannot repeat: so the class is the shortest list the document admits that has
        # a duplicate to forbid, and the length is PINNED rather than floored -- an
        # unpinned draw may take any length above it, and a class whose value varies run to
        # run is a class that reports a narrowing it did not reach.
        least = max(2, node.get("minItems") or 0)
        ceiling = node.get("maxItems")
        if ceiling is not None and ceiling < least:
            return ()  # the document admits no list long enough to repeat
        return (
            (
                f"{least} distinct members",
                _restricted(node, minItems=least, maxItems=least),
            ),
        )
    if keyword in ("pattern", "multipleOf", *keywords.EXCLUSIVE):
        # One class: the node as it stands, drawn with the keyword in force.  A second
        # class would need a value one step from the bound, and for a ``pattern`` or a
        # float bound there is no step this module can name.  The exclusive pair is the
        # declaration's EXCLUSIVE column (:data:`keywords.EXCLUSIVE`) and not a second
        # list of the two: an exclusive bound admits no instance AT the bound, so it has
        # no "exactly" class for the arm above to draw.
        return ((f"a value the {keyword} admits", dict(node)),)
    if keyword == "properties" and isinstance(node.get("properties"), dict):
        return tuple(
            (f"the property {key!r} present", _restricted(node, required=[key]))
            for key in sorted(node["properties"])
        )
    if keyword == "required" and isinstance(node.get("required"), list):
        return (("every required name present", dict(node)),)
    if keyword in _A_KEY:
        return ((f"a key the {keyword} admits", _restricted(node, minProperties=1)),)
    if keyword in _A_MEMBER:
        return ((f"a list the {keyword} admits", _restricted(node, minItems=1)),)
    if keyword in _SAME_INSTANCE:
        return ((f"a value the {keyword} admits", dict(node)),)
    return ()


#: The keywords whose subschema is a mapping's VALUE, DERIVED from the descent column
#: rather than named: ``keywords.descends_at`` is "the ONE descent table", and a keyword
#: holding a MAPV subschema is exactly what a mapping value IS.  Read at PROP, which is
#: where a mapping sits in the documents that state one; the column's answer is the same
#: at every position that gives one.
#:
#: Each is paired with how many pointer segments it spends: ``patternProperties`` is a MAP
#: from an expression to a schema, so its own word plus the expression, and
#: ``additionalProperties`` is one schema, so its word alone.  Read off
#: :data:`_DESCEND_MAP`, which is the same distinction one line up.
_MAPPING_VALUE = {
    keyword: 2 if keyword in _DESCEND_MAP else 1
    for keyword, position in keywords.descends_at(Position.PROP).items()
    if position is Position.MAPV
}


def _mapping_key(node: Any, expression: str | None) -> Any:
    """ONE key the mapping ``node`` admits, for a widening declared on its VALUE.

    §8: "A mapping value -- ``#/properties/x/additionalProperties``, and the same for
    ``patternProperties``.  The location is ``x`` then any key the mapping admits; a key
    is a free choice and the draw makes one, so the location exists and simply was not
    read."  This is that choice, and it is a DRAW from what the document says about keys
    rather than a literal: 4 of the bundle's 5 mapping-valued widening sites state
    ``propertyNames: {"pattern": ...}``, so a fixed key would be a key the document
    refuses and the obligation would report ``unproved`` for the instrument's own reason
    instead of the document's.

    :data:`_ALIEN_KEY` where the document says NOTHING about keys, which is not a fallback
    but the same choice made deterministically: every string is admitted, so the one worth
    picking is the one that cannot collide with a declared property's own schema.

    ``None`` where a key constraint is stated and nothing can be drawn from it, so
    :func:`check_widening` reports the widening unproved rather than placing a key the
    document refuses.
    """
    names = node.get("propertyNames") if isinstance(node, Mapping) else None
    key: dict[str, Any] = {"type": "string"}
    if expression is not None:
        key["pattern"] = expression
    if isinstance(names, Mapping):
        key |= {k: v for k, v in names.items() if k != "type"}
    if set(key) == {"type"}:
        return _ALIEN_KEY
    try:
        return one_instance(key, {})
    except Exception:  # an undrawable key constraint has no location
        return None


def instance_path(pointer: str, schema: Any = None) -> tuple[Any, ...] | None:
    """The INSTANCE location a schema pointer describes, or ``None`` where it has none.

    ``#/properties/x`` describes the value under the key ``x``; ``#/items`` describes
    every element, so index 0 stands for it; a same-instance hop -- ``#/allOf/0``,
    ``#/oneOf/1``, ``#/then`` -- describes the SAME instance and contributes no segment,
    which is ``adcp.types._base.SAME_INSTANCE_LIST``'s own rule read the other way.

    **A MAPPING VALUE has a location too, and §8 settled that it was simply not read**:
    ``#/properties/x/additionalProperties`` is ``x`` then any key the mapping admits, and
    ``#/properties/x/patternProperties/<expr>`` is ``x`` then a key the expression
    matches.  The key is a free choice (:func:`_mapping_key`), which is the same sentence
    ``items`` already stands on -- "describes every element, so index 0 stands for it".
    ``schema`` is what the choice is read off, so a caller grading a pair passes the
    pair's own node; with none supplied the key constraint cannot be read and such a
    pointer has no location, which is the fail-safe direction.

    ``None`` for a pointer whose segments describe no instance location at all -- a
    ``#/definitions/x`` reached only through a ``$ref``, an ``#/if``, a
    ``#/propertyNames`` -- and :func:`check_widening` reports that as
    ``no_instance_path`` rather than placing a value somewhere the document does not mean.

    **A ``definitions`` entry stays without one and needs none** (§8): "an entry is
    reachable only through a ``$ref`` that names it, and §5 declares no entry nothing
    references", so it has no location of its own -- and the rule that a declaration
    travels with the fact (``emit.repointed``) has already re-pointed it to the referring
    ``properties`` segment, which this function does place.
    """
    walked = _steps(pointer, schema)
    return None if walked is None else tuple(segment for segment, _ in walked[0])


def _down(node: Any, *keys: str) -> Any:
    """The subschema ``keys`` names under ``node``, or ``None``.

    A LIST index is a segment like any other, because a combinator's branches and a
    conjunction's members are a list in the document: without it, a declaration one
    ``allOf/1`` hop in lost every subschema below it and :func:`_reached` had nothing to
    draw an absent intermediate from.
    """
    for key in keys:
        if isinstance(node, list):
            if not key.isdigit() or int(key) >= len(node):
                return None
            node = node[int(key)]
        elif isinstance(node, Mapping) and key in node:
            node = node[key]
        else:
            return None
    return node


def _written_and_settled(node: Any, root: Any) -> tuple[Any, Any]:
    """``node`` read the way the DOCUMENT states it, and the node it was settled FROM:
    one reading in two halves, because the two halves answer two different questions
    about one pointer.

    :func:`_normalize` and :func:`_composed` are the two readings and this is the pair of
    them in the one order that is correct -- normalisation FIRST, "so a reference whose
    TARGET composes still has its conjuncts folded".  Anything that is not a mapping is
    handed back unchanged, which is what a list of branches is.  ``root`` reaches BOTH
    readings, because both resolve a local pointer against it: the node's own
    (:func:`_normalize`) and a bare conjunct's (:func:`_composed`).

    **The composed half decides what the document STATES at a pointer; the written half
    decides what a pointer SPELLS.**  :func:`_composed` folds a conjunct's facts into the
    node it composes and removes ``allOf`` from the merged node for exactly that reason --
    the fact is now at the composing pointer and must not also be found one hop away.
    What it cannot do is remove the ``allOf`` segment from the POINTER LANGUAGE: a fact
    outside ``FOLDED_FACTS`` is not folded anywhere, so the document still states it at
    ``#/allOf/0`` and ``emit`` declares it there.

    Measured over the 1,054 portable documents: **90 of the 103 provable declarations sit
    at a pointer ending ``/allOf/N``** -- every ``if`` the bundle states but one, and two
    of the four ``else`` -- and every one of them was reported "the document states no
    such keyword at that pointer" by :func:`check_widening` with nothing drawn, because
    the merged node the walk was descending from no longer carried the list the segment
    names.  :func:`_steps` therefore takes a same-instance LIST hop on the written half
    and everything else on the composed one.
    """
    written = _normalize(node, root, declared_null=True) if isinstance(node, Mapping) else node
    return written, (_composed(written, root) if isinstance(written, Mapping) else written)


def _steps(
    pointer: str, schema: Any, stated: Any = None
) -> tuple[list[tuple[Any, Any]], Any, Any] | None:
    """Each instance segment the pointer's location is made of, with the DOCUMENT's own
    subschema for the value at it -- the node the pointer itself names, and the node at
    the instance LOCATION that node is a statement about.

    :func:`instance_path` is the segments alone, :func:`_reached` is the subschemas and
    :func:`check_widening` is the last two: one walk answers all three, because a path
    whose intermediate nodes are read by a DIFFERENT reading of the pointer than the path
    itself is two walks that can disagree about which node a segment names.

    **Every node on the way is COMPOSED and NORMALIZED first, which is the reading the
    EMITTER makes** (:func:`_settled`): a conjunct's facts are folded into the node it
    composes at every depth, so a fact a conjunct states is found at the pointer the
    walk reaches it at and at no other.  Without it the declaration and the obligation
    pointed at it disagreed about where the fact is -- measured at
    ``core/account-with-authorization.json``, whose widening is declared at the composed
    pointer (``emit._folded``) and whose raw document holds the keyword one ``allOf/1``
    hop away, so the obligation reported "the document states no such keyword".

    **A SAME-INSTANCE LIST HOP IS TAKEN ON THE WRITTEN HALF, because composition CONSUMES
    the list the segment names** (:func:`_written_and_settled`).  That paragraph is about a
    fact the fold MOVES, and the fold moves only ``FOLDED_FACTS``: an ``if`` is not one, so
    the document states it at ``#/allOf/0`` and nowhere else, while the merged node the
    walk was descending from had no ``allOf`` left to descend through.  90 of the bundle's
    103 provable declarations sit at such a pointer and every one of them reported "the
    document states no such keyword" with nothing drawn.

    **AND A LEADING ``allOf`` INDEX IS AN INDEX INTO THE LIST THE DOCUMENT STATES, WHICH
    IS NOT THE LIST ``schema`` CARRIES.**  ``schema`` is the node the ACCESSOR produced
    (``adcp.types._base.applied_schema``), and at a union branch that accessor splices
    what the enclosing node asserts about the same instance IN FRONT of the branch's own
    conjuncts -- "the enclosing statements come FIRST and the node's own conjuncts after".
    A declaration's pointer is the document's own spelling (``emit.stated_where_declared``
    gates it against ``bundle.node_at``), so ``#/oneOf/0/allOf/0`` names the BRANCH's first
    conjunct and index 0 of the applied node is the ROOT's.  ``stated`` is the starting
    node as the document states it -- unspliced -- and a leading ``allOf`` hop is taken on
    its own conjunct list, which is ``docs/plan/architecture.md``'s "A READER DERIVES ITS
    KEY FROM THE ACCESSOR THE GRADE READS THROUGH" applied to the one segment where the
    two readings of a pointer differ: a reader keyed on the other form "matches NOTHING,
    and a check that matches nothing is green."

    Measured over the 459 (pair, declaration) obligations of the bundle: **4 of them walk
    to a different node with this reading and every other one walks to the same node**, and
    those 4 -- ``account/sync-accounts-response.json#/oneOf/0``,
    ``media-buy/create-media-buy-response.json#/oneOf/0``,
    ``media-buy/request-proposals-response.json#/anyOf/1`` and
    ``media-buy/sync-catalogs-response.json#/oneOf/1``, each at ``.../allOf/0`` on ``if``
    -- are exactly the four ``docs/plan/unimplemented.md``'s A-9 names: a pointer the
    document states and a strict segment-walk of the composed node could not reach.  Only
    a LEADING hop, because the splice happens at the pointer the accessor was asked for and
    nowhere below it: every node further in is reached by :func:`_written_and_settled` off
    the document's own text.  ``None`` -- every caller that has no document -- walks
    exactly as it did.

    **``host`` is the node at the last INSTANCE segment AS THE DOCUMENT WRITES IT, which
    is what a same-instance hop is a statement about, and ``None`` where the pointer ends
    at that segment and there is no hop.**  ``#/properties/age/allOf/1`` describes the
    value under ``age``, and what that value has to satisfy is everything the document
    says about ``age`` -- that conjunct AND its siblings -- so a caller that drew from the
    conjunct alone draws a value the document refuses.  Measured on
    ``core/demographic-reporting-capability.json``, whose ``age`` states two conditionals:
    drawn from ``allOf/1`` alone the value declared ``exact_predicates`` without the four
    names ``allOf/0`` then demands, and the placement reported a payload the document
    refuses.

    The WRITTEN half and not the composed one, for the same reason the list hop takes it:
    ``_composed`` removes the conjunct list, so the composed node at ``age`` has lost the
    sibling conditional that refused the value.  ``None`` rather than the node itself
    where no hop was taken, so a caller cannot conjoin a node with itself and every
    declaration this check already proved draws exactly what it drew.
    """
    segments = [s for s in pointer.lstrip("#").split("/") if s]
    out: list[tuple[Any, Any]] = []
    written, node = _written_and_settled(schema, schema)
    at_location, hops = written, 0
    i = 0
    while i < len(segments):
        word = segments[i]
        if word == "properties" and i + 1 < len(segments):
            written, node = _written_and_settled(_down(node, word, segments[i + 1]), schema)
            at_location, hops = written, 0
            out.append((bundle.unescape_key(segments[i + 1]), node))
            i += 2
        elif word == "items":
            written, node = _written_and_settled(_down(node, word), schema)
            at_location, hops = written, 0
            out.append((0, node))
            i += 1
        elif word in _MAPPING_VALUE and i + _MAPPING_VALUE[word] <= len(segments):
            spent = _MAPPING_VALUE[word]
            expression = bundle.unescape_key(segments[i + 1]) if spent == 2 else None
            key = _mapping_key(node, expression)
            if key is None:
                return None
            written, node = _written_and_settled(
                _down(node, *segments[i : i + spent]), schema
            )
            at_location, hops = written, 0
            out.append((key, node))
            i += spent
        elif word in _DESCEND_LIST and i + 1 < len(segments):
            # A same-instance hop through a LIST: no instance segment, and two pointer
            # segments spent (the keyword and the index).  ``_DESCEND_LIST`` is the
            # descent column's own answer to "which keywords hold their subschemas in a
            # list", so the three are read here and not restated.
            #
            # **Off ``written`` and not off ``node``**, because ``_composed`` removes
            # ``allOf`` from the merged node and the pointer still spells it; the
            # docstring above carries the measurement.  ``node`` is the fall-back and not
            # dead code -- a conjunct whose own statement is a combinator IS kept on the
            # merged node, and a ``oneOf``/``anyOf`` hop is a branch list the fold never
            # touches, so the written half answers for ``allOf`` and the composed half for
            # the hops that were already reachable.
            #
            # **A LEADING ``allOf`` HOP IS TAKEN ON ``stated``, the starting node as the
            # DOCUMENT states it**: the docstring carries why and what it measures.  It is
            # AUTHORITATIVE and not a first guess -- where the document states a conjunct
            # list at this node, the index the pointer spells is an index into THAT list,
            # and an index outside it is a declaration at a pointer the document does not
            # have, which walks to no node and is reported rather than resolved against a
            # list the accessor assembled.
            own = (
                stated.get("allOf")
                if word == "allOf" and not out and hops == 0 and isinstance(stated, Mapping)
                else None
            )
            if isinstance(own, list):
                child = _down(stated, word, segments[i + 1])
            else:
                child = _down(written, word, segments[i + 1])
                if child is None:
                    child = _down(node, word, segments[i + 1])
            written, node = _written_and_settled(child, schema)
            hops += 1
            i += 2
        elif word in ("then", "else"):
            written, node = _written_and_settled(_down(node, word), schema)
            hops += 1
            i += 1  # a same-instance hop
        else:
            return None
    return out, node, (at_location if hops else None)


def _reached(
    schema: Any,
    pointer: str,
    instance: Any,
    custom_formats: Mapping[str, Any],
    draws: _Draws,
    stated: Any = None,
) -> Any:
    """``instance`` with every node on the way to ``pointer``'s location PRESENT.

    §8's "every position a widening can land at has an instance location" is a claim about
    the DOCUMENT, and a drawn payload that happened to omit an optional property on the way
    to that location does not refute it -- it says only that the draw went another way.  So
    each node the path passes through that the instance does not carry is DRAWN from the
    document's OWN subschema at that point, which keeps the payload one the document
    admits; a bare ``{}`` there does not, and that is what the measurement said: three of
    the twelve declared widenings reported ``unproved`` because an intermediate object
    created empty violated its own ``required``, or because an ``items`` index had no list
    under it at all.

    The LAST segment is left alone -- :func:`_placed` is what writes the drawn value there,
    and drawing a value for it first would be a draw thrown away.

    ``instance`` unchanged where a step's subschema is unknown, which is the fail-safe
    direction: the placement then either lands or :func:`check_widening` reports it
    unproved, and neither invents a payload the document does not admit.

    **THE DRAW IS HELD AND THIS IS WHERE §8's OBLIGATION SPENDS MOST OF ITS TIME**
    (``adcp-client-python-3be.25``): 1,441 s of the obligation's 1,606 s over the declaring
    population, in 17 draws.  ``draws`` is :class:`_Draws` and its docstring carries the
    rest of the measurement.  The node a step reaches is a subschema of a RESOLVED document,
    so one of these draws is a whole-document draw -- 117.9 s and then 122.8 s on the SAME
    4,619,199-byte node of ``core/async-response-data.json#/anyOf/28``, once per value
    class of one declaration, and 600 s on a 6.8 MB one without finishing -- and the
    caller's loop asks for it once per value class and once per base candidate.  Held, that
    pair's two became one.  The position is ``("reached", pointer,
    step index)``: the step is reached by walking the pair's own node along a POINTER the
    bundle fixes, so two runs, two pairs of one document and two value classes of one
    declaration all name the same draw.  The index and not the instance path, because two
    declarations of one pair can reach one instance segment along different pointers and
    the node is then not the same node.

    ``stated`` is :func:`_steps`' own argument passed straight through, for that function's
    own reason: a path whose intermediate nodes are read by a different reading of the
    pointer than the path itself is two walks that can disagree about which node a segment
    names, and the caller's walk and this one must not be the two.
    """
    walked = _steps(pointer, schema, stated)
    if walked is None or not walked[0]:
        return instance
    steps = walked[0]
    out = copy.deepcopy(instance)
    cursor = out
    for index, (segment, node) in enumerate(steps[:-1]):
        if isinstance(segment, int):
            if not isinstance(cursor, list):
                return out
            if len(cursor) <= segment:
                if node is None:
                    return out
                held = draws.one(node, ("reached", pointer, index), custom_formats)
                if len(held) > 1:  # an undrawable node is left absent
                    return out
                while len(cursor) <= segment:
                    cursor.append(copy.deepcopy(held[0]))
        else:
            if not isinstance(cursor, dict):
                return out
            if segment not in cursor:
                if node is None:
                    return out
                held = draws.one(node, ("reached", pointer, index), custom_formats)
                if len(held) > 1:
                    return out
                cursor[segment] = held[0]
        cursor = cursor[segment]
    return out


def _placed(instance: Any, path: Sequence[Any], value: Any) -> Any:
    """``instance`` with ``value`` at ``path``, as a copy.

    A path segment the instance does not carry is CREATED, because a widened fact can sit
    at an optional property the drawn instance happened to omit: the point of the draw is
    the value at the pointer, so an instance without it says nothing.  :func:`_reached` is
    what makes that creation a node the DOCUMENT admits rather than a bare ``{}``.
    """
    if not path:
        return value
    out = copy.deepcopy(instance)
    cursor = out
    for segment in path[:-1]:
        if isinstance(segment, int):
            if not isinstance(cursor, list) or len(cursor) <= segment:
                return None
            cursor = cursor[segment]
        else:
            if not isinstance(cursor, dict):
                return None
            cursor = cursor.setdefault(segment, {})
    last = path[-1]
    if isinstance(last, int):
        if not isinstance(cursor, list):
            return None
        while len(cursor) <= last:
            cursor.append(value)
        cursor[last] = value
    else:
        if not isinstance(cursor, dict):
            return None
        cursor[last] = value
    return out


def _conjoined(host: Any, sub: Any) -> Any:
    """``sub`` as a statement about an instance ``host`` ALSO constrains, or ``sub`` alone.

    **A same-instance hop says "this as well", never "this instead"**, which is what
    :func:`_steps`' third answer is for: ``#/properties/age/allOf/1`` is a statement about
    the value under ``age``, and that value has to satisfy everything the document says
    about ``age`` -- that conjunct AND its siblings.  So a value class derived from the
    conjunct is drawn, and graded, under the conjunction of the two; drawn from the
    conjunct alone it is a value the document refuses, which
    :func:`check_widening` then reports as a payload the document refuses rather than as
    anything about the class.

    ``host`` is ``None`` where the pointer ends AT its instance segment and no hop was
    taken, and then there is nothing to conjoin and the subject is unchanged -- which is
    every declaration this check proved before the host existed.
    """
    return {"allOf": [host, sub]} if isinstance(host, Mapping) else sub


def _value_at(instance: Any, path: Sequence[Any]) -> list[Any]:
    """``[the value at ``path``]``, or ``[]`` where the instance does not carry it.

    :func:`_placed`'s inverse, and a LIST rather than a value for :class:`_Draws`' own
    reason: a document can admit ``null``, so a sentinel value could not tell "the value
    there is null" from "there is nothing there".  An empty path reads the whole instance,
    which is what a declaration at a pointer of same-instance hops describes.
    """
    cursor = instance
    for segment in path:
        if isinstance(segment, int):
            if not isinstance(cursor, list) or len(cursor) <= segment:
                return []
        elif not isinstance(cursor, dict) or segment not in cursor:
            return []
        cursor = cursor[segment]
    return [cursor]


def _demanding(path: Sequence[Any]) -> dict:
    """The schema that DEMANDS an instance location, derived from the path alone.

    §8: "every position a widening can land at has an instance location."  A borrowed
    payload may not HAVE it -- :func:`_reached` creates an intermediate node the draw
    omitted, but a branch of the document's own union can refuse the location outright,
    and then there is nothing to create.  Measured on
    ``compliance/comply-test-controller-response.json``, whose ``recorded_calls`` items
    node pairs ``attestation_mode: digest`` with ``not: {"required": ["payload"]}``: a
    payload with a ``payload`` key added is a payload the document REFUSES, so the
    placement says nothing about the class however many borrowed instances are tried.

    So the obligation asks the document for an instance that has the location, by
    conjoining this with the document's own schema (``{"allOf": [schema, demand]}``).
    **It is a reading of the POINTER and not of the document**: a key segment demands
    the key, an index segment demands a list long enough to hold it, and the draw is
    the document's own -- the conjunction can only NARROW what hypothesis draws from,
    never admit something the document does not.  A document whose location is
    genuinely unreachable makes the conjunction unsatisfiable, and the draw then fails
    and the widening is reported ``unproved``, which is the right answer for a pointer
    no instance can carry.

    It costs a whole-document draw, which is why it is the LAST candidate: the borrowed
    instances cost nothing and answer for every declaration whose location the accepts
    draw already reached.  Measured over the declared set: 1 of 13 declarations needs
    it, and only because of that ``not``.
    """
    if not path:
        return {}
    segment, rest = path[0], path[1:]
    inner = _demanding(rest)
    if isinstance(segment, int):
        demand: dict[str, Any] = {"type": "array", "minItems": segment + 1}
        if inner:
            demand["items"] = inner
        return demand
    demand = {"type": "object", "required": [segment]}
    if inner:
        demand["properties"] = {segment: inner}
    return demand


def _bases(
    schema: dict,
    path: Sequence[Any],
    instances: Sequence[Any],
    cf: Mapping[str, Any],
    memo: list[Any],
    draws: _Draws,
) -> Iterator[Any]:
    """The base payloads §8's obligation may place a drawn value into, cheapest first.

    Every instance the accepts check already drew, then -- only if none of them hosted
    the location -- one drawn from the document CONJOINED with :func:`_demanding`, whose
    docstring carries why that last one exists and what it costs.  A generator, so the
    extra draw is not paid for at all where a borrowed instance answers.

    ``memo`` is the caller's one-slot store for that draw, held across the value classes
    of ONE declaration: the demand is a function of the pointer alone, so every class of
    a declaration wants the same base and drawing it twice doubles the only expensive
    thing here.  An empty list means "not drawn yet"; a list of TWO means the draw was
    tried and failed, which is remembered for the same reason -- and the length and not the
    value is what says so, because a document can admit ``null`` and the old spelling
    (``memo == [None]`` for a failure) could not tell that from one.

    **``memo`` DOES its documented job, and the measurement says so rather than assuming
    it** (``adcp-client-python-3be.25``): over the declaring population one completed pass
    reached this draw for **24 declarations over 14 pairs, and the one slot saved 3 draws**
    -- the second and later value classes of the declarations that have more than one.  So
    the slot is not the gap.  What it cannot reach is the repetition ACROSS declarations of
    a pair, across the PAIRS of a document -- a nested class and every ancestor whose node
    contains it are separate pairs carrying the same declaration -- and across every RUN,
    cold or warm.  ``draws`` is :class:`_Draws`, which spans all three; the position is
    ``("demand", the instance path)``, which is what the demand is a function of.

    The two stay side by side rather than one replacing the other: the memo answers within
    a declaration without a file read, and a declaration whose store is ``None`` -- every
    caller in ``tests/test_approximation.py`` -- keeps exactly the behaviour it had.
    """
    yield from instances or (None,)
    if not path:
        return
    if not memo:
        memo.extend(draws.one({"allOf": [schema, _demanding(path)]}, ("demand", list(path)), cf))
    if len(memo) == 1:
        yield memo[0]


@dataclass
class WideningResult:
    """Whether each declared approximation really WIDENS, by value and by pointer.

    Section 8: "An approximation is a claim about this check, and this check is what
    proves it ... An approximation that still refuses a value the document admits is a
    NARROWING wearing a declaration, and it fails here, by value and by pointer.  This is
    what keeps 'approximated' from being an allowlist."

    ``unproved`` is as much a failure as ``narrowings``, and that is the decision rather
    than an omission: a declaration whose classes this module cannot enumerate, or whose
    pointer describes no instance location, is a widening nobody has proved -- and section
    9's "a check is exhaustive over the set of nodes it claims, or it does not exist" says
    what to do with it.
    """

    #: How many declarations were put to the check.
    declarations: int = 0
    #: How many drawn values reached the entry point and were accepted.
    accepted: int = 0
    #: A value the DOCUMENT admits and the class REFUSES, by pointer and by value.
    narrowings: list[str] = field(default_factory=list)
    #: A declaration this check could not reach, with the reason.
    unproved: list[str] = field(default_factory=list)
    detail: str = ""

    #: How many base instances this check DREW, and how many a held one answered.
    #: **REPORTED for ``AcceptsResult.replayed``'s reason**: the values are the same values
    #: either way -- every one of them is placed and offered to the DOCUMENT before the
    #: entry point sees it -- but a reader of a green pair is entitled to know which run
    #: paid for its evidence, and a census that cannot tell a drawn pair from a replayed
    #: one cannot measure a cold run against a warm one.  :class:`_Draws` is where they
    #: come from and its docstring carries what the draws cost.
    drawn: int = 0
    replayed: int = 0
    #: How many answers came from a draw ANOTHER check of this pair already paid for;
    #: :meth:`_Draws.one`'s ``borrowed`` carries what that is and why it is not a weaker
    #: value.  Reported for ``drawn``/``replayed``'s reason: a reader of a green pair is
    #: entitled to know which draw paid for its evidence.
    borrowed: int = 0

    @property
    def outcome(self) -> str:
        if self.detail:
            return "error"
        if self.narrowings:
            return "narrowing_wearing_a_declaration"
        if self.unproved:
            return "unproved_widening"
        if not self.declarations:
            return "no_declarations"  # nothing was claimed, so nothing is owed
        return "pass"


def node_as_stated(document: Any, at: str) -> Any:
    """``document``'s own node at ``at`` -- the node as the DOCUMENT STATES it, or ``None``.

    **A PLAIN POINTER WALK OF THE DOCUMENT AND NOT THE ACCESSOR, and that is the whole
    point of it.**  ``adcp.types._base.applied_schema`` is the accessor the grade reads a
    pair's node through, and at a union branch it splices what the enclosing node asserts
    about the same instance IN FRONT of the branch's own ``allOf`` conjuncts.  A
    declaration's pointer is the document's own spelling -- ``emit.stated_where_declared``
    gates every one of them against ``bundle.node_at`` -- so the index that pointer spells
    is an index into the list the DOCUMENT states here, and this is the one reading that
    has it.  :func:`_steps`' ``stated`` argument carries what the difference costs and the
    four pointers it reaches.

    **ONE DERIVATION, because the obligation and the census that claims the obligation can
    reach every site must ask the walk the SAME question.**
    ``tests/test_approximation.py::test_no_declaration_the_tree_carries_is_one_its_pair_cannot_put_to_a_draw``
    asks ``_steps`` whether a site is reachable, and a reading of this node there that is
    not the reading :func:`check_widening` makes is a census over a different set from the
    one the grade acts in.

    ``None`` for a pointer the document does not hold and for no document at all, which is
    the fail-safe direction: the walk then reads the accessor's node exactly as it did
    before this argument existed.
    """
    if document is None:
        return None
    inside = at.lstrip("#").strip("/")
    if not inside:
        return document
    try:
        return bundle.node_at(document, inside)
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def check_widening(
    schema: dict,
    accept: Callable[[Any], Any],
    declared: Sequence[Approximation],
    *,
    at: str = "#",
    instances: Sequence[Any] = (),
    custom_formats: Mapping[str, Any] = (),
    corpus: Any = None,
    identity: Any = None,
    fixtures: "Fixtures | None" = None,
    document: Any = None,
) -> WideningResult:
    """Section 8's accepts OBLIGATION, one declaration at a time.

    ``instances`` are the payloads the accepts check already drew for this pair, which is
    what keeps this from costing a second whole-document draw: the obligation is about the
    value at ONE pointer, so the rest of the payload is any payload the document admits.
    With none supplied the obligation can still run for a declaration at the pair's own
    root, where the drawn class value IS the whole instance.

    **It is a SEQUENCE and the obligation walks it, which is ``_reached``'s own rule one
    level up.**  That function already says "a drawn payload that happened to omit an
    optional property on the way to that location does not refute [section 8's claim] --
    it says only that the draw went another way", and creates the node the document's own
    subschema describes.  A branch of the node's own ``oneOf`` can refuse the location
    outright, and then there is nothing to create: measured on
    ``compliance/comply-test-controller-response.json``, whose ``recorded_calls`` items
    pair ``attestation_mode: digest`` with ``not: {required: [payload]}`` -- so the
    declaration on ``payload``'s ``maxLength`` is placeable only in the ``raw`` branch,
    and the accepts check's FIRST draw is a digest call.  The base instance is a free
    choice the draw already made several times over, so the obligation takes one that
    admits the location instead of reporting the draw's own branch as a widening nobody
    proved.

    The walk cannot turn a narrowing into a pass: a candidate is skipped only where the
    DOCUMENT refuses the placed payload, which is decided before the entry point is
    offered anything, so every candidate that reaches ``accept`` is graded and the first
    one's verdict stands.

    Each class is a RESTRICTION of the document's own node (:func:`value_classes`), so a
    value drawn from it is a value the document admits -- asserted against the node anyway,
    because a restriction is a claim about :func:`_restricted` and checking it is cheap.
    The value is then placed at the pointer's instance location and offered to the entry
    point.  A ``ValidationError`` there is the one thing section 2 says must never happen:
    "An annotation tighter than its document refuses a payload the protocol permits, and
    ``strict_validate`` cannot repair it."

    **``corpus`` IS WHERE THIS CHECK'S OWN DRAWS ARE HELD, and it is a second store beside
    the accepts one and not the same one** (``adcp-client-python-3be.25``).  ``check_pair``
    used to hand its corpus "straight to the accepts check and to nothing else", and the
    measurement :class:`_Draws` tabulates is what that cost: the obligation draws from
    schemas it DERIVES out of the pair's node -- a value class, an intermediate node on the
    way to an instance location, the node conjoined with a demand -- and every one of those
    was paid again on every run, for every pair of a document and for every value class of
    a declaration.  :class:`_Draws` says what the key is over and why these are different
    questions from the accepts draw rather than more of it.

    **A SEPARATE KEY SPACE, DELIBERATELY.**  ``tests/accepts-corpus``'s gate asserts an
    equality in BOTH directions -- the committed floor holds no entry the graded population
    does not ask for -- and a widening entry landing there would make that assertion read
    false while nothing was wrong, which would retire the gate that has just landed.  So
    ``tests/corpus.py`` gives this draw its own floor and its own cache, and
    ``tests/test_widening_corpus.py``'s
    ``test_a_held_widening_base_lands_in_no_accepts_key_space`` is the reading.

    ``identity`` is REQUIRED beside a ``corpus`` and there is no fallback, for
    :func:`check_accepts`' reason: the schema handed here is a rendering of a document and
    keying on it is the defect :func:`corpus_key` exists to close.  With no ``corpus`` this
    check draws exactly as it always did.

    **``document`` IS WHAT MAKES A DECLARED POINTER'S ``allOf`` INDEX READABLE**, and it is
    the same argument :class:`Pair` already carries for the same reason -- "the scope a
    LOCAL ``$ref`` on the document side is relative to, which a nested pair's node does not
    contain".  ``schema`` is the ACCESSOR's node, and at a union branch the accessor splices
    the enclosing node's same-instance statements in front of the branch's own conjuncts; a
    declaration's pointer is the document's own spelling, so the index it spells is an index
    into the list the DOCUMENT states at this pointer.  :func:`_steps`' ``stated`` carries
    the reading and the measurement -- 4 of the bundle's 459 obligations, each
    ``docs/plan/unimplemented.md`` A-9's "a pointer a strict segment-walk of their own
    document of record cannot reach".  ``None`` -- every caller in
    ``tests/test_approximation.py`` -- walks exactly as it did.
    """
    if corpus is not None and identity is None:
        raise ValueError(
            "a corpus needs the draw's STATIC identity: the schemas this check draws "
            "from are derived from the one handed here, which is a RENDERING of a "
            "document, so keying on it moves every entry when the compiler moves "
            "(harness.corpus_key).  Pass identity=... (Pair.identity) or corpus=None."
        )
    res = WideningResult()
    cf = dict(custom_formats)
    draws = _Draws(corpus=corpus, identity=identity, fixtures=fixtures)
    validator_cls = validator_for(schema)
    #: The node under grade AS THE DOCUMENT STATES IT, read once per pair: a plain pointer
    #: walk of the document and not the accessor, because what every walk below needs off
    #: it is the one thing the accessor respells -- its own ``allOf`` list.  A pointer the
    #: document does not hold leaves this ``None`` and the walks read ``schema`` exactly as
    #: they did, which is the fail-safe direction and the behaviour of every caller that
    #: supplies no document.
    stated = node_as_stated(document, at)
    for one in declared:
        res.declarations += 1
        if one.kind == UNDERDETERMINED:
            # Section 2: "No draw or dump can see one, which is precisely why
            # it is declared and why its instrument is different (section 8)."  Its check
            # is the disjointness equality (:func:`underdetermined_census`) and claiming
            # it here would report a pass this check cannot earn.
            res.declarations -= 1
            continue
        relative = "" if one.pointer == at else one.pointer[len(at.rstrip("/")) :]
        # **The node READ THE WAY THE DOCUMENT STATES IT** (:func:`_steps`): a local
        # ``$ref`` resolved and a conjunction folded at every depth, so the declaration
        # and the obligation that proves it agree about where the fact is.
        walked = _steps(relative, schema, stated)
        if walked is None:
            res.unproved.append(
                f"{one.pointer}/{one.keyword}: the pointer describes no instance "
                "location, so no drawn value can be placed at it"
            )
            continue
        node = walked[1]
        if not isinstance(node, Mapping) or one.keyword not in node:
            res.unproved.append(
                f"{one.pointer}/{one.keyword}: the document states no such keyword at "
                "that pointer, so there is no fact to prove dropped (section 9: never "
                "approximate on a keyword the walk itself inserted)"
            )
            continue
        path = tuple(segment for segment, _ in walked[0])
        # The node at this declaration's instance LOCATION, which every value class below
        # is drawn and graded UNDER where the pointer took a same-instance hop to reach
        # the fact: :func:`_conjoined` carries that sentence and :func:`_steps` carries
        # what the node is.  ``None`` where no hop was taken, and then nothing changes.
        host = walked[2]
        classes = value_classes(one.keyword, node)
        if not classes:
            res.unproved.append(
                f"{one.pointer}/{one.keyword}: no value class is derivable for this "
                "keyword, so the widening is declared and unproved"
            )
            continue
        # One slot per DECLARATION for :func:`_bases`'s demanded draw, because the demand
        # is a function of the pointer and every value class of one declaration shares it.
        demanded: list[Any] = []
        #: **The value at this location in every payload the accepts check already drew**,
        #: offered to each class before anything is drawn (:meth:`_Draws.one`).  A
        #: declaration's location is a free choice of base and that is already how the
        #: BASE is chosen; this is the same sentence about the VALUE, and
        #: :meth:`_Draws.one` carries the measurement that forced it -- a same-instance
        #: class at a root-located pointer is a whole-document draw the accepts check has
        #: already paid for and committed.
        at_the_location = [
            found for base in instances for found in _value_at(base, path)
        ]
        for label, restriction in classes:
            # Held like the other two, and for the same reading: a value class is a
            # RESTRICTION of the pair's node, so for the nodes that cost anything it is a
            # whole-document draw too -- 2.1 s on a 2,208,067-byte restriction of
            # ``core/async-response-data.json#/anyOf/28`` -- and the restriction is a
            # function of the declared pointer, the keyword and the class label
            # (:func:`value_classes`), which is the position.  A draw failure is unproved
            # and never a pass, and the REASON travels with the held answer so a replayed
            # run reports what a drawn one reports.
            drawn_class = _conjoined(host, restriction)
            held = draws.one(
                drawn_class,
                ("class", one.pointer, one.keyword, label),
                cf,
                borrowed=at_the_location,
            )
            if len(held) > 1:  # by LENGTH, never by the value: a document can admit null
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} could not be drawn: {held[1]}"
                )
                continue
            value = held[0]
            graded_against = _conjoined(host, node)
            if (
                conforms(graded_against, value, validator_cls=validator_for(graded_against))
                is False
            ):
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} drew {_dump(value)}, which the "
                    "document's own node refuses -- the restriction is not one"
                )
                continue
            # The base instance is a FREE CHOICE among the ones the accepts check already
            # drew, and :func:`_demanding` is the last resort where none of them can host
            # the location.  Two reasons are reported apart: nowhere to put the value, or
            # a placed payload the document refuses.
            payload = None
            refused = False
            for base in _bases(schema, path, instances, cf, demanded, draws):
                attempt = _placed(
                    _reached(schema, relative, base, cf, draws, stated), path, value
                )
                if attempt is None:
                    continue
                if conforms(schema, attempt, validator_cls=validator_cls) is False:
                    refused = True
                    continue
                payload = attempt
                break
            if payload is None:
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} placed at {list(path)} makes a "
                    "payload the document refuses, so it says nothing about the class"
                    if refused
                    else f"{one.pointer}/{one.keyword}: {label} has nowhere to go in the "
                    f"drawn instance at {list(path)}"
                )
                continue
            try:
                accept(payload)
            except ValidationError as e:
                err = e.errors()[0]
                res.narrowings.append(
                    f"{one.pointer}/{one.keyword}: {label} -- the document admits "
                    f"{_dump(value)} and the class refuses it "
                    f"({err['type']} at {err['loc']}: {err['msg']}); declared "
                    f"approximated at rung {one.rung}, {one.attribution}"
                )
                continue
            except Exception as e:
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} raised "
                    f"{type(e).__name__}: {e}"[:300]
                )
                continue
            res.accepted += 1
    res.drawn, res.replayed, res.borrowed = draws.drawn, draws.replayed, draws.borrowed
    return res


#: **The length floor ``hypothesis`` refuses outright**, read off the library's own
#: constant rather than restated: ``ListStrategy.__init__`` raises ``InvalidArgument``
#: -- "can never generate a value, because min_size is larger than Hypothesis supports"
#: -- for any ``min_size`` above it, and every string strategy is a collection strategy.
#: So this is a ceiling on the INSTRUMENT and says nothing about any document.  Imported
#: rather than written down (it is 8,192 on the pinned ``hypothesis``), for the reason
#: ``lower.const.LITERALS`` reads ``DataType.literals``'s annotation: a copy of a
#: library's limit goes stale at a version bump and the check then reports the wrong
#: reason for a value it cannot draw.
_DRAWABLE_SIZE: int = _HYPOTHESIS_BUFFER_SIZE

#: Every keyword that constrains a STRING's content rather than its length, plus the
#: whole-instance keywords a padded value could fail.  :func:`_padded_string` refuses to
#: build a value for a schema stating any of them, because the pad is "a" repeated and
#: nothing here knows what else would satisfy them.  Length is the only axis it answers.
_PAD_FORBIDS = frozenset(
    {
        "pattern",
        "format",
        "enum",
        "const",
        "contentMediaType",
        "contentEncoding",
        "not",
        "allOf",
        "anyOf",
        "oneOf",
        "if",
        "$ref",
    }
)


def _padded_string(schema: Mapping[str, Any]) -> str | None:
    """A string at a length floor :data:`_DRAWABLE_SIZE` puts out of ``hypothesis``'s
    reach, or ``None`` where this function has no business building one.

    **The gap this closes is the INSTRUMENT's and not a document's**, which is why the
    answer is to reach the value rather than to drop the class.  §8: "The draw COVERS the
    node's admissible space by constraint class; it does not sample it", and §9: "A check
    is exhaustive over the set of nodes it claims, or it does not exist."  A ``maxLength``
    class pins the length at the bound (:func:`value_classes`), and a bound above
    ``hypothesis``'s own buffer makes that pin undrawable -- so §8's accepts obligation
    reported ``unproved_widening`` for a widening that is perfectly real, on a limit of
    the drawing library.

    **It is gated by SHAPE and then checked by the DOCUMENT.**  The gate is
    :data:`_PAD_FORBIDS` plus a ``type`` that admits a string: a repeated character
    satisfies a node whose only string-applicable statements are its two length bounds,
    and this function declines every other node rather than guessing.  The check is
    :func:`check_widening`'s own, which validates the value against the document's node
    AND against the whole document before it counts -- so a value this builds wrongly is
    reported ``unproved``, never passed.  Two independent gates, and the second is the
    document's own validator.

    Measured over the 1,054 portable documents: **one** declaration reaches it,
    ``compliance/comply-test-controller-response.json``'s ``maxLength: 65536`` on a
    typeless node, which is the first bound-keyword widening the bundle has declared.
    Every other bound the obligation draws is inside ``hypothesis``'s reach and never
    arrives here.
    """
    floor = schema.get("minLength")
    if not isinstance(floor, int) or isinstance(floor, bool) or floor <= _DRAWABLE_SIZE:
        return None
    if _PAD_FORBIDS & set(schema):
        return None
    word = schema.get("type")
    if word is not None and word != "string" and not (
        isinstance(word, list) and "string" in word
    ):
        return None
    ceiling = schema.get("maxLength")
    if isinstance(ceiling, int) and ceiling < floor:
        return None
    return "a" * floor


def one_instance(schema: Mapping[str, Any], custom_formats: Mapping[str, Any]) -> Any:
    """ONE value the schema admits.

    ``hypothesis``'s ``example()`` is not available outside a test, so this runs the same
    ``given`` machinery :func:`check_accepts` runs, with one example, and keeps the first
    value.  ``derandomize`` is on in :data:`_SETTINGS`, so the value is the same on every
    run -- which is what makes a narrowing this check reports reproducible from the report.

    :func:`_padded_string` is asked FIRST and answers for one shape only: a length floor
    the library refuses to draw at all.  Its docstring carries the reasoning and the
    gates; everything else is ``hypothesis``'s as it always was.
    """
    padded = _padded_string(schema)
    if padded is not None:
        return padded
    drawn: list[Any] = []

    def body(instance: Any) -> None:
        drawn.append(instance)

    with (
        canonicalisation_shared_within_one_call(),
        validator_classes_shared_within_one_call(),
        #: **AND THE SAME RULE REACHES EVERY DERIVED DRAW, which is the measured half of
        #: the row rather than a tidiness.**  Two of the four pairs §8's residue names --
        #: ``creative/sync-creatives-response.json#`` and
        #: ``media-buy/get-media-buys-response.json#`` -- draw in 0.13 s and 0.03 s in
        #: ``check_accepts`` and were cut in ``check_widening``, one check further on,
        #: inside the same library call.  Every derived draw in this module arrives here:
        #: :meth:`_Draws._draw` for a widening's proving value, :meth:`Fixtures.value` for
        #: a frontier pin and :meth:`Fixtures._derived` for a referenced document's
        #: fixture.  One seam, so reading 2 cannot stay blocked where reading 1 is not.
        a_combinator_is_covered_and_never_enumerated(),
    ):
        run = given(instance=strategy(dict(schema), dict(custom_formats)))(body)
        settings(max_examples=1, phases=[Phase.explicit, Phase.generate], **_SETTINGS)(run)()
    if not drawn:
        raise HypothesisException("the strategy produced no instance")
    return drawn[0]


def _why(e: BaseException) -> str:
    """``hypothesis``'s own reason, up to the point where it starts advising.

    ``Unsatisfiable``'s message is the reason followed by advice -- *"Try making your
    filters or assumes less strict, or rewrite using strategy parameters..."* -- and
    the advice is for whoever wrote the test, not a fact about the document.  The
    reason half carries the number this report needs (*"459 of 459 test cases failed
    a .filter() or assume() condition"*), so the cut keeps the measurement and drops
    the boilerplate that was pushing it past the truncation.
    """
    return f"{type(e).__name__}: {str(e).split(' Try making')[0].strip()}"[:200]


def _dump(x: Any) -> str:
    try:
        return json.dumps(x, default=str)[:600]
    except Exception:
        return repr(x)[:600]


# --------------------------------------------------------------------------- #
# the document-side reading: what the document STATES at a pointer
# --------------------------------------------------------------------------- #
#: The facts the document-side FOLDS range over: a composed conjunct's and a union
#: branch agreement's -- **DERIVED from ``codegen.keywords``, never written here.**
#:
#: ``keywords.rendered_at`` is the set and ``keywords.TABLE`` the order, because a
#: hand-written list beside a fold is the one way a reading can be complete with respect
#: to itself and blind to everything beyond it: a keyword missing from it is a keyword
#: the fold silently refuses to carry across an ``allOf``, and the walk that then looks
#: for it at the composed pointer does not find it.
#:
#: At ROOT, which is the position those readings are taken at: a conjunct applies to the
#: same instance as the node it composes, and a branch of a root union is read under the
#: root's own siblings, so both are the node's own position and ROOT is the one every
#: pair is entered at.
#:
#: ``title`` is absent, and it is the table that says so: §6's row ends "Never
#: rendered."  pydantic derives one for every class and every property and the documents
#: carry one only at a root, so it is a name the compiler makes up rather than a fact
#: about a value.
FOLDED_FACTS = tuple(k for k in keywords.TABLE if k in keywords.rendered_at(Position.ROOT))


# --------------------------------------------------------------------------- #
# section 7's declaration, read off the artifact as a CONSUMER reads it
# --------------------------------------------------------------------------- #
#: A site: the document, the pointer, and the keyword whose fact is dropped.  The key
#: section 8's declaration audit ranges over, and the key ``codegen.attribution``'s
#: registry is already keyed by -- one spelling of an approximation's ADDRESS, so the two
#: never have to be reconciled.
Site = tuple[str, str, str]


def site_of(declared: Approximation) -> Site:
    return (declared.document, declared.pointer, declared.keyword)


def declarations_of(subject: Any) -> tuple[Approximation, ...]:
    """Section 7's ``__adcp_approximations__``, off a class or off a module.

    Section 9 forbids the verifier the walk, so this is the whole of how a declaration
    reaches the grader: "``render.py`` writes ``__adcp_approximations__`` onto the class,
    the root model or the enumeration, and beside the module for an alias ... and
    ``verify/`` reads it as a consumer reads any other class attribute."  ONE function for
    both, because ``vars()`` answers for a class and for a module alike.

    **``vars`` and not ``getattr``, so an INHERITED declaration is not read as this
    class's own.**  A union branch subclasses its base, and the base is at ``#`` and so
    declares everything in the document (``render.declared_at``'s containment rule); read
    through ``getattr`` a branch would claim its base's declarations and the equality would
    pass over a widening nothing at that branch widened.  ``graded()`` already draws the
    same line for ``__adcp_schema__`` and for the same reason.
    """
    found = vars(subject).get(APPROXIMATIONS, ())
    return tuple(found)


def composed_declarations(subject: Any) -> tuple[Approximation, ...]:
    """:func:`declarations_of`, plus every declaration an INLINED document states.

    **§8 sentence 2's other half, and it is the half that had no reader**
    (``adcp-client-python-wvod``, ``-szfx``).  ``emit.declared_once`` states the rule in
    full: "An approximation's identity is ``(stating document, stating pointer,
    keyword)``, and every inlined occurrence resolves to it -- **which is a reader's job
    and not a declaration per occurrence**."  :func:`declarations_of` is the reader and it
    did only the first part: it reads what the class's own module declared, and a fact the
    pair's COMPOSED document states because a ``$ref`` inlined it was declared once, in
    the target's module, where nothing at this pair could see it.

    Measured over the 37 pairs the undeclared check reddened: 11 of them are exactly that
    shape.  ``core/assets/url-asset.json#/properties/macro_declarations/items`` is
    ``MacroDeclarationsItem(MacroDeclaration)``, its node is
    ``{"allOf": [{"$ref": ".../core/macro-declaration.json"}, {...}]}``, and the 15
    conditionals its grade is put to are ``core/macro-declaration.json``'s -- declared
    there, at ``#/allOf/4`` and its siblings, and unknown here.  The class admitted
    ``{"encoding": {"depth": 0}, "required": true, ...}``, which the document refuses at
    ``allOf/0/allOf/4/then/properties/required/const``: the fact IS declared, and the pair
    could not read the declaration.

    **A BASE IN ANOTHER DOCUMENT IS AN INLINED OCCURRENCE, and a base in the SAME
    document is not.**  That is the whole of the gate, and it is what keeps
    :func:`declarations_of`'s own rule intact: a union branch subclasses a base at ``#``
    of its own document, so "read through ``getattr`` a branch would claim its base's
    declarations" -- and ``render.declared_at``'s containment rule has already carried
    every one of those onto the branch that can reach it, by a prefix test on the pointer.
    Nothing here adds to that.  What it adds is the hop containment CANNOT make: across a
    document boundary, where a prefix test on a pointer means nothing because the two
    pointers are in different spaces.

    **The keywords and NOT the obligation.**  ``check_pair`` hands :func:`check_refuses`
    the KEYWORDS of this set, because §2's rule in that direction is a comparison of
    keywords; it hands :func:`check_widening` ``pair.declared`` -- the pair's own -- and
    must keep doing so, because that obligation walks the declaration's pointer FROM this
    pair's node, and a pointer in another document's space describes no location it can
    reach.  One set per question, which is the division those two functions already are.
    """
    out = list(declarations_of(subject))
    #: ``vars`` on both sides, for :func:`declarations_of`'s reason read about the OTHER
    #: class attribute: an inherited ``__adcp_schema__`` is the base's node and not this
    #: class's, so a subject with none of its own has no document to compare against and
    #: takes the empty answer rather than its base's.  ``graded()`` draws the same line.
    document = getattr(vars(subject).get("__adcp_schema__"), "document", None)
    if document is None:
        return tuple(out)
    #: **A UNION BASE REACHES THE INLINED DOCUMENT THROUGH ITS BRANCHES**, so the branches
    #: are walked beside the MRO.  §5's DISTRIBUTION clause is why: where the ``$ref``
    #: target is a union ROOT, the node "is a union whose branches each take one of the
    #: target's branches as a base and add the node's own fields" -- so the base class
    #: subclasses nothing of the target and its cross-document hop is one level down.
    #: Measured at ``adagents.json#/oneOf/1/properties/formats/items``: the base is
    #: ``FormatsItem(BranchDispatchMixin, AdCPBaseModel)``, the 16 branches each subclass a
    #: class of ``core/product-format-declaration.json``, and the three conditionals its
    #: grade is put to are that document's own ``#/allOf/{0,2,5}``.  §4 makes the base's
    #: instance one of its branches, so a fact every branch's document states is a fact at
    #: the base's node.
    #: ``vars`` for the branch list too, and for the reason the recursion found: a branch
    #: INHERITS ``_branch_models`` from the base it subclasses, so ``getattr`` on a branch
    #: answers with the base's tuple -- which contains that branch -- and a walk of it is
    #: a cycle.  A base declares its own (``render``'s ``UnionInstall``), so ``vars`` is
    #: the reading that answers "whose branches are these".
    branches = vars(subject).get("_branch_models", ())
    reach = [*getattr(subject, "__mro__", ())[1:]]
    for branch in branches:
        reach += [*getattr(branch, "__mro__", ())]
    for base in reach:
        there = vars(base).get("__adcp_schema__")
        if there is None or there.document == document:
            continue
        out += [one for one in declarations_of(base) if one not in out]
    return tuple(out)




def _silent_about_extras(node: Any) -> Any:
    """A MAPPING's ``additionalProperties: true``, read as the silence it is.

    **A reading THIS PIPELINE'S OWN OUTPUT forces, so §9 keeps it.**
    ``docs/plan/architecture.md`` §9 keeps "the readings this pipeline's own output
    forces" and names three of them -- a nested class hoisted to ``$defs``, D4's
    ``| None``, a type list rendered as a union.  Those three are EXAMPLES of the
    criterion and not the whole of it: §4's mapping row renders a property-less object as
    ``dict[K, V]``, and pydantic 2.13.5 has no spelling of ``dict[str, Any]`` that omits
    ``additionalProperties: true`` -- so the keyword is one of the two spellings a
    property-less object arrives in, and a reading that admits only one of them reads one
    node two ways.

    **The two spellings are ONE acceptance fact.**  draft-07's ``additionalProperties``
    constrains the keys a schema does not already declare, and ``true`` admits every one
    of them, which is what silence admits; the two schemas accept and refuse identical
    instances.  §2's "silence -> ``ignore``, ``true`` -> ``allow``" is a statement about
    PYDANTIC's retention of an extra key on a CLASS, not about a document's accepted set,
    and what this reading is about is the accepted set.

    **SCOPED TO A MAPPING -- a node that declares no ``properties`` -- and the scope is
    the whole of its correctness.**  On a node WITH ``properties`` the distinction is
    load-bearing exactly as §2 says, a store's extras are retained or ignored by it, and
    nothing here touches such a node.  What this replaces was a shape-blind
    ``keyword == "additionalProperties" and value is True``, justified by a one-site
    measurement of the delegated resolver's redundant-key drop -- a blanket predicate
    whose population nobody had split.  One blanket predicate is not replaced by
    another: the gate reads the node's own shape.

    ``additionalProperties: false`` is NOT touched.  It forbids what silence permits, so
    the two are different accepted sets, and reading the one as the other would hand the
    fold a node LOOSER than the document.  A TYPED value is not touched either -- it
    restricts the value schema, which silence does not.

    No ``type`` gate, because none is needed: for an object with no declared property the
    two spellings admit the same keys, and for a non-object the keyword constrains
    nothing either way.
    """
    # **"Declares no ``properties``" means an EMPTY map as well as an absent one**, which
    # is a difference in spelling and not in what the node admits: a document that
    # declares no property writes no ``properties`` key, and this pipeline's own rendering
    # of such a node writes ``properties: {}`` -- so a membership test reads one shape as
    # a mapping and the other as something else.  ``core/format-option-ref.json#`` is the
    # first node of the shape to emit (§14 step 9), a union base over a root that declares
    # no property of its own.  The gate is the docstring's own words and the direction is
    # unchanged -- ``false`` and a typed value are still untouched.
    if not isinstance(node, Mapping) or node.get("properties"):
        return node
    if node.get("additionalProperties") is not True:
        return node
    return {k: v for k, v in node.items() if k != "additionalProperties"}




#: The two combinators a union of types is spelled with, and BOTH are read,
#: because the DOCUMENT spells it both ways.  ``anyOf`` is the spelling §4 renders;
#: ``oneOf`` is the DOCUMENT's at 2 of this bundle's 3
#: fold positions (``creative/creative-feature-result.json#/properties/value``
#: and ``property/property-feature-value.json#/properties/value``, each
#: ``oneOf: [{"type": "boolean"}, {"type": "number"}, {"type": "string"}]``).
#: Reading only ``anyOf`` left those two unfolded, so the type list the document
#: spells there never reached the composed pointer -- the asymmetry
#: ``salesagent-j3k2l.33`` is about.
#:
#: **A ``oneOf`` of bare types is a type list because a value has exactly one
#: JSON type -- with one exception, gated below**: ``integer`` and ``number``
#: both admit ``5``, so a ``oneOf`` naming both REFUSES every integer while the
#: type list admits it.  That pair is the only overlap in draft-07's type
#: vocabulary, and ``true`` is ``boolean`` and not ``number`` in it.
_UNION_KEYWORDS = ("anyOf", "oneOf")


def _target(ref: Any, root: Any) -> Any:
    """The node a LOCAL ``$ref`` names, found by walking its POINTER from ``root``.

    **A pointer walk and not the last segment of the reference**, which is what
    this used to be: measured over all 1,054 portable documents of the bundle there
    are 405 local-``$ref`` sites, and 3 of them name a ``definitions`` section
    NESTED inside a property
    (``brand/get-brand-identity-response.json`` ->
    ``#/oneOf/0/properties/fonts/definitions/font_role``).  A last-segment lookup
    answers those 3 from whatever section happens to hold that key, silently, and
    the walk answers all 405 for the same amount of code.

    ``None`` for anything that does not resolve, which is the FAIL-SAFE direction:
    the caller leaves the node's own keys in place and folds in nothing, so a fact
    only the target states is ABSENT at the composed pointer and a declaration there
    is reported ``unproved``.  A reading that invented facts for an unresolvable
    reference would do the opposite -- it would prove a declaration against a node
    the document does not state.
    """
    if not isinstance(ref, str) or not ref.startswith("#"):
        return None
    try:
        target = at(root, ref[1:])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return target if isinstance(target, dict) else None


def _branch_target(member: Any, root: Any) -> Any:
    """A combinator MEMBER that is a bare local ``$ref``, read as the node it names.

    **The same reading :func:`_normalize` already takes at a NODE, taken one level in
    at a BRANCH, by the one function.**  §9's "a nested class
    hoisted to ``$defs``" is the reading: ``bundle.record`` inlines a REMOTE reference
    and leaves a LOCAL one as written, so the document spells a branch that is another
    node as a ``$ref`` -- and a reading
    applied at the node and not at the branch makes a branch state nothing where its
    document states a type, a ``required`` and a shape.  Measured: a root union whose
    first two branches are ``{"$ref": "#/definitions/ScalarBinding"}`` and
    ``{"$ref": "#/definitions/AssetPoolBinding"}``, each a ``type: object``, read
    without the hop as two SILENT branches -- so the ``type: object`` the document
    states at every branch was nowhere in the node this reading handed on.

    **ONE HOP, and the gate is that the branch is BARE.**  Measured over the records of
    all 1,054 portable documents there are 33 union branches that are a local ``$ref``,
    in 28 union nodes, and **all 33 carry no key beside the ``$ref``** -- so the gate
    costs no site and keeps the rule off a shape nobody showed it.  A branch with a
    sibling, and a target that is itself a reference, are both left as they are: no hop
    happens, the branch states no ``type`` word, so :func:`_type_list` declines and the
    node stays a combinator -- the fold carries NOTHING rather than a fact read off a
    node this reading guessed at.  The targets bear this out -- 3 of
    the 33 resolve to a node whose own content is a ``oneOf``, which states no ``type``,
    and that is exactly the answer the one hop gives.

    **AT AN ``allOf`` CONJUNCT TOO, which is why the parameter is a MEMBER and not a
    branch** (``adcp-client-python-fte``).  A branch and a conjunct are the same
    POSITION as far as this reading goes -- a member of a combinator list, written as a
    pointer because ``bundle.record`` leaves a local one as the document writes it -- and
    a conjunct is where the reading was missing: :func:`_composed` folds a conjunct's
    facts into the node it composes, so a conjunct left as a pointer states nothing in
    ``FOLDED_FACTS`` and folds to nothing -- and every fact the base declares is then
    absent from the composed node, at the root and at every pointer below it
    (``core/registry-event.json`` and ``core/account-identity-change-preview.json`` are
    two of the documents that compose through a local pointer).

    The two positions are gated the same way and the bundle says the gate costs nothing
    here either: there are **54 ``allOf`` conjuncts that are a local ``$ref``, one per
    ``allOf`` node, in 5 documents, and all 54 carry no key beside the ``$ref``**.  All
    54 resolve, 1 to a node carrying a union -- ``core/registry-event.json``'s
    ``#/$defs/publisherAdagentsPayload`` -- which :func:`_composed` keeps as the
    assertion it is rather than folding, exactly as it keeps a conjunct that spells its
    combinator inline.

    ``None`` from :func:`_target` is the same fail-safe: the member stays as written.
    """
    if not isinstance(member, dict) or set(member) != {"$ref"}:
        return member
    target = _target(member["$ref"], root)
    return member if target is None else target


def _conjoined_type(node: dict, kw: str, branches: list[dict]) -> tuple[dict, list[dict]]:
    """A ``type`` word BESIDE a union is conjoined into every branch, which is what
    draft-07 says it is.

    **A reading THIS PIPELINE'S OWN OUTPUT forces, so §9 keeps it** -- the emitter is
    what conjoins the word, through ``_base.applied_schema``, and nothing of the
    delegated resolver is involved.  Every branch of a draft-07 combinator is applied to
    the SAME instance, so a sibling ``type`` asserts about that instance too and a
    branch stating none of its own has it: ``{"type": "string", "anyOf": [{"format":
    "uri-template"}, ...]}`` and ``{"anyOf": [{"type": "string", "format":
    "uri-template"}, ...]}`` are one document said two ways.  **And the second is the way
    the EMITTER says it**: the document states the word once beside the union, and the
    emitter conjoins it into each branch -- ``_base.applied_schema``, which is the
    schema half's own reading of what a branch says, and ``lower.union.applied_type``
    is where the walk asks it.

    Without this fold the two readings of one document disagree about which node states
    the ``type``: the emitter put it on each branch and this reading would leave it on
    the node, so a declaration travelling with the branch cannot meet the keyword where
    it is looked for.  ``core/macro-bearing-url.json`` is the bundle's only graded node
    stating a ``type`` beside a union, and the first document to reach it
    (``salesagent-j3k2l.41``).

    **Conjoining DOWN and not hoisting up, and the keyword's own semantics is what
    decides it.**  Hoisting a word every branch states up to the node is a reading of
    AGREEMENT AMONG BRANCHES, and agreement is not what the keyword means: draft-07 puts
    a sibling's assertion on the instance each branch applies to, and the emitter puts it
    on each branch for exactly that reason (``_base.applied_schema``) -- so DOWN is the
    direction both the vocabulary and this pipeline's own rendering already go.
    Conjoining down fires on the SHAPE the keyword's own semantics name -- a ``type``
    word beside a combinator -- and so fires wherever that shape is.

    **KNOWN CEILING: the word stops being CARRIED to that node.**  This reading does not
    recurse into a branch, so a ``type`` moved into the branches is not a fact the
    composed node states, and a declaration whose pointer is the node ITSELF cannot be
    proved there: :func:`check_widening` finds "the document states no such keyword at
    that pointer" and the obligation stays ``unproved``.  What bounds it: the fold fires
    only where the node states a ``type`` BESIDE a union, 1 graded node in this bundle,
    and that node's accepted set is still graded by the accepts draw and the
    dump-and-revalidate against the document's own schema.  Closing it needs this reading
    to recurse into a union's branches, which is a reading of which branch answers which
    and is not this function's.
    """
    word = node.get("type")
    if not isinstance(word, str):
        return node, branches
    conjoined = [b if "type" in b else {**b, "type": word} for b in branches]
    return {k: v for k, v in node.items() if k != "type"} | {kw: conjoined}, conjoined


def _type_list(live: list[dict]) -> tuple[list[str], dict] | None:
    """A union of ARMS read back as the ``type`` LIST it spells, plus the per-arm facts.

    ``None`` where these branches are not a type list, and that is the FAIL-SAFE
    direction every gate below is in: the caller leaves the node as a combinator, it
    states no fact in ``FOLDED_FACTS``, and a declaration pointed at a keyword the lift
    would have put on the node is reported ``unproved`` rather than proved against a type
    list this reading invented.

    **This is the inverse of ``schema.parse``'s CUT, and it reads the same
    declaration.**  draft-07 applies a constraint keyword only to instances of the type
    it is defined for, so a node whose ``type`` is a list and which states ``minLength``
    means "``minLength`` on the string arm" -- which is the reading the walk makes when
    it cuts the node into one member per word (``keywords.ARM``), and pydantic has no
    spelling for the result but a union of the arms.  Lifting each arm's own keywords
    back onto the list is therefore not an approximation of the union: it is the
    document's own node, respelled.

    **The gates, and each is what makes the lift LOSSLESS rather than merely green.**

    * **Every branch states a ``type`` WORD of the vocabulary.**  A branch with no
      ``type`` of its own has no arm to be -- a bare ``$ref`` the hop could not resolve,
      a branch that is itself a combinator -- and a branch whose ``type`` is itself a
      list is not an arm either.  Read with ``get``, because a typeless branch reaches
      here: ``_normalize`` counts a branch as LIVE by its type not being ``null``, which
      a branch stating no type satisfies.
    * **The words are DISTINCT.**  A type LIST is a set of words -- ``multi_type``
      refuses a repeated one by name -- so two branches naming one type are a union of
      two differently-constrained instances of that type, which no type list expresses.
      Measured over all 1,054 portable documents: 0 of the bundle's 62 multi-type nodes
      repeats a word, so the gate costs no site and keeps the rule off a shape nobody
      showed it.
    * **Every key a branch carries beside ``type`` is one that word's ARM carries.**
      This is the whole of the lift's soundness and not a tidiness check: a keyword in
      the arm is ignored for every other type, so moving it to the node changes no
      accepted set, while a keyword that is NOT -- an ``enum``, a ``const``, a
      ``description`` -- applies to every instance or to none, and lifting it would state
      a fact about the other arms that the union does not.  So ``{"anyOf": [{"type":
      "object"}, {"type": "string", "enum": ["a"]}]}`` does not fold, and that is
      correct: as a type list it would refuse every object.
    * **And that key holds no SUBSCHEMA**, which is what keeps the lift off a branch that
      is a NODE IN ITS OWN RIGHT.  ``keywords.descends_at`` is the one descent column;
      a key in it holds a subschema, and §4 makes a branch holding one a CLASS or a
      ``list[X]`` -- a node the emitter renders, and declares at, by that branch's own
      pointer.  Lifting its keys onto the type list would move a fact off the pointer a
      declaration names and onto one it does not, which is a fold stating something
      neither the document nor the emitter says.  The shape is in the bundle:
      ``sponsored-intelligence/si-capabilities.json`` and its two session documents,
      whose ``modalities`` properties are a ``oneOf`` of a ``boolean`` and an OBJECT
      WITH ``properties``; ``brand/get-brand-identity-response.json``'s ``colors`` and
      ``fonts``; and ``core/creative-item.json``.
      A branch whose own content is a scalar CONSTRAINT has no such problem:
      D5's alias module puts the bound on the arm's own type, so the branch is
      ``{"type": "string", "minLength": 1}`` and the lift fires.
    * **No two branches lift the same key.**  ``integer`` and ``number`` share the
      numeric ARM, so a union of both carrying a ``minimum`` has two values for one
      position on the node and the lift has no answer; a repeated word is already gone
      by the gate above.  0 nodes of the bundle state a keyword two live arms carry.

    The subschema gate costs this bundle no site of the shape this exists for: measured
    over all 1,054 portable documents, the one multi-type node stating a keyword beside
    two live arms states ``minLength``, and the ``object`` arm with ``properties``
    (``core/delivery-metrics.json#/properties/quartile_data``) has ONE live arm and so
    takes the ``null`` fold instead.  A document whose type list puts ``properties`` on
    an object arm beside another live arm does not fold, so the keyword stays off the
    composed node and a declaration there reports ``unproved`` rather than being proved
    against a lift that moved it; closing that needs this reading to recurse into a
    union's branches -- the reading ``_conjoined_type``'s own ceiling names, and still
    not this function's.
    """
    words = [b.get("type") for b in live]
    if not all(isinstance(w, str) and w in keywords.ARM for w in words):
        return None
    if len(set(words)) != len(words):
        return None
    descends = keywords.descends_at(Position.ROOT)  # the ONE descent column, position-free
    arms: dict = {}
    for branch, word in zip(live, words, strict=True):
        # The branch is read the way the NODE is: ``additionalProperties: true`` on a
        # mapping that declares no property is the silence it is, by the one function
        # that says so -- and read HERE because the gate below asks what the branch
        # STATES, and a key stating nothing must not decide it.  §4's ``dict[K, V]``
        # row is why it can arrive at all: an ``object`` arm with no declared property
        # is a mapping, and the keyword and silence admit the same keys there.
        for key, value in _silent_about_extras(branch).items():
            if key == "type":
                continue
            if key not in keywords.ARM[word] or key in descends or key in arms:
                return None
            arms[key] = value
    return words, arms


def _normalize(
    node: Any,
    root: Any,
    depth: int = 0,
    *,
    declared_null: bool = False,
    null_is_absence: bool = True,
) -> dict:
    """One node for one position, written the way the DOCUMENT states it.

    **Every normalization below is a statement about one SPELLING of a fact**, and
    the spelling has to be read the way the EMITTER read it (``salesagent-j3k2l.32``
    and ``.33``): the emitter declares an approximation at the pointer its own
    reading puts the fact at, so a reading here that respells the node differently
    puts the document's keyword at one node and the declaration at another -- and
    the obligation then reports "the document states no such keyword at that
    pointer" for a fact the document plainly states.

    ``root`` is the schema a ``$ref`` resolves against: the whole resolved
    DOCUMENT, because a nested pair's node is a sub-node and
    ``#/definitions/x`` is relative to the document root, which is why
    :class:`Pair` carries the document and not only the node.

    **Every normalization left here is a reading THIS PIPELINE'S OWN OUTPUT forces,
    which is the half ``docs/plan/architecture.md`` §9 keeps.**  The
    one-member-``enum`` respelling that stood first in this list is
    deleted with the delegated resolver: ``canonicalish`` rewrote ``enum: [v]`` into
    ``const: v`` while inlining a remote reference, so one accepted set arrived in two
    spellings depending on whether the document stated it or referenced one that did.
    ``bundle.record`` copies the
    document's own spelling, and §4's enumeration row renders an ``enum`` for an
    ``enum`` node and a ``Literal`` -- so a ``const`` -- for a ``const`` one, so the
    node arrives with the keyword the document writes and there is nothing to fold.

    * **A local ``$ref``.**  A nested object is a nested CLASS and a
      cross-document reference is an IMPORT (P2), so pydantic hoists both into
      ``$defs`` and references them.  ``codegen.bundle.record`` inlines a REMOTE
      reference and leaves a LOCAL one as written, so the document says ``$ref`` too,
      and this is the "nested class hoisted to ``$defs``" reading §9 names.

      **AT A UNION BRANCH TOO, and that is one reading in one place rather than a
      second rule.**  The reading was taken at the node and not at the branches inside
      a combinator, so a branch that is a bare local ``$ref`` stated nothing and a root
      union's branches read as typeless where the document
      types every one of them -- ``core/requirements/catalog-field-binding.json#``, which
      states ``type: object`` at each of its three branches and spells every one of them
      as a pointer.  :func:`_branch_target` carries the hop and the measurement that
      scopes it.
    * **An ``anyOf`` with a ``null`` branch, AND WHICH OF THE TWO THINGS IT IS.**
      D4 renders an optional property ``T | None``, because the attribute holds
      ``None`` for an omitted key.  §4 states that as a union; the document
      states the type and leaves presence to ``required``.  Unwrapping the null
      branch reads the position the way the document writes it.

      **A document that DECLARES ``null`` spells the same union, and unwrapping
      that one erases the document's own fact.**  ``["string", "null"]`` is a TYPE
      fact the document states, and unwrapping it leaves a node that no longer
      states the ``null`` -- so a declaration at that node's ``type`` would meet a
      reading that has dropped half of what the document says.  D4 renders
      ``str | None`` for an optional ``{"type": "string"}`` as well, which is why
      ``lower.containers.multi_type``
      refuses a ``null`` arm by name rather than emit a rendering that stands for two
      different documents.

      So the distinction comes from ``declared_null``, which the caller states:
      :func:`_settled` is reading the DOCUMENT and passes ``True``, so a ``null``
      branch there is the document's own type fact and is folded INTO the type list;
      where it is not declared the branch is
      presence and is unwrapped exactly as before.  Measured on
      ``core/webhook-activity-record.json``'s ``completed_at``
      (``["string", "null"]``, ``format: date-time``),
      ``core/delivery-metrics.json``'s ``completion_rate`` and
      ``core/error.json``'s discriminator ``value``
      (``["string", "number", "boolean", "null"]``).

      **``null_is_absence`` is the OTHER half of that same question.**  D4 renders
      ``None`` for an OPTIONAL property; a REQUIRED one has no default, so at a
      position the parent DEMANDS there is no absence for a ``null`` branch to
      spell and the branch can only be a type fact.  Unwrapping it regardless made
      those two cases one cell again from the other direction -- a required
      ``[boolean, number, string]`` read exactly as an optional one.  So the null is
      folded into the
      ``type`` unless the caller says the position really can be absent, and a
      caller that knows reads that off the parent document's ``required``.
      KNOWN CEILING: the axis is "the parent demands this
      key", which cannot tell an OPTIONAL property from a position with no
      presence question at all (an ``items``, a root, a mapping's value), so a
      null branch at one of those is read as absence and the document's ``null`` is
      not carried to the composed node -- a declaration at that node's ``type``
      cannot be proved there.  Closing that needs a
      third state on the axis rather than a wider rule here.
    * **A union of ARMS is a ``type`` LIST.**  draft-07 lets a node name
      several types at once and pydantic has no spelling for that but a union, so
      ``{"type": ["number", "string"]}`` comes back
      ``{"anyOf": [{"type": "number"}, {"type": "string"}]}`` -- one fact in two
      spellings, and without this fold the node this reading hands on states no
      ``type`` at all.  ``error-details/conflict.json``'s two
      multi-type properties were the first of the shape in the emitted
      population.

      **A BRANCH CARRIES ITS OWN CONSTRAINTS, and the lift is the CUT'S INVERSE.**
      This read "the fold applies only where EVERY branch is a bare ``{"type":
      X}``", and that reading carried NOTHING at the bundle's one node stating a
      keyword beside a type list with two live arms -- ``core/attestation-reference.json``
      at ``/properties/embedded_credential/properties/value``, ``["object",
      "string"]`` with ``minLength: 1`` -- and carried nothing transitively, because 43
      documents reference that one.  The walk CUTS such a node into one arm per
      word, each arm carrying only what that word carries (``keywords.ARM``), and
      D5's alias module puts the bound on the arm's own type.  Lifting the arms'
      keywords back onto the list therefore restates the document's own node and
      moves no fact; folding to the type list and DROPPING the constraint would be
      the widening this module's folds exist not to be, which is why the earlier
      reading carried nothing rather than hand on a looser node.
      :func:`_type_list` carries the lift, its four
      gates, and the KNOWN CEILING for a branch with an annotation.
    * **The outer keys win.**  ``default`` and ``description`` sit outside the
      ``anyOf`` and the type facts inside the branch.

      **KNOWN CEILING, and the measurement that bounds it.**  Draft-07 IGNORES
      every sibling of a ``$ref``, so a document stating
      ``{"$ref": X, "minimum": 5}`` means X alone, and letting the sibling win
      there would make this reading state a bound the document does not.  What
      bounds it is the bundle: of the 405 local-``$ref`` sites the only keys ever
      beside one are ``description`` (58) and ``deprecated`` (4), so **0 sites
      carry a constraint keyword beside a local ``$ref``** and the rule's unsafe
      half has no population.  ``description`` winning is not optional in the
      other direction -- the compiler transcribes the sibling onto the field, so
      the sibling is the one the emitter read and a reading preferring the
      target's would disagree with it at 58 sites.  The upgrade path, if a document
      ever states a constraint
      beside a local ``$ref``, is to keep only the keys outside ``FOLDED_FACTS``.
    """
    if depth > 16 or not isinstance(node, dict):  # a self-referential $defs chain
        return node if isinstance(node, dict) else {}
    if "$ref" in node:
        target = _target(node["$ref"], root)
        # ``declared_null`` deliberately does NOT travel through here.  It would be an
        # arm with no site: measured over the graded population, 5 positions have a
        # document declaring ``null`` and **all 5 spell it as an ``anyOf``, 0 as a
        # ``$ref``** -- a pointer names a nested CLASS, and a class is not a
        # null arm.  A derivation matching nothing is green for free, and this one
        # also fails SAFE if such a position ever appears: the fold does not fire, so
        # the document's own ``null`` is not carried past the reference, and the fact
        # is ABSENT at the composed pointer rather than invented there.
        outer = {k: v for k, v in node.items() if k != "$ref"}
        return {**_normalize(target, root, depth + 1), **outer} if target is not None else outer
    for kw in _UNION_KEYWORDS:
        stated = node.get(kw)
        if not (isinstance(stated, list) and stated and all(isinstance(b, dict) for b in stated)):
            continue
        # The branches as the DOCUMENT writes them.  They were read through the
        # delegated resolver's finite-type rewrite here, because that resolver wrote a
        # finite type out as its members WHILE INLINING and so gave one union two
        # shapes depending on whether the document stated it or referenced one that
        # did: the three documents referencing
        # ``creative/creative-feature-result.json#/properties/value`` carried
        # ``oneOf: [{"enum": [false, true]}, ...]`` where the two that state it carry
        # ``{"type": "boolean"}``.  ``bundle.record`` copies the branch, so all five
        # now carry the one shape and the rewrite has nothing to undo (§9).
        #
        # A branch that is a bare local ``$ref`` is read as the node it NAMES
        # (:func:`_branch_target`) -- the same reading this function already takes at a
        # node, taken one level in, and taken ONCE here, before anything reads a
        # branch.  The node is rebuilt with the resolved branches below, so every reader
        # downstream -- :func:`_conjoined_type` and the two fold arms, which ask each
        # branch for its ``type`` word -- sees what the branch states rather than the
        # pointer it states it through.
        branches = [_branch_target(b, root) for b in stated]
        node, branches = _conjoined_type(node, kw, branches)
        # ``_conjoined_type`` rebuilds the node when a sibling ``type`` conjoins and
        # leaves it alone otherwise, so the resolved branches are put back here: a
        # fall-through returns ``node``, and returning it with the branches AS WRITTEN
        # would make this reading reach the fold arms and nothing else.
        node = {**node, kw: branches}
        live = [b for b in branches if b.get("type") != "null"]
        nulls = [b for b in branches if b.get("type") == "null"]
        outer = {k: v for k, v in node.items() if k != kw}
        # The null branch is a TYPE FACT unless the position can really be absent:
        # the document declares it, or it sits at a key the parent DEMANDS and so
        # has no absence to spell.  Either way it is folded INTO the type rather
        # than unwrapped.
        keep_null = declared_null or not null_is_absence
        if len(nulls) == 1 and len(live) == 1:
            one = {**_normalize(live[0], root, depth + 1), **outer}
            if not keep_null:
                return one
            kind = one.get("type")
            # The null is a TYPE FACT here, so the fold has to carry it forward or
            # not fire.  Returning ``one`` without it would drop the document's own
            # ``null`` and leave a node that states the type the document states
            # without the arm it also states, which is the conflation
            # ``test_a_declared_null_is_never_read_as_absence`` exists to redden on.
            # A live branch with no ``type`` word of its own has nowhere to put it, so
            # that case does not fold: the node stays a combinator and states no fact
            # in ``FOLDED_FACTS``, which leaves the fact absent at the composed pointer
            # instead of restating it wrong.
            if isinstance(kind, str):
                return {**one, "type": [kind, "null"]}
            if isinstance(kind, list) and "null" in kind:
                return one
            return node
        folded = _type_list(live) if len(nulls) <= 1 and len(live) > 1 else None
        if folded is not None:
            kinds, arms = folded
            if kw == "oneOf" and {"integer", "number"} <= set(kinds):
                # The one overlap in draft-07's type vocabulary: both branches admit
                # ``5``, so this ``oneOf`` refuses every integer and the type list
                # admits it.  Folding would state a fact the document does not.
                return node
            # The per-arm facts sit between the type list and the OUTER keys, because
            # outer still wins: a ``default`` or a ``description`` beside the combinator
            # is the node's own and an arm cannot carry one anyway (``keywords.ARM``).
            return {
                "type": [*kinds, "null"] if keep_null and nulls else kinds,
                **arms,
                **outer,
            }
        # **DELETED WITH THE DELEGATED RESOLVER (§9): the same-title lift.**  It fired
        # where every branch of a combinator carried the SAME ``title``, which was the
        # signature of ``canonicalish`` rewriting a root ``if``/``then`` into an
        # ``anyOf`` of the two cases and copying the node's own ``title`` into both.
        # The pair it existed for -- ``media-buy/sync-catalogs-request.json`` at
        # ``/properties/item_availability_updates/items``, which references
        # ``core/catalog-item-availability-update.json``, whose root carries
        # ``if``/``then`` -- now reads the target's own node, with its ``properties``,
        # its ``required``, its ``type`` and its ``description`` where the document
        # writes them, so there are no agreed facts to lift back up.  ``_agreed`` and
        # ``_widest`` were its only readers and go with it.
    return node


#: How deep an ``allOf`` chain ``_composed`` folds before it stops folding.  Same
#: constant and same shape as ``_normalize``'s, deliberately: two instruments that
#: cut a traversal at different places disagree about node identity for no reason
#: anyone can read off either of them (``docs/plan/rebuild-plan.md`` §9).
_COMPOSE_DEPTH = 16

#: The answer :func:`_tighter` gives for a keyword whose two values it cannot order.
#: A sentinel rather than ``None``, because ``None`` is a legal JSON value and a
#: keyword can hold it -- ``default: null`` is in the bundle.
_UNDECIDED = object()

#: The ordering keywords of :data:`FOLDED_FACTS`, and which direction is TIGHTER: ``max``
#: for a floor (the higher of two minima binds) and ``min`` for a ceiling -- READ OFF the
#: declaration (:data:`keywords.RANGES`, :func:`keywords.pins_a_floor`) rather than listed.
#:
#: **It was eight entries and the walk's own copy was ten** (``adcp-client-python-3be.8``):
#: ``compiler._narrower`` ordered ``minProperties``/``maxProperties`` and this did not, so a
#: conjunct narrowing a property count was NARROWER to the walk and ``_UNDECIDED`` to the
#: grader -- the divergence §9 forbids in its own words, "both halves must read the same
#: declaration or the grade means nothing".  Closing it changes nothing in this bundle and
#: that is measured rather than assumed: **0 nodes state ``minProperties`` or
#: ``maxProperties`` on both a node and one of its ``allOf`` conjuncts**, over all 1,054
#: portable documents (48 ``minProperties`` sites and 19 ``maxProperties`` sites in total),
#: so the two entries the fold gains have no pair to decide today and the fold was taking
#: the node's own by the ``_UNDECIDED`` path anyway.
_TIGHTER_BOUND = {
    keyword: (max if keywords.pins_a_floor(keyword) else min)
    for keyword in keywords.FLOORS | keywords.CEILINGS
}


def _in_vocabulary(value: Any, members: Any) -> bool:
    """Is ``value`` one of ``members``, where ``members`` is a stated ``enum``?

    ``False`` for anything that is not a list, which is what makes the vocabulary-axis
    collapse in :func:`_composed` conditional on the two actually agreeing: a ``const``
    OUTSIDE a composed ``enum`` is an EMPTY intersection, and dropping the vocabulary
    there would read the composed node as admitting one value where the document
    admits none.  The empty intersection is the emitter's refusal to make, so this
    leaves both facts standing rather than settling an axis the document does not.
    """
    return isinstance(members, list) and any(value == member for member in members)


def _one_vocabulary(node: dict, conjunct: dict) -> tuple[dict, dict]:
    """``node`` and ``conjunct`` with ONE statement left on the vocabulary axis.

    ``const: v`` and ``enum: [...v...]`` state the same kind of fact about an instance,
    so the intersection of the two is the PIN and the vocabulary is not a second fact
    beside it.  Whichever view supplies the pin, the other's vocabulary goes -- so the
    gap-fill below cannot leave a merged node carrying both, which is a shape no
    document states.

    Measured on ``core/canonical-media-buy-action.json``, whose branch states
    ``{"const": "control_media_buy"}`` for ``task`` over a composed base's three-member
    ``enum``: keeping both left the merged node stating an ``enum`` beside the ``const``
    that pins it, at each of the 3 branches -- a shape no document states, and §4
    renders a ``Literal`` for it.

    Gated on the pin being IN the vocabulary.  A ``const`` outside it is an EMPTY
    intersection -- the emitter's refusal to make -- and dropping the vocabulary there
    would read the merged node as admitting one value where the document admits none,
    so both facts are left standing.
    """
    if "const" in conjunct and _in_vocabulary(conjunct["const"], node.get("enum")):
        return {k: v for k, v in node.items() if k != "enum"}, conjunct
    if "const" in node and _in_vocabulary(node["const"], conjunct.get("enum")):
        return node, {k: v for k, v in conjunct.items() if k != "enum"}
    return node, conjunct


def _vocabulary(view: Any) -> list | None:
    """The value set ``view`` states, or ``None`` where it states none.

    A ``const`` is read as the one-member set it is, which is the same rewrite
    ``codegen.intersect.as_enum`` makes when it lowers a node, and for the same reason: a
    pin and a vocabulary are one axis, so one reader answers ``const`` against ``const``,
    ``const`` against ``enum`` and ``enum`` against ``enum``.  Read BEFORE
    :func:`_one_vocabulary` collapses the axis, because that collapse drops one of the
    two statements and the question here is which VIEW made the surviving one.
    """
    if not isinstance(view, dict):
        return None
    if "const" in view:
        return [view["const"]]
    members = view.get("enum")
    return members if isinstance(members, list) else None


def _inside(inner: list | None, outer: list | None) -> bool:
    """Is ``inner`` a STRICT subset of ``outer``, both read as stated value sets?

    Strictness is "every member of ``inner`` is in ``outer`` and some member of
    ``outer`` is not in ``inner``" and not a length comparison, so a duplicate member --
    which the ``enum`` row refuses at emission but which this reader meets before any
    such check -- cannot make a set read as smaller than the one it equals.
    """
    if inner is None or outer is None:
        return False
    return all(_in_vocabulary(m, outer) for m in inner) and any(
        not _in_vocabulary(m, inner) for m in outer
    )


def _described_by_the_conjunct(node: dict, conjunct: dict) -> dict:
    """``node`` with its ``description`` stood down where the CONJUNCT states the one.

    **The view that states the composed node's VALUE SET states its description**, which
    is ``docs/plan/rebuild-plan.md`` §6's description row read where §2's intersection
    puts it: "a composed base's loses to the document's own".  Under ``allOf`` the
    composed node admits the intersection, and where one view's vocabulary is strictly
    inside the other's the intersection IS that view's declaration -- so that view is
    the one the document states at this pointer, and its description comes with it.
    The EMITTER reads it the same way one step earlier: ``intersect.intersection`` decides
    the field from the narrowing declaration and carries that declaration's annotations
    (``intersect.RENDERED``), so the element type is the narrowing ``$ref``'s class and
    its docstring is that target's description.  §9 keeps the two spellings apart and
    requires them to agree; this is the document half of the one in the compiler.

    Measured on ``core/media-buy-frequency-cap-requirement.json`` at
    ``/properties/supported_control_modes/items``, whose base declares the element as
    ``enums/frequency-cap-control-mode.json`` (three members, "A supported package
    frequency-cap control shape.") and whose own overlay narrows it to
    ``enums/media-buy-frequency-cap-control-mode.json`` (one member, "The aggregate
    MediaBuy frequency-cap control shape supported in 3.2."): the merged node took the
    conjunct's ``enum`` by :func:`_tighter` and kept the BASE's description, so the
    composed node stated the NARROWING declaration's value set beside the WIDER one's
    description -- a pair of facts no single view of the document states.
    ``core/media-buy-support-requirements.json`` reaches the same node
    through a ``$ref``.

    **Three gates, and each one has to be here.**

    * **The conjunct must state a description.**  Silence inherits (§6 clause 3), so a
      narrowing conjunct that says nothing to a reader leaves the base's description
      standing rather than deleting it.  Measured: ``core/canonical-media-buy-action.json``
      narrows ``task`` to a ``const`` and states no description of its own, and dropping
      the base's there would leave the composed node describing nothing where §6 clause 3
      says the base's description is what a reader inherits.
    * **The conjunct's set must be INSIDE the node's.**  Where the node is the narrower
      view the node already states the composed declaration and its own description is
      the answer -- 3 sites on this tree, each a response's own ``status`` pinned to one
      member of the task-status vocabulary ``core/protocol-envelope.json`` states.
    * **STRICTLY inside.**  Two views stating the same value set state the same
      declaration, and then §6's default stands: the node's own wins.  That is also
      where the other 277 sites land -- two descriptions differing on no narrowing at
      all -- and the gap-fill's own measurement is the reason: at a
      pointer the document declares itself, the node IS the document's own.

    The axis is the VOCABULARY and not every keyword :func:`_tighter` can order.  A
    conjunct narrowing a BOUND beside a description of its own has **0 sites** on this
    tree, and so does one widening a vocabulary; an arm for either would be a derivation
    matching nothing (``restatement``'s own precedent).  ``default`` is left out for the
    same measurement: the 7 sites where two views default a property differently are
    all at ``neither``, where this rule does not fire.
    """
    if "description" not in conjunct:
        return node
    if not _inside(_vocabulary(conjunct), _vocabulary(node)):
        return node
    return {k: v for k, v in node.items() if k != "description"}


def _tighter(keyword: str, node: Any, conjunct: Any) -> Any:
    """The INTERSECTION of two views of one keyword, or :data:`_UNDECIDED`.

    Section 2's rule, in the two spellings it names for a keyword both views state: "an enum is
    the intersection of the members, a bound is the tighter one".  Anything else is
    ``_UNDECIDED`` and the caller keeps the node's own, which is the behaviour this
    replaced and the safe direction: the node's own is the LOOSER of the two readings, so
    a value class derived from it can draw a value the document itself refuses, which
    :func:`check_widening` reports as ``unproved`` -- a visible failure, where a silently
    tightened reading would prove a declaration against a node the document does not state.
    """
    if node == conjunct:
        return node
    if keyword == "enum" and isinstance(node, list) and isinstance(conjunct, list):
        both = [member for member in node if _in_vocabulary(member, conjunct)]
        # An EMPTY intersection is a document that admits nothing at this node, which
        # is the emitter's refusal to make and not a fact to hand the fold: the
        # node's own is kept so the obligation reports rather than drawing against a
        # vocabulary no instance satisfies.
        return both or _UNDECIDED
    if keyword in _TIGHTER_BOUND:
        if isinstance(node, bool) or isinstance(conjunct, bool):
            return _UNDECIDED  # draft-04's boolean exclusiveMinimum, a different keyword
        if not isinstance(node, int | float) or not isinstance(conjunct, int | float):
            return _UNDECIDED
        return _TIGHTER_BOUND[keyword](node, conjunct)
    return _UNDECIDED


def _composed(doc: Any, root: Any, depth: int = 0) -> Any:
    """The document's node with every ``allOf`` conjunct's facts folded in.

    **``allOf`` conjoins, so a conjunct's unconditional facts ARE the
    document's.**  Draft-07 applies every conjunct to the whole instance, and a
    composing class flattens every inherited field into its own ``properties``
    and its own ``required`` -- so a reading that left a conjunct's facts where the
    document writes them would put them at a different pointer from the one the
    EMITTER declares them at.  Measured on a root stating ``required: ['label']``
    beside a conjunct requiring ``kind``: unfolded, the node demands one name where
    the document demands two, ``/properties/kind`` has no node at all, and the
    conjunct's own ``maximum`` sits one ``allOf`` hop away from every pointer a
    declaration names.

    Three rules, and each is the one the vocabulary forces:

    * **``required`` composes by union.**  It is a set of names and every
      conjunct contributes its own.
    * **``properties`` composes by key.**  A key two views declare is not merged
      here: the conjunct's declaration is stashed as an ``allOf`` on the merged
      node, and this function folds it again when the walk descends
      (:func:`_steps` settles every node on the way).  One mechanism for
      composition at every depth rather than a second rule for properties.
    * **A CONSTRAINING fact two views state composes to the intersection**
      (:func:`_tighter`), and one only the conjunct states fills a gap.  That is
      §2 in its own words -- "an enum is the intersection of the members, a bound
      is the tighter one" -- and the keyword this function cannot order keeps the
      node's, which is a looser expectation and so a visible false failure rather
      than a pair that passes for nothing.
    * **A ``description`` two views state goes with the view that states the
      composed VALUE SET** (:func:`_described_by_the_conjunct`), which is §6's
      "a composed base's loses to the document's own" read where §2's
      intersection puts it.  **This bullet WAS the KNOWN CEILING and the ceiling
      is gone.**  It read "every other fact fills a gap and never overrides, the
      node's own declaration wins", measured over 61 of the 342 ``allOf``-root
      documents of the 3.2 bundle at a ROOT, where "the node winning is also the
      right answer" because at a root the node IS the document's own.  It is not
      the node at an OVERLAY: once the conjunct's ``properties`` and ``items``
      are stashed and folded on descent, the node at the descended pointer is
      the BASE's declaration and the stash is the document's own, so the polarity
      flips and the gap-fill graded the WIDER of two descriptions.  Re-measured
      over the whole graded tree rather than at roots alone: 2 sites where a
      conjunct both narrows the vocabulary and states a description of its own,
      3 where the NODE is the narrower view, 277 where neither narrows, and 0
      where the narrowing is a BOUND.

    **``if`` / ``then`` / ``else`` / ``not`` need no code and that is not an
    oversight.**  A conjunct holding only those states nothing unconditional
    about the value, and none of them is in ``FOLDED_FACTS``, so such a conjunct
    contributes nothing by construction.  That is the dominant conjunct shape in
    the bundle: 352 ``if``/``then`` conjuncts against 21 that state
    ``properties``.

    **``anyOf`` / ``oneOf`` at a root are left alone, and must be.**  A branch's
    properties are satisfied by SOME branch, not by every instance, so folding
    one in the way a conjunct is folded would state a fact the document does not
    state.  What that costs is nothing here: a union root emits a base and one
    subclass per branch (§4), each naming its own node on ``__adcp_schema__``, so
    a branch is graded as a pair in its own right rather than reached through its
    parent.

    **A LOCAL ``$ref`` CONJUNCT IS RESOLVED HERE, against ``root``, and that paragraph
    USED TO SAY IT WAS NOT** (``adcp-client-python-fte``).  It read "the caller hands
    this a RESOLVED document ... and 0 of the conjuncts in that 61-document sample still
    carried a ``$ref``", and that is TRUE of a REMOTE conjunct -- ``bundle.record``
    inlines one -- and FALSE of a LOCAL one, which §4 leaves exactly as the document
    writes it (``tests/test_fragment_ref.py``
    ``::test_a_local_reference_is_left_in_the_record_exactly_as_the_document_writes_it``).
    A pointer states no fact in ``FOLDED_FACTS``, so such a conjunct folded to NOTHING
    and every fact the base declares was absent from the composed node -- at the root
    and at every pointer below it, which is where ``emit._folded`` puts a declaration.
    ``core/registry-event.json`` and ``core/account-identity-change-preview.json`` are
    two of the documents of the shape.

    **ONE READING AND NOT A SECOND ONE**: the hop is :func:`_branch_target`, the same
    function :func:`_normalize` already uses at a union BRANCH, called here because a
    conjunct is the same POSITION -- a member of a combinator list, spelled as a
    pointer.  It is taken ONCE over the list and before anything reads it, so the fold
    arms below, the ``properties`` and ``items`` stashes, and the ``kept`` clause at the
    bottom all see what the conjunct STATES rather than the pointer it states it
    through; and a member whose target is a union is kept by that clause for the same
    reason an inline combinator is.  ``root`` is threaded in for it and is the same
    root :func:`_normalize` reads a node's ``$ref`` against: the whole resolved
    DOCUMENT.

    A conjunct the hop declines -- a pointer with a sibling, a target that is itself a
    reference, a pointer naming nothing -- is left as written, states no fact in
    ``FOLDED_FACTS``, and folds to nothing.  That is the FAIL-SAFE direction and the
    pre-existing behaviour: the composed node states LESS than the document does, so a
    declaration at a fact only that conjunct states is reported ``unproved`` rather than
    proved against a node this reading guessed at.
    """
    conjuncts = doc.get("allOf") if isinstance(doc, dict) else None
    if not isinstance(conjuncts, list) or depth > _COMPOSE_DEPTH:
        return doc
    # The conjuncts as the DOCUMENT writes them, with a bare local pointer read as the
    # node it NAMES (:func:`_branch_target`).  Here rather than inside the loop because
    # ``kept`` below reads the list again, and resolving in two places is the second copy
    # §3 forbids -- one of them would then see a pointer where the other sees a union.
    conjuncts = [_branch_target(c, root) for c in conjuncts]
    out = {k: v for k, v in doc.items() if k != "allOf"}
    for conjunct in conjuncts:
        if not isinstance(conjunct, dict):
            continue
        # The conjunct as the DOCUMENT writes it.  It was read through the delegated
        # resolver's finite-type rewrite and its one-member respelling first, because
        # that resolver dropped the ``type`` when it wrote a boolean out as
        # ``{"enum": [false, true]}`` and an inlined base's boolean then arrived here
        # typeless -- 9 sites over 5 ``formats/canonical`` documents, each restating an
        # inherited boolean, where the composed node then carried an ``enum`` the
        # document does not write and no ``type`` at all.  ``bundle.record``
        # copies the base's ``{"type": "boolean"}``, so the conjunct arrives in the
        # document's own spelling and both undoings are deleted (§9).
        c = _composed(conjunct, root, depth + 1)
        # **The view that states the composed node's VALUE SET states its description**
        # (:func:`_described_by_the_conjunct`), read BEFORE the vocabulary axis
        # collapses: the collapse drops one of the two statements and this asks which
        # VIEW made the surviving one.  Written as a stand-down of the node's own rather
        # than as a second write, so the gap-fill below stays the one place a fact
        # crosses from a conjunct to the merged node.
        out = _described_by_the_conjunct(out, c)
        # One statement on the vocabulary axis before anything is gap-filled, so the
        # merged node cannot carry a ``const`` beside the ``enum`` it pins.
        out, c = _one_vocabulary(out, c)
        for kw in FOLDED_FACTS:
            if kw == "required" or kw not in c:
                continue
            if kw not in out:
                out[kw] = c[kw]
                continue
            # **Section 2's intersection rule, where the KNOWN CEILING below used to gap-fill
            # and keep the node's.**  "Where composed schemas constrain the same
            # property, the field carries the INTERSECTION, never the union: an enum is
            # the intersection of the members, a bound is the tighter one."  The ceiling
            # was measured as a population of zero at a root and is no longer zero:
            # ``core/audience-evidence-requirements.json`` at
            # ``/properties/maximum_age`` composes ``core/duration.json`` (whose ``unit``
            # is a five-member ``enum``) with a conjunct narrowing ``unit`` to four, and
            # the node that KEPT the five read as admitting a value the composed document
            # refuses -- at the node and at its parent.
            #
            # Derived HERE and not imported from ``codegen.compiler``, which carries the
            # same rule where it lowers a node.  The shared alternative is tempting and
            # is the hazard §9's two spellings exist to avoid: "One body of code deciding
            # what the model states and what the document states agrees with itself by
            # construction, so a defect in it is green on both sides."
            narrower = _tighter(kw, out[kw], c[kw])
            if narrower is not _UNDECIDED:
                out[kw] = narrower
        req = c.get("required")
        if isinstance(req, list):
            have = out["required"] if isinstance(out.get("required"), list) else []
            out["required"] = [*have, *(k for k in req if k not in have)]
        props = c.get("properties")
        if isinstance(props, dict):
            mine = dict(out["properties"]) if isinstance(out.get("properties"), dict) else {}
            for name, sub in props.items():
                node = mine.get(name)
                if isinstance(node, dict):
                    pending = node["allOf"] if isinstance(node.get("allOf"), list) else []
                    mine[name] = {**node, "allOf": [*pending, sub]}
                else:
                    mine[name] = sub
            out["properties"] = mine
        # ``items`` composes the way ``properties`` does, by the SAME mechanism: the
        # conjunct's declaration is stashed as an ``allOf`` on the merged node and this
        # function folds it when the walk descends.  It gap-filled instead, so an
        # overlay narrowing an array's element left the composed node stating the WIDER
        # element -- measured on
        # ``core/media-buy-frequency-cap-requirement.json`` at
        # ``/properties/supported_control_modes``, whose conjunct narrows the element
        # from a three-member enumeration to one, and the element the fold handed on was
        # the enumeration.  Section 2: the intersection holds at any depth,
        # INCLUDING an overlay under ``items``.
        if isinstance(c.get("items"), dict):
            mine_items = out.get("items")
            if isinstance(mine_items, dict):
                pending = mine_items["allOf"] if isinstance(mine_items.get("allOf"), list) else []
                out["items"] = {**mine_items, "allOf": [*pending, c["items"]]}
            else:
                out["items"] = c["items"]
    # **A conjunct whose own statement is a COMBINATOR is KEPT and not dropped**
    # (``adcp-client-python-10l.21``).  The clause above says a branch list is "left
    # alone, and must be" -- a branch's properties are satisfied by SOME branch, so
    # folding them in would state a fact the document does not -- and that is right about
    # FOLDING and was wrong about dropping: the conjunct applies to the whole instance,
    # so its combinator is an assertion the composed node makes, and removing ``allOf``
    # from the merged node took the assertion with it.  The conjunct states nothing in
    # ``FOLDED_FACTS``, so it folded to NOTHING and the merged node read as typeless.
    #
    # Kept by the SAME mechanism ``properties`` and ``items`` already use -- stashed
    # under ``allOf`` on the merged node, folded again when the walk descends -- and
    # ``allOf`` is not in ``FOLDED_FACTS``, so a kept conjunct adds no fact to the fold.
    # What reads it is the node's own VERDICT: :func:`check_widening` screens every drawn
    # value against this node before offering it anywhere, so a conjunct dropped here
    # would leave a node admitting instances the document refuses, and a value class
    # could be proved against a reading looser than the document.
    #
    # Measured over the graded tree at ``ad0a48cc``: 4 sites, all §5's
    # ``$ref``-row-at-CONJ shape where the conjunct resolves to a UNION ROOT.  The
    # document types the instance twice over -- every branch of the conjunct's own
    # ``oneOf`` says ``object`` -- and dropping the conjunct left a composed node stating
    # no ``type`` at all.  A conjunct whose facts DO fold is unaffected: an ``enum``
    # conjunct's ``enum`` and ``type`` are in ``FOLDED_FACTS``, which is why the other
    # five sites of the same row need nothing from this clause.
    #
    # Read off the RESOLVED list above, so a conjunct that spells its combinator through
    # a local pointer is kept on the same terms as one that spells it inline -- 1 of the
    # bundle's 54 local-``$ref`` conjuncts does
    # (``core/registry-event.json#/$defs/publisherAdagentsPayload``), and before the hop
    # it was invisible to this clause as well as to the fold.
    kept = [
        c for c in conjuncts if isinstance(c, dict) and ("oneOf" in c or "anyOf" in c)
    ]
    if kept:
        out["allOf"] = kept
    return out




# --------------------------------------------------------------------------- #
# the pair, and one entry point over a sequence of them
# --------------------------------------------------------------------------- #
@dataclass
class Pair:
    """One graded unit: a name for reporting, a resolved document, a model, and
    the entry point the caller says an instance is offered through."""

    name: str
    schema: dict
    model: Any
    accept: Callable[[Any], Any]
    #: The WHOLE resolved document ``schema`` is a node of, read only as the scope a
    #: local ``$ref`` inside the node resolves against (:func:`check_pair`'s
    #: ``referrer``).
    #:
    #: **A second field and not a wider ``schema``, because they answer different
    #: questions.**  ``schema`` is what the pair is GRADED against -- the node the
    #: class names, which is what the accepts check must draw instances from.  The
    #: root is only the scope a ``#/definitions/x`` is relative to, and a nested
    #: pair's node does not contain it: measured on
    #: ``core/bidding-policy-capability.json``, whose
    #: ``#/definitions/scope_capability`` pair references
    #: ``#/definitions/policy_profile``, a SIBLING in the root's own
    #: ``definitions`` section.
    #:
    #: ``None`` means "the node is the root", which is true of a root pair and
    #: FAIL-SAFE for a nested one: the resolution raises, :func:`check_pair` falls
    #: back to the node as it stands, and no reference is silently inlined.
    document: dict | None = None

    #: WHICH document and pointer this node is, for ``codegen.dump_exemptions``.
    #:
    #: **A stated field and not a read off ``model``, because the two are not the
    #: same fact for every pair.**  D2's root-scalar row is graded as an ALIAS: the
    #: model is an ``Annotated`` and the ``__adcp_schema__`` is on its MODULE, so
    #: ``pair.model.__adcp_schema__`` answers for a class and raises for an alias.
    #: ``pair.accept.__self__`` reaches it for a class too and is worse -- it makes
    #: the dependency invisible in the signature, which is the thing a signature is
    #: for.
    #:
    #: ``None`` is FAIL-SAFE in the direction that matters: a caller grading a bare
    #: node supplies none, ``dump_exemptions.applying_to`` then matches nothing, and
    #: the dump is validated against the node as it stands.  An absent ref loses an
    #: exemption; it can never invent one.
    ref: SchemaRef | None = None

    #: **Section 7's approximation declaration for this pair's own artifact.**
    #:
    #: A stated field for :attr:`ref`'s exact reason, and it is the same reason: section 7
    #: puts the declaration "onto the class, the root model or the enumeration, and beside
    #: the MODULE for an alias", so ``pair.model.__adcp_approximations__`` answers for a
    #: class and does not exist for an alias.  :func:`declarations_of` is the reader for
    #: both -- the caller says which object holds it and this module does the reading, so
    #: section 9's "the verifier reads the declaration off the class, as a consumer" stays
    #: true of the code that grades it.
    #:
    #: ``()`` is FAIL-SAFE in the direction that matters: a caller grading a bare node
    #: supplies none, :func:`check_widening` reports ``no_declarations``, and nothing is
    #: credited as proved.  An absent declaration loses an obligation; it can never
    #: invent a proof.
    declared: tuple[Approximation, ...] = ()

    #: **The STATIC identity of the question this pair's draw asks**, for the held accepts
    #: corpus and for nothing else.  ``harness.corpus_key`` hashes it; this module never
    #: derives it.
    #:
    #: **A stated field and not a read off :attr:`schema`, which is the whole point.**
    #: :attr:`schema` is ``bundle.record``'s rendering of a document -- our inliner's
    #: output read at a pointer -- so an identity taken from it moves when the inliner
    #: does and the corpus is redrawn for a bundle nobody changed.  The caller is the half
    #: of the seam that can see upstream: ``catalogue.admitted_identities`` is what a
    #: document ADMITS with every reference resolved and the instances it STATES, and the
    #: pointer beside it says which node of that document this pair is.
    #:
    #: ``None`` is NOT fail-safe here and is not treated as such: ``check_accepts`` raises
    #: rather than falling back to the schema, because a silent fallback is the defect
    #: (:func:`corpus_key`).  A caller with nothing static to offer grades with no corpus.
    identity: Any = None


@dataclass
class PairReport:
    name: str
    model_repr: str = ""
    accepts: AcceptsResult | None = None
    liveness: LivenessResult | None = None
    #: Section 8's accepts obligation for this pair's declarations, and ``None`` where the
    #: pair declares nothing -- which is every pair of the tree at section 14 step 8.
    #: ``None`` and not an empty result, so ``outcome`` can tell "nothing was claimed" from
    #: "a claim was checked", the way it already tells ``accepts:unrun`` from a pass.
    widening: WideningResult | None = None
    #: **Reading 2's OTHER direction**: every value this pair's document REFUSES, offered
    #: to the CONSTRUCTOR, and an admission that no declaration names (:func:`check_refuses`).
    #:
    #: A separate field from :attr:`widening` because the two grade opposite directions of
    #: one sentence and ``docs/plan/final-state.md`` reading 2 states both: "a model may be
    #: wider than its document and never tighter; each widening is declared at its own
    #: pointer, the declared set equals the set a run mints in both directions, and every
    #: declaration holds a value that demonstrates it."  :func:`check_widening` grades the
    #: declarations that EXIST; this grades the widenings that are not declared at all, and
    #: :attr:`RefusesResult.undeclared` is the only place in this module that reports one.
    #:
    #: ``None`` and not an empty result, for :attr:`widening`'s reason: ``outcome`` can
    #: then tell "the check was never put to this pair" -- no accepted instance to reduce
    #: -- from "the check ran and the class refused everything the document refuses".
    undeclared: RefusesResult | None = None
    #: **Reading 1's FIRST CHECK over a witness the draw cannot make**
    #: (:func:`check_admits`, ``adcp-client-python-87ll``).  A separate field from
    #: :attr:`accepts` because the two grade the same check over two witness classes and
    #: one of them was empty: the generator honours a ``format``, so every drawn instance
    #: landed inside the pydantic type substituted for that format and the check could not
    #: fail at 404 pairs of 2,587.
    #:
    #: ``None`` and not an empty result, for :attr:`widening`'s reason: ``outcome`` can
    #: then tell "the check was never put to this pair" -- no accepted instance to perturb,
    #: or a budget spent -- from "the class admitted every value the document admits".
    admits: AdmitsResult | None = None
    missing_formats: list[str] = field(default_factory=list)
    #: The DOCUMENT's own format-beside-pattern positions a draw CANNOT REACH, each
    #: measured by drawing that node alone (:func:`undrawable_formats`).  Filled by
    #: :func:`check_pair` because a report does not hold the document it graded, and
    #: filled only where the accepts check errored, because that is the only pair it
    #: says anything about.  Read by :attr:`no_instrument` to name the shape behind an
    #: accepts check that could not draw.
    accepts_undrawable: tuple[str, ...] = ()
    #: How many §8 FIXTURES were pinned at a referring position of this pair's node
    #: (:class:`Fixtures`).  Reported for ``AcceptsResult.replayed``'s reason: the draw
    #: varied this class's own payload and took each referenced document's value as given,
    #: and a reader of a green pair is entitled to know how much of the node was a fixture.
    fixtures: int = 0
    #: How many INSTANCE LOCATIONS of this pair's node were pinned to one value read off
    #: the node itself (:meth:`Fixtures.reduced`).  The same fact keyed the other way, and
    #: reported for the same reason: the draw varied what the node leaves open and took
    #: each location's value as given, and a green pair is entitled to say how much of its
    #: node was a fixture rather than a draw.
    pinned: int = 0

    @property
    def graded_instances(self) -> int:
        """How many instances reached the class and came back out through its dump.

        The one denominator this harness has, and it is the accepts check's: an
        instance is drawn, constructed, dumped, and the document decides on the
        dump.  A pair reporting zero here was never exercised by an instance at
        all, which :attr:`outcome` turns into a refusal rather than a pass.
        """
        return self.accepts.round_tripped if self.accepts is not None else 0

    @property
    def no_instrument(self) -> tuple[str, ...]:
        """Every check of this pair that could not DRAW, with its CAUSE.

        **Tracking, with no ratchet on it, and that is the decision rather than an
        omission.**  A shrink-only count assumes a fixed or shrinking population and
        the emitted tree GROWS every merge, so each new batch of documents can
        legitimately contribute new undrawable pairs and a shrink-only gate would
        redden on correct work.  It can only shrink once ``hypothesis`` draws these
        shapes, which is unscheduled, so shrink-only is unachievable in principle and
        not merely premature.

        **The CAUSE matters more than the count**, because this is the population the
        eventual generator work starts from, so the entry names a shape to act on
        rather than "cannot draw": hypothesis's own message -- which carries the
        filtered-draw count -- beside the document's own positions a draw cannot
        reach, because that is the shape ``hypothesis_jsonschema``'s ``string_schema``
        filters and cannot satisfy.  The positions are DERIVED from the document, not
        guessed: hypothesis raises over the whole schema and names no node.

        **They are the MEASURED positions and not the co-occurrences**
        (:func:`undrawable_formats`), and the difference is this exit's whole
        admissibility: 72 of the bundle's 73 format-beside-pattern positions draw, so
        an entry naming every co-occurrence would speak for a ``strategy_error`` from
        any cause at all in a document that happens to state the two keywords
        somewhere.

        **So this is EMPTY where no position of the document is undrawable, and that
        is the refusal rather than a gap.**  A generator failure nothing explains has
        no admitted exit: :attr:`outcome` reads this and reports
        ``accepts:strategy_error``, which is a verdict on the pair.
        """
        if self.accepts is None or self.accepts.outcome != "strategy_error":
            return ()
        if not self.accepts_undrawable:
            return ()
        return (f"accepts: {'; '.join(self.accepts_undrawable)}; {self.accepts.detail}",)

    @property
    def outcome(self) -> str:
        """One verdict for the pair, and **a zero denominator is a refusal**.

        Structural here rather than a convention a caller is trusted to apply,
        because a report can enforce it and a reader cannot.  What it guards is a
        pair no instance reached: an entry point raising an exception this module
        does not catch leaves the accepts check with nothing round-tripped.

        The order is the same one it always had, and for the same reason: a MODEL
        defect outranks an INSTRUMENT one, so every verdict about the model is read
        before ``no_instrument``, and the zero-denominator exits come last so a pair
        whose generator produced nothing names that instead of "nothing was graded".

        **``no_instrument`` is ADMITTED only where a measured position explains the
        generator's failure**, which is ``salesagent-j3k2l.10``'s decision made
        structural: the shape is the designed exit, so a ``strategy_error`` nothing
        identifies as that shape falls through to ``accepts:strategy_error`` and is a
        verdict on the pair like any other accepts outcome.
        """
        if self.missing_formats:
            return "missing_formats"
        if self.accepts is None:
            return "accepts:unrun"
        # ``strategy_error`` is held back here and answered by ``no_instrument``
        # below: it says the GENERATOR produced nothing, which is not a verdict on
        # the model.  Every other accepts outcome is a verdict and still wins.
        if self.accepts.outcome not in ("pass", "strategy_error"):
            return "accepts:" + self.accepts.outcome
        #: **Reading 1's first check over the witness the draw cannot make, ranked
        #: IMMEDIATELY BELOW the drawn one because it is the SAME check**
        #: (``adcp-client-python-87ll``).  A class that refuses a value its own document
        #: admits is the one thing reading 1 forbids outright, and ranking it anywhere
        #: below the reading-2 columns would say a declaration's proof outranks the
        #: correctness the declarations are exceptions TO.
        #:
        #: **AND IT IS RANKED AT ALL, which is the whole of this row.**  The witnesses
        #: existed as a probe in a scratch directory and the table said nothing, so 404
        #: pairs read ``verdict=pass`` on a check that could not fail at them.  A check
        #: whose result reaches no verdict is the defect ``adcp-client-python-x63t``
        #: names one column over.
        #:
        #: ``no_witness`` and ``unrun`` are exempt for :func:`_admits_verdict`'s reason:
        #: both say the class was never asked, which is a fact about the document or about
        #: the draw, and the cell beside this says which.  A CAPPED pass is exempt here
        #: too and reads ``absent`` in its own cell, exactly as an unreached conditional
        #: does: the ranking carries verdicts about the class.
        if self.admits is not None and self.admits.outcome not in (
            "pass",
            "no_witness",
            "unrun",
        ):
            return "admits:" + self.admits.outcome
        if self.liveness is None:
            return "liveness:unrun"
        if self.liveness.outcome not in ("pass", "no_payload"):
            return "liveness:" + self.liveness.outcome
        # Section 8's accepts obligation, ranked with the accepts check it is part of and
        # BELOW it: a model that refuses a drawn instance outright is a verdict about the
        # whole pair, where this is a verdict about one declaration's claim.
        if self.widening is not None and self.widening.outcome not in ("pass", "no_declarations"):
            return "widening:" + self.widening.outcome
        #: **Reading 2's OTHER direction, ranked WITH the declaration check and BELOW it**,
        #: because the two grade the same sentence and the declared half is the one a
        #: reader acts on first: a declaration that no value proves is a claim the artifact
        #: makes and cannot support, and a widening nobody declared is a claim the artifact
        #: never made.
        #:
        #: **AND IT IS RANKED AT ALL, WHICH IS THE WHOLE OF ``adcp-client-python-x63t``.**
        #: ``check_refuses`` existed for one merge with no caller on the graded path -- a
        #: mechanism that computes and decides nothing -- and a check whose result reaches
        #: no verdict is the same defect one level up.  So an undeclared widening is a
        #: verdict about the pair, and the pair grade reddens by however many there are.
        #:
        #: ``no_witness`` and ``unrun`` are exempt for :func:`_undeclared_verdict`'s
        #: reason: both say the class was never asked, which is a fact about the document
        #: or about the draw, and the cell beside this says which.  An UNREACHED
        #: conditional is exempt here too and reads ``absent`` in its own cell -- the
        #: ranking carries verdicts about the class, exactly as ``widening``'s
        #: ``no_declarations`` is exempt above.
        if self.undeclared is not None and self.undeclared.outcome not in (
            "pass",
            "no_witness",
            "unrun",
        ):
            return "undeclared:" + self.undeclared.outcome
        if self.accepts.outcome == "strategy_error":
            return "no_instrument" if self.no_instrument else "accepts:strategy_error"
        if not self.graded_instances:
            return "no_accepts_check_evidence"
        return "pass"


# --------------------------------------------------------------------------- #
# section 8's declaration audit, over the run
# --------------------------------------------------------------------------- #
def unattributed(declared: Sequence[Approximation] | Any) -> list[str]:
    """Every declaration whose attribution names neither a cell nor a live issue.

    Section 2's attribution "is a choice of two and not a free-text note", and this is
    where that bites on the artifact: an ``Ours`` attribution is the cell's own address, so
    it is ``keywords.address`` of the keyword and nothing else; an ``Upstream`` one is an
    entry of ``codegen.attribution``'s registry, so the site has to be in it.  A string
    that is neither is a free-text note wearing an attribution.

    This is the verifier's half of section 9's grader row.  ``attribution.py``'s own test
    holds the other half -- that an entry with no issue cannot exist -- and the two are
    different claims: that one is about the REGISTRY, this is about what an artifact says
    it read out of it.
    """
    out: list[str] = []
    for one in declared:
        issue = attribution.issue_for(one.document, one.pointer, one.keyword)
        expected = issue.attribution if issue is not None else keywords.address(one.keyword)
        if one.attribution != expected:
            out.append(
                f"{one.document}{one.pointer}/{one.keyword}: the artifact says "
                f"{one.attribution!r} and the declaration says {expected!r}; section 2 "
                "makes the attribution a choice of two -- the cell's own address, or an "
                "entry of codegen.attribution -- and never a free-text note"
            )
        if one.rung not in set(Rung):
            out.append(
                f"{one.document}{one.pointer}/{one.keyword}: rung {one.rung!r} is not one "
                f"of section 2's ladder, {[r.value for r in Rung]}"
            )
        if one.kind not in KINDS:
            out.append(
                f"{one.document}{one.pointer}/{one.keyword}: kind {one.kind!r} is not one "
                f"of section 2's two, {list(KINDS)}"
            )
    return out


# --------------------------------------------------------------------------- #
# the UNDERDETERMINED equality: the one approximation no check above can see
# --------------------------------------------------------------------------- #
#: The combinators whose branches a union's dispatch has to separate, DERIVED from the
#: declaration: ``keywords.combinators`` is "the keywords whose subschemas occupy a BRANCH,
#: which is what a combinator IS -- so the pair is a reading of the declaration and not a
#: literal".  Section 9's rule that nothing under ``codegen/`` names a keyword in a set
#: literal holds of the verifier too, and section 9's own permitted import is what makes it
#: possible: the keyword table is "the declared semantics, and both halves must read the
#: same declaration or the grade means nothing".
#:
#: At ROOT, because a union's branches are read under the enclosing node's own position and
#: ROOT is where the derivation enters; the pair is the same at every position the table
#: gives one.
_COMBINATORS = tuple(sorted(keywords.combinators(Position.ROOT)))


#: The keywords whose subschema sits at RULE, DERIVED from the descent column rather than
#: named: ``keywords.descends_at`` is "the ONE descent table, where today there are three",
#: and a keyword holding a RULE subschema is exactly what a conditional is.  Section 11
#: names the three descent tables as a repetition with one owner, and the verifier's own
#: walk of the record is one of the three readers section 3 gives that column.
_RULE_KEYWORDS = tuple(
    sorted(k for k, p in keywords.descends_at(Position.ROOT).items() if p is Position.RULE)
)


def _rule_free_nodes(schema: Any, pointer: str = "") -> list[tuple[str, dict]]:
    """Every dict node of the document that is NOT under a conditional, with its pointer.

    :func:`_nodes` with one difference, and the difference is a POSITION carried by the
    descent: a subschema reached through ``if``, ``then``, ``else`` or ``not`` is at RULE,
    and section 3 of the semantics document says no type is lowered from a RULE node -- so
    the subtree has no declaration for a derivation over declarations to range over.

    Not a filter over :func:`_nodes`' pointers, deliberately: section 6 of the
    architecture document makes deriving position from a pointer string the repetition
    section 11 names, and "a pointer cannot tell a RULE node from a PROP one" in general --
    a document may hold a property literally named ``then``.  The descent knows it
    structurally, so the descent is what carries it.
    """
    out: list[tuple[str, dict]] = []
    if isinstance(schema, list):
        for i, v in enumerate(schema):
            out += _rule_free_nodes(v, f"{pointer}/{i}")
        return out
    if not isinstance(schema, dict):
        return out
    out.append((pointer or "/", schema))
    for k, v in schema.items():
        if k in _RULE_KEYWORDS:
            continue  # at RULE: no type is lowered from here (semantics §3)
        if k in _DESCEND_MAP and isinstance(v, dict):
            for kk, vv in v.items():
                out += _rule_free_nodes(vv, f"{pointer}/{k}/{_esc(kk)}")
        elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
            out += _rule_free_nodes(v, f"{pointer}/{k}")
        elif k in _DESCEND_LIST and isinstance(v, list):
            out += _rule_free_nodes(v, f"{pointer}/{k}")
    return out


def _pins(node: Mapping[str, Any]) -> dict[str, Any]:
    """Each property this branch pins to a single value, by key.

    A one-member ``enum`` is a ``const`` -- section 5's ``enum`` row says so of the model
    side and draft-07 says so of the document -- so both spellings are read.

    **This answers the FOURTH separator now and not the first** (2026-10-29): "one branch
    forbids a VALUE another pins" is about a single value, because ``_forbidden_values``
    reads a single pinned value off a ``not``.  The first separator reads
    :func:`_value_sets`, which is a different question -- which values the branch ADMITS,
    not which one it spells.
    """
    out: dict[str, Any] = {}
    for key, declaration in (node.get("properties") or {}).items():
        if not isinstance(declaration, dict):
            continue
        if "const" in declaration:
            out[key] = declaration["const"]
        elif isinstance(declaration.get("enum"), list) and len(declaration["enum"]) == 1:
            out[key] = declaration["enum"][0]
    return out


def _value_sets(node: Mapping[str, Any]) -> dict[str, tuple[frozenset, bool]]:
    """For each key this branch constrains to a value set, that set and whether it is a
    COMPLEMENT.

    **Section 4's first separator, which reads SETS as of 2026-10-29**: "An ``enum`` is a
    set of pinned values and a ``not: {"enum": [...]}`` is its complement, so two branches
    whose sets do not intersect are disjoint for the same reason two different ``const``\\ s
    are -- the single-value case is the one-member set."

    **A second spelling of ``codegen.lower.union.value_sets``, over the DOCUMENT**, for
    :func:`separates`' reason: a verifier that asked the walk which values a branch admits
    would compare the walk's answer with itself.  Written from section 4, not from it.

    Nothing but ``const``, ``enum`` and a ``not`` over either contributes: a bound, a
    pattern or a ``$ref`` constrains the value without NAMING the values, so there is no
    set to intersect.
    """
    out: dict[str, tuple[frozenset, bool]] = {}
    for key, declaration in (node.get("properties") or {}).items():
        if not isinstance(declaration, dict):
            continue
        for sub, complement in ((declaration, False), (declaration.get("not"), True)):
            if not isinstance(sub, Mapping):
                continue
            named = bundle.named_values(sub)
            if named is not None:
                out[key] = (named, complement)
                break
    return out


def _disjoint(one: tuple[frozenset, bool], other: tuple[frozenset, bool]) -> bool:
    """Do these two value sets share no value?

    Two POSITIVE sets are disjoint where they do not intersect; a positive set and a
    COMPLEMENT are disjoint where the positive one is CONTAINED in the complemented one;
    two COMPLEMENTS are never reported disjoint, because whether their two finite sets
    cover the value space is not something the branches state -- and section 4's "a pair
    the derivation cannot separate is treated as overlapping" is the answer where they do
    not.
    """
    (ours, ours_complement), (theirs, theirs_complement) = one, other
    if ours_complement and theirs_complement:
        return False
    if ours_complement:
        return theirs <= ours
    if theirs_complement:
        return ours <= theirs
    return not (ours & theirs)


def _requires(node: Mapping[str, Any]) -> frozenset[str]:
    """The names present in every instance of this branch: :func:`_demands`' singletons.

    Read off the one reading of what a branch requires rather than off ``required`` a
    second time, so a branch stating its requirement in an ``allOf`` conjunct or as a
    presence combinator is read the same way here as by the second separator.
    """
    return frozenset(name for group in _demands(node) for name in group if len(group) == 1)


def _views(node: Any) -> list[Mapping[str, Any]]:
    """``node`` and every node its ``allOf`` applies to the SAME instance.

    **A second spelling of ``codegen.schema.parse.applies_to_one_instance``, over the
    DOCUMENT**, for :func:`separates`' reason: a verifier that asked the walk which nodes
    a branch's facts are stated at would compare the walk's answer with itself.

    Draft-07 conjoins an ``allOf`` conjunct with the node that holds it, so a ``not``, a
    ``required``, a ``properties`` or an ``additionalProperties`` a conjunct states is a
    statement about the instance the branch describes.  Every reading below ranges over
    these views rather than over the branch node alone, which is the widening
    ``adcp-client-python-10l.30`` landed: ``account/sync-accounts-request.json`` states
    its two branches' ``not`` guards as four and six ``allOf`` conjuncts, and read at the
    top level alone each branch forbids nothing.

    A ``$ref`` conjunct contributes NOTHING: the fact is in the target, and §4's "a pair
    the derivation cannot separate is treated as overlapping" is what that costs.
    Flattened to any depth, because an ``allOf`` of an ``allOf`` conjoins just the same.
    """
    if not isinstance(node, Mapping):
        return []
    out = [node]
    if isinstance(node.get("allOf"), list):
        for conjunct in node["allOf"]:
            if isinstance(conjunct, Mapping) and "$ref" not in conjunct:
                out.extend(_views(conjunct))
    return out


def _demands(node: Mapping[str, Any]) -> frozenset[frozenset[str]]:
    """Each set of names at least ONE of which every instance of ``node`` carries.

    **A second spelling of ``codegen.schema.parse.demanded_names``, over the DOCUMENT.**

    §4's second separator asks for "a ``required`` name one branch declares", and a
    branch does not always declare one name: ``anyOf: [{"required": ["brands"]},
    {"required": ["brand_refs"]}]`` requires one of two, so a sibling forbidding both is
    disjoint from it.  So the answer is a set of SETS -- a plain ``required: [a, b]``
    gives the singletons ``{a}`` and ``{b}``, and a combinator gives one set, the union of
    what its branches guarantee.  A branch guaranteeing nothing makes its combinator
    guarantee nothing, because an instance can then satisfy the combinator carrying none
    of the other branches' names.
    """
    out: set[frozenset[str]] = set()
    for view in _views(node):
        required = view.get("required")
        if isinstance(required, list):
            out |= {frozenset({n}) for n in required if isinstance(n, str)}
        for keyword in _COMBINATORS:
            branches = view.get(keyword)
            if not isinstance(branches, list) or not branches:
                continue
            guaranteed: set[str] = set()
            for branch in branches:
                names = {
                    n
                    for group in (_demands(branch) if isinstance(branch, Mapping) else ())
                    for n in group
                }
                if not names:
                    guaranteed = set()
                    break
                guaranteed |= names
            if guaranteed:
                out.add(frozenset(guaranteed))
    return frozenset(out)


def _closed_maps(node: Mapping[str, Any]) -> tuple[frozenset[str], ...]:
    """For each view of ``node`` that admits only what it declares, the names it declares.

    ``additionalProperties: false`` puts an instance's members inside that view's own
    ``properties``, so a name the view never declares is a name it refuses.  A
    ``patternProperties`` beside it takes the closure back for whatever the pattern
    matches.  One entry per closed view, because closure is a fact about the NODE: a
    conjunct closing the instance over its own map closes it, and the branch's other views
    do not widen that.
    """
    return tuple(
        frozenset(view.get("properties") or {})
        for view in _views(node)
        if view.get("additionalProperties") is False and "patternProperties" not in view
    )


def _element(node: Mapping[str, Any]) -> tuple[Any, bool]:
    """The ``type`` ``node`` applies to every ELEMENT, and whether it refuses ``[]``.

    An array branch states what its instance is one level down, so two array branches
    whose elements are a string and an object are told apart by any member -- the type
    separator at the position an array states it.  ``[]`` satisfies ``items`` vacuously,
    so the pair is disjoint only where one of the two refuses the empty array, which
    ``minItems`` of at least 1 is.  The word is ``None`` where ``items`` states none,
    which includes an ``items`` that is a ``$ref``.
    """
    items = node.get("items")
    word = items.get("type") if isinstance(items, Mapping) else None
    minimum = node.get("minItems")
    return word, isinstance(minimum, int) and not isinstance(minimum, bool) and minimum >= 1


def _forbids(node: Mapping[str, Any]) -> frozenset[str]:
    """The names ``node`` forbids ONE AT A TIME, read off its ``not`` over ``required``.

    **A second spelling of ``codegen.lower.rules``' reduction, over the DOCUMENT**, for
    the reason :func:`separates` is one of the walk's: a verifier that asked the walk
    which names a branch forbids would compare the walk's answer with itself.

    ``not: {"required": [n]}`` says ``n`` is not present.  ``not`` over an ``anyOf`` of
    those says none of them is -- "not (a or b)" is "not a and not b" -- and over an
    ``allOf`` of them says the same, because every member asserts the presence of its own
    name.  A group of MORE than one name forbids no single name: "not (a and b)" leaves
    either one present, so a longer group is read and contributes nothing, which is the
    same distinction ``adcp.types._runtime.ForbiddenGroups`` draws between its shapes.

    **A member stating MORE than ``required`` forbids the VALUE and not the NAME, and
    reading it as the name is the over-read §4 settled out on 2026-10-27.**  This
    collected every singleton ``required`` it found anywhere under a ``not``, so it read
    ``{"properties": {"status": {"const": "submitted"}}, "required": ["status"]}`` as
    forbidding ``status`` by name -- which the document does not say.  At
    ``media-buy/sync-catalogs-response.json`` the conclusion was right and the reasoning
    wrong; at a branch pinning some OTHER value it would separate a pair that overlaps,
    which is the defect §4's third source exists to prevent.  "That over-reading is a
    defect whether or not this separator lands, and it goes either way."  The value the
    member does forbid is :func:`_forbidden_values`' answer and §4's fourth separator is
    what reads it.
    """
    found: set[str] = set()

    def groups(sub: Any) -> None:
        if not isinstance(sub, Mapping):
            return
        names = sub.get("required")
        stated = {k for k in sub if keywords.declares(k, Position.RULE)}
        if (
            stated == {"required"}
            and isinstance(names, list)
            and len(names) == 1
            and isinstance(names[0], str)
        ):
            found.add(names[0])
        for keyword in ("anyOf", "allOf"):
            if isinstance(sub.get(keyword), list):
                for member in sub[keyword]:
                    groups(member)

    for view in _views(node):
        groups(view.get("not"))
    return frozenset(found)


def _forbidden_values(node: Mapping[str, Any]) -> dict[str, Any]:
    """Each ``(key, value)`` pair ``node``'s ``not`` forbids, read off a PINNED property.

    **A second spelling of ``codegen.schema.parse.forbidden_values``, over the DOCUMENT**,
    for :func:`_forbids`' reason: a verifier that asked the walk which values a branch
    forbids would compare the walk's answer with itself.

    ``not: {"properties": {"k": {"const": v}}, "required": ["k"]}`` says no instance
    carries ``k == v``; the ``required`` is what makes the member a statement about the
    VALUE rather than one an absent key satisfies.  An ``anyOf`` of such members forbids
    each, because "not (a or b)" is "not a and not b"; an ``allOf`` is not read, because
    "not (a and b)" leaves either member -- the same distinction :func:`_forbids` draws
    between a singleton group and a longer one.
    """
    out: dict[str, Any] = {}

    def member(sub: Any) -> None:
        if not isinstance(sub, Mapping):
            return
        stated = {k for k in sub if keywords.declares(k, Position.RULE)}
        if stated == {"anyOf"} and isinstance(sub.get("anyOf"), list):
            for one in sub["anyOf"]:
                member(one)
            return
        properties = sub.get("properties")
        required = sub.get("required")
        if stated != {"properties", "required"} or not isinstance(properties, Mapping):
            return
        if not isinstance(required, list) or len(required) != 1:
            return
        (name,) = required
        declaration = properties.get(name)
        if set(properties) != {name} or not isinstance(declaration, Mapping):
            return
        if "const" in declaration:
            out[name] = declaration["const"]
        elif isinstance(declaration.get("enum"), list) and len(declaration["enum"]) == 1:
            out[name] = declaration["enum"][0]

    for view in _views(node):
        member(view.get("not"))
    return out


def separates(
    a: Mapping[str, Any],
    b: Mapping[str, Any],
    a_type: Any,
    b_type: Any,
    *,
    root_required: frozenset[str] = frozenset(),
) -> str | None:
    """What tells two branch NODES apart, or ``None`` where nothing does.

    **A second spelling of ``codegen.lower.union.separates``, over the DOCUMENT, and
    deliberately so.**  Section 9: "the intersection rule it carries stays a second
    spelling of the one in ``lower/composition.py`` on purpose ... One body of code
    deciding what the model states and what the document states agrees with itself by
    construction, so a defect in it is green on both sides."  The same reasoning holds
    exactly here: if the verifier asked the walk which unions it could not separate, the
    equality below would compare the walk's answer with itself.

    Section 4's four separators, each read off the branch nodes of the record:

    * one property constrained to DISJOINT VALUE SETS;
    * a ``required`` name one branch declares and the other forbids -- BY NAME, through a
      ``not`` over ``required`` (:func:`_forbids`), which is the idiom §4 itself names
      ("each branch forbidding a name the other requires"), or by admitting no name
      outside its own map;
    * one branch forbidding a VALUE another pins;
    * scalar branches of different ``type``.

    **THE FIRST SEPARATOR READS SETS AND IS GATED ON PRESENCE, 2026-10-29**
    (``adcp-client-python-10l.102``).  Section 4: "An ``enum`` is a set of pinned values
    and a ``not: {"enum": [...]}`` is its complement … the single-value case is the
    one-member set."  ``_value_sets`` is the reading and ``_disjoint`` the comparison.
    The gate is the half the single-value reading never had: a ``properties`` entry is
    satisfied by the key being ABSENT, so two branches naming disjoint sets for a key
    neither requires are both satisfied by an instance carrying no such key -- measured
    under ``Draft7Validator``, ``{}`` is valid against both
    ``{"properties": {"kind": {"const": "a"}}}`` and its ``"b"`` sibling.  So the key has
    to be present in every instance of one of the two branches, which is ``_requires`` of
    that branch plus ``root_required``: section 4 applies a root keyword to every branch,
    and 19,520 of the 70,446 pairs this arm separates over the bundle get their presence
    from the ROOT alone.

    **WHERE each one is read is wider, 2026-10-28** (``adcp-client-python-10l.30``), and
    the four readings moved on this side for the reason they moved on the walk's: the
    documents separate these pairs in their own idiom, one level from where each reading
    looked.  A ``not`` and a ``required`` and a closure are read over every view of the
    branch (:func:`_views`, the ``allOf`` descent draft-07 already asserts); what a branch
    requires is a set of GROUPS, so a presence combinator counts (:func:`_demands`);
    closure is asked of each closed view (:func:`_closed_maps`); and the type separator
    descends to ``items`` for two array branches (:func:`_element`).  No fifth separator:
    each is a reading of one §4 names.

    The two spellings moved in the same commit and each was written from §4 rather than
    from the other, which is what keeps the equality an instrument: the walk reads the
    branch through ``compiler.rules_at`` and ``codegen.schema.parse``, and this reads the
    document node.
    """
    first, second = _value_sets(a), _value_sets(b)
    present = (_requires(a) | root_required, _requires(b) | root_required)
    for key in sorted(set(first) & set(second)):
        if _disjoint(first[key], second[key]) and any(key in names for names in present):
            return f"{key!r} is constrained to disjoint value sets"
    for one, other in ((a, b), (b, a)):
        for group in sorted(_demands(one), key=sorted):
            if group <= _forbids(other):
                return (
                    f"one branch requires one of {sorted(group)} and the other forbids "
                    "each by name"
                )
    for one, other in ((a, b), (b, a)):
        # **§4's FOURTH separator (2026-10-27): one branch forbids a VALUE another pins.**
        # The pinning branch must also REQUIRE the key, or an instance of it omitting the
        # key satisfies the forbidding branch too and the pair is not separated.
        forbidden = _forbidden_values(other)
        pinned = _pins(one)
        demanded = {n for n in (one.get("required") or []) if isinstance(n, str)}
        named = sorted(
            key
            for key, value in pinned.items()
            if key in forbidden and forbidden[key] == value and key in demanded
        )
        if named:
            return f"one branch pins {named} to a value the other forbids outright"
    for one, other in ((a, b), (b, a)):
        for declared in _closed_maps(other):
            for group in sorted(_demands(one), key=sorted):
                if not group & declared:
                    return (
                        f"one branch requires one of {sorted(group)} and the other "
                        "forbids every one of them"
                    )
    scalars = a_type not in (None, "object") and b_type not in (None, "object")
    if scalars and a_type != b_type:
        return f"the branches are scalars of type {a_type!r} and {b_type!r}"
    if a_type == b_type == "array":
        # The type separator one level down, at ``items``: two branches of one container
        # word are not told apart by the word, and the element schema describes every
        # member.  ``[]`` satisfies ``items`` vacuously, so one of the two has to refuse
        # the empty array or the pair overlaps at exactly that value.
        one_word, nonempty_a = _element(a)
        two_word, nonempty_b = _element(b)
        if (
            one_word is not None
            and two_word is not None
            and one_word != two_word
            and (nonempty_a or nonempty_b)
        ):
            return (
                f"the branches are arrays whose elements are {one_word!r} and "
                f"{two_word!r}, and one of them refuses the empty array"
            )
    return None


def _branch_is_a_shape(applied: Any, branch: Mapping[str, Any]) -> bool:
    """Does §4 lower this branch to a BRANCH CLASS whose declaration order can decide?

    :func:`_inseparable`'s shape test, read once here because it has two answers and the
    second one is not a special case of the first.

    **A ``required``-ONLY BRANCH IS A SHAPE, AND THE WALK IS WHAT SAYS SO.**  The premise
    :func:`_inseparable` was written on -- "a union whose branches are not all shapes
    lowers to an alias over the union of their types, so there are no branch classes for a
    declaration order to choose between" -- is true of the union whose EVERY branch is
    ``required``-only, and that one leaves at the presence-only clause before this test is
    reached.  It is FALSE of the MIXED union, measured at
    ``media-buy/proposal-refinement.json#/oneOf/1/anyOf`` (``adcp-client-python-tsg``): 6
    of its 7 branches expand through the store to ``{"required": [one name]}`` and the
    seventh pins ``change_kind`` to ``cancellation``, and §4 lowers the node to a base plus
    **seven** branch subclasses in the document's own branch order, dispatching on no key.

    The payload ``{"proposal_id": "p-1", "action": "revise", "constraints":
    {"impressions": {"min": 1000}}, "ask": "cheaper please"}`` is admitted by branches 0
    AND 3 of that ``anyOf`` and becomes ``ProposalRefinementReviseConstraints``; the same
    payload without ``constraints`` becomes ``ProposalRefinementReviseAsk``.  So which
    class an overlapping payload becomes is a property of declaration order -- the whole of
    what UNDERDETERMINED names -- the declaration at that site is EARNED, and this test was
    the half of the equality that disagreed.

    A branch stating only ``required`` constrains the very object instance the ROOT
    describes, which is a shape in exactly the sense this question asks about: it owns a
    class, it carries a field the base leaves optional, and its position in the branch list
    is what an overlapping payload is resolved by.

    Measured over the 1,059-document bundle: this answer admits ONE union, the one above;
    the stale direction of the census goes 1 to 0 and its silent direction is unchanged at
    the same 5 sites.
    """
    if branch.get("required") and set(branch) <= {"required"}:
        return True
    #: **EVERY VIEW OF THE BRANCH and not the branch node alone**, which is §8's third
    #: pairing rule ("a node at a CONJUNCT of an ``allOf`` is paired with its node read AS
    #: THE COMPOSITION") and the reading every other clause of this derivation already
    #: makes (:func:`_views`, "``node`` and every node its ``allOf`` applies to the SAME
    #: instance").
    #:
    #: Measured on ``core/async-response-data.json#/anyOf``: 3 of its 42 branches -- 6, 8
    #: and 28 -- state their object-ness in an ``allOf`` conjunct and carry neither
    #: ``type`` nor ``properties`` at their own top level, so the node-only test rejected
    #: them and the 42-branch union was skipped whole.  With the composition read,
    #: ``separates`` answers ``None`` for 846 of its 861 pairs.  The payload says the same
    #: thing independently: the instance the accepts corpus holds for branch pair
    #: ``#/anyOf/0`` -- ``{"cache_scope": "public", "status": "failed", "unchanged": true,
    #: "wholesale_feed_version": ""}`` -- satisfies 17 of the 42 branches, so the union IS
    #: overlapping, ``lower.union.overlapping`` is right, and the disagreement was this
    #: gate.
    return any(
        (view.get("type") or applied) == "object"
        or ((view.get("type") or applied) is None and view.get("properties"))
        for view in _views(branch)
    )


def inseparable_unions(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Every union POINTER of this record whose branches the derivation cannot separate.

    :func:`inseparable_sites` is the same derivation read as §8's IDENTITIES, and the two
    share :func:`_inseparable` so there is one reading of "cannot separate" and two
    spellings of where the answer is.
    """
    return tuple(sorted(at for at, _, _ in _inseparable(record)))


def inseparable_sites(
    record: Mapping[str, Any], origins: bundle.Origins
) -> set[tuple[str, str]]:
    """:func:`inseparable_unions` as §8's identity: ``(stating document, stating pointer)``.

    **§8 sentence 2: "An approximation's identity is ``(stating document, stating pointer,
    keyword)``, and every inlined occurrence resolves to it."**  This is the resolving, and
    ``origins`` is what makes it possible: the record inlines a target at the REFERRING
    pointer, so one inseparable union has as many record pointers as there are paths
    through the reference graph that reach it, and the derivation run over a record alone
    reports every one of them as a site owed a declaration.  Measured: with the
    declaration at the stating site and the derivation over record pointers, the census's
    silent direction reports 89 sites for 24 unions.

    By IDENTITY and never by pointer arithmetic (``bundle.Origins``): the record places ONE
    OBJECT at every occurrence of one target, so the occurrences of one stating site are
    literally one object and the map answers in one lookup.  A pointer-keyed map cannot --
    the relation is not a function in that direction.

    A node with no origin is left out, which cannot arise over a record this package built
    (the inliner records every node it makes) and is the fail-safe direction if it ever
    does: a site nothing can locate is not a site this equality can hold anyone to.
    """
    out: set[tuple[str, str]] = set()
    for _, kw, node in _inseparable(record):
        site = origins.get(id(node))
        if site is None:
            continue
        document, stated = site
        out.add((document, f"#{stated}/{kw}"))
    return out


def _inseparable(
    record: Mapping[str, Any],
) -> Iterator[tuple[str, str, Mapping[str, Any]]]:
    """``(pointer of the combinator, the combinator, the node stating it)``, per union of
    this record whose branches §4's derivation cannot separate.

    Section 8: an UNDERDETERMINED approximation "is invisible to all three checks, and that
    is why it needs an instrument of its own ... Its check is section 4's disjointness
    derivation: **the set of unions declaring one equals the set the derivation cannot
    separate**, in both directions, so a union that becomes separable loses its declaration
    and a union that stops being separable gains one."

    Pairwise, for ``lower.union.overlapping``'s reason: "Where the branches are pairwise
    disjoint, the payload selects its own branch and the order they are tried in cannot
    change which one it reaches."  One unseparated pair makes the answer a property of
    declaration order, which is what UNDERDETERMINED names.

    A union whose branches are NOT all shapes is not in this set: section 4 lowers one to
    an alias over the union of their types, where "which branch an overlapping payload
    becomes" is not a question a declaration order answers -- there are no branch classes
    to order.  A branch is a shape here where its node, under the root's applied ``type``,
    is an object.

    **A union at a RULE position is not in it either, and the POSITION is carried by the
    descent rather than read off the pointer string.**  Section 3 of the semantics
    document: under a conditional "a keyword describes what a rule tests, so no type is
    lowered from it", so there is no branch class at all.  Section 6 of the architecture
    document is explicit that a pointer STRING cannot answer this -- "a handler never
    derives position from a pointer string", and "a pointer cannot tell a RULE node from a
    PROP one" -- so :func:`_rule_free_nodes` sets the flag where it descends through
    ``if``/``then``/``else``/``not`` and the question is never asked of a pointer.
    Measured over the emitted tree: 3 of this derivation's pointers are at a RULE position
    and all 3 leave with this clause.
    """
    for pointer, node in _rule_free_nodes(record):
        for kw in _COMBINATORS:
            branches = node.get(kw)
            if not isinstance(branches, list) or len(branches) < 2:
                continue
            if not all(isinstance(b, Mapping) for b in branches):
                continue
            # **A PRESENCE-ONLY combinator is not a union at all**, and §4 of the
            # architecture document decides it where the parser reads it: "a combinator
            # whose every branch is ``required``-only is not a ``Union`` but a rule source
            # of the enclosing object (the ``presence_only`` reading, read once here)".
            # It lowers to a ``RequiredGroups`` rule on the enclosing class, so there are
            # no branch classes for a declaration order to choose between -- which is the
            # whole of what UNDERDETERMINED names.  Measured: without this clause the
            # derivation reports 185 pointers, 16 of them roots whose documents emit as a
            # single class with a presence rule.
            #: **EVERY BRANCH IS READ THROUGH THE RECORD'S OWN STORAGE, which is §8
            #: sentence 3a applied to this derivation** -- and the reading
            #: ``architecture.md`` already settled: *a reader asking what the document
            #: states reads through the storage, because a reference to a storage entry is
            #: not a fact the document states but where the fact is kept*.  FIRST, before
            #: either clause below, because both of them are such readers.
            #:
            #: Without it a branch the store replaced with ``{"$ref":
            #: "#/definitions/Shared<N>"}`` carries no ``required``, no ``type`` and no
            #: ``properties``, so the presence-only clause does not fire and the shape test
            #: rejects it, the whole union is skipped, and a union the declaration
            #: correctly calls inseparable reports as DECLARED AND SEPARABLE.  Measured:
            #: 6 of the 7 sites the stale direction named have at least one bare storage
            #: reference among their branches, and
            #: ``media-buy/proposal-refinement.json#/oneOf/1/anyOf`` has 6 of 7 -- all
            #: seven of them ``{"required": [one name]}``, which is the presence-only
            #: clause's own subject, read by nothing until now.
            branches = [bundle.expanded(b, record) for b in branches]
            if all(set(b) <= {"required"} for b in branches):
                continue
            applied = [b.get("type") or node.get("type") for b in branches]
            #: **THE SHAPE TEST IS :func:`_branch_is_a_shape`**, which carries both of its
            #: answers and the measurement behind each: the composed view of a branch that
            #: states its object-ness in an ``allOf`` conjunct, and the ``required``-only
            #: branch of a MIXED union, which §4 lowers to a branch class like any other.
            if not all(
                _branch_is_a_shape(t, b)
                for t, b in zip(applied, branches, strict=True)
            ):
                continue
            base = "" if pointer == "/" else pointer
            # The ROOT's own ``required`` is handed to every pair, because section 4
            # applies a keyword beside the combinator to every branch -- "and every
            # branch inherits it" -- so a name the root requires is present in every
            # instance of every branch.  The first separator's presence gate is the one
            # reading that asks, and the walk hands the same field down
            # (``lower.union.overlapping``, off ``nodes.Union.required``).
            root_required = frozenset(
                name for name in (node.get("required") or []) if isinstance(name, str)
            )
            if any(
                separates(
                    branches[i],
                    branches[j],
                    applied[i],
                    applied[j],
                    root_required=root_required,
                )
                is None
                for i in range(len(branches))
                for j in range(i + 1, len(branches))
            ):
                yield f"#{base}/{kw}", kw, node


def underdetermined_census(
    declared: Sequence[Approximation],
    records: Mapping[str, tuple[Mapping[str, Any], bundle.Origins]],
    collapsed: Mapping[str, Collection[str]] = {},
) -> tuple[list[str], list[str]]:
    """Section 8's UNDERDETERMINED equality, in BOTH directions.

    Returns ``(declared and separable, inseparable and undeclared)``.  Both empty is the
    equality; either non-empty is a defect, and the two say different things -- a union that
    became separable keeps a declaration it has not earned, and one that stopped being
    separable carries no declaration at all and the value it constructs is then a property
    of declaration order with nothing saying so.

    ``records`` is document -> ``bundle.recorded``'s pair: the document of record, which is
    the verifier's own reading of what the document states (section 9), and the origin map
    beside it.

    **BOTH SIDES ARE SETS OF §8's IDENTITY, which is what makes this an equality at all
    (decided 2026-11-03).**  The declared side is identities by construction -- §8 sentence
    2 declares a fact once, at the node the document states it -- so the derived side has to
    be the same thing, and it is not what a record yields: a record spells one stating
    pointer once per path through the reference graph that reaches it.  So the derivation is
    read through :func:`inseparable_sites`, and an inlined occurrence resolves to the site it
    states rather than being counted as a site of its own.  Without that resolution the
    silent direction reports 89 sites for 24 unions and the equality is about the reference
    graph instead of about the declarations.

    **AND §3a's CATALOGUE IS THE SECOND RESOLUTION, for the same reason the first one is
    here.**  This docstring's own sentence about L0 -- "§3a settled the same question for a
    vocabulary: *the entry, not the declaration site*" -- reaches L2 the moment the object
    layer collects: a position whose type is a catalogue entry declares **nothing** in this
    module, so a union beneath it is not a site this document's module could declare at,
    and the entry's HOME states the same structure and is counted there.  ``collapsed`` is
    ``catalogue.Shapes.restating`` read for its pointers, document -> the pointers this
    document RESTATES, and a site at or beneath one of them resolves to the home's.

    Measured over this bundle: two sites,
    ``content-standards/update-content-standards-request.json`` at
    ``#/properties/calibration_exemplars/properties/{pass,fail}/items/oneOf``, whose
    ``calibration_exemplars`` is the same structure
    ``content-standards/create-content-standards-request.json`` states and whose two
    inseparable unions are declared there.  Without the resolution the silent direction
    reports them as undeclared, which is the per-DOCUMENT reading of a fact the catalogue
    makes per ENTRY -- and the class a consumer actually holds carries the declaration.

    Empty by default, which is the reading this instrument had before the object layer
    collected anything: a run with no catalogue restates every structure and every site is
    its own document's.
    """
    declared_at = {
        (one.document, one.pointer)
        for one in declared
        if one.kind == UNDERDETERMINED
    }
    inseparable = {
        site
        for document, (record, origins) in records.items()
        for site in inseparable_sites(record, origins)
        if not any(
            site[0] == document and site[1].lstrip("#").startswith(at)
            for at in collapsed.get(document, ())
        )
    }
    return (
        sorted(f"{d}{p}: declared UNDERDETERMINED and the derivation separates it" for d, p in declared_at - inseparable),
        sorted(f"{d}{p}: the derivation cannot separate these branches and nothing declares it" for d, p in inseparable - declared_at),
    )


def check_pair(
    pair: Pair,
    *,
    accepts_examples: int = 1,
    custom_formats: Mapping[str, Any] = (),
    corpus: Any = None,
    widening_corpus: Any = None,
    fixtures: "Fixtures | None" = None,
) -> PairReport:
    """ONE CLASS AGAINST ONE SCHEMA: the whole harness, per section 6.

    Resolve the document once (the caller's documents arrive resolved), draw a
    payload the schema accepts, construct the class from it, dump the instance and
    validate the dump against the schema; and send one payload the schema refuses
    through the entry point, which proves that class's schema half is connected.
    That is 1,055 units of work over the graded population rather than 27,791, and
    the only recursion anywhere in it belongs to reference resolution.

    **``max_steps`` and ``refuses_examples`` are gone with the check they
    parametrised.**  A step site mutated one keyword, drew an instance the mutated
    schema accepts, and handed it to ``accept`` -- which validates against THE
    DOCUMENT first, so the assertion was that ``jsonschema`` rejects a payload
    violating the schema it was handed and the generated class took no part in the
    outcome.  Nothing read the result of those 27,791 draws that a faithful class
    and a class carrying ``Any`` on every field did not produce identically.

    The payload the liveness check offers is DERIVED from the accepted instance
    (:func:`refusing_payload`) and screened by the document, so it costs no draw.
    That is the one place a pair's instance is reused, and the reuse is why there are
    two document validations per pair instead of thousands.

    **``corpus`` is handed straight to the accepts check, and ``widening_corpus`` to §8's
    obligation; they are TWO STORES over two key spaces** (``adcp-client-python-3be.25``).
    What stood here said the first was "handed to the accepts check and to nothing else,
    which is the whole of its reach: the liveness payload and §8's obligation both read the
    instance the accepts check produced, so a replayed instance reaches them exactly as a
    drawn one does and neither needs a store of its own."  The liveness half of that is
    still true -- :func:`refusing_payload` derives its payload and draws nothing.  The §8
    half was measured false: the obligation borrows the accepts instance as a BASE and then
    draws, from schemas it derives out of the pair's node, and :class:`_Draws` tabulates
    what those cost -- 246.7 s on one pair of ``core/async-response-data.json`` and over
    600 s on another, with the accepts draw already replayed from the committed floor in
    both.

    Two stores and not one, because the accepts floor's gate asserts in both directions
    that it holds no entry the graded population does not ask for, and a widening entry in
    that key space would read as a violation of an obligation nothing had broken.
    :func:`check_widening` carries the decision; ``tests/corpus.py`` holds both.

    :func:`check_accepts` says what a hit, a miss and a rejected entry each do, and
    :class:`WideningResult`'s ``drawn``/``replayed`` report the same thing for the second.

    The key the store is read under comes from :attr:`Pair.identity` and never from
    :attr:`Pair.schema`: the schema is a RENDERING of a document and the identity is the
    document, which is :func:`corpus_key`'s whole argument.  A ``corpus`` beside a pair
    carrying no identity raises there rather than keying on the rendering.
    """
    rep = PairReport(
        name=pair.name, model_repr=getattr(pair.model, "__name__", repr(pair.model))[:120]
    )
    rep.missing_formats = sorted(missing_formats(pair.schema, custom_formats))
    accepted: list[Any] = []
    #: **The instance checks need a self-contained schema, which is the whole of why
    #: this line exists.**  ``bundle.record`` inlines
    #: a remote reference and leaves a LOCAL one, so a nested node can say
    #: ``{"$ref": "#/definitions/rectangle"}`` -- a pointer into its DOCUMENT.  Handed
    #: that node alone, ``hypothesis_jsonschema``'s generator raises
    #: ``_RefResolutionError`` and the pair reports ``model_error``, which is a
    #: statement about the GENERATOR wearing the model's name: measured at 5 pairs
    #: over ``core/placement-presentation.json`` and
    #: ``core/bidding-policy-capability.json`` (``salesagent-j3k2l.28``).  Resolving
    #: against the document is what ``adcp.types._base._refuse`` does for the same
    #: reason, by evolving a document-rooted validator onto the node, so the schema
    #: the runtime decides with and the schema the harness draws from agree.
    #:
    #: FAIL-SAFE, and the direction matters: with no document supplied -- which is
    #: ``Pair``'s own default and what a caller grading a bare node passes -- a local
    #: ``$ref`` does not resolve and the library RAISES, so the unresolved node is
    #: used and the checks report what they report.  Resolution is a convenience for
    #: the generator, never a licence: a reference the resolution cannot inline leaves
    #: the node exactly as the document writes it, the draw raises there rather than
    #: widening anything silently, and the pair reports what the checks say instead of
    #: passing blind.
    try:
        drawn_from = resolve(pair.schema, store={}, referrer=pair.document)
    except Exception:  # any resolution failure falls back to the node
        drawn_from = pair.schema
    #: **§8's FIXTURE RULE, and it is a change to the DRAW and to nothing else.**  "A
    #: referenced document is graded by its own pair, so at a referring position it is a
    #: fixture and not a draw."  Every position under this node that the BUNDLE spells as a
    #: reference to another document is pinned to one instance that document admits
    #: (:class:`Fixtures`), and the draw then varies this class's OWN payload.  The result
    #: is a restriction of ``drawn_from``, so ``drawn_from`` stays what the dump, the
    #: liveness payload, the held corpus and §8's obligation are all decided by -- which is
    #: ``check_accepts``' ``draw_from`` argument and the reason it is a second argument
    #: rather than a replacement.
    #:
    #: FAIL-SAFE with no ``fixtures``: the pair draws exactly as it did before, which costs
    #: the time the rule exists to remove and grades the same thing.
    #:
    #: **AND THE SAME RULE KEYED ON THE NODE BEING GRADED, which is the half the reference
    #: rule cannot reach** (the owner's correction, 2026-11-04).  ``substitute`` asks the
    #: RAW document which positions refer, and at a COMPOSED position the answer is
    #: nothing: ``applied_schema`` conjoins the enclosing node's statements about the same
    #: instance, so the reference is in the graded node at a pointer the document does not
    #: spell.  :meth:`Fixtures.reduced` reads the frontier off the node itself and pins one
    #: value per instance location; :func:`locations` carries the rule and the measurement.
    #: Applied AFTER the reference rule and to its output, so the two savings compose
    #: instead of competing for the same pointer.
    #:
    #: **A THUNK AND NOT A NODE, which is what keeps the cost off the replayed path.**  The
    #: substitution derives a value per instance location, and the 2,674 pairs the
    #: committed floor answers draw nothing at all -- so this is forced inside
    #: ``check_accepts`` on a corpus MISS and nowhere else.  ``rep.fixtures`` and
    #: ``rep.pinned`` are therefore 0 on a replayed pair, which says what happened: no
    #: fixture was placed because no draw was made.
    def draw_from() -> dict | None:
        if fixtures is None or pair.ref is None:
            return None
        try:
            substituted, rep.fixtures = fixtures.substitute(
                drawn_from, pair.ref.document, pair.ref.pointer
            )
            substituted, rep.pinned = fixtures.reduced(substituted)
        except OverBudget:
            raise
        except Exception:  # noqa: BLE001 -- a derivation that raises loses the saving only
            rep.fixtures, rep.pinned = 0, 0
            return None
        return substituted if (rep.fixtures or rep.pinned) else None
    rep.accepts = check_accepts(
        drawn_from,
        pair.accept,
        examples=accepts_examples,
        custom_formats=custom_formats,
        seen=accepted,
        ref=pair.ref,
        corpus=corpus,
        identity=pair.identity,
        draw_from=draw_from,
    )
    #: Measured only where the generator errored, because that is the only pair the
    #: measurement says anything about -- 2 of 1,079 on the emitted tree, so the
    #: isolated draws cost nothing over the population.  The node is drawn from the
    #: SAME schema the accepts check drew from, so a position the resolution inlined
    #: is screened too.
    if rep.accepts.outcome == "strategy_error":
        rep.accepts_undrawable = undrawable_formats(drawn_from, custom_formats=custom_formats)
    rep.liveness = (
        check_liveness(drawn_from, pair.accept, accepted[0])
        if accepted
        else LivenessResult(outcome="no_payload", detail="the accepts check drew no instance")
    )
    #: **READING 1's FIRST CHECK OVER THE WITNESS THE DRAW CANNOT MAKE**
    #: (``adcp-client-python-87ll``).  ``_validating``'s own docstring already recorded why
    #: the drawn instance cannot decide this check at a formatted position --
    #: "hypothesis_jsonschema HONOURS a format it knows when generating ... so every drawn
    #: instance landed inside the narrow type and the draw was green on a model that
    #: refused every other shape the format admits" -- and that sentence was written about
    #: the format checker being ABSENT.  The checker is present; the sentence is still true
    #: about the DRAW, so 404 pairs of 2,587 passed reading 1 check 1 without the
    #: document's own wider value ever being offered.
    #:
    #: **IT COSTS NO DRAW.**  :func:`admitted_witnesses` is a REDUCTION of the same
    #: ``accepted[0]`` the two lines around it already reuse -- one ``conforms`` per
    #: candidate, plus one cached ``from_regex`` per distinct pattern of the bundle -- and
    #: never ``from_schema``, which is 74.9% of a pair.  Measured over the whole graded
    #: population in one process: 16.0 s.
    #:
    #: ``drawn_from`` and not ``pair.schema``, which is every instance check's rule here:
    #: the witness is screened against the node the instance was drawn from, so a position
    #: the resolution inlined is screened too.
    rep.admits = (
        check_admits(drawn_from, pair.accept, accepted[0])
        if accepted
        else AdmitsResult(outcome="unrun", detail="the accepts check drew no instance")
    )
    #: **READING 2's UNDECLARED DIRECTION, and the obstruction this line removes was the
    #: INSTANCE** (``adcp-client-python-x63t``).  ``check_refuses``' own docstring recorded
    #: the gap: "WHAT IS NOT HERE.  The sweep over the whole graded population, and the
    #: obstruction is the INSTANCE rather than the check: over that population the
    #: accepted instance is ``check_accepts``' draw, held under a key whose computation
    #: needs the pair."  ``check_pair`` is the frame that HAS the pair, so the instance is
    #: one argument away -- the same ``accepted[0]`` the liveness check above is already
    #: handed, which is why that line reuses it rather than drawing.
    #:
    #: **IT COSTS NO DRAW.**  :func:`refused_witnesses` is a REDUCTION of that one
    #: instance -- one ``conforms`` per keyword the node states about itself -- and never
    #: ``from_schema``, which is 74.9% of a pair (``tests/test_emit.py``'s
    #: ``GRADED_REPORTS_GROUP``).  So this ranges over the WHOLE graded population and not
    #: over a selection, which is the one thing it had to do: the 15-pair selection in
    #: ``tests/test_refuses_check.py`` is how an undeclared widening at an ``allOf``
    #: conjunct stayed invisible (``adcp-client-python-wvod``).
    #:
    #: **``construct`` AND NEVER ``pair.accept``**, which is the one rule
    #: :func:`check_refuses`' signature exists to enforce: ``accept`` validates against
    #: the DOCUMENT first, so a witness offered there measures ``jsonschema`` and the
    #: class takes no part in the outcome -- the exact shape of the 27,791-site instrument
    #: §8 deleted.  :func:`_constructor` is the reading of "the constructor" that answers
    #: for a class and for D2's root-scalar ALIAS alike.
    #:
    #: ``declared`` is the COMPOSED document's declarations by KEYWORD, which is
    #: ``pair.declared`` -- ``render.declared_at``'s containment rule, at or inside this
    #: node -- plus the declarations of every document a ``$ref`` inlined at it
    #: (:func:`composed_declarations`, which carries the measurement).  §2's rule is then
    #: a comparison and not an allowlist: an admission is a ``pass`` where a declaration
    #: names its keyword and ``widened_undeclared`` where none does.  The WIDENING check
    #: above keeps ``pair.declared`` and must: its obligation walks a declaration's
    #: pointer from this pair's node, and a pointer in another document's space describes
    #: no location it can reach.
    #:
    #: With no accepted instance there is nothing to reduce, and ``unrun`` says so rather
    #: than a pass: the table reads ``undeclared=absent:unrun``, which is a fact about the
    #: draw and not evidence about the class.
    rep.undeclared = (
        check_refuses(
            drawn_from,
            _constructor(pair.model),
            accepted[0],
            declared=tuple(
                one.keyword
                for one in (*pair.declared, *composed_declarations(pair.model))
            ),
        )
        if accepted
        else RefusesResult(outcome="unrun", detail="the accepts check drew no instance")
    )
    #: **Section 8's accepts obligation, and it runs only where a declaration claims
    #: something.**  "An approximation is a claim about this check, and this check is what
    #: proves it."  A pair declaring nothing owes nothing, so this costs no draw over the
    #: 769-module tree as it stands -- which is section 14 step 8's exit condition read
    #: from the verifier's side.
    #:
    #: The instances are the accepts check's OWN draws, so the obligation costs one draw
    #: per value class and no whole-document draw.  With none -- the accepts check drew
    #: nothing -- only a declaration at the pair's own root can be proved, and every other
    #: one is reported ``unproved`` rather than passed.  **The whole list and not the
    #: first**: a declaration can sit at a property one branch of the node's own union
    #: forbids, and :func:`check_widening` says why the base instance is a free choice
    #: among draws the pair has already paid for.
    if pair.declared:
        rep.widening = check_widening(
            drawn_from,
            pair.accept,
            pair.declared,
            at=pair.ref.pointer if pair.ref is not None else "#",
            instances=accepted,
            custom_formats=custom_formats,
            corpus=widening_corpus,
            identity=pair.identity,
            fixtures=fixtures,
            #: **The scope a DECLARED POINTER's ``allOf`` index is read in**, and the same
            #: object ``resolve`` above is handed for the neighbouring reason.  The
            #: obligation walks a declaration's pointer from ``drawn_from``, which is the
            #: ACCESSOR's node; at a union branch the accessor splices the enclosing node's
            #: same-instance statements in front of the branch's own conjuncts, so the
            #: index the document spells names one conjunct and the index into that node
            #: names another.  :func:`check_widening`'s ``document`` and :func:`_steps`'
            #: ``stated`` carry the reading and the four pointers it reaches.
            document=pair.document,
        )
    return rep


# --------------------------------------------------------------------------- #
# §10's per-pair verdict TABLE: the run's artifact
# --------------------------------------------------------------------------- #
#: The three states a check's verdict can take, and **the third is why this exists**.
#:
#: ``docs/plan/architecture.md`` §10: "one row per graded pair, written to a FILE by the
#: run -- document, pointer, and each check's verdict -- because a figure that exists only
#: in a terminal cannot be reviewed, and because a check that computed nothing shows up
#: there as a blank column instead of as a pass."
#:
#: The consequence that forces :data:`ABSENT` to be a VALUE rather than an empty cell has
#: already happened twice on this epic: two checks were counted as passing while having
#: never run at all -- one died at ``brand.json`` in a first loop before the loop holding
#: its assertion, and one raised in its own setup so it never computed anything.  In a
#: pass/fail summary a check that computed nothing is indistinguishable from success.  So
#: there is no empty cell anywhere in this table: every check of every pair reads
#: ``pass``, ``fail:<cause>`` or ``absent:<cause>``, and the two non-pass states each carry
#: the cause that produced them.
#:
#: **``absent`` is NOT ranked between the other two and is not a softer ``fail``.**  It
#: says the obligation was not put to the pair at all, which is a fact about the
#: INSTRUMENT; ``fail`` says the pair was asked and answered wrongly, which is a fact about
#: the class.  A reader who wants one or the other greps for the word; a reader who wants
#: "everything that is not a pass" greps for the absence of ``=pass``.
PASS = "pass"
FAIL = "fail"
ABSENT = "absent"

#: The checks a row carries, in the order the table's columns are written, and the
#: order is the order a defect is read in: the class took the value, the class refused what
#: the document refuses, what the class BUILT came back out, every declaration it makes
#: was earned, and nowhere is it wider than its document without saying so.  ``refuses`` is
#: this module's ``check_liveness`` under the name §10 and
#: ``adcp-client-python-82m.4`` give it; ``dump`` is the half of ``check_accepts`` that
#: reads what the class DID with the value, reported as its own column because it is its
#: own obligation and because ``AcceptsResult`` merges the two outcomes into one field.
#:
#: **``undeclared`` IS A FIFTH COLUMN AND THAT IS A CHANGE TO §10's TABLE**
#: (``adcp-client-python-x63t``).  §10 states the artifact as "one row per graded pair ...
#: document, pointer, and each check's verdict", so the table's width is whatever the set
#: of checks is -- and the set grew, because ``check_refuses`` existed with no caller on
#: the graded path: 308 lines whose only callers were a 15-pair selection in
#: ``tests/test_refuses_check.py`` and a spike reading a field ``PairReport`` did not have.
#: ``docs/plan/final-state.md`` reading 2 is one sentence with two directions -- "a model
#: may be wider than its document and never tighter; each widening is declared at its own
#: pointer" -- and with only ``widening`` in the table the second direction was graded and
#: the first was not, over the whole population and silently.
#:
#: **APPENDED and never inserted.**  ``verdict_table`` reads a row BY COLUMN POSITION
#: (the note field is free text and can carry an ``=`` of its own), so a column added in
#: the middle would renumber every reader's ``awk`` and silently re-point the census of
#: every check before it.  A column appended leaves ``accepts``, ``refuses``, ``dump`` and
#: ``widening`` at the positions they have always had, and the new one arrives at the end
#: of the row where a diff against the previous run shows it as an addition rather than as
#: four columns changing meaning.
#:
#: **``admits`` IS A SIXTH COLUMN AND IT IS APPENDED FOR THE RULE ABOVE**
#: (``adcp-client-python-87ll``).  It grades the SAME obligation ``accepts`` does --
#: reading 1's "every class accepts every value its document admits" -- over the witness
#: class the draw cannot produce, and it is its own column rather than folded into
#: ``accepts`` for two reasons.  The census of ``accepts`` is read ACROSS RUNS and ranges
#: over the instances a run drew; folding a second witness class into it would renumber
#: that census while saying nothing new about those instances.  And the two have different
#: REPAIRS: an ``accepts`` failure is a class that refused a value its generator produced,
#: and an ``admits`` failure is a pydantic type substituted for a document's ``format``
#: whose own rules are narrower -- which is a decision in ``codegen/lower/scalars.py`` and
#: not a defect at the pair.
CHECKS: tuple[str, ...] = ("accepts", "refuses", "dump", "widening", "undeclared", "admits")


@dataclass(frozen=True)
class Verdict:
    """One check's answer about one pair: a state and the cause that produced it.

    Rendered ``pass``, ``fail:<cause>`` or ``absent:<cause>``.  A ``pass`` carries no
    cause, and that asymmetry is deliberate: the two states a reader acts on are the two
    that say WHY, and a pass that carried a cause would invite a grep for the cause rather
    than for the state.
    """

    state: str
    cause: str = ""

    def __str__(self) -> str:
        return self.state if not self.cause else f"{self.state}:{self.cause}"


def _accepts_verdict(a: AcceptsResult | None) -> Verdict:
    """Did the class admit every drawn payload the document admits.

    ``pass`` demands that the check COVERED its obligation, which is why the instance
    counts are read and not only ``outcome``: the draw is asked for ``examples``
    instances, each is offered to the entry point, and the first one the class refuses
    ends the run -- so an ``outcome`` of anything but ``pass`` means the later instances
    were never offered.

    ``model_dropped_a_fact`` is ABSENT here and FAIL under ``dump``, and that is the one
    split in this function that is not obvious.  ``check_accepts`` runs both halves per
    instance and reports one outcome, so a dump the document refuses stops the accepts
    half too -- and reporting that as an accepts failure would name the wrong check,
    while reporting it as an accepts pass would claim an obligation the run abandoned.
    ``absent:stopped_at_the_dump`` says exactly what happened and points at the column
    that carries the verdict.

    ``strategy_error`` is ABSENT for the reason :attr:`PairReport.no_instrument` already
    gives: the generator produced nothing, so the class was never asked anything.  An
    unknown outcome is FAIL and never a pass, so an outcome added to ``check_accepts``
    later cannot enter this table as a green cell.
    """
    if a is None:
        return Verdict(ABSENT, "unrun")
    if a.outcome == "pass":
        if not a.examples:
            return Verdict(ABSENT, "no_instance_was_drawn")
        return Verdict(PASS)
    if a.outcome == "model_dropped_a_fact":
        return Verdict(ABSENT, "stopped_at_the_dump")
    if a.outcome in ("strategy_error", "unrun"):
        return Verdict(ABSENT, a.outcome)
    return Verdict(FAIL, a.outcome)


def _dump_verdict(a: AcceptsResult | None) -> Verdict:
    """Did the instance the class BUILT validate against the document it names.

    Its own column because it is its own obligation -- "a class that takes an instance
    and loses a key, or renames one, or coerces it to a shape the document refuses,
    accepts every instance there is" -- and because ``AcceptsResult`` carries both
    answers in one ``outcome`` field, so a reader of that field alone cannot tell which
    half spoke.

    ``pass`` is every drawn instance round-tripped and not merely one: ``round_tripped``
    counts the instances the document admitted the dump of, so the equality with
    ``examples`` is what makes this a statement about the draw rather than about its
    first value.  A dump that needed a ``codegen.dump_exemptions`` strike is still a
    pass here and the strike is reported in the row's note, which is
    :attr:`AcceptsResult.dump_exempt`'s own rule: a non-empty list beside a pass is a
    CONDITIONAL pass and a reader of a green pair is entitled to see it.
    """
    if a is None:
        return Verdict(ABSENT, "unrun")
    if a.outcome == "model_dropped_a_fact":
        return Verdict(FAIL, "model_dropped_a_fact")
    if not a.round_tripped:
        return Verdict(ABSENT, "no_instance_reached_the_dump")
    if a.round_tripped != a.examples:
        return Verdict(ABSENT, f"stopped_after_{a.round_tripped}_of_{a.examples}")
    return Verdict(PASS)


def _refuses_verdict(live: LivenessResult | None) -> Verdict:
    """Did the class refuse a payload the document refuses.

    ``no_payload`` is ABSENT and not a pass: it says the derivation found no payload to
    offer -- either because the draw produced no instance to perturb or because the
    document refuses nothing -- so the entry point was never asked.  Both causes are
    facts about the document and the draw, and neither is evidence about the class.
    """
    if live is None:
        return Verdict(ABSENT, "unrun")
    if live.outcome == "pass":
        return Verdict(PASS)
    if live.outcome in ("no_payload", "unrun"):
        return Verdict(ABSENT, live.outcome)
    return Verdict(FAIL, live.outcome)


def _widening_verdict(w: WideningResult | None) -> Verdict:
    """For each declaration at this pair, was it proved by a value.

    ``None`` and ``no_declarations`` are the same fact -- the pair claims nothing, so
    nothing is owed -- and both read ABSENT rather than ``pass``: a pair that was never
    asked has earned no verdict, and a table where "claims nothing" and "proved every
    claim" share a cell cannot be used to count either.
    """
    if w is None:
        return Verdict(ABSENT, "no_declarations")
    if w.outcome == "pass":
        return Verdict(PASS)
    if w.outcome == "no_declarations":
        return Verdict(ABSENT, "no_declarations")
    return Verdict(FAIL, w.outcome)


def _undeclared_verdict(r: RefusesResult | None) -> Verdict:
    """Is the class wider than its document anywhere the module does not SAY it is.

    Reading 2's undeclared direction, which no column of this table carried until
    ``adcp-client-python-x63t``: ``widening`` beside it grades the declarations that
    exist, and a widening nobody declared is invisible to that check by construction --
    ``check_widening`` iterates ``pair.declared``, so a pair declaring nothing owes it
    nothing and reads ``absent:no_declarations``, which is exactly the cell a dropped fact
    produces.

    ``no_witness`` is ABSENT and not a pass, for the reason :func:`check_refuses` gives:
    "a document that refuses nothing this reduction can build -- an open typeless object,
    which draft-07 admits every instance of -- has nothing for the class to refuse, and
    the pair is neither graded nor failed."  A pass here would make a pair that offered
    NOTHING read identically to one that offered every witness and refused each, which is
    the shape §8 deleted an instrument for.

    ``model_error`` is FAIL and not ABSENT, and that is the one split here that is not
    obvious.  It says the constructor raised something that is not a ``ValidationError`` --
    not a refusal a consumer could catch -- which is a fact about the CLASS and not about
    the instrument; the witness was built, screened by the document and offered, so the
    pair was asked and answered badly.  An unknown outcome is FAIL for
    :func:`_accepts_verdict`'s reason: an outcome added to ``check_refuses`` later cannot
    enter this table as a green cell.

    **AND A PASS WITH AN UNREACHED CONDITIONAL IS ``absent`` AND NOT A PASS**, which is
    ``_dump_verdict``'s ``stopped_after_N_of_M`` rule applied to the boundary this check
    can miss.  A conditional's boundary lies inside the region its ``if`` selects and the
    reduction has one drawn instance, so where that instance is outside the region there is
    no arm in force and the class is never asked
    (:func:`unreached_conditionals`).  Measured on ``adcp-client-python-wvod``'s third
    site, which drew an instance carrying no ``authentication`` and so satisfied neither of
    its two ``if``s: a ``pass`` there would have claimed a green on the one fact the row is
    about.  A FAILURE still wins over this -- a widening found is a verdict about the
    class, and an unreached boundary is a fact about the draw.
    """
    if r is None:
        return Verdict(ABSENT, "unrun")
    if r.outcome == "pass":
        if r.unreached:
            return Verdict(
                ABSENT, f"{len(r.unreached)}_of_{r.conditional_sites}_conditionals_unreached"
            )
        return Verdict(PASS)
    if r.outcome in ("no_witness", "unrun"):
        return Verdict(ABSENT, r.outcome)
    return Verdict(FAIL, r.outcome)


def _admits_verdict(r: AdmitsResult | None) -> Verdict:
    """Is the class NARROWER than its document at a value the draw cannot produce.

    Reading 1's first check over :func:`admitted_witnesses`, and the three states are the
    three the column beside it already uses.

    ``no_witness`` is ABSENT and not a pass, for :func:`_undeclared_verdict`'s reason: the
    document admitted none of the candidates this derivation makes, so the class was never
    asked, and a pass would make a pair that offered NOTHING read identically to one that
    was offered every witness and admitted each.  That is the shape this whole column
    exists to remove one level down.

    **AND A PASS OVER A CAPPED INSTANCE IS ``absent``**, which is ``_dump_verdict``'s
    ``stopped_after_N_of_M`` rule applied to :data:`WITNESS_LEAVES`.  An instance carrying
    more string leaves than the budget reaches was probed over a prefix of them, so "the
    class admitted every value the document admits" is a claim about the prefix; 18 of
    2,582 instances are in that case.  A REFUSAL still wins -- a narrowing found is a
    verdict about the class, and an unprobed leaf is a fact about the budget.
    """
    if r is None:
        return Verdict(ABSENT, "unrun")
    if r.outcome == "pass":
        if r.capped:
            return Verdict(ABSENT, f"stopped_after_{WITNESS_LEAVES}_leaves")
        return Verdict(PASS)
    if r.outcome in ("no_witness", "unrun"):
        return Verdict(ABSENT, r.outcome)
    return Verdict(FAIL, r.outcome)


def verdicts(report: PairReport | None, *, error: str = "") -> dict[str, Verdict]:
    """This pair's verdict per check, or one ABSENT verdict per check with the cause.

    ``error`` is the row for a pair that never reached a check at all -- the pairing
    raised building it, or a check raised out through this module.  It is the case
    ``adcp-client-python-82m.4`` is about: "one raised in its own setup so it never
    computed anything", and in a per-pair table that has to be one blank column per
    check, each with a cause, not a missing row.  A pair with no report and no error named is still
    ABSENT in every column, because there is nothing else it could honestly be.
    """
    if error or report is None:
        cause = error or "not_graded"
        return {check: Verdict(ABSENT, cause) for check in CHECKS}
    return {
        "accepts": _accepts_verdict(report.accepts),
        "refuses": _refuses_verdict(report.liveness),
        "dump": _dump_verdict(report.accepts),
        "widening": _widening_verdict(report.widening),
        "undeclared": _undeclared_verdict(report.undeclared),
        "admits": _admits_verdict(report.admits),
    }


def evidence_of(report: PairReport | None) -> str:
    """Whether this pair's instances were DRAWN by this run or replayed from a store.

    §10's row has to say which run paid for the evidence, which is
    :attr:`AcceptsResult.replayed`'s own argument one level up: "the instances are the
    same instances either way -- re-offered to the document before they count -- but a
    reader of a green pair is entitled to know which run paid for its evidence, and a
    census that cannot tell the two apart cannot measure a cold run against a warm one."

    ``none`` where no instance exists, which is not the same as ``drawn`` with a count of
    zero: a pair whose generator produced nothing paid a draw and holds no instance, and
    the count beside this says so.
    """
    if report is None or report.accepts is None or not report.accepts.examples:
        return "none"
    a = report.accepts
    if a.replayed == a.examples:
        return "replayed"
    if not a.replayed:
        return "drawn"
    return "mixed"


def _cell(text: Any) -> str:
    """One field of one row, with every character that would break a column removed.

    A tab inside a field would make the column count differ between rows, and a newline
    would make one pair two rows -- so both are replaced rather than quoted.  Quoting is
    what CSV does and it is what makes a CSV ungreppable: a reader's ``grep`` and ``awk``
    would each need the quoting rule.  A field is therefore guaranteed free of the two
    characters that carry structure, and the format needs no escape at all.
    """
    return (
        str(text).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip() or "-"
    )


#: The table's column names, in order.  ``class`` is the model's own name, which is what a
#: reader looking for a pair in the emitted tree greps for.
COLUMNS: tuple[str, ...] = (
    "document",
    "pointer",
    "class",
    "verdict",
    *CHECKS,
    "examples",
    "evidence",
    "note",
)


def _pair_verdict(report: PairReport | None, error: str) -> str:
    """:attr:`PairReport.outcome`, in the three-state spelling the cells beside it use.

    ``absent`` for a pair that reached no check -- an error building it, no held instance,
    a budget spent -- and for the two outcomes that say the GENERATOR produced nothing
    (``no_instrument``, ``accepts:strategy_error``) or that nothing was graded
    (``no_accepts_check_evidence``).  ``fail`` for every outcome that is a verdict about
    the class.  ``pass`` only for a pass.

    Stated as a function rather than inline, because the mapping has to agree with the
    per-check cells and an inline conditional in a row builder is where the two drift.
    """
    if error or report is None:
        return f"{ABSENT}:{error or 'not_graded'}"
    outcome = report.outcome
    if outcome == "pass":
        return PASS
    if outcome in ("no_instrument", "accepts:strategy_error", "no_accepts_check_evidence"):
        return f"{ABSENT}:{outcome}"
    return f"{FAIL}:{outcome}"


def verdict_row(
    ref: SchemaRef | None,
    report: PairReport | None,
    *,
    name: str = "",
    model: str = "",
    error: str = "",
) -> str:
    """One pair's row: its document, its pointer, its class and one verdict per check.

    **Each check's cell is written ``<check>=<verdict>`` and not bare**, which is the one
    redundancy in this format and the reason the format is usable.  ``docs/plan`` asks for
    an artifact that is greppable AND diffable, and a reviewer's two questions are "show me
    every pair that fails dump" and "what changed since the last run".  Bare cells answer
    the second (one line per pair, stable order, so a diff is a diff of verdicts) and
    answer the first only through the column number, which a reader has to count and which
    moves whenever a check is added.  Named cells answer it with ``grep dump=fail``, and
    the columns are still there for ``awk``.

    ``name`` stands in where there is no ``ref`` -- a pair the pairing could not build --
    so that a row exists for it: a pair missing from the table is the blank column this
    artifact exists to remove, one level up.
    """
    document, pointer = (ref.document, ref.pointer) if ref is not None else (name, "")
    if ref is None and "#" in name:
        document, _, rest = name.partition("#")
        pointer = "#" + rest
    v = verdicts(report, error=error)
    a = report.accepts if report is not None else None
    notes: list[str] = []
    if error:
        notes.append(error)
    if a is not None:
        if a.detail:
            notes.append(a.detail)
        if a.counterexample:
            notes.append(f"counterexample {a.counterexample}")
        if a.dump_exempt:
            notes.append(f"dump exempt at {', '.join(a.dump_exempt)}")
    #: **THE NARROWING'S OWN VALUE, for the reason the note above carries one**: a row
    #: saying a class is narrower than its document and nothing else leaves the reader to
    #: rebuild the witness before they can act, and reading 1 is about values.  The
    #: witness, how it was DERIVED -- which is the half that says the value is the
    #: document's and not the instrument's invention -- and the class's own error, so the
    #: two reasons can be compared without re-running anything.
    #:
    #: ONE row and not two, because the witness text is up to :data:`WITNESS_LENGTH`
    #: characters and the whole note field is truncated to 400: a second would push the
    #: first one's reason past the cut, which is the failure mode ``check_accepts``' own
    #: "the CAUSE goes first" comment names.  The count travels with it.
    #:
    #: **PLACED HERE, IN THE ORDER :attr:`PairReport.outcome` RANKS THE CHECKS**, and
    #: measured rather than tidy: written last it sat behind ``undeclared``'s unreached
    #: conditionals, whose sentence quotes the document's own ``if`` region, and on
    #: ``aao/agent-publishers.json#/definitions/PublisherEntry`` that pushed this pair's
    #: whole cause past the 400-character cut.  A note field whose order disagrees with
    #: the verdict's order loses exactly the reason the verdict names.
    if report is not None and report.admits is not None:
        m = report.admits
        #: ``refusal`` and NOT ``error``, which is the function's own parameter: bound here
        #: it shadowed it, and ``_pair_verdict(report, error)`` below then read the CLASS's
        #: ValidationError as "this pair reached no check at all" -- so every one of the
        #: 444 narrowings read ``verdict=absent:<pydantic's message>`` where the cell
        #: beside it read ``admits=fail:model_refused_admitted``.  ``absent`` and ``fail``
        #: are the one distinction this artifact exists to make, and a row that spells a
        #: verdict about the CLASS as a fact about the INSTRUMENT is the defect
        #: :data:`ABSENT` carries its whole comment about.
        #: **THE CAUSE GOES FIRST**, which is ``check_accepts``' own rule about this field:
        #: the note is truncated to 400 characters and a witness is up to
        #: :data:`WITNESS_LENGTH`, so a cause written after the value is a cause nothing
        #: can read.  Measured on the first table that carried this column: 345 of 444
        #: rows had their error type cut off.
        for witness, kind, how, cause, refusal in m.rows[:1]:
            notes.append(
                f"narrower than its document [{cause}] on {kind}: {how}; the class "
                f"refused it with {refusal[:120]}; the document admits {witness[:120]}"
            )
        if m.refused > 1:
            notes.append(f"and {m.refused - 1} more admitted values refused")
        if m.detail and m.outcome != "pass":
            notes.append(m.detail)
    if report is not None and report.missing_formats:
        notes.append(f"no strategy for format {', '.join(report.missing_formats)}")
    if report is not None and report.liveness is not None and report.liveness.detail:
        notes.append(report.liveness.detail)
    if report is not None and report.widening is not None:
        w = report.widening
        notes.extend(w.narrowings[:2])
        notes.extend(w.unproved[:2])
        if w.detail:
            notes.append(w.detail)
    #: **The undeclared widening's own VALUE, because reading 2 is about values.**  "Every
    #: declaration holds a value that demonstrates it", and the complement of that is that
    #: an undeclared widening is reported with the value that demonstrates IT -- otherwise
    #: a row says a class is too wide and the reader has to rebuild the witness to see
    #: where.  The keyword the reduction AIMED at is beside it, and the keywords the
    #: document actually refused on, which is the split :func:`refused_witnesses` names:
    #: those are ``violated_keywords``' answer and not the aim.
    #:
    #: **Two rows at most, exactly as the widening notes above are capped.**  A pair can be
    #: wider on every keyword its node states and the note field is one cell of one line;
    #: the count travels with them so a reader of the cap knows it is a cap.
    if report is not None and report.undeclared is not None:
        r = report.undeclared
        for candidate, keyword, refused_on, _ in r.undeclared[:2]:
            notes.append(
                f"undeclared widening on {keyword}: the class admitted {candidate} "
                f"which the document refuses on {', '.join(refused_on) or '(unnamed)'}"
            )
        if len(r.undeclared) > 2:
            notes.append(f"and {len(r.undeclared) - 2} more undeclared witnesses")
        notes.extend(r.unreached[:2])
        if len(r.unreached) > 2:
            notes.append(f"and {len(r.unreached) - 2} more unreached conditionals")
        if r.detail:
            notes.append(r.detail)
    return "\t".join(
        _cell(x)
        for x in (
            document,
            pointer,
            model or (report.model_repr if report is not None else ""),
            #: The PAIR's one verdict, in the same three-state spelling as the cells
            #: beside it, so "every row that is not a pass" is one grep whichever column
            #: a reader reaches for.  A pair that reached no check at all reads
            #: ``absent`` and never ``fail``: the distinction is the whole artifact.
            f"verdict={_pair_verdict(report, error)}",
            *(f"{check}={v[check]}" for check in CHECKS),
            f"examples={a.examples if a is not None else 0}",
            f"evidence={evidence_of(report)}",
            "; ".join(notes)[:400],
        )
    )


def verdict_table(rows: Sequence[str]) -> str:
    """The whole artifact: a preamble of counts, the column names, then the sorted rows.

    **Sorted by the row text, which begins with the document and the pointer**, so the
    order is a function of the population and not of the order a run happened to grade in.
    That is what makes ``diff`` between two runs a diff of VERDICTS: an xdist run hands
    pairs out in whatever order its workers finish, and an unsorted table would differ from
    itself on every run.

    **The preamble carries counts and NOTHING THAT MOVES ON ITS OWN** -- no timestamp, no
    duration, no path, no worker count.  A run's wall clock belongs on stdout, where it is
    read once; in the file it would make every diff report a change when nothing about the
    SDK had changed, which is the one way a diffable artifact stops being diffed.

    The preamble is ``#``-prefixed, so ``grep -v '^#'`` is the whole of "give me the rows"
    and every reader's ``awk`` sees a rectangle.
    """
    body = sorted(rows)
    per_check: dict[str, Counter[str]] = {check: Counter() for check in CHECKS}
    pair_states: Counter[str] = Counter()
    for row in body:
        #: Read by COLUMN POSITION and not by splitting on ``=``: the note field is free
        #: text and can carry an ``=`` of its own -- a counterexample is a dumped JSON
        #: instance -- so a name-based reading would let a note name a column.  The
        #: positions come from :data:`COLUMNS`, which is the same declaration the row was
        #: written from.
        cells = row.split("\t")
        by_name = {
            name: cells[i].split("=", 1)[1] if "=" in cells[i] else cells[i]
            for i, name in enumerate(COLUMNS)
            if i < len(cells)
        }
        for check in CHECKS:
            per_check[check][str(by_name.get(check, ABSENT)).split(":")[0]] += 1
        pair_states["pass" if by_name.get("verdict") == "pass" else "not_pass"] += 1
    head = [
        f"# verdicts over {len(body)} graded pairs: "
        f"{pair_states['pass']} pass, {pair_states['not_pass']} not pass",
        "# "
        + "  ".join(
            f"{check} {per_check[check][PASS]}/{per_check[check][FAIL]}/"
            f"{per_check[check][ABSENT]}"
            for check in CHECKS
        )
        + "   (pass/fail/absent)",
        "# a cell is pass, fail:<cause> or absent:<cause>; absent is NOT a pass -- it is "
        "the check that was never put to this pair",
        "\t".join(COLUMNS),
    ]
    return "\n".join([*head, *body]) + "\n"


# --------------------------------------------------------------------------- #
# THE PAIRING: which emitted class answers which document and pointer
# --------------------------------------------------------------------------- #
class Paired(NamedTuple):
    """One pair of an emitted tree, as :func:`pairs` finds it.

    The ``SchemaRef`` the holder declares, the model, the entry point an instance is
    offered through, and the DEFINING module's name.
    """

    ref: SchemaRef
    model: Any
    accept: Any
    module: str


def pairs(package: Any, path: Sequence[str] | None = None) -> tuple[list[Paired], dict[str, str]]:
    """Every class and alias ``package`` carries, with the schema each one names.

    ``path`` is WHICH DIRECTORIES the walk enumerates, defaulting to the package's own
    ``__path__``.  A caller passes one when the package resolves from more than one
    directory and only one of them is the subject: ``codegen/__main__.py`` prepends the
    tree the run just WROTE to ``adcp.types._schemas.__path__`` so that the absolute
    imports an emitted module writes reach this run's output, and then grades the written
    tree ALONE -- a module the run did not write resolves from the committed tree behind
    it, and grading it would put a pair in the table that this run says nothing about.
    The modules are still IMPORTED under the full package name, because an emitted module
    says ``from adcp.types.constraints import ...`` and cannot be loaded from a path.

    **HERE because the pairing is a READING OF THE EMITTED TREE, which is what §9 says
    this module does** -- "the verifier reads the document of record and the emitted
    package, and never the walk that produced them" -- and because there must be exactly
    ONE pairing.  ``tests/compared.py`` carries the argument for the second half and it
    applies to any second reader, this one included: "a reader with a pairing of its own
    would range over however many pairs that second walk turned out to find, and the two
    would disagree silently the moment either moved."  The run writes the table and the
    suite grades the population, so both need the pairing; stated twice it is the
    two-populations defect, and the suite's module is not importable from the run.  So the
    walk is here, ``tests/compared.py`` performs it against the FRESH tree and keeps every
    decision about WHICH tree, and ``codegen/__main__.py`` performs it against the tree the
    run just wrote.

    A class is taken from the module that DEFINES it (``__module__``) and ONCE per module
    whatever names it is bound under (by ``id``), because D3's content dedup gives one
    class a name at every position its node occupies -- keyed on names the pair count read
    1,085 where 1,079 pairs existed.

    **:class:`SchemaBound` and not the base model is the predicate**, because §8 requires a
    ROOT MODEL to be paired exactly as a class is: "each must carry ``__adcp_schema__``,
    ``strict_validate`` and a rule tuple exactly as a class does, or a root model and a
    class disagree about what their document accepts."  ``SchemaBound`` is the mixin that
    carries those two, so it is the predicate that says "this object is a pair".

    An ALIAS is D2's root-scalar row -- not a class, so its MODULE carries
    ``__adcp_schema__`` and ``strict_validate``, and the model is the one name the module
    exports.

    **A module that does not import is RECORDED and never raised**, and the second return
    value is that record.  A raise here takes down whatever is reading: in the suite it
    errors a COLLECTION, which was measured as one unimportable module collecting ZERO
    tests -- every pair, every census and the import obligation itself, gone, with the
    reader left holding a traceback instead of a named failure.  In the run it would take
    down the verdict table, which is the artifact that exists to REPORT such a module.
    ``docs/plan/architecture.md``'s rule for it is "a tree that does not build fails one
    named test instead of disabling the file".
    """
    out: list[Paired] = []
    unimportable: dict[str, str] = {}
    if package is None:
        return out, unimportable
    walked = pkgutil.walk_packages(
        list(package.__path__ if path is None else path), package.__name__ + "."
    )
    for info in sorted(walked, key=lambda i: i.name):
        try:
            module = importlib.import_module(info.name)
        except Exception:  # recorded, never raised; see the docstring
            unimportable[info.name] = traceback.format_exc(limit=3)[-600:]
            continue
        taken: set[int] = set()  # by IDENTITY: one class, one pair, whatever it is called
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, SchemaBound)
                and "__adcp_schema__" in value.__dict__
                and value.__module__ == info.name
                and id(value) not in taken
            ):
                taken.add(id(value))
                out.append(
                    Paired(value.__adcp_schema__, value, value.strict_validate, info.name)
                )
        ref = vars(module).get("__adcp_schema__")
        if isinstance(ref, SchemaRef) and callable(vars(module).get("strict_validate")):
            (symbol,) = module.__all__
            out.append(Paired(ref, getattr(module, symbol), module.strict_validate, info.name))
    return out, unimportable


#: Seconds between retries of :func:`within`'s timer once the budget has been spent.  Not a
#: second budget: it is how long a SWALLOWED signal costs, and the docstring below measures
#: why a swallowed signal is reachable at all.  Short enough that the bound still bounds,
#: long enough that a block already unwinding is not re-interrupted on every bytecode.
_BUDGET_RETRY = 2.0


class OverBudget(BaseException):
    """One pair's grade spent the budget a caller gave it; see :func:`within`.

    **NOT an ``Exception``, and that is the whole of ``adcp-client-python-pjc``'s third
    part.**  Every check in this module ends in a broad handler that turns what it caught
    into a VERDICT about a document -- ``check_accepts``' last clause is "a model that
    raises something other than ``ValidationError``" and spells it ``model_error``,
    :func:`conforms` answers ``None`` for "the document is not usable as a validator",
    :func:`undrawable_formats` names the position, :meth:`_Draws._draw` says "this position
    cannot be drawn".  A budget cut reaching any of them is read as a fact about the
    document, and it is a fact about THIS PROCESS's clock.

    **Measured over all 2,793 graded pairs at a 20 s budget: 73 reported
    ``accepts:model_error`` and every one of the 73 was a cut.**  So the category that
    means "the model raised" held nothing but the instrument, and a cut was spelled exactly
    like a defect -- only the clock told them apart.  Those 73 are false reds in the one
    column a reader scans for real ones.

    **Outside ``Exception`` and not re-raised at each site, because the sites are the
    problem.**  There are more than twenty broad handlers between :func:`within` and the
    draw, two of them inside ``hypothesis``, and a rule that has to be restated at each one
    is a rule that is missing from the next one somebody writes.  ``BaseException`` is the
    language's own answer to "this is not a failure of the code it passes through", which
    is what ``KeyboardInterrupt`` and ``SystemExit`` are, and a cut is the same kind of
    thing: the caller stopped asking.  A cut is then catchable only BY NAME, which is how
    ``codegen/__main__.py`` has always caught it -- one row, with the budget in the cause,
    distinct from every verdict in the table.

    **Measured that it still arrives, which is the one thing this change could have broken.**
    A ``SIGALRM`` handler raising a ``BaseException`` subclass from inside
    ``hypothesis``'s draw machinery -- past ``core.py``'s own two ``except BaseException``
    frames -- propagates past an enclosing ``except Exception`` as the same type, with the
    same message, at the same latency as the ``Exception`` subclass did (4.0 s against a 4 s
    budget, on a draw with no filtering in it).  ``hypothesis`` re-raises what it did not
    recognise as a test failure rather than wrapping it, which is the behaviour
    ``KeyboardInterrupt`` already depends on.

    :func:`within` says what forces a budget at all, and ``Refusal``'s "nothing raises one
    and nothing catches one" is about a different class for a different reason.
    """


@contextmanager
def within(seconds: int) -> Iterator[None]:
    """Give the enclosed grade ``seconds`` of wall clock, then raise :class:`OverBudget`.

    **A budget belongs to GRADING and so it is here**, which is the division
    ``_DumpRefused`` already stands in: an exception raised inside a check and caught BY
    NAME one frame out, carrying a verdict about one pair rather than a refusal of any
    document.  §2's "nothing raises one and nothing catches one" is about
    :class:`codegen.refusal.Refusal`, and this is not one -- a pair the harness cannot
    grade inside a budget is a statement about the INSTRUMENT, which is exactly what
    ``PairReport.no_instrument`` and the verdict table's ``absent`` already report.

    **What forces a budget at all.**  §8's obligation derives its draws from the declared
    pointer, so which positions a pair asks for is known only by running it and no caller
    can pre-check a store for them; and a draw over a multi-megabyte node has no bound of
    its own -- measured at 2 h 57 m and 32 GB of RSS on one 44 MB node without finishing
    (``adcp-client-python-3be.26``).  A reader of the verdict table needs the table more
    than it needs that pair's verdict, and an unobtainable artifact is the terminal figure
    §10 replaced.

    ``SIGALRM`` and not a thread, because the harness is pure Python on the calling thread
    and a timer that cannot interrupt it is not a bound.  **Main thread only** -- the
    signal module raises ``ValueError`` elsewhere, which is the honest failure: a caller
    that cannot be bounded finds out rather than believing it is.

    **REPEATING, and that is measured rather than tidy.**  A one-shot ``signal.alarm``
    does not bound anything, because the signal can land in a context where Python
    DISCARDS the exception it raises -- a garbage-collection callback or a ``__del__`` --
    and ``hypothesis`` installs one (``junkdrawer.gc_callback``).  Measured: a one-shot
    alarm fired twice inside that callback, was ignored both times with "Exception ignored
    in", and the pair then ran 13 minutes against a 45 s budget with no alarm left to
    fire.  So the timer repeats until the block exits and a swallowed signal costs the
    interval and not the bound.

    The previous handler is restored on the way out, and the timer is cleared BEFORE the
    restore, so a signal that fires during teardown cannot reach a handler that is no
    longer the one this block installed.
    """
    import signal

    def over(signum: int, frame: Any) -> None:
        _FIRED[0] = True
        raise OverBudget(f"the grade did not finish inside {seconds} s")

    previous = signal.signal(signal.SIGALRM, over)
    was = _FIRED[0]
    _FIRED[0] = False
    signal.setitimer(signal.ITIMER_REAL, seconds, _BUDGET_RETRY)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        _FIRED[0] = was


#: Whether the alarm :func:`within` installed has already raised, read by
#: :func:`budget_expired`.  A list and not a module name rebound, so the handler can set it
#: from inside a signal frame without a ``global`` statement.
_FIRED = [False]


def budget_expired() -> bool:
    """Whether the enclosing :func:`within` has already cut this grade.

    **The clause :class:`OverBudget`'s type alone could not carry, and it is measured.**
    Making ``OverBudget`` a ``BaseException`` stops an enclosing ``except Exception`` from
    reading a cut as a verdict, and that works for the cut ITSELF.  It does not work when
    something between the alarm and the handler SWALLOWS the cut and raises its own
    exception instead -- and ``hypothesis`` does exactly that: the first ``OverBudget``
    lands inside a draw, ``hypothesis`` re-runs the strategy to see whether the failure
    reproduces, the second run behaves differently because the alarm interrupted the first
    one, and what arrives at ``check_accepts`` is ``FlakyStrategyDefinition`` -- an
    ordinary ``Exception`` in the ``HypothesisException`` family, caught by name, reported
    as ``accepts:strategy_error``.

    Measured over all 2,793 graded pairs at a 20 s budget, single process: 2 pairs reported
    ``accepts:strategy_error`` and both were cuts, each at 20.2 s against the 20 s budget,
    each with ``FlakyStrategyDefinition: Inconsistent data generation!`` as its whole
    detail -- ``core/signal-coverage-forecast.json#`` and
    ``media-buy/media-buy-commitment-response.json#/oneOf/0``.  So the column that means
    "the generator produced nothing for this schema" held two facts about this process's
    clock, which is the same defect the 73 false ``model_error``s were, arriving by a
    different door.

    **So a handler that is about to name a document asks the CLOCK first.**  Once the
    alarm has fired, nothing that follows it inside the same :func:`within` is a statement
    about the document: the draw was interrupted part-way and whatever the interrupted
    machinery then raised is an artefact of the interruption.  The three handlers that turn
    an arbitrary exception into a reported outcome re-raise :class:`OverBudget` instead.

    ``False`` with no :func:`within` active, so a caller grading without a budget -- every
    direct caller in ``tests/`` -- is untouched.
    """
    return _FIRED[0]
