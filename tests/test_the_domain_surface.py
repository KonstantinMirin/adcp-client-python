"""The surface a consumer touches: ``adcp.types.<domain>`` and the two halves of it.

``docs/plan/rebuild-plan.md`` §1 states both, in two sentences:

    a document compiles to a module at its own path under a private tree ... **and is
    re-exported from** ``adcp.types.<domain>``, **where the domain is derived from the
    document's own path**.

    There is **one import path per class**, and never a second way to reach the same
    class.  ... The one path is the domain surface's.

So the obligation has two halves and they fail differently, which is why there are two
tests and not one:

* **EXACTLY ONE.**  Every class the emitted tree declares resolves at exactly one
  ``adcp.types.<domain>.<Name>``.  Two failure shapes live under that one sentence and
  both are reported: a class that resolves at NO public name, and a name that TWO
  declarations of one domain both want -- which Python resolves by binding whichever
  import ran last, silently, so a re-export of both is a surface where one of them is
  unreachable and nothing says which.
* **THE SAME OBJECT.**  The class reached at the public name ``is`` the class reached at
  its private ``adcp.types._schemas.<path>`` name.  Without this half a surface could
  satisfy the first by MINTING a second class of the same name, and a consumer's
  ``isinstance`` would then be false against the class the runtime actually built --
  the defect §1's one-path rule exists to make unrepresentable.

**The set is named BY CLASS and never by count** (§8's last paragraph, and
``tests/nodeset.py``): the question a reader of a failure asks is "which class can I not
name", and only the list answers it.  A count would also go stale on the next emitting
row, which is what ``tests/test_every_check_names_its_set.py`` exists to stop.

**The population is the FRESH tree** (``tests/fresh.py``), not ``src/``, for that
module's own reason: the committed tree is an artifact verified by one byte-compare and
is never the subject, so a domain surface that the compiler stopped emitting would
otherwise still be graded green off the checkout.

**The DOMAIN is derived here and never listed.**  §1 says it is "derived from the
document's own path", so it is the first path segment of the module's own dotted name
under ``adcp.types._schemas`` -- which is what makes a new document appear in its domain
with nobody editing anything.  A test carrying the list of domains would be the second
place that derivation lives, and the first to go stale.  The derivation answers **23**
scopes where the epic's own list names 22: ``adagents.json`` sits at the tree's root with
no directory beside it, so its 39 classes are a domain of one module, and the first test
reports ``adagents`` with the other 22 rather than quietly dropping it.

**THIS FILE IS RED, and what it reports is the blocker rather than the absence.**  The
surface does not exist yet -- the first test names all 23 domains as having no public
module -- and the reading that says why it could not simply be written is the first test's
own second clause, measured by running it against a generated surface over every declared
class: of the **3,449** classes the tree declares, grouped into **3,056** distinct
``(domain, name)`` pairs, **237 names are wanted by 630 declarations** -- ``core.Status``
by 14 of them, ``core.Reason`` by 11, ``core.Location`` by 10.  Narrowed to what §1 itself
spells, a symbol per document, the figure is **0**: every document's own root class is
already unique in its domain.  Adding the 613 union branches, which is the whole reason
for the rewrite, costs **11**.  Taking every declared class costs the other 226, almost
all of them generic nested property names.

The second and third tests pass against that surface, so what stands between this file and
green is exactly those 237 names: §4 settles a name inside one MODULE, and nothing yet
settles one inside a DOMAIN.  Widening §4 to the domain renames classes, which is not this
file's to do.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import fresh
from codegen import emit
from nodeset import claimed


def declared() -> dict[tuple[str, str], list[type]]:
    """``(domain, class name)`` -> every class the FRESH tree declares under it.

    A class and not a name: the two halves below ask about object identity, so the
    derivation carries the objects the runtime actually built.

    ``value.__module__ == name`` is what makes this DECLARED rather than merely visible:
    an emitted module imports a base from the module that declares it (§2's ``$ref``
    row), so a scan of module contents without that test would count one class once per
    module that names it.

    **Every class and not every MODEL**, which is the one thing here that had to be
    measured rather than borrowed.  ``tests/_imports_a_tree.py`` filters on
    ``pydantic.BaseModel`` because its question is ``model_json_schema()``; the question
    HERE is what a consumer can name, and §1's own worked example is
    ``from adcp.types.enums import MatchType`` -- a ``StrEnum``, which is not a
    ``BaseModel`` and which that filter drops.  Taking the filter unchanged was tried
    first and reported ``adcp.types.core.Format`` as a second class wearing a public
    name, because the enumeration declaring it was outside the derivation while the
    model of that name was inside it.

    A list and not a single class, because a name two declarations want is exactly what
    the first half has to report, and a mapping to one class could not hold both.

    **Deduplicated by IDENTITY, which is §1's own carve-out and not a convenience**: "A
    second name bound to a class by identity (§4, two nodes of identical content) is that
    class and not a second one: ``X is Y`` holds, and the surface exports it once."  The
    tree carries such bindings, so a module's namespace offers one class under two names
    and a walk of ``vars`` meets it twice; the list holds it once, and the ambiguity below
    is therefore about two DIFFERENT classes and never about that carve-out.
    """
    package = fresh.schemas()
    assert package is not None, fresh.FAILURE
    out: dict[tuple[str, str], dict[int, type]] = {}
    for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        module = importlib.import_module(info.name)
        under = info.name.removeprefix(f"{emit.PACKAGE}.")
        domain = under.split(".")[0]
        for value in vars(module).values():
            if isinstance(value, type) and value.__module__ == info.name:
                out.setdefault((domain, value.__name__), {})[id(value)] = value
    return {key: list(found.values()) for key, found in out.items()}


@pytest.fixture(scope="module")
def tree_classes() -> dict[tuple[str, str], list[type]]:
    """The derivation, once per process: it imports every module of the fresh tree."""
    return declared()


def test_every_class_the_tree_declares_resolves_at_exactly_one_domain_name(
    tree_classes: dict[tuple[str, str], list[type]],
) -> None:
    """§1: "one import path per class ... The one path is the domain surface's".

    Three things are reported, each BY NAME:

    * ``no domain module`` -- the domain has no public module at all, so none of its
      classes can be named by a consumer;
    * ``ambiguous`` -- two or more declarations of one domain want one name, so the
      public name can only mean one of them and the surface cannot say which.  This is
      the scope §4's collision rule does not reach: §4 settles a name inside one
      MODULE, and a domain is many modules;
    * ``absent`` -- the domain module exists and does not carry the name.
    """
    claimed("classes the fresh tree declares", tree_classes)

    ambiguous = {
        f"{domain}.{name}": sorted(f"{c.__module__}.{c.__name__}" for c in classes)
        for (domain, name), classes in tree_classes.items()
        if len(classes) > 1
    }
    missing_module: dict[str, str] = {}
    absent: list[str] = []
    for (domain, name), classes in sorted(tree_classes.items()):
        if f"{domain}.{name}" in ambiguous:
            continue
        try:
            module = importlib.import_module(f"adcp.types.{domain}")
        except ImportError as why:
            missing_module[domain] = str(why)
            continue
        if getattr(module, name, None) is None:
            absent.append(f"adcp.types.{domain}.{name} ({classes[0].__module__})")

    assert not missing_module, {
        "domains with no public module": sorted(missing_module),
        "why": missing_module,
    }
    assert not ambiguous, {
        "names two declarations of one domain both want": ambiguous,
    }
    assert not absent, {"classes no domain module names": absent}


def test_the_domain_name_gives_the_same_object_as_the_private_path(
    tree_classes: dict[tuple[str, str], list[type]],
) -> None:
    """§1's other half: the public name is the class, not a second one of that name.

    What this stops is specific and has a precedent in this epic: a surface built by
    DECLARING rather than re-exporting would pass the test above and give a consumer a
    class whose ``isinstance`` is false against every instance the runtime builds, and
    whose ``__adcp_schema__`` would be a second copy to keep in agreement.  ``is`` is
    the whole assertion.
    """
    claimed("classes the fresh tree declares", tree_classes)
    not_the_same: dict[str, str] = {}
    unreachable: list[str] = []
    for (domain, name), classes in sorted(tree_classes.items()):
        if len(classes) > 1:
            continue  # the test above owns the ambiguity; this one owns identity
        (cls,) = classes
        try:
            module = importlib.import_module(f"adcp.types.{domain}")
        except ImportError:
            unreachable.append(f"adcp.types.{domain} (for {name})")
            continue
        public = getattr(module, name, None)
        if public is None:
            unreachable.append(f"adcp.types.{domain}.{name}")
        elif public is not cls:
            not_the_same[f"adcp.types.{domain}.{name}"] = (
                f"{public.__module__}.{public.__name__} is not "
                f"{cls.__module__}.{cls.__name__}"
            )
    assert not unreachable, {"not reachable at a public name": sorted(set(unreachable))}
    assert not not_the_same, {"a second class wearing the public name": not_the_same}


def test_a_caller_can_name_the_branch_a_union_handed_it() -> None:
    """The reason this is a rewrite and not a patch set, as four import lines.

    ``docs/plan/surface-goal.md``: "A class a union can return is reachable and named
    for what it is ... a caller who receives an ``AssetRequirements`` cannot name the
    branch it got.  This is the whole reason for the rewrite".

    ``core/requirements/asset-requirements.json`` is the document that measurement was
    taken on: its module declares the union base and twelve branches and writes
    ``__all__ = ["AssetRequirements"]``.  ``AssetRequirementsJavaScript`` is the branch a
    dispatch hands back; ``JavaScriptAssetRequirements`` is the document it composes,
    which is a class of the same domain and is named here for the same reason -- a caller
    who holds the branch may want to ask about either.
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
