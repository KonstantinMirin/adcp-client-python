"""Reading 10's alias layer, graded as BEHAVIOUR: a name, never a second type.

``docs/plan/final-state.md`` reading 10:

    **An alias is a NAME and never a second type.**  Reading 6 still holds with the
    aliases counted: export paths equal distinct declarations, and ``isinstance`` holds
    across every spelling.  An alias that is a second class is the duplication this whole
    project exists to remove, arriving as compatibility.

**NOTHING HERE READS THE TEXT OF THE ALIAS MODULE.**  ``src/adcp/types/compat.py`` is
written by ``survey/alias_surface.py`` and a check that greps it for ``as`` would pass on a
file full of ``class X: pass``.  The two assertions are ``is`` and ``isinstance``, which no
second class can satisfy, and the third is an arithmetic over DECLARATIONS.

**THE POPULATION IS A COMMITTED TABLE AND NOT A LIST ANYBODY WROTE HERE**:
``survey/alias-surface-9.6.1.tsv``, written by that script from upstream's own 9.6.1 wheel
and ours, one row per name the layer decides with the module it is DECLARED at.  The table
is in the repository for a reason this project has already paid for once -- a bead citing a
reading under ``.adcp-cache/`` is citing a path ``.gitignore`` line 39 deletes, and three of
the four files the drop-in readings were written from are already gone from that directory
while this was being written (``manifest-upstream.tsv``, ``manifest-ours.tsv``,
``ours-declared.tsv``).  The generator and its output are both committed, so the gate needs
no upstream wheel and a re-derivation needs one command.

**WHICH UPSTREAM VERSION, STATED IN THE FILENAME AND IN THE FILE.** 9.6.1, the release the
owner's goal names ("a drop-in replacement for the **v9.6** classes").  ``/srv/ws/wt-v92``
is 9.2.0 and is the consumer corpus for phase 0 only; a figure here that did not say which
version it was against would be the error ``adcp-client-python-2m5`` corrected in itself.

**WHAT THIS FILE DOES NOT GRADE is stated by name and asserted non-empty**, the discipline
``tests/test_the_wheel_is_the_artifact.py`` uses for its 39 unnamed records: the 35 names
whose word ours carries for a DIFFERENT subject, and the 1,214 whose subject ours carries
under a word the bundle never gives.  Neither set is in the owed 1,038 and neither is
aliased; both are findings, and :func:`test_what_this_file_does_not_grade` reddens the day
either set empties rather than leaving a stale sentence above.
"""

from __future__ import annotations

import csv
import importlib
from pathlib import Path

import fresh
import pytest
from compiled import compiled
from nodeset import claimed
from test_the_domain_surface import declaring, surface

from codegen import emit  # noqa: F401  -- `surface` needs it; imported for the same tree

ROOT = Path(__file__).resolve().parents[1]

#: The committed evidence.  Named with the upstream version it was derived against, so a
#: second version is a second file rather than a silent overwrite of this one's numbers.
TABLE = ROOT / "survey" / "alias-surface-9.6.1.tsv"

#: The one module reading 10's "a declared set of canonical modules" resolves to here.
#: Declared in ONE place -- the table's own `declared_at` column is read, not this constant
#: -- and spelled here only so a failure message can name it.
MODULE = "adcp.types.compat"


def _alias_names() -> set[str]:
    """Every upstream spelling the flat namespace carries, read off the alias module.

    Both of its statements: ``__all__`` is what that module declares and
    ``__adcp_flat_only__`` names the ``PRESENT`` rows it declines to bind.  Read from the
    module rather than from the table, because the question here is what the RUNTIME would
    expose.
    """
    compat = importlib.import_module(MODULE)
    return {*compat.__all__, *compat.__adcp_flat_only__}


