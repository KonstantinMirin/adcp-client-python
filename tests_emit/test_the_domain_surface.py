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

So the obligation has FOUR halves and they fail differently, which is why there are four
tests and not one:

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
* **EVERY CLASS REACHED.**  Reading 6's FIRST sentence, which the three above cannot ask
  because all three range over the EXPORT SET: "``from adcp.types.<domain> import
  <Name>`` **reaches every class the tree declares**".  A class the export set never held
  is invisible to the other three, and from 2026-10-30 to 2026-11-07 that was **1,342 of
  the 3,091 classes the run declares**.  See
  :func:`test_every_class_the_tree_declares_is_reachable_at_one_domain_path`.

  **WITH ONE SET CARVED OUT OF IT BY THE OWNER'S RULING OF 2026-11-10**
  (``lower/names.A_POSITIONAL_NAME_IS_PRIVATE``): a class whose only available name is
  ``<Base>Branch<i>`` is declared and is reachable at NO domain path.  Not an exception to
  reading 6 so much as reading 4's placeholder rule meeting it -- "a name minted for want
  of a subject must not become a name an application depends on" -- and the two sentences
  disagreed in writing for ten days while the surface published six such names.  The
  set is the run's own record and not a list, so the carve-out shrinks by itself as
  the bundle titles those branches;
  ``tests_emit/test_no_positional_name_is_public.py`` asserts the other direction.

**WHAT THE SURFACE EXPORTS is §1's decision of 2026-10-30 as amended by reading 6 on
2026-11-07, and is DERIVED here, never listed**: every document **ROOT**, every union
**BRANCH**, every D2 type **ALIAS**, and every untitled **INNER** node.  Not the per-module
``strict_validate`` helper, because a domain name cannot stand for 241 functions and a
caller reaches one through its class.  §1 carries the table.

**THE FOURTH KIND IS THE ONE WITHDRAWN ON 2026-10-30 AND RETURNED WITH ITS WORD.**  "Every
class the tree declares" was decided and withdrawn the same day on the measurement,
"because it makes ``core.Status`` name one of fourteen declarations" -- and that was a
finding about the WORD, not about the set.  Reading 6's clause of 2026-11-07 supplies the
word: **an untitled inner node is exported under its parent's name and its key, ALWAYS**,
which read transitively is the node's whole chain through the document
(``lower/names.THE_INNER_EXPORT``).  All fourteen are now reachable and none is spelled
``Status``.  Measured over this bundle: **3,221 export paths over 3,221 declarations**, of
which **1,343 are inner** -- 1,020 roots, 736 branches, 122 aliases -- with 0 words two
positions of one domain want and 0 classes at two paths.  The literal depth-2 reading of
the clause leaves 18 words contested over 38 positions and 3 colliding with an existing
export, which is why the reading is transitive; ``THE_INNER_EXPORT`` carries that
measurement.

