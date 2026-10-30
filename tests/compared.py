"""§8's COMPARISON over every pair of the fresh tree, in under a minute.

**Why this is a module of its own, measured.**  The comparison is the one check of §8
that can see a model WIDER or NARROWER than its document, and until this row its reading
existed in exactly one place: two tests in ``tests/test_emit.py`` that read it off
``graded()`` and ``graded_reports()``.  That pass is the suite's pole -- 2,793 pair
reports, a draw and a dump per pair, 55 minutes at best and 6-7 hours as the tree stands,
and twice killed by the kernel (``pyproject.toml``'s memory paragraph is the reading).  So
the instrument that would have said "155 pairs are red" did not run, and
``COMPARISON_FACTS`` sat at **0 entries against a live 155 pairs carrying 1,086 facts**
with nothing red anywhere.  That is the ninth stale census of this epic and the second of
exactly this shape: ``tests/test_the_declared_backlog.py`` records the first --
"``DECLARED_WIDENINGS`` came to hold 11 sites against a live 117 ... with nothing red" --
and this module is that row's remedy applied to the one census it left behind.

**THE COMPARISON NEEDS NO DRAW, NO DUMP AND NO CORPUS**, which is the whole of why it can
leave the pole.  ``harness.check_pair`` reaches it with

    compare_schema(pair.schema, pair.model, document=pair.document,
                   declared=pair.declared, at=pair.ref.pointer)

and :func:`census` calls it with those five arguments, derived the same way -- the node
and the document root through ``_base.schema_at``, the declarations through
``harness.declarations_of`` off the CLASS for a class and the MODULE for an alias, the
pointer off the pair's own ``SchemaRef``.  Argument for argument the same call, so the
reading here is the reading the pole produces and **no detection is traded away**: what is
dropped is the accepts draw, the liveness payload and the widening proof, none of which
the comparison reads.

**THE MEASUREMENT, on this box at ``adcp-client-python-3be.23``, as a RANGE over four
runs** -- the spread is box load and the figure to believe is the one ``./check --compare``
prints at the moment it is asked:

=========================================  =================
importing the 919-module fresh tree          5 - 7 s
``compare_schema`` over 2,789 pairs         31 - 47 s
----------------------------------------   -----------------
the whole census                            36 - 53 s
=========================================  =================

A cold run pays the fresh tree's 840 MB write once on top of that (~3 m 45 s), under
``tests/fresh.py``'s lock and shared by every process afterwards.  ``pytest
tests/test_the_comparison_census.py`` is 45 s for all four of its tests, because they
share one pass through ``functools.cache`` and one worker through ``xdist_group``.

**ONE WALK, and it is here rather than in ``tests/test_emit.py`` for the reason that file
already gives about two populations**: a census over a pairing of its own would be a
census over however many pairs that second walk turned out to find, and the two would
disagree silently the moment either moved.  :func:`pairs` is therefore the suite's only
pairing of the fresh tree -- ``test_emit.graded()`` reads it and wraps each row in its own
``Graded`` -- so "the 2,793 pairs" means one thing in both files.

**``schema_at`` RAISES at four pairs and that is reported, not skipped.**  The two refs of
``media-buy/buy-products-request.json`` and ``media-buy/request-proposals-request.json``
through a synthetic ``allOf`` pointer raise ``KeyError: '0'``
(``adcp-client-python-3be.15``, ex ``10l.108``).  A pair whose document cannot be read at
is not comparable and is not a pass either: it is held in :attr:`Census.unreadable` with
the raise, and ``tests/test_the_comparison_census.py`` pins the set -- so a fifth such
pair reddens there instead of quietly leaving the comparable population.
"""

from __future__ import annotations

import collections
import functools
import importlib
import pkgutil
import time
import traceback
from typing import Any, NamedTuple

from adcp.types._base import SchemaBound, SchemaRef, schema_at

from codegen import harness

import fresh


class Paired(NamedTuple):
    """One pair of the fresh tree, as the walk finds it.

    The four fields ``tests/test_emit.py``'s ``Graded`` carries, in its order, because
    that file wraps these rows in it: the ``SchemaRef`` the holder declares, the model,
    the entry point an instance is offered through, and the DEFINING module's name.
    """

    ref: SchemaRef
    model: Any
    accept: Any
    module: str


#: Modules of the fresh tree that did not import, as ``name -> the tail of the traceback``.
#:
#: **:func:`pairs` records an unimportable module and does not raise.**  It is read at
#: PARAMETRIZE time by ``tests/test_emit.py``, where a raise is not a red test -- it errors
#: the COLLECTION of that file, and the measurement is that one module which did not import
#: collected ZERO tests there: every pair, every census and the import obligation itself,
#: gone, with the reader left holding a traceback instead of a named failure.
#: ``docs/plan/architecture.md``'s rule for it is "a tree that does not build fails one
#: named test instead of disabling the file", and
#: ``test_emit.test_no_module_of_the_graded_tree_failed_to_import`` is the test that reads
#: this.  It is the SAME dict object that file exposes, so either name reports the same
#: walk.
UNIMPORTABLE: dict[str, str] = {}


