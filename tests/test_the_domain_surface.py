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

So the obligation has two halves and they fail differently, which is why there are two
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
branches and 115 aliases where the run's record answers **1,951 with 756 branches and 141
aliases** -- 196 declarations invisible, and four of the collisions below among them.  A
module's own text cannot say which of its class statements a union declared, so no reader
of the text can ask §1's question.

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

**THIS FILE IS RED, and the first test names the blocker rather than the absence.**  The
surface does not exist yet -- all 23 domains have no public module.  Behind that sits the
one thing that must land first, and it is this file's own second clause: the export set is
**1,951 declarations -- a root for each of the 1,054 emitted documents, 756 union branches
and 141 further aliases -- carrying 1,932 distinct ``(domain, name)`` pairs, and 18 of
those names are wanted by more than one declaration** (``adcp-client-python-82m.9``;
``core.GeoProximity`` is wanted by three).  §4's collision rule settles a name inside one
MODULE, and a domain is many modules.  The root axis of the rule has landed -- the
domain's ROOT symbols are a bundle-wide reading that costs no lowering
(``emit.domain_roots``) -- and it closed eight: the six async-response ``…Submitted``
roots against their sync response's branch, plus ``core.FormatOptionReference`` and
``core.PlacementSelection``, both nested-union arms this file could not see while it read
the text.  What is left needs the domain's NESTED names, which needs the bundle-wide
naming pass §9's ruling calls for.

The second and third tests pass against a generated surface over this set, so those 18
names are the whole of what stands between this file and green.
"""

from __future__ import annotations

import importlib
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
    (``lower/names.py``'s ``the_surface_exports``).  The DOMAIN is ``emit.domain``, §1's
    one derivation of it, so nothing here spells a domain or a kind twice.

    A LIST and not one entry, because a name two declarations want is exactly what the
    first test has to report, and a mapping to one could not hold both.
    """
    out: dict[tuple[str, str], list[tuple[str, str]]] = {}
    held = compiled(BUNDLE, fresh.population())
    for document, exported in held.surface.items():
        module = emit.module_path(document).replace("/", ".")
        for name, kind in exported.items():
            out.setdefault((emit.domain(document), name), []).append((module, kind))
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