**AND ONE NAME LEFT THE SURFACE, which is §1's own cross-module rule reaching a case it
could not reach before.**  ``adcp.types.core.VerificationTokenGradingProfile`` was a path
named after ``core/verification-token-claims.json``, which merely ``$ref``s the class
``core/registry-event.json`` declares; §1 drops such a name once the DECLARING module
publishes the class ("a named node that is a bare ``$ref`` to another document binds the
symbol that document declares ... this position's name is the second one §1 forbids"), and
the clause is what made the declaring module publish it.  The class is reached at
``adcp.types.core.RegistryEventAgentVerificationEarnedAgentPayloadGradingProfile``, and
upstream's own spelling of the word is carried by the alias layer, where
``survey/alias-surface-9.6.1.tsv`` already had it.

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

import fresh
import pytest
from compiled import compiled
from nodeset import claimed

from codegen import emit
from codegen.lower import names

#: **The bundle a RUN reads, re-exported from ``tests/fresh.py``** -- the one seam that
#: answers "which bundle is this run's".  Not a path of this module's own, and that is the
#: whole of the fix it carries: :func:`surface` and
#: :func:`test_the_export_paths_number_the_declarations_behind_them` read a COMPILE of
#: this bundle over ``fresh.population()``, which is the document set of the bundle
#: ``tests/fresh.py`` materialised the graded tree from.  Spelled separately, the two can
#: name different bundles -- and the measurement is that they did: with the build's patch
#: sets applied, ``fresh.population()`` carries ``core/country-code.json``, which exists
#: only in the patched bundle, and ``compiled()`` opened it under this module's own
#: published path and raised ``FileNotFoundError`` in the setup of three tests
#: (``adcp-client-python-lzzj.9``).  One run must not range over two bundles, so there is
#: one spelling of the bundle and the readers take it from there.
BUNDLE = fresh.BUNDLE


def surface() -> dict[tuple[str, str], list[tuple[str, str, str]]]:
    """``(domain, word)`` -> every ``(private module, kind, symbol)`` the surface exports it
    from.

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

    **THE KEY IS THE WORD THE SURFACE PUBLISHES AND THE SYMBOL RIDES BESIDE IT** (reading
    6's inner clause, 2026-11-07, ``lower/names.THE_INNER_EXPORT``).  For a ROOT, a BRANCH
    and an ALIAS the two are one string; for an untitled INNER node the private module
    declares ``Method`` and the surface publishes ``PixelTrackerAssetMethod``, so a reader
    asking "which name can I not use" wants the word and a reader asking "is it the same
    object" wants the symbol.  Both are here because both tests below ask, and deriving
    either from the other is the second derivation ``emit.published`` exists to prevent.
    """
    out: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    held = compiled(BUNDLE, fresh.population())
    for module, exported in held.surface.items():
        renamed = held.published.get(module, {})
        for name, kind in exported.items():
            out.setdefault((emit.module_domain(module), renamed.get(name, name)), []).append(
                (module.replace("/", "."), kind, name)
            )
    return out


@pytest.fixture(scope="module")
def exported() -> dict[tuple[str, str], list[tuple[str, str, str]]]:
    """The export set, read once per process off the fresh tree."""
    assert not fresh.FAILURE, fresh.FAILURE
    return surface()


def test_every_name_the_surface_exports_resolves_at_exactly_one_domain_name(
    exported: dict[tuple[str, str], list[tuple[str, str, str]]],
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
        f"{domain}.{name}": sorted(
            f"{kind} {symbol} in {module}" for module, kind, symbol in sources
        )
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
    exported: dict[tuple[str, str], list[tuple[str, str, str]]],
) -> None:
    """§1's other half: the public name is the thing, not a second one of that name.

    What this stops is specific: a surface built by DECLARING rather than re-exporting
    would pass the test above and give a consumer a class whose ``isinstance`` is false
    against every instance the runtime builds, and whose ``__adcp_schema__`` would be a
    second copy to keep in agreement.  ``is`` is the whole assertion.

    **AND THE WORD AND THE SYMBOL ARE BOTH READ, which is what reading 6's inner clause
    adds here** (2026-11-07): the public name is the clause's WORD and the private name is
    the SYMBOL §4 derived, so the two sides of the ``is`` are spelled differently and a
    check that used one string for both would ask nothing at all of the 1,343 statements
    the clause writes -- ``getattr(public, word) is getattr(held, word)`` raises
    ``AttributeError`` on the private module rather than comparing anything.
    """
    claimed("the names the surface exports", exported)
    not_the_same: dict[str, str] = {}
    unreachable: list[str] = []
    for (domain, name), sources in sorted(exported.items()):
        if len(sources) > 1:
            continue  # the test above owns the ambiguity; this one owns identity
        ((private, _, symbol),) = sources
        try:
            public = importlib.import_module(f"adcp.types.{domain}")
        except ImportError:
            unreachable.append(f"adcp.types.{domain} (for {name})")
            continue
        if not hasattr(public, name):
            unreachable.append(f"adcp.types.{domain}.{name}")
            continue
        held = importlib.import_module(f"adcp.types._schemas.{private}")
        if getattr(public, name) is not getattr(held, symbol):
            not_the_same[f"adcp.types.{domain}.{name}"] = (
                f"is not adcp.types._schemas.{private}.{symbol}"
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
    exported: dict[tuple[str, str], list[tuple[str, str, str]]],
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
        # **THE SYMBOL AND NOT THE WORD, which is what reading 6's inner clause needs of
        # ``declaring``**: that reading's non-class arm keys a binding on the name the
        # RECORD holds, and the record holds §4's symbol.  The word is the public path and
        # is what a failure is reported under, which is the other side of the pair.
        symbol = sources[0][2]
        module = importlib.import_module(f"adcp.types.{domain}")
        key = declaring(private, symbol, getattr(module, name), held.binds.get(private, {}))
        if key is None:
            undecided[f"{domain}.{name}"] = held.binds[private][symbol][1]
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


def test_every_class_the_tree_declares_is_reachable_at_one_domain_path(
    exported: dict[tuple[str, str], list[tuple[str, str, str]]],
) -> None:
    """Reading 6's FIRST sentence, which no check in this file could ask before.

    ``final-state.md`` reading 6: "``from adcp.types.<domain> import <Name>`` **reaches
    every class the tree declares** -- roots, union branches and aliases alike -- at
    exactly one such path."  The three checks above range over the EXPORT SET and ask
    whether it resolves, is unambiguous and counts right; **a class the export set never
    held is invisible to all three**, and from 2026-10-30 to 2026-11-07 that was 1,342 of
    them.  So this is the sentence read the other way round: the population is the classes
    the RUN declares and the question is how many domain paths reach each.

    Reading 6's clause of 2026-11-07 is what makes it answerable
    (``lower/names.THE_INNER_EXPORT``): "**an untitled inner node is exported under its
    parent's name and its key, ALWAYS -- never only when the key collides**", with the
    reason being stability -- "a document arriving later with a colliding key would RENAME
    an export an application already imports".

    **BOTH DIRECTIONS ARE ONE EQUALITY AND BOTH ARE REPORTED BY NAME**, because the two
    failures this change can introduce are opposite:

    * ``no domain path`` -- the clause was withheld for a class, so the tree declares
      something an application cannot import.  This is the arm that reddens when the
      export is taken out of the EMITTER, which is the only place it can be taken out of:
      the surface is generated from ``emit.surface`` and ``emit.published``, so a
      perturbation of the committed text is overwritten by the next run and grades nothing
      (``tests/fresh.py``: "the committed tree is an ARTIFACT, verified by one
      byte-compare, and is never the subject").
    * ``two domain paths`` -- the clause was applied to a class some other position
      already exports, which is reading 6's "no second way reaches the same class" and the
      error the uniform rule most plausibly introduces.  Measured over this bundle, 20
      inner positions declare a class the surface already carries under the word of the
      position that ADOPTED it -- ``adagents``'s ``TagsValue``, reached at
      ``adcp.types.adagents.SignalTagsValue`` -- and an export per declaring POSITION
      rather than per unreached CLASS would give every one of them a second path.

    **The population is the RUN's record of what it declared** (``emit.Emitted.declared``,
    minus the bindings in ``emit.Emitted.binds``), and the identity is the RUNTIME's, for
    ``declaring``'s own reason: a class carries its declaring position in ``__module__``
    and ``__qualname__``, so the key is the one §1 settles the counting on and is not
    ``id()``.  Restricted to the classes, because reading 6's sentence is about classes
    and an annotated alias is interned -- the exact charge §1 refuses.
    """
    held = compiled(BUNDLE, fresh.population())
    #: Every declaration the run made that is a CLASS, keyed the way ``declaring`` keys an
    #: export path: the private module it was declared in and the symbol it was declared
    #: under.  A binding is not a declaration (§1's own reading), so it is subtracted.
    classes: dict[tuple[str, str], str] = {}
    for document, declared in held.declared.items():
        module = emit.module_path(document)
        bound = held.binds.get(module, {})
        private = importlib.import_module(f"adcp.types._schemas.{module.replace('/', '.')}")
        # **THE POSITIONAL NAMES ARE SUBTRACTED, by the owner's ruling of 2026-11-10**
        # (``lower/names.A_POSITIONAL_NAME_IS_PRIVATE``).  Reading 6's sentence is "reaches
        # every class the tree declares", and the ruling carves one set out of it: a class
        # whose only available name is ``<Base>Branch<i>`` is DECLARED -- deleting it would
        # drop a branch from the union and refuse payloads the document admits -- and is reachable at
        # NO domain path, because "a name minted for want of a subject must not become a
        # name an application depends on".
        #
        # It is subtracted from the SET and not excused in the report, which is the
        # difference between an amended reading and a suppression list: the run's own
        # record says which names the ruling withheld (``emit.Emitted.positional``), so a
        # class that stops being positional rejoins this test with nobody editing it, and
        # ``tests_emit/test_no_positional_name_is_public.py`` is where the other direction
        # is asserted -- that the withheld set is non-empty and that none of it is public.
        # Measured over this bundle: 6 classes, over 6 modules of 4 domains.
        for symbol in set(declared.values()) - set(bound) - held.positional.get(module, frozenset()):
            obj = getattr(private, symbol, None)
            if isinstance(obj, type):
                classes[(obj.__module__, obj.__qualname__)] = f"{module}.{symbol}"
    claimed("the classes the run declares", classes)

    reaches: dict[tuple[str, str], list[str]] = {}
    for domain, name in exported:
        module = importlib.import_module(f"adcp.types.{domain}")
        obj = getattr(module, name)
        if isinstance(obj, type):
            reaches.setdefault((obj.__module__, obj.__qualname__), []).append(
                f"adcp.types.{domain}.{name}"
            )
    none_of_them = sorted(where for key, where in classes.items() if key not in reaches)
    two_of_them = {
        classes[key]: sorted(found)
        for key, found in reaches.items()
        if len(found) > 1 and key in classes
    }
    assert not none_of_them, {
        "the rule": names.THE_INNER_EXPORT,
        "classes the tree declares that no domain path reaches": none_of_them,
        "classes declared": len(classes),
    }
    assert not two_of_them, {
        "the rule": names.THE_INNER_EXPORT,
        "classes two domain paths reach": two_of_them,
    }
