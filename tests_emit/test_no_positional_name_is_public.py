"""THE OWNER'S RULING OF 2026-11-10: a positional name may exist, and may never be public.

``codegen/lower/names.py``'s ``A_POSITIONAL_NAME_IS_PRIVATE`` is the sentence, and it is
quoted here rather than paraphrased so that the rule the compiler states and the rule a
failure reports against are one string.  The condemnation the ruling acts on was already
written twice before anything enforced it:

* ``docs/plan/rebuild-plan.md`` section 4 -- "A positional name is the one outcome a
  consumer cannot work with: a caller writing ``isinstance(req, AssetRequirementsBranch7)``
  has to count the document's branches to know that it means JavaScript."
* ``docs/plan/final-state.md`` reading 4 -- "a name minted for want of a subject must not
  become a name an application depends on", beside "A NAME THIS RULE MINTS IS STILL
  PENDING AN UPSTREAM TITLE".

**AND THE SURFACE CARRIED SIX OF THEM WHILE THE SUITE WAS GREEN**, which is the defect
this file is the missing half of.  ``adcp.types.core.PostalAreaBranch9``,
``adcp.types.core.PostalCountrySystemBranch9``,
``adcp.types.media_buy.BuyProductsRequestBranch1``,
``adcp.types.media_buy.FieldsItemBranch1``,
``adcp.types.content_standards.GetContentStandardsResponseBranch0`` and
``adcp.types.adagents.AdCPAgentsAuthorizationCommunityFormatRegistryBranch0`` were each in
two public ``__all__`` lists -- their domain's and the flat consolidation's -- and no check
in the suite asked the question, while
``tests_emit/test_names_collision.py`` asserted the positional spelling as the EXPECTED
output of the name rule.

**WHAT IS FORBIDDEN IS PUBLISHING ONE, NEVER HAVING ONE.**  The branch is still declared
under ``_schemas/`` and is still a branch of its union: deleting the class would drop a branch
and refuse payloads the document admits, so ``isinstance`` through the union and validation
both still hold.  :func:`test_a_withheld_class_is_still_declared_and_still_validates` is
that half, and it is as much of the ruling as the ban is.

**THE SET IS THE COMPILER'S OWN RECORD AND IS ASSERTED NON-EMPTY FIRST.**
``emit.Emitted.positional`` is written by ``names.the_positional_names`` off the walk's hop
table and the naming pass's symbol table -- not off the emitted text, and not off a regex
over names: a regex for ``Branch\\d+`` was measured at 467 hits over this tree of which 457
were ALIASES onto correctly-titled classes and one was a ``StrEnum`` read as "a class with
no subject".  A gate whose set silently emptied would pass every assertion below
while saying nothing, and a gate founded on today's six names would go vacuous the moment
one of them is renamed; so the first test is that the rule still finds something, and
every other test ranges over whatever it found.
"""

from __future__ import annotations

import ast
import importlib

import fresh
import pytest
from compiled import compiled
from nodeset import claimed

from codegen import emit
from codegen.lower import names

#: One spelling of the bundle, re-exported from ``tests_emit/fresh.py`` for
#: ``test_the_domain_surface.py``'s reason: a file that spells its own path can come to
#: range over a different bundle from the compile it reads.
BUNDLE = fresh.BUNDLE


@pytest.fixture(scope="module")
def run() -> emit.Emitted:
    """One compile, shared: ``tests_emit/compiled.py`` holds it per document set."""
    return compiled(BUNDLE, fresh.population())


@pytest.fixture(scope="module")
def withheld(run: emit.Emitted) -> dict[str, frozenset[str]]:
    """Module -> the positional names the ruling withheld from it, off the run's record."""
    return {module: words for module, words in run.positional.items() if words}


def test_the_rule_still_finds_a_positional_name_to_withhold(
    withheld: dict[str, frozenset[str]],
) -> None:
    """The gate's own non-vacuity, asserted before anything is asserted about the surface.

    Every other test in this file is a statement about the members of this set, so an
    empty set makes all of them pass while grading nothing -- and the two ways it could
    empty are both defects rather than progress: the derivation stops recognising §4's
    last resort (``names.positional_chain`` answering ``None``, or
    ``names.spelled_from`` no longer matching a name the collision rule lengthened), or
    the record stops being written at all.

    **Measured on bundle 3.2: 587 branch positions are named with an index available and
    6 of them are spelled from it**, across 6 modules of 4 domains.  The assertion is
    "at least one", not "exactly six": the count is a property of the BUNDLE, and a bundle
    that titles one of those six branches upstream should move this figure without
    anybody editing a test.
    """
    claimed("the names the ruling withholds", withheld)
    assert withheld, {
        "the positional set is EMPTY": names.A_POSITIONAL_NAME_IS_PRIVATE,
        "so every assertion in this file is vacuous": (
            "names.the_positional_names found nothing to withhold over the whole "
            "set; either the derivation no longer recognises section 4's last "
            "resort or emit stopped recording it"
        ),
    }


