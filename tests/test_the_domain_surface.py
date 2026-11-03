"""The surface a consumer touches: ``adcp.types.<domain>`` and the two halves of it.

``docs/plan/rebuild-plan.md`` §1 states both, in two sentences:

    a document compiles to a module at its own path under a private tree ... **and is
    re-exported from** ``adcp.types.<domain>``, **where the domain is derived from the
    document's own path**.

    There is **one import path per class**, and never a second way to reach the same
    class. ... The one path is the domain surface's.

and §1's amendment of 2026-10-30 states the other direction of the same rule, which is
the one a surface actually breaches: **no ``adcp.types.<domain>.<Name>`` may name two
declarations.**

So the obligation has THREE halves and they fail differently, which is why there are
three tests and not one:

* **EXACTLY ONE.**  Every name the surface exports resolves at exactly one
  ``adcp.types.<domain>.<Name>``.  Two failure shapes live under that one sentence and
  both are reported: a name that resolves at NO public module, and a name that TWO
  declarations of one domain both want -- which Python resolves by binding whichever
  import ran last, silently, so a re-export of both is a surface where one of them is
  unreachable and nothing says which.
* **THE SAME OBJECT.**  What is reached at the public name ``is`` what is reached at its
  private ``adcp.types._schemas.<path>`` name.  Without this half a surface could
  satisfy the first by MINTING a second class of the same name, and a consumer's
  ``isinstance`` would then be false against the class the runtime actually built --
  the defect §1's one-path rule exists to make unrepresentable.
* **ONE DECLARATION PER PATH.**  Reading 6's own sentence -- "the number of export paths
  equals the number of distinct objects behind them" -- and the one the first half cannot
  ask: "a check that resolves every export and requires exactly one path each is answered
  ``yes`` by two names for one object, each resolving cleanly, so it reads green while
  this reading is false.  **Both checks belong; the per-name one is incomplete, not
  wrong.**"  Measured before this landed: **1,945 export paths over 1,927 distinct
  declarations**, with 13 declarations reached at 31 paths and 16 objects at 40.  §1
  settles the COUNTING there and it is not ``id()``: see :func:`declaring`.

**WHAT THE SURFACE EXPORTS is §1's decision of 2026-10-30 and is DERIVED here, never
listed**: every document **ROOT**, every union **BRANCH**, and every D2 type **ALIAS**.
Not every class the tree declares -- that was decided and withdrawn the same day on the
measurement, because it makes ``core.Status`` name one of fourteen declarations.  Not the
per-module ``strict_validate`` helper either, because a domain name cannot stand for 241
functions and a caller reaches one through its class.  §1 carries the table.

**THE EXPORT SET IS THE RUN'S OWN RECORD AND IS NOT RE-DERIVED HERE** (``emit.surface``,
written from ``lower/names.py``'s ``the_surface_exports``).  This file derived it twice
and the second derivation was WRONG, which is the whole reason it reads the record now: a
reading over the emitted TEXT has to spell "branch" as "a class one of whose bases this
module declares", and that **misses every arm of a nested ``A | B`` union**, which
subclasses nothing local.  Measured, the text-reading answered 1,755 declarations with 613
branches and 115 aliases where the run's record answered **1,951 with 756 branches and 141
aliases** -- 196 declarations invisible, and four of the collisions below among them.  A
module's own text cannot say which of its class statements a union declared, so no reader
of the text can ask §1's question.

**AND THE RECORD IS WHERE §1's ONE-PATH RULE IS APPLIED, not only where it is read**
(2026-11-03): a position that merely NAMES a declaration made somewhere else is not an
export of it, so the pass relocates the export to the declaring position and the record
answers **1,927** -- 1,054 roots, 743 branches and 130 aliases.  23 names left the surface
and 5 joined it, because for five objects the name §1 keeps was not exported at all: the
surface assigns no kind to a declaration at a property or element position.

Identity is the opposite question and only the RUNTIME can answer it, so the second test
imports.  The two agree because ``tests/fresh.py`` materialises the tree from the same
compile this record comes from.

**The set is named BY NAME and never by count** (§8's last paragraph, and
``tests/nodeset.py``): the question a reader of a failure asks is "which name can I not
use", and only the list answers it.  A count would also go stale on the next emitting
row, which is what ``tests/test_every_check_names_its_set.py`` exists to stop.

**The population is the bundle's portable set compiled FRESH**, not ``src/``, for
``tests/fresh.py``'s own reason: the committed tree is an artifact verified by one
byte-compare and is never the subject, so a surface the compiler stopped emitting would
otherwise still be graded green off the checkout.

**The DOMAIN is derived here and never listed.**  §1 says it is "derived from the
document's own path", so it is the first path segment of the module's own path under
``_schemas`` -- which is what makes a new document appear in its domain with nobody
editing anything.  A test carrying the list of domains would be the second place that
derivation lives, and the first to go stale.  The derivation answers **23** scopes, which
§1 confirms: ``adagents.json`` sits at the tree's root with no directory beside it, so its
classes are a domain of one module.

**THE COLLISION BLOCKER IS CLOSED** -- every export set this file has measured sits over
as many DISTINCT ``(domain, name)`` pairs as it has members, so §1's "no
``adcp.types.<domain>.<Name>`` may name two declarations" holds with nothing left over
(``adcp-client-python-82m.9``).  It was 26 collisions; §4's collision rule at domain scope
closed every one, 8 of them off the bundle-wide ROOT symbols (``emit.domain_roots``, 0.23 s
and no lowering) and the other 18 off ``emit.domain_exports``, which repeats §4's step
until no two documents of one domain export one name.  Dropping 23 names and adding 5
moved the set the rule ranges over and un-lengthened nothing: measured, no retained name
changed its spelling.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path

import pytest

import fresh
from codegen import emit
from compiled import compiled
from nodeset import claimed


BUNDLE = Path(__file__).resolve().parents[1] / "schemas" / "cache" / "3.2"


def surface() -> dict[tuple[str, str], list[tuple[str, str]]]:
    """``(domain, name)`` -> every ``(private module, kind)`` the surface exports it from.

    Read off ``emit.surface``, the run's own record of §1's export set, which is written
    from the one place a position's hop and its declaration are both in hand
    (``lower/names.py``'s ``the_surface_exports``).  The DOMAIN is
    ``emit.module_domain``, §1's one derivation of it, so nothing here spells a domain or
    a kind twice.

    **THE RECORD IS KEYED ON THE MODULE** (§3a, 2026-11-02), so there is no document to
    turn into one here and no second reading of D1: "every document already maps to the
    module it produced, so the key becomes that module and a catalogue module is simply
    one with no document.  The readers that take a document to answer a domain or a path
    take the module instead, which is what they were always asking about."  This file was
    one of the two readers and spelled ``emit.module_path(document)`` to get exactly this.

    Measured over the record, before the catalogue module and after -- the row that moved
    the KEY, so the figures are that row's and the pair count is the one it read:

    ============================  ======  =====
    the record                    before  after
    ============================  ======  =====
    modules                        1,054  1,058
    ... of those exporting none        0      4
    exported ``(domain, name)``    1,950  1,950
    domains ON the record             23     24
    domains that export a name        23     23
    ============================  ======  =====

    The four are §3a's catalogue modules, one per namespace its scope rule names, and
    they export nothing because "nothing here is a type" -- a value list is private to
    the modules that build a type over it.  So the exported pairs did not move and the
    24th domain, ``common``, has no public module: §1's surface is stated over what is
    EXPORTED, and ``emit.domain_modules`` reads that rather than being told.


    A LIST and not one entry, because a name two declarations want is exactly what the
    first test has to report, and a mapping to one could not hold both.
    """
    out: dict[tuple[str, str], list[tuple[str, str]]] = {}
    held = compiled(BUNDLE, fresh.population())
    for module, exported in held.surface.items():
        for name, kind in exported.items():
            out.setdefault((emit.module_domain(module), name), []).append(
                (module.replace("/", "."), kind)
            )
    return out


@pytest.fixture(scope="module")
def exported() -> dict[tuple[str, str], list[tuple[str, str]]]:
    """The export set, read once per process off the fresh tree."""
    assert not fresh.FAILURE, fresh.FAILURE
    return surface()


def test_every_name_the_surface_exports_resolves_at_exactly_one_domain_name(
    exported: dict[tuple[str, str], list[tuple[str, str]]],
) -> None:
    """§1: "no ``adcp.types.<domain>.<Name>`` may name two declarations".

    Three things are reported, each BY NAME:

    * ``no domain module`` -- the domain has no public module at all, so none of its
      names can be used;
    * ``ambiguous`` -- two declarations of one domain want one name, so the public name
      can only mean one of them and the surface cannot say which.  This is the scope §4's
      collision rule does not reach: §4 settles a name inside one MODULE, and a domain is
      many modules;
    * ``absent`` -- the domain module exists and does not carry the name.
    """
    claimed("the names the surface exports", exported)

    ambiguous = {
        f"{domain}.{name}": sorted(f"{kind} in {module}" for module, kind in sources)
        for (domain, name), sources in exported.items()
        if len(sources) > 1
    }
    missing_module: dict[str, str] = {}
    absent: list[str] = []
    for (domain, name), sources in sorted(exported.items()):
        if f"{domain}.{name}" in ambiguous:
            continue
        try:
            module = importlib.import_module(f"adcp.types.{domain}")
        except ImportError as why:
            missing_module[domain] = str(why)
            continue
        if not hasattr(module, name):
            absent.append(f"adcp.types.{domain}.{name} ({sources[0][0]})")

    assert not missing_module, {
        "domains with no public module": sorted(missing_module),
        "why": missing_module,
    }
    assert not ambiguous, {"names two declarations of one domain both want": ambiguous}
    assert not absent, {"names no domain module carries": absent}


def test_the_domain_name_gives_the_same_object_as_the_private_path(
    exported: dict[tuple[str, str], list[tuple[str, str]]],
) -> None:
    """§1's other half: the public name is the thing, not a second one of that name.

    What this stops is specific: a surface built by DECLARING rather than re-exporting
    would pass the test above and give a consumer a class whose ``isinstance`` is false
    against every instance the runtime builds, and whose ``__adcp_schema__`` would be a
    second copy to keep in agreement.  ``is`` is the whole assertion.
    """
    claimed("the names the surface exports", exported)
    not_the_same: dict[str, str] = {}
    unreachable: list[str] = []
    for (domain, name), sources in sorted(exported.items()):
        if len(sources) > 1:
            continue  # the test above owns the ambiguity; this one owns identity
        ((private, _),) = sources
        try:
            public = importlib.import_module(f"adcp.types.{domain}")
        except ImportError:
            unreachable.append(f"adcp.types.{domain} (for {name})")
            continue
        if not hasattr(public, name):
            unreachable.append(f"adcp.types.{domain}.{name}")
            continue
        held = importlib.import_module(f"adcp.types._schemas.{private}")
        if getattr(public, name) is not getattr(held, name):
            not_the_same[f"adcp.types.{domain}.{name}"] = (
                f"is not adcp.types._schemas.{private}.{name}"
            )
    assert not unreachable, {"not reachable at a public name": sorted(set(unreachable))}
    assert not not_the_same, {"a second object wearing the public name": not_the_same}


def declaring(
    module: str, name: str, obj: object, binds: Mapping[str, tuple[str | None, str]]
) -> tuple[str, str] | None:
    """The DECLARATION one export path is a path to, or ``None`` where nothing says.

    §1 (2026-11-03): "**A gate on this counts DECLARATIONS, not ``id()`` and not names**.
    Three readings were available and the middle one is right."  This is the middle one,
    and all three of its arms are §1's own sentences:

    * **A CLASS carries its own declaring position**, in ``__module__`` and
      ``__qualname__``: the class statement ran once, Python recorded where, and the name
      it recorded is the name §4 derived at the declaring position.  So a binding to a
      class and the class's own export path collapse onto one key with nothing told to
      this function, which is why the class arm is FIRST.
    * **A BINDING declares nothing of its own**, so the key is the declaration it names:
      "an ``X = <bare Name>`` is a binding, not a declaration", and "the other spellings
      are the names of positions that REFERENCE it, and a position that references a
      class does not name it".  Read off the run's own record
      (``emit.Emitted.binds``), because for an alias no other reader can answer: the
      runtime cannot -- the type system interns an ``Annotated`` and a ``Literal``, so
      ``X`` and ``Y`` are one object whether or not either names the other -- and §1
      forbids the emitted TEXT to be the subject.
    * **ANYTHING ELSE is its own declaration at its own module-level statement**, which is
      §1's reason for refusing ``id()``: "Counting ``id()`` is too STRONG, and it charges
      us for something we did not do.  Where several documents each state the same
      constrained scalar, the walk emits an independent alias statement in each ... The
      runtime then binds them to one object because the type system interns it, and the
      same happens to an interned literal.  **A gate keyed on object identity reports
      those as a violation with no available repair.**"  Those are reading 4's, §3a's
      collection is their repair, and this arm is what keeps them out of this gate.

    ``None`` is the UNDECIDABLE answer and not a pass: ``emit._declaring_module`` answers
    ``None`` where the run cannot say which module declares a binding's target, and the
    caller REPORTS that rather than keying the path on the module that merely references
    the class -- which would count a second path as its own declaration, the exact
    blindness this check exists to end.  Measured over the 3.2 bundle: 0.
    """
    if isinstance(obj, type):
        return (obj.__module__, obj.__qualname__)
    where, held, seen = module, name, {name}
    #: The chain is followed only while it stays in THIS module, because ``binds`` is this
    #: module's record: ``X = Y`` beside ``Y = Z`` charges ``Z``, and a hop out of the
    #: module is the end of what this record can say.
    while where == module and held in binds and binds[held][1] not in seen:
        where, held = binds[held]
        if where is None:
            return None
        seen.add(held)
    return (where, held)


def test_the_export_paths_number_the_declarations_behind_them(
    exported: dict[tuple[str, str], list[tuple[str, str]]],
) -> None:
    """Reading 6, counted the way §1 settles: **one declaration per export path**.

    ``final-state.md`` reading 6: "**Decided by** counting OBJECTS, not names: the number
    of export paths equals the number of distinct objects behind them ... A check that
    resolves every export and requires exactly one path each is answered ``yes`` by two
    names for one object, each resolving cleanly -- so it reads green while this reading is
    false.  **Both checks belong; the per-name one is incomplete, not wrong.**"  So this
    test joins the two above rather than replacing either.

    **AND WHAT IS COUNTED IS DECLARATIONS AND NOT ``id()``** (§1, 2026-11-03), which is
    the one thing this check could get wrong in the expensive direction: the type system
    interns an ``Annotated`` alias and a ``Literal``, so a gate on object identity charges
    a defect to two documents that each state one constrained scalar -- "a gate nobody can
    satisfy rather than one that finds a defect".  :func:`declaring` is the three-armed
    reading §1 rules for, and the arithmetic is the one sentence over it.

    Two failures sit under the one equality and both are reported BY NAME:

    * ``two paths to one declaration`` -- the defect itself, named by the declaration and
      listing every path that reaches it.  §1's repair is the rename: "the surface keeps
      only the declaring position's spelling", and it is not purely subtractive -- where
      the declaring position is a property or an element the surface assigned it no kind,
      so the name the rule keeps was not exported at all and the rename ADDS one.
    * ``no declaration this reading can name`` -- an export whose declaration is an alias
      in another module, which the record states as a symbol with no module beside it.
      That is an answer this check does not have rather than one it passes, because
      keying such a path on its OWN module would count a second path as a declaration,
      which is the blindness the per-name check already has.
    """
    claimed("the names the surface exports", exported)
    held = compiled(BUNDLE, fresh.population())
    behind: dict[tuple[str, str], list[str]] = {}
    undecided: dict[str, str] = {}
    for (domain, name), sources in sorted(exported.items()):
        # :func:`surface` spells the module the way an IMPORT does; the record is keyed
        # on the module's own path, which is what ``Emitted.binds`` and ``declares`` hold.
        private = sources[0][0].replace(".", "/")
        module = importlib.import_module(f"adcp.types.{domain}")
        key = declaring(private, name, getattr(module, name), held.binds.get(private, {}))
        if key is None:
            undecided[f"{domain}.{name}"] = held.binds[private][name][1]
            continue
        behind.setdefault(key, []).append(f"{domain}.{name}")
    shared = {
        f"{where}.{symbol}": sorted(found)
        for (where, symbol), found in behind.items()
        if len(found) > 1
    }
    assert not undecided, {"no declaration this reading can name": undecided}
    assert not shared, {
        "two paths to one declaration": shared,
        "export paths": len(exported),
        "declarations behind them": len(behind),
    }
    assert len(exported) == len(behind), {
        "export paths": len(exported),
        "declarations behind them": len(behind),
    }


def test_a_caller_can_name_the_branch_a_union_handed_it() -> None:
    """The reason this is a rewrite and not a patch set, as the lines a consumer writes.

    ``docs/plan/surface-goal.md``: "A class a union can return is reachable and named
    for what it is ... a caller who receives an ``AssetRequirements`` cannot name the
    branch it got.  This is the whole reason for the rewrite".

    ``core/requirements/asset-requirements.json`` is the document that measurement was
    taken on: its module declares the union base and twelve branches and writes
    ``__all__ = ["AssetRequirements"]``, so twelve of its thirteen classes are reachable
    by no public path today.  The branch a dispatch hands back is
    ``AssetRequirementsJavaScript`` and ``JavaScriptAssetRequirements`` is the separate
    document it composes -- both are names a caller who holds the branch may want, and
    the two are not interchangeable: only the branch is an ``AssetRequirements``.
    """
    core = importlib.import_module("adcp.types.core")
    enums = importlib.import_module("adcp.types.enums")
    base = core.AssetRequirements
    branch = core.AssetRequirementsJavaScript
    composed = core.JavaScriptAssetRequirements
    assert enums.MatchType("broad")
    held = branch.model_construct()
    assert isinstance(held, branch)
    assert isinstance(held, base)
    assert isinstance(held, composed)
