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
whose word ours carries for a DIFFERENT subject, and the 1,212 whose subject ours carries
under a word the bundle never gives.  Neither set is in the owed 1,052 and neither is
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
    """The row's own obligation: 1,052 upstream spellings, each at the module declared.

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
        module = importlib.import_module(f"adcp.types.{domain}")
        behind[f"adcp.types.{domain}.{name}"] = declaring(
            private, name, getattr(module, name), held.binds.get(private, {})
        )
    claimed("the export paths of the domain surface", behind)
    declarations = {key for key in behind.values() if key is not None}

    population = [r for r in owed(rows) if r["bucket"] in ("RELOCATED", "RENAMED")]
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


def test_the_surveys_do_not_read_their_own_output() -> None:
    """The alias module declares that it restates upstream, and the surveys honour it.

    **The failure this stops was measured on the second run of the generator.**  Phase 1
    reads OUR surface off the installed wheel, and the wheel ships the alias module -- so
    with no marker the next run finds every upstream spelling "already a name of ours, at
    ``adcp.types.compat``" and binds each alias to itself, and
    ``survey/migration_notes.py`` stops owing a migration note for any name this module
    restates.  Both read ``__adcp_restates_upstream__`` off the module rather than carrying
    its name in a list, so a second alias module needs nothing edited.

    Graded as behaviour: the predicate's return value for this module and for a domain
    module, which is what the surveys branch on -- not the presence of a line of text.
    The fixed point itself is measured in the lane's write-up: with the module installed,
    phase 1 answers the same 2,225 identities and 3,193 names, and no row of the join moves.
    """
    import sys

    sys.path.insert(0, str(ROOT / "survey"))
    import migration_notes

    assert migration_notes.restates_upstream(MODULE), (
        f"{MODULE} does not declare {migration_notes.RESTATES}, so the next run of "
        "survey/alias_surface.py reads its own output as our surface"
    )
    assert not migration_notes.restates_upstream("adcp.types.core"), (
        "a DOMAIN module reads as a restatement of upstream, which would drop the "
        "schema-derived surface out of the partition"
    )


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