def test_no_positional_name_is_in_the_export_set(
    withheld: dict[str, frozenset[str]], run: emit.Emitted
) -> None:
    """The ruling, over EVERY declared name of the emitted tree, on the run's own record.

    ``emit.Emitted.surface`` is §1's export set -- the names ``_surface/<domain>.py``
    imports and lists in ``__all__``, and through the consolidation the names
    ``_surface/_flat.py`` does too -- so this is the ban asked of the one record both
    artifacts are generated from.  Asked per MODULE and not over a union of names, because
    a word is withheld from the module that declares it and §1 lets two domains hold one
    word: a global intersection would read a legitimate word of another domain as a leak.
    """
    leaked = {
        module: sorted(found)
        for module, words in withheld.items()
        if (found := words & frozenset(run.surface.get(module, ())))
    }
    assert not leaked, {
        "a positional name is on the surface": leaked,
        "the rule": names.A_POSITIONAL_NAME_IS_PRIVATE,
    }


def test_no_public_all_carries_a_positional_name(
    withheld: dict[str, frozenset[str]], run: emit.Emitted
) -> None:
    """The same ruling asked of the ARTIFACT: every ``__all__`` the compiler writes.

    The record above is what the surface is generated FROM; this is the text it generated,
    parsed rather than grepped -- ``ast`` over each module the run writes beside the tree,
    reading the literal ``__all__`` assignment ``render.domain_module`` and
    ``render.flat_surface`` emit.  Both halves belong: a record that is right and a writer
    that re-derives a name from somewhere else would pass the test above and ship the
    leak, which is the kind of defect §1's "read one record" rule exists against.

    The scope is every file of ``emit.Emitted.beside`` -- the domain aggregators, the
    flat consolidation and D5's alias module -- so a fifth artifact gaining an ``__all__``
    is covered with no edit here.
    """
    everything = frozenset().union(*withheld.values())
    leaked: dict[str, list[str]] = {}
    for path, text in sorted(run.beside.items()):
        if not path.endswith(".py"):
            continue
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
            ):
                continue
            found = sorted(
                {
                    element.value
                    for element in getattr(node.value, "elts", [])
                    if isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                    and element.value in everything
                }
            )
            if found:
                leaked[path] = found
    assert not leaked, {
        "a public __all__ carries a positional name": leaked,
        "the rule": names.A_POSITIONAL_NAME_IS_PRIVATE,
    }


def test_no_positional_name_resolves_at_a_public_module(
    withheld: dict[str, frozenset[str]],
) -> None:
    """And the ruling asked of the IMPORT a consumer would write.

    ``__all__`` governs ``from adcp.types.<domain> import *`` and what a type checker calls
    a re-export; it does not govern ``from adcp.types.<domain> import <Name>``, which
    resolves against the module's own namespace.  So a surface that dropped the name from
    its list and kept the import statement would pass every test above and still let an
    application depend on the placeholder -- the import is the thing the ruling is about,
    and this is the only test here that asks it.
    """
    assert not fresh.FAILURE, fresh.FAILURE
    reachable: dict[str, list[str]] = {}
    for module, words in sorted(withheld.items()):
        domain = emit.module_domain(module)
        public = importlib.import_module(f"adcp.types.{domain}")
        # ACCUMULATED and never assigned: a domain is many modules, so two modules each
        # leaking one word onto one domain would report as the second module's word alone.
        for word in sorted(word for word in words if hasattr(public, word)):
            reachable.setdefault(f"adcp.types.{domain}", []).append(word)
    assert not reachable, {
        "a positional name resolves at a public import": reachable,
        "the rule": names.A_POSITIONAL_NAME_IS_PRIVATE,
    }


def test_a_withheld_class_is_still_declared_and_still_validates(
    withheld: dict[str, frozenset[str]],
) -> None:
    """The other half of the ruling, which is as much of it as the ban is.

    "Do not delete the branch's class -- that would drop a branch from the union and refuse payloads
    the document admits."  So every withheld name is still a declaration of its private
    module, and the union whose branch it is still lists it: an instance of the branch is
    still an instance of the union, which is what makes a consumer's ``isinstance`` over
    the dispatch true and the validation of a payload the document admits possible.

    The private path is ``_schemas`` and is reached by name here deliberately: P8 makes it
    private to an APPLICATION, and this is the compiler's own suite asserting that the
    object the ruling withheld a public name from still exists.
    """
    missing: dict[str, str] = {}
    not_a_branch: dict[str, str] = {}
    for module, words in sorted(withheld.items()):
        private = importlib.import_module(f"adcp.types._schemas.{module.replace('/', '.')}")
        for word in sorted(words):
            held = getattr(private, word, None)
            if held is None:
                missing[f"{module}.{word}"] = "the class the ruling withheld a name from is gone"
                continue
            # The union's branches, as the runtime holds them: a branch class subclasses its
            # union base, and the base lists its branches for the dispatch.  Both directions
            # are asserted because the ban could break either -- a class dropped from the
            # branch list still imports, and a class that is no longer a subclass still
            # appears in the list.
            bases = [
                base
                for base in held.__mro__[1:]
                if getattr(base, "_branch_models", None) is not None
            ]
            if bases and not any(held in (base._branch_models or ()) for base in bases):
                not_a_branch[f"{module}.{word}"] = (
                    f"is not among the branches of {bases[0].__name__}, so a payload the "
                    "document admits would be refused"
                )
    assert not missing, {"a withheld class was deleted": missing}
    assert not not_a_branch, {"a withheld class lost its place among the union's branches": not_a_branch}