@functools.cache
def pairs() -> list[Paired]:
    """Every class and alias the FRESH tree carries, with the schema each one names.

    The whole of the pairing, and the suite's only one.  A class is taken from the module
    that DEFINES it (``__module__``) and ONCE per module whatever names it is bound under
    (by ``id``), because D3's content dedup gives one class a name at every position its
    node occupies -- keyed on names the pair count read 1,085 where 1,079 pairs existed.

    **``SchemaBound`` and not ``AdCPBaseModel`` is the predicate, because §8 of the
    architecture document requires a ROOT MODEL to be paired exactly as a class is**:
    "each must carry ``__adcp_schema__``, ``strict_validate`` and a rule tuple exactly as
    a class does, or a root model and a class disagree about what their document accepts."
    ``SchemaBound`` is the mixin that carries those two, so it is the predicate that says
    "this object is a pair"; ``AdCPBaseModel`` says "this object is a class", which is a
    narrower question and the wrong one here.  Measured at §14 step 9: the six root models
    the step's three producers declare -- ``core/acceptance-policy-profile-ids.json``,
    ``core/forecast-point-dimensions.json``,
    ``core/reporting-verification-profile-set.json``, ``media-buy/product-fields.json``
    and the two ``core/targeting-*-age-*-constraint.json`` -- emitted into the tree and
    reached NO pair, which
    ``test_emit.test_the_pairing_is_intrinsic_to_every_class_the_tree_carries`` reports as
    a document that emits and is not graded.

    An ALIAS is D2's root-scalar row -- not a class, so its MODULE carries
    ``__adcp_schema__`` and ``strict_validate``, and the model is the one name the module
    exports.  ``test_emit``'s own checks assert both cases non-empty, so neither is graded
    by an empty loop.

    **The TREE is the one a FRESH run emits**, which ``tests/fresh.py`` both decides and
    performs: it writes the emission and binds ``adcp.types``'s generated half to it, so
    the import below reaches this compiler's output and its aliases resolve through this
    compiler's ``constraints`` module.  A fresh ``_schemas`` imported beside the COMMITTED
    alias module would resolve its aliases through that one, and an alias this run mints
    that the committed module lacks is exactly a defect the pairing is meant to find.

    **Nothing it reads can take a caller's collection down**: no tree at all is an empty
    list (``fresh.schemas()`` answers ``None`` and a named test reads the reason), and a
    module that does not import is recorded in :data:`UNIMPORTABLE` and skipped.

    Cached because it imports the whole emitted tree and a union root's
    ``model_rebuild(force=True)`` is not cheap.  The returned list is SHARED: read it, do
    not mutate it.
    """
    pkg = fresh.schemas()
    if pkg is None:
        return []

    out: list[Paired] = []
    for info in sorted(pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."), key=lambda i: i.name):
        try:
            module = importlib.import_module(info.name)
        except Exception:  # noqa: BLE001 -- see UNIMPORTABLE: a raise errors a collection
            UNIMPORTABLE[info.name] = traceback.format_exc(limit=3)[-600:]
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
                out.append(Paired(value.__adcp_schema__, value, value.strict_validate, info.name))
        ref = vars(module).get("__adcp_schema__")
        if isinstance(ref, SchemaRef) and callable(vars(module).get("strict_validate")):
            (symbol,) = module.__all__
            out.append(Paired(ref, getattr(module, symbol), module.strict_validate, info.name))
    return out


class Census(NamedTuple):
    """The comparison's verdict over the whole pairing.

    :attr:`red` is the one the pin is written against: ``document#pointer -> the sorted
    facts``, each fact ``"<direction> <pointer>"``.  The DIRECTION is in the fact because a
    fact that MOVED between ``added``, ``missing`` and ``differs`` is a different fact
    about the model -- a count per direction cannot see that, and three counts would be
    green on a swap.
    """

    #: Every pair the comparison reddens, with its facts.  A pair that compares clean is
    #: not here, which is why ``len(red)`` is a reading and not a denominator.
    red: dict[str, list[str]]
    #: ``document#pointer -> the raise``, for a pair whose document cannot be read at --
    #: ``adcp-client-python-3be.15``'s synthetic ``allOf`` pointer.  NOT a pass.
    unreadable: dict[str, str]
    #: **Every comparable pair whose outcome is not ``pass``, BY NAME**, and not only the
    #: ones :attr:`red` can hold.  Three of ``ComparisonResult.outcome``'s verdicts carry
    #: no ``added``/``missing``/``differs`` fact at all -- §8's sixth outcome
    #: ``declaration_outlived_its_widening``, a ``harness_error`` from a model whose
    #: schema cannot be built, and ``no_evidence`` from a pair whose document states
    #: nothing -- so a census read off the facts alone would call all three a pass.  Each
    #: is pinned empty in ``tests/test_the_comparison_census.py`` off this field.
    verdicts: dict[str, str]
    #: ``ComparisonResult.outcome`` over the comparable pairs, which is where ``pass``,
    #: ``model_drops_a_fact`` and ``model_adds_a_fact`` are counted.
    outcomes: collections.Counter[str]
    #: The whole pairing, comparable or not: ``len(pairs())``.
    paired: int
    #: The wall clock of the comparison itself, for the reader who has to decide whether
    #: this is a loop or a pole.
    seconds: float


@functools.cache
def census() -> Census:
    """``compare_schema`` over every pair, with the pole's own five arguments.

    One pass, cached per process.  The returned value is SHARED: read it, do not mutate
    it.
    """
    started = time.time()
    red: dict[str, list[str]] = {}
    unreadable: dict[str, str] = {}
    verdicts: dict[str, str] = {}
    outcomes: collections.Counter[str] = collections.Counter()
    for one in pairs():
        name = f"{one.ref.document}{one.ref.pointer}"
        holder = one.model if isinstance(one.model, type) else importlib.import_module(one.module)
        try:
            node = schema_at(one.ref)
            document = schema_at(SchemaRef(one.ref.document, "#"))
        except Exception as e:  # noqa: BLE001 -- the raise is the finding; see Census
            unreadable[name] = f"{type(e).__name__}: {e}"[:200]
            continue
        result = harness.compare_schema(
            node,
            one.model,
            document=document,
            declared=harness.declarations_of(holder),
            at=one.ref.pointer,
        )
        outcomes[result.outcome] += 1
        if result.outcome != "pass":
            verdicts[name] = result.outcome
        facts = sorted(
            f"{direction} {line.split(':')[0]}"
            for direction, lines in (
                ("added", result.added),
                ("missing", result.missing),
                ("differs", result.differs),
            )
            for line in lines
        )
        if facts:
            red[name] = facts
    return Census(red, unreadable, verdicts, outcomes, len(pairs()), time.time() - started)


def shape_of(fact: str) -> str:
    """The SHAPE a red fact has: its direction and the keyword it is about.

    Two kinds of tail, because the pointer of a fact says which: a fact under
    ``.../properties/<name>`` is about a whole PROPERTY ENTRY -- the document states the
    property and the model carries no field for it, or the reverse -- and every other
    fact is about the KEYWORD its pointer ends in.  Grouping on the raw tail would split
    one shape into as many rows as the bundle has property names: ``missing
    format_option_id`` and ``missing display_name`` are not two findings.
    """
    direction, pointer = fact.split(" ", 1)
    segments = [one for one in pointer.split("/") if one]
    if len(segments) >= 2 and segments[-2] == "properties":
        return f"{direction} a property entry"
    return f"{direction} {segments[-1] if segments else '/'}"


def by_direction(red: dict[str, list[str]]) -> collections.Counter[str]:
    """``added`` / ``missing`` / ``differs``, counted over the facts.

    §2 reads the three in two groups and they are not interchangeable: ``missing`` and
    ``differs`` are a model WIDER than its document, which §2 permits only where a
    declaration says so, and ``added`` is a model NARROWER -- which §2 forbids outright
    and no declaration absorbs, because a narrower model refuses traffic the document
    admits.
    """
    return collections.Counter(fact.split(" ")[0] for facts in red.values() for fact in facts)


def by_shape(red: dict[str, list[str]]) -> dict[str, tuple[int, int, int]]:
    """``shape -> (facts, pairs, documents)``, which is the grouping a row is cut along.

    Three denominators and never one, for ``DECLARED_WIDENINGS``' reason: "``K`` and ``D``
    are different counts over different denominators and the report never adds them".  A
    shape at 390 facts in 18 pairs is one cause; a shape at 76 facts in 68 pairs across 38
    documents is another, and the two want different rows.
    """
    facts: collections.Counter[str] = collections.Counter()
    seen_pairs: dict[str, set[str]] = collections.defaultdict(set)
    seen_documents: dict[str, set[str]] = collections.defaultdict(set)
    for name, group in red.items():
        for fact in group:
            shape = shape_of(fact)
            facts[shape] += 1
            seen_pairs[shape].add(name)
            seen_documents[shape].add(name.split("#")[0])
    return {
        shape: (count, len(seen_pairs[shape]), len(seen_documents[shape]))
        for shape, count in facts.most_common()
    }


def by_document(red: dict[str, list[str]]) -> dict[str, tuple[int, int]]:
    """``document -> (pairs, facts)``, ordered by pairs then facts.

    The other axis the 155 are read along, and the one that says where a row lands: a
    document with ten red pairs is one node emitted ten ways, not ten findings.
    """
    pairs_of: dict[str, int] = collections.Counter()
    facts_of: dict[str, int] = collections.Counter()
    for name, group in red.items():
        document = name.split("#")[0]
        pairs_of[document] += 1
        facts_of[document] += len(group)
    return {
        document: (pairs_of[document], facts_of[document])
        for document in sorted(pairs_of, key=lambda d: (-pairs_of[d], -facts_of[d], d))
    }