def tabled() -> list[dict[str, str]]:
    """Every row of the table, with its comment header dropped."""
    lines = [line for line in TABLE.read_text().splitlines(True) if not line.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    got = tabled()
    claimed(f"the names {TABLE.name} decides", {r["name"] for r in got})
    return got


def owed(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """The three buckets a types-scope phase 3 must make resolve.

    `adcp-client-python-2m5`'s deciding sentence: "resolving every name of the cross-check's
    PRESENT, RENAMED and RELOCATED buckets".  A refusal is not in here and is not supposed
    to be; :func:`test_what_this_file_does_not_grade` is where those are named.
    """
    return [r for r in rows if r["bucket"] in ("PRESENT", "RELOCATED", "RENAMED")]


def test_every_name_the_table_declares_imports_from_the_module_it_names(
    rows: list[dict[str, str]],
) -> None:
    """The row's own obligation: 1,038 upstream spellings, each at the module declared.

    A REAL IMPORT STATEMENT per name, so what is measured is the import system and not a
    ``getattr`` over an already-bound module object -- the same choice
    ``tests/test_the_wheel_is_the_artifact.py``'s probe makes and for the same reason.

    This runs against the SOURCE TREE.  The wheel is the artifact and reading 8 owns that
    direction: ``test_every_upstream_spelling_is_on_the_installed_surface`` in that file
    asks the same question of an environment that has never seen this repository, and
    without it a green here says nothing about what ships.
    """
    population = owed(rows)
    claimed("the names this layer owes", {r["name"] for r in population})
    failed: dict[str, str] = {}
    for row in population:
        namespace: dict[str, object] = {}
        try:
            exec(f"from {row['declared_at']} import {row['name']}", namespace)  # noqa: S102
        except BaseException as error:  # noqa: BLE001 -- the payload is the report
            failed[f"{row['declared_at']}.{row['name']}"] = f"{type(error).__name__}: {error}"
    assert not failed, {
        "upstream spellings that do not resolve at the module declared for them": failed,
        "owed": len(population),
        "unresolved": len(failed),
    }


def test_every_alias_is_the_object_its_canonical_path_reaches(
    rows: list[dict[str, str]],
) -> None:
    """``is``, and then ``isinstance`` -- the two a second class cannot satisfy.

    ``is`` is the whole assertion about duplication: a layer that MINTED a class per
    upstream spelling would resolve every name above and give a consumer an object whose
    ``isinstance`` is false against every instance the runtime builds, which is the defect
    reading 6's one-path rule exists to make unrepresentable.

    ``isinstance`` is asserted in both directions of the spelling for the rows whose target
    is a class: an instance built through OUR name is an instance of the ALIAS, and an
    instance built through the alias is an instance of ours.  For a ``D2`` alias --
    ``Annotated[...]``, ``A | B`` -- there is no class to construct and ``is`` is the whole
    of what can be asked, which is also all reading 6 asks of one.
    """
    population = [r for r in owed(rows) if r["bucket"] in ("RELOCATED", "RENAMED")]
    claimed("the aliases", {r["name"] for r in population})
    not_the_same: dict[str, str] = {}
    not_an_instance: list[str] = []
    for row in population:
        where, ours = row["ours"].rsplit(".", 1)
        alias = getattr(importlib.import_module(row["declared_at"]), row["name"])
        target = getattr(importlib.import_module(where), ours)
        if alias is not target:
            not_the_same[f"{row['declared_at']}.{row['name']}"] = f"is not {row['ours']}"
            continue
        if isinstance(target, type) and hasattr(target, "model_construct"):
            # ``model_construct`` validates nothing, which is the point -- the question is
            # whether the two spellings name one class, not whether a payload is valid.
            # A ``RootModel`` takes its ``root`` positionally and raises without one, so
            # the field set decides the call rather than a try/except swallowing a real
            # failure of this assertion.
            fields = getattr(target, "model_fields", {}) or {}
            held = target.model_construct(root=None) if "root" in fields else target.model_construct()
            if not (isinstance(held, alias) and isinstance(held, target)):
                not_an_instance.append(f"{row['name']} / {row['ours']}")
    assert not not_the_same, {"a second object wearing the upstream spelling": not_the_same}
    assert not not_an_instance, {"isinstance does not hold across the spellings": not_an_instance}


def test_every_owed_spelling_resolves_at_the_flat_namespace(
    rows: list[dict[str, str]],
) -> None:
    """**Reading 10's third layer, which is the import an application has already written.**

    ``final-state.md`` reading 10 names ``adcp.types`` flat "the compatibility surface: an
    alias for every name an application actually imports today", and its amendment of
    2026-11-06 settles the one bucket that made the two halves disagree: "**'already
    resolves' is measured at the SPELLING A CONSUMER WRITES, never at the module that
    declares it** ... a name counted present because its domain path matches owes a flat
    alias exactly as a relocated one does -- the buckets differ in where the alias points,
    never in whether one is owed."

    **SO THE POPULATION IS ALL THREE OWED BUCKETS AND NOT THE TWO THE ALIAS MODULE
    DECLARES.**  ``PRESENT`` writes no statement at ``adcp.types.compat`` -- a second path
    there to a name that already resolves at the one the surface gives it is the
    duplication this layer exists not to reintroduce -- so those 79 are reached through
    ``compat.__adcp_flat_only__``, which names the module each one is carried at.

    A real import statement per name, and ``is`` against the module the table DECLARES for
    it: a flat surface built by copying would resolve every name here and hand a consumer
    an object whose ``isinstance`` is false against every instance the runtime builds.
    Reading 8 asks the same question of the installed wheel
    (``tests/test_the_wheel_is_the_artifact.py``), because an alias that resolves only from
    the source tree is not shipped.

    **AND THE IDENTITY CLAUSE HAS ONE EXCEPTION, WHICH IS UPSTREAM'S OWN STATEMENT AND NOT A
    CONCESSION** (``adcp-client-python-y34k``).  This table is keyed on a DOCUMENT and the
    word that document gives, which is the right key for the domain spelling and for
    ``adcp.types.compat``.  It is not the right key for the FLAT word where upstream's own
    ``_eager.py`` binds that word to one of their hand-written files: they write
    ``Format = _canonical_creative.Format``, so ``from adcp.types import Format`` is their
    canonical class -- requiring ``format_kind`` and ``params`` -- and not
    ``core/format.json``'s root, which requires ``format_id`` and ``name``.  262 of the 866
    remaining ``ValidationError`` tests of their suite were this table's object answering the
    flat word.

    So for the 26 words ``adcp.types._restored.STATED`` names, the reading is BOTH halves and
    neither is dropped: the flat word is upstream's stated subject, **and the table's own
    object is still reachable at the module the table declares** -- which is what keeps this
    an exception about WHICH SUBJECT A NAMESPACE DENOTES and not a name the layer stopped
    serving.  The split is keyed on upstream's statement, so a word they stop binding that
    way rejoins the identity clause by itself.
    """
    stated = importlib.import_module("adcp.types._restored").STATED
    population = owed(rows)
    claimed("the flat spellings this layer owes", {r["name"] for r in population})
    failed: dict[str, str] = {}
    not_the_same: dict[str, str] = {}
    upstream_states: dict[str, str] = {}
    lost: dict[str, str] = {}
    for row in population:
        namespace: dict[str, object] = {}
        try:
            exec(f"from adcp.types import {row['name']}", namespace)  # noqa: S102
        except BaseException as error:  # noqa: BLE001 -- the payload is the report
            failed[row["name"]] = f"{type(error).__name__}: {error}"
            continue
        declared = getattr(importlib.import_module(row["declared_at"]), row["name"])
        if namespace[row["name"]] is declared:
            continue
        where = stated.get(row["name"])
        if where is None:
            not_the_same[row["name"]] = (
                f"adcp.types.{row['name']} is not {row['declared_at']}.{row['name']}"
            )
            continue
        # Upstream's own statement decides the flat word.  Both halves asserted.
        theirs = getattr(importlib.import_module(f"adcp.types.{where}"), row["name"])
        if namespace[row["name"]] is not theirs:
            not_the_same[row["name"]] = (
                f"adcp.types.{row['name']} is neither {row['declared_at']}.{row['name']} nor "
                f"adcp.types.{where}.{row['name']}, which upstream's own _eager states"
            )
            continue
        if getattr(importlib.import_module(row["declared_at"]), row["name"], None) is not declared:
            lost[row["name"]] = f"{row['declared_at']}.{row['name']} no longer resolves"
        upstream_states[row["name"]] = f"adcp.types.{where}.{row['name']}"
    assert not failed, {
        "upstream spellings that do not resolve at the flat namespace": failed,
        "owed": len(population),
        "unresolved": len(failed),
    }
    assert not not_the_same, {"a second object wearing the flat spelling": not_the_same}
    claimed("flat words upstream's own _eager takes from a restored file", upstream_states)
    assert upstream_states, (
        "no owed spelling is decided by upstream's own statement, so the exception above "
        "grades nothing -- read adcp.types._restored.STATED"
    )
    assert not lost, {"the table's own object stopped resolving at the module it names": lost}


def test_a_present_name_gains_the_flat_path_and_no_path_at_the_alias_module(
    rows: list[dict[str, str]],
) -> None:
    """The amendment's other half: the ONE namespace an application imports from.

    ``final-state.md`` reading 10, amended: "**THIS IS NOT THE SPELLING RULE'S OPPOSITE, IT
    IS ITS BOUNDARY.**  Refusing to reproduce upstream's spellings means refusing to put one
    object at every module upstream happens to expose it from.  It does not mean refusing the
    **one** namespace an application imports from."

    So a ``PRESENT`` name ends with exactly two public paths -- the domain one reading 6
    gives it, and the flat one a consumer writes -- and NOT a third at
    ``adcp.types.compat``.  Graded as behaviour: the import resolves at the first two and
    raises at the third.
    """
    present = [r for r in rows if r["bucket"] == "PRESENT"]
    claimed("the PRESENT rows, which owe the flat spelling alone", {r["name"] for r in present})
    wrong: dict[str, str] = {}
    for row in present:
        at_compat: dict[str, object] = {}
        try:
            exec(f"from {MODULE} import {row['name']}", at_compat)  # noqa: S102
        except ImportError:
            continue
        wrong[row["name"]] = (
            f"{MODULE}.{row['name']} resolves, which is a second path to a name already at "
            f"{row['declared_at']}"
        )
    assert not wrong, {"PRESENT names that gained a path at the alias module": wrong}


def test_the_alias_layer_adds_no_declaration(rows: list[dict[str, str]]) -> None:
    """Reading 6 WITH the aliases counted: they add names and not declarations.

    ``final-state.md`` reading 6 is decided by "counting OBJECTS, not names: the number of
    export paths equals the number of distinct objects behind them", and §1 settles the
    counting as DECLARATIONS rather than ``id()``
    (``tests/test_the_domain_surface.declaring``, imported here rather than restated).
    Reading 10 then says this reading "still holds with the aliases counted: export paths
    equal distinct declarations".

    **So the arithmetic over this layer is that it contributes ZERO declarations**, and
    that is the only reading of the two sentences that is satisfiable at all: an alias is by
    construction a second PATH to one declaration, so a count that charged it a declaration
    of its own would make reading 10 contradict reading 6 and no alias layer could exist.
    What the gate therefore asks is the thing that distinguishes a name from a class --
    every declaration behind an alias is one the domain surface already counted, and the
    set of declarations is unchanged by this module existing.

    The failure it catches is exact: a compat module that declared ``class Account`` rather
    than re-exporting ours would put a declaration behind an export path that the domain
    surface does not carry, and this assertion names it.
    """
    assert not fresh.FAILURE, fresh.FAILURE
    exported = surface()
    held = compiled(fresh.BUNDLE, fresh.population())
    behind: dict[str, tuple[str, str] | None] = {}
    for (domain, name), sources in exported.items():
        private = sources[0][0].replace(".", "/")
        # The SYMBOL for ``declaring``'s record arm and the WORD for the path, which is
        # reading 6's inner clause (``tests/test_the_domain_surface.surface``).
        symbol = sources[0][2]
        module = importlib.import_module(f"adcp.types.{domain}")
        behind[f"adcp.types.{domain}.{name}"] = declaring(
            private, symbol, getattr(module, name), held.binds.get(private, {})
        )
    claimed("the export paths of the domain surface", behind)
    declarations = {key for key in behind.values() if key is not None}

    # **ALL THREE OWED BUCKETS, since reading 10's amendment of 2026-11-06**: a `PRESENT`
    # row is a flat alias too, so it is counted here exactly as a relocated one is, and its
    # target being on the surface is the same question.
    population = owed(rows)
    # **EVERY ALIAS IS A PATH TO A DECLARATION THE SURFACE ALREADY COUNTED**, which is
    # asked by resolving the alias's TARGET on the surface rather than by keying the alias
    # on its own module -- "keying such a path on its OWN module would count a second path
    # as a declaration, which is the blindness the per-name check already has" (§1, through
    # `declaring`'s own docstring).
    off_surface: dict[str, str] = {}
    fresh_declarations: dict[str, str] = {}
    for row in population:
        target = row["ours"]
        if target not in behind:
            off_surface[f"{MODULE}.{row['name']}"] = target
            continue
        if behind[target] not in declarations:
            fresh_declarations[f"{MODULE}.{row['name']}"] = target
    assert not fresh_declarations, {
        "aliases that are a declaration of their own rather than a name": fresh_declarations,
    }
    # **THE OFF-SURFACE TARGETS ARE THE TWO PUBLIC NON-DOMAIN MODULES AND NOTHING ELSE.**
    # `adcp/types/__init__.py` names them and says why neither is a domain: "what they hold
    # has no document to bind".  `emit.surface` is stated over documents, so a D5
    # constrained type has no row there -- it is public, it is importable, and it is not an
    # export path this reading counts.  An alias reaching anywhere ELSE off the surface is
    # an alias to a name reading 6 does not export, which is a defect and is named here.
    allowed = {"adcp.types.constraints", "adcp.types.envelopes"}
    outside = {
        alias: target
        for alias, target in off_surface.items()
        if target.rsplit(".", 1)[0] not in allowed
    }
    assert not outside, {"aliases reaching a name the surface does not export": outside}
    assert len(declarations) == len(behind), {
        "export paths": len(behind),
        "declarations behind them": len(declarations),
        "aliases counted as names": len(population),
        "of those, reaching a public non-domain module": len(off_surface),
    }


def test_the_name_rule_the_table_was_built_with_is_the_one_the_emitter_uses() -> None:
    """``survey/alias_surface.class_name`` and §4's are the same rule, over the bundle's words.

    The survey copy exists because phase 3 of that script must run on an interpreter with
    only the standard library -- ``codegen.bundle`` imports ``adcp.types._base``, which
    imports ``jsonschema`` -- and a second spelling of a rule is a second thing to go stale.
    So the two are compared on the TITLES THE BUNDLE ACTUALLY STATES rather than on an
    invented list: if §4's acronym handling moves and the survey's does not, the name a
    RENAMED row was keyed on stops being the name the emitter gives and this reddens.
    """
    import sys

    sys.path.insert(0, str(ROOT / "survey"))
    import alias_surface

    from codegen.lower import names

    index = alias_surface.bundle_index(ROOT / "schemas" / "cache" / "3.2")
    titles = claimed("the document titles the bundle states", index["stems"])
    disagree = {
        title: (alias_surface.class_name(title), names.class_name(title))
        for title in sorted(index["documents"])
        if alias_surface.class_name(title) != names.class_name(title)
    }
    assert not disagree, {"two spellings of §4's name rule": disagree}
    assert len(titles) > 500, {"the bundle's vocabulary is implausibly small": len(titles)}


def test_the_surveys_do_not_read_their_own_output(tmp_path) -> None:
    """The alias module declares that it restates upstream, and the surveys honour it.

    **The failure this stops was measured on the second run of the generator.**  Phase 1
    reads OUR surface off the installed wheel, and the wheel ships the alias module -- so
    with no marker the next run finds every upstream spelling "already a name of ours, at
    ``adcp.types.compat``" and binds each alias to itself, and
    ``survey/migration_notes.py`` stops owing a migration note for any name this module
    restates.  Both read ``__adcp_restates_upstream__`` off the module rather than carrying
    its name in a list, so a second alias module needs nothing edited.

    **AND THE PREDICATE HAS THREE ANSWERS, NOT TWO, WHICH IS THE HALF THAT COST A
    DIAGNOSIS.**  Its first form returned a boolean and caught every exception into
    ``False``, so a module that does not IMPORT read as "a module of ours".  Merged against
    a surface that had dropped one of the table's targets, this test then said
    "``adcp.types.compat`` does not declare ``__adcp_restates_upstream__``" about a module
    whose line 1012 declares exactly that -- and a reader was sent after a missing marker
    rather than after the ``ImportError``.  So the third answer is asserted here too, on a
    module written for the purpose: ``unimportable`` carries the exception, and the
    misreading is unrepresentable rather than merely fixed.

    Graded as behaviour -- three return values -- and not as the presence of a line of text.
    """
    import sys

    sys.path.insert(0, str(ROOT / "survey"))
    import migration_notes

    assert migration_notes.restatement(MODULE)[0] == "restates", (
        f"{MODULE} does not read as a restatement of upstream, so the next run of "
        f"survey/alias_surface.py reads its own output as our surface: "
        f"{migration_notes.restatement(MODULE)}"
    )
    assert migration_notes.restatement("adcp.types.core")[0] == "ours", (
        "a DOMAIN module does not read as ours, which would drop the schema-derived "
        f"surface out of the partition: {migration_notes.restatement('adcp.types.core')}"
    )
    # The third answer, on a module that raises at import.  Written here rather than
    # fixtured: what is being graded is that a raise is reported AS a raise, so the raise
    # has to be real.
    (tmp_path / "a_module_that_raises.py").write_text(
        "raise ImportError('cannot import name Gone from adcp.types.core')\n"
    )
    sys.path.insert(0, str(tmp_path))
    answer, detail = migration_notes.restatement("a_module_that_raises")
    assert answer == "unimportable", (answer, detail)
    assert "ImportError" in detail and "Gone" in detail, detail
    # **AND THE FLAT NAMESPACE IS THE THIRD WAY THE SURVEYS COULD READ THEIR OWN OUTPUT,
    # WHICH IS WHY `adcp.types.__getattr__` IS LAZY AND NOT A `from compat import *`.**
    # `migration_notes.dump_ours` walks `adcp.types` INCLUDING the package itself and reads
    # `vars(mod)`; a star-import would have put 1,038 upstream spellings into that `vars()`
    # and every one would have read as "already a name of ours, at `adcp.types`", which is
    # the same fixed-point failure the marker above exists for, arriving through the
    # package instead of through a module.  `vars()` does not call `__getattr__`, so the
    # lazy form is invisible to it -- and that is a property worth a check rather than a
    # comment, because it is what makes the derivation re-runnable.
    import adcp.types

    assert "adcp.types" in migration_notes.walk("adcp.types"), (
        "the dumper no longer walks the package itself, so this clause grades nothing -- "
        "re-point it at whatever enumerates the modules the dump reads"
    )
    leaked = sorted(set(vars(adcp.types)) & set(_alias_names()))
    assert leaked == [], (
        "the flat namespace has bound upstream spellings into its own `vars()`, so "
        "`survey/migration_notes.py` will read them as our surface and the next run of "
        f"`survey/alias_surface.py` will bind every alias to itself: {leaked[:10]}"
    )


def test_the_generator_refuses_to_write_a_table_that_points_at_nothing() -> None:
    """A dangling target is caught where the table is MADE, not where a consumer imports it.

    **THE DEFECT, measured on this branch.**  The table was derived against a dump of our
    surface and committed; ``sdk/home2`` landed meanwhile and took the surface from 1,881
    names to 1,879, removing ``DAASTTrackerConstraintsDaastTarget``.  One stale row then
    made ``adcp.types.compat`` raise ``ImportError`` at import, which took down six clauses
    of the reading-8 wheel gate with it -- "the installed wheel's own probe exited 1, so
    every reading below is about nothing" -- and reported itself, through the predicate
    above, as a missing marker.  One row, six gates saying nothing, one wrong diagnosis.

    So ``survey/alias_surface.prove_the_targets`` imports every target before anything is
    written and a miss is a refusal naming every row.  **SHOWN RED** off the test, as this
    repository's own banked-perturbation idiom: a dump repointed from
    ``adcp.types.core.Account`` to ``adcp.types.enums.Account`` -- a module that exists and
    a name it does not carry -- makes the generator exit 1 and write neither file.

    Graded on the function's RETURN VALUE and not on a message: the fabricated row is the
    one reported, and a row whose target does resolve is not.
    """
    import sys

    sys.path.insert(0, str(ROOT / "survey"))
    import alias_surface

    decided = {
        "Account": {"bucket": "RELOCATED", "target": "adcp.types.core.Account"},
        "GoneAway": {"bucket": "RELOCATED", "target": "adcp.types.enums.GoneAway"},
        "WrongModule": {"bucket": "RENAMED", "target": "adcp.types.no_such_domain.Thing"},
        # **A `PRESENT` ROW IS PROVED TOO, SINCE READING 10's AMENDMENT**: it writes no
        # statement at the alias module, but `__adcp_flat_only__` names the module the flat
        # spelling is reached at, so a target the surface stops carrying breaks
        # `from adcp.types import <Name>` -- the DaastTarget defect one layer out.  The
        # resolving one is asserted absent from the report beside it.
        "StillThere": {"bucket": "PRESENT", "target": "adcp.types.media_buy.GetMediaBuysRequest"},
        "WentAway": {"bucket": "PRESENT", "target": "adcp.types.media_buy.NoSuchRequest"},
        "NotOwed": {"bucket": "ABSENT", "why": "not a target at all"},
    }
    dangling = alias_surface.prove_the_targets(decided)
    assert set(dangling) == {"GoneAway", "WrongModule", "WentAway"}, dangling
    assert "is not a name adcp.types.enums carries" in dangling["GoneAway"], dangling
    assert "ModuleNotFoundError" in dangling["WrongModule"], dangling
    assert "is not a name adcp.types.media_buy carries" in dangling["WentAway"], dangling


def test_what_this_file_does_not_grade(rows: list[dict[str, str]]) -> None:
    """The two REFUSALS, named and non-empty -- findings, not oversights.

    * ``MEANING-DIFFERS`` -- ours carries upstream's word for a different subject.  35
      names, and the measurement is the reason they are refused rather than aliased:
      upstream's ``Format``, ``Product``, ``Package`` and ``Placement`` are all defined by
      ``adcp.types.canonical_creative``, a hand-written layer, and its ``Brand``,
      ``Targeting`` and ``AttributionWindow`` by an INNER node of
      ``protocol/get-adcp-capabilities-response.json`` -- not by the document whose subject
      ours names.  An alias there would hand a caller a type that is not the one their code
      means, and an ``ImportError`` is the louder and the more repairable of the two.
      **This is the one place this layer's measurement contradicts the cross-check it was
      briefed from**, which keyed those rows on the word alone and counted them inside its
      RELOCATED 907 and RENAMED 143.
    * ``ABSENT-SUBJECT-NO-WORD`` -- an identity of ours is equal under a word the bundle
      never gives: ``MacroDeclaration16``, ``Payload6``, ``AuthorizedAgents41``.  Their
      generator disambiguating a collision, and already carrying the cross-check's
      ``V1-FOLD-NONODE`` / ``V2-DUP`` verdicts.

    Both are asserted NON-EMPTY, so the day either closes this file reddens and the
    sentences above are rewritten rather than quietly going stale.
    """
    differs = claimed(
        "names whose word we carry for another subject",
        {r["name"] for r in rows if r["bucket"] == "MEANING-DIFFERS"},
    )
    artifacts = claimed(
        "names whose subject we carry under a word the bundle does not give",
        {r["name"] for r in rows if r["bucket"] == "ABSENT-SUBJECT-NO-WORD"},
    )
    assert {"Format", "Brand", "TaskStatus", "Targeting"} <= differs, sorted(differs)
    assert len(artifacts) > 1_000, len(artifacts)


def test_every_provisional_alias_is_paired_with_its_migration_entry() -> None:
    """Reading 10's narrowed prohibition, graded over the PAIR and never over the alias.

    ``final-state.md`` reading 10: "**NO ALIAS POINTS AT A NAME THIS COMPILER MINTED FROM
    STRUCTURE** ... such a name is *pending* an upstream title.  Publishing an alias onto it
    makes a placeholder permanent and public" -- **"UNLESS THE ALIAS IS UPSTREAM'S OWN
    PUBLISHED WORD, DECLARED DEPRECATED AND PENDING ... an alias RECORDS it rather than
    minting it ... So the alias is admissible AND THE MIGRATION ENTRY MUST SAY THE WORD IS
    PROVISIONAL -- naming the untitled node by pointer and the upstream ask that would title
    it."**

    **THE ENTRY IS WHAT MAKES THE ALIAS ADMISSIBLE, so the two are one unit and the unit is
    what is asserted.**  An alias without its entry is not a documented name missing a
    paragraph: it is reading 10's prohibition unnarrowed -- a permanent public commitment to
    a placeholder -- and the alias should not have been written.  That is why this reddens on
    the alias rather than on the guide.

    Four things are required of each pair, each reported BY NAME:

    * the word RESOLVES, flat and at the alias module, which is what an application writes;
    * it ``is`` the object reading 6's own surface word reaches -- an alias is a NAME, so a
      provisional one is held to the same ``is`` every other row of this module is;
    * the guide NAMES the word and NAMES the node's POINTER, which is reading 10's "naming
      the untitled node by pointer";
    * the guide says **PROVISIONAL**, which is the sentence the reading asks for in those
      words and the one thing a reader has to be told.

    The ASK is prose and is not grepped for: reading 10 requires it to be stated and no check
    can decide whether a sentence is one.  What is checked is that the entry exists, is about
    this node, and carries the word the reading fixes.
    """
    compat = importlib.import_module(MODULE)
    provisional: dict[str, str] = compat.__adcp_provisional__
    claimed("the provisional words", provisional)
    guide = (ROOT / "docs" / "migration-from-upstream.md").read_text(encoding="utf-8")

    unresolved: dict[str, str] = {}
    not_the_same: dict[str, str] = {}
    unentered: dict[str, str] = {}
    for word, pointer in sorted(provisional.items()):
        namespace: dict[str, object] = {}
        try:
            exec(f"from adcp.types import {word}", namespace)  # noqa: S102
        except BaseException as error:  # noqa: BLE001 -- the payload is the report
            unresolved[word] = f"{type(error).__name__}: {error}"
            continue
        if namespace[word] is not getattr(compat, word):
            not_the_same[word] = f"adcp.types.{word} is not {MODULE}.{word}"
        missing = [
            what
            for what, found in (
                ("the word", f"`{word}`" in guide),
                ("the node's pointer", f"`{pointer}`" in guide),
                ("the word PROVISIONAL", "PROVISIONAL" in guide),
            )
            if not found
        ]
        if missing:
            unentered[word] = f"{pointer}: the guide does not carry {', '.join(missing)}"
    assert not unresolved, {"provisional words that do not resolve flat": unresolved}
    assert not not_the_same, {"a provisional word reaching a second object": not_the_same}
    assert not unentered, {
        "provisional aliases with no migration entry -- reading 10 unnarrowed": unentered,
    }
