"""Every public word this package advertises or imports must RESOLVE, or be DECLARED.

**`./check` reported `emitted 1059 / refused 0` while `import adcp.client` raised
`ImportError`.** The emitter was right about every one of its 1,059 classes and the package
it describes could not be imported, because `adcp.types.Format` was bound to nothing: the
`LegacyFormat` override landed its rename and the alias half -- `Format` ->
`ProductFormatDeclaration`, which `codegen/overrides.py`'s own docstring states -- did not.
Nine of our own modules import that word at module scope, so `adcp.server`,
`adcp.decisioning`, `adcp.canonical_formats` and `adcp.client` all stopped importing, 246 of
our own test files stopped collecting, and the drop-in run read 5,190 of 15,286 tests with
one chunk writing no report at all.

**No number was showing it.** That is what this file is for. It is course item (1) --
*the class agrees with its document* -- at its most basic: a public word with nothing behind
it is an outage, and an outage is not a count of anything.

**THE RULE HAS TWO HALVES, AND THE SECOND IS WHY THIS IS NOT A BLANKET RESOLVE CHECK.**
This project refuses names on purpose: a word upstream publishes that has no subject in the
pinned bundle gets a migration note and never a class, and the refusal is served as an
`AttributeError` *carrying its reason*. So:

* a word that resolves is fine;
* a word refused with a **DECLARED** reason is fine -- it is a decision, and
  `docs/plan/rebuild-plan.md` §2 is explicit that where a check reports a decision as a
  failure the defect is the missing declaration and never the decision;
* a word that is bound to nothing and declared nowhere is a **DEFECT**.

The declaration is `__adcp_refused__`, a module-level mapping of name to reason that
`adcp.types._adapter` and `adcp.types.legacy` already carry. This file reads it off the
module rather than restating any part of it, so a newly refused word needs no edit here --
only its reason.

**AND IT MUST RUN WHILE THE PACKAGE IS BROKEN, which decides how it reads the demand.**
`tests/test_import_layering.py` could not run during this outage: it imports the modules it
grades, so the ImportError took the grader with the graded. The demand side here is read by
**AST** -- the import statements as written, never executed -- and the only things imported
are `adcp` (a lazy facade, which survives) and `adcp.types` and its submodules (which
survive). A gate that goes down with the thing it watches is not a gate.

No allowlist and no ratchet: the two sets are derived, one from the source and one from the
package, and a word is in exactly one of three states.
"""

from __future__ import annotations

import ast
import importlib
import pathlib

import pytest

#: The package's own source, read as text.  `src/adcp/**` and nothing else: this grades the
#: words OUR code depends on, and a test's or an example's import is not a shipping promise.
SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "adcp"

#: The one name this file may not resolve through, because it is the subject under test:
#: a module that fails to import cannot answer for its own words.
_TYPES = "adcp.types"


def _demanded() -> dict[tuple[str, str], list[str]]:
    """``(module, name) -> import sites``, by AST over the package's own source.

    Reads `from adcp.types… import X` statements as WRITTEN.  Nothing here is executed, so
    the sweep is unaffected by whether the importing module can be imported -- which is the
    case this file exists for.
    """
    demanded: dict[tuple[str, str], list[str]] = {}
    for path in sorted(SOURCE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            parsed = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as e:  # pragma: no cover - a syntax error is its own failure
            pytest.fail(f"{path} does not parse: {e}")
        for node in ast.walk(parsed):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = node.module or ""
            if module != _TYPES and not module.startswith(_TYPES + "."):
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                site = f"{path.relative_to(SOURCE.parents[1])}:{node.lineno}"
                demanded.setdefault((module, alias.name), []).append(site)
    return demanded


def _declarations() -> dict[str, str]:
    """Every refusal the types package declares, as ``name -> "<module>: <reason>"``.

    **THE DECLARATION DOES NOT HAVE TO BE ON THE MODULE THE IMPORT NAMES, and reading only
    that module is how a decision gets reported as a defect.**  Measured while writing this:
    `from adcp.types import AcceptedLoss` raises on the FACADE, whose own message is a
    pointer to the migration note, while the reason -- ``DOCUMENT-NO-WORD-NO-IDENTITY:
    upstream declares it at …`` -- sits in `adcp.types._adapter.__adcp_refused__`, one module
    along.  Consulting only the facade reported eleven declared decisions as outages, which
    is exactly what `docs/plan/rebuild-plan.md` §2 was written about: 1,239 of 1,907
    not-passing pairs were decisions nobody could find.

    So the declared set is the union over the package, and a word declared ANYWHERE in it is
    a decision.  Collected by walking `adcp.types`' own modules; a module that does not
    import contributes nothing and is not an error here -- this file does not grade imports,
    it grades words.
    """
    import pkgutil

    types_package = importlib.import_module(_TYPES)
    declared: dict[str, str] = {}
    candidates = [types_package]
    for found in pkgutil.iter_modules(types_package.__path__):
        try:
            candidates.append(importlib.import_module(f"{_TYPES}.{found.name}"))
        except Exception:  # noqa: S112 - an unimportable module declares nothing
            continue
    for module in candidates:
        refused = getattr(module, "__adcp_refused__", None)
        if not isinstance(refused, dict):
            continue
        for name, reason in refused.items():
            if isinstance(name, str) and isinstance(reason, str) and reason.strip():
                declared.setdefault(name, f"{module.__name__}: {reason}")
    return declared


_DECLARED: dict[str, str] = {}


def _declared_refusal(module: object, name: str) -> str | None:
    """The reason the package declares for refusing ``name``, or ``None`` if it declares none."""
    if not _DECLARED:
        _DECLARED.update(_declarations())
    own = getattr(module, "__adcp_refused__", None)
    if isinstance(own, dict) and isinstance(own.get(name), str) and own[name].strip():
        return own[name]
    return _DECLARED.get(name)


def _state(module_name: str, name: str) -> tuple[str, str]:
    """``("resolves" | "declared" | "undeclared" | "module", detail)`` for one word."""
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        return "module", f"{module_name} does not import: {type(e).__name__}: {e}"
    try:
        getattr(module, name)
    except AttributeError as e:
        reason = _declared_refusal(module, name)
        if reason is not None:
            return "declared", reason
        return "undeclared", str(e).splitlines()[0]
    except Exception as e:
        # An ImportError here is a CASCADE: the word's own definition reaches a module that
        # does not import.  Still an outage, and named as one rather than as a missing word.
        return "undeclared", f"{type(e).__name__}: {str(e).splitlines()[0]}"
    return "resolves", ""


def test_every_word_our_source_imports_from_adcp_types_resolves_or_is_declared() -> None:
    """The demand side: what `src/adcp/**` asks of the type surface at module scope."""
    demanded = _demanded()
    assert demanded, "the sweep found no imports from adcp.types -- the reader is broken"

    broken: list[str] = []
    for (module_name, name), sites in sorted(demanded.items()):
        state, detail = _state(module_name, name)
        if state in ("resolves", "declared"):
            continue
        broken.append(
            f"  {module_name}.{name}\n      {detail}\n"
            f"      imported at: {', '.join(sites)}"
        )

    assert not broken, (
        f"{len(broken)} of {len(demanded)} words this package imports from the type surface "
        f"are bound to nothing and declared nowhere.\n\n"
        + "\n".join(broken)
        + "\n\nEach is either a word that should resolve -- bind it -- or a refusal taken on "
        "purpose, which belongs in that module's `__adcp_refused__` with the verdict that "
        "classifies it. An undeclared unbound word is an outage: every module importing it "
        "at module scope stops importing, and `./check` stays green while it does."
    )


def test_every_word_the_package_advertises_resolves_or_is_declared() -> None:
    """The supply side: `adcp.__all__` is a promise, and 92 of its words once did not keep it.

    Separate from the test above because the two fail independently: a word can be advertised
    and unbound without our own source importing it, and that is just as broken for a
    consumer who reads `__all__` or relies on tab completion.
    """
    package = importlib.import_module("adcp")
    advertised = getattr(package, "__all__", None)
    assert advertised, "adcp.__all__ is empty or absent -- there is nothing to grade"

    broken: list[str] = []
    for name in sorted(advertised):
        try:
            getattr(package, name)
        except AttributeError as e:
            if _declared_refusal(package, name) is None:
                broken.append(f"  adcp.{name}\n      AttributeError: {str(e).splitlines()[0]}")
        except Exception as e:
            broken.append(f"  adcp.{name}\n      {type(e).__name__}: {str(e).splitlines()[0]}")

    assert not broken, (
        f"{len(broken)} of {len(advertised)} words in `adcp.__all__` do not resolve.\n\n"
        + "\n".join(broken)
        + "\n\n`__all__` is the package's own statement of its public surface, so a word in "
        "it that raises is a promise the package does not keep. An `ImportError` here is a "
        "CASCADE -- the word is fine and something it reaches is not -- so fix the cascade's "
        "root and these clear together."
    )


def test_the_refusal_table_and_the_public_surface_agree() -> None:
    """A word is REFUSED or it is BOUND. Both, or neither, and the surface lies either way.

    **Measured on trunk: 54 of `adcp.__all__`'s 748 words are declared refused, and they
    split 27/27 into two OPPOSITE contradictions.** Reading the counts together is the whole
    point -- each group alone looks like the other's fix.

    **(A) 27 are advertised, declared refused, and raise.** The refusal is the decision and
    it stands; `__all__` listing the word anyway is the defect. It costs a consumer
    `from adcp import *`, `dir(adcp)` and tab completion, and leaves a reader of `__all__` no
    way to tell these from the other 721. Removing them costs nothing an error message needs:
    `__getattr__` still answers by name with the declared reason, so the migration note still
    reaches whoever asks.

    **(B) 27 are declared refused and RESOLVE ANYWAY.** This is the worse direction, because
    the refusal tables exist precisely so that a word with no subject fails *"rather than
    resolving to something that silently is not what the caller asked for"* -- their own
    words. Here the binding landed and the row did not move. `Format` is the clearest case:
    it now resolves to `ProductFormatDeclaration`, which is correct and is what the decision
    index states, while `_adapter.__adcp_refused__["Format"]` still reads *"NO-DOCUMENT-NO-
    SUBJECT: upstream declares it at `adcp.types.canonical_creative.Format`"* -- a module this
    repository withdrew. `UpdateMediaBuySuccessResponse`, `CreateMediaBuySuccessResponse` and
    seven more carry the same stale citation.

    Both groups are the same artifact disagreeing with itself: `_adapter.py` is GENERATED by
    `survey/adapter_surface.py`, so neither is fixed by editing it. (A) is a reviewed surface
    change -- take the words out of `__all__` and regenerate
    `tests/fixtures/public_api_snapshot.json`, because a public name leaving the surface is a
    fact about every consumer who imports it. (B) is a re-derivation of the census against the
    tree as it is, which `test_every_declared_refusal_cites_a_location_that_exists` below is
    the narrower, earlier signal for.
    """
    package = importlib.import_module("adcp")
    advertised = getattr(package, "__all__", None)
    assert advertised, "adcp.__all__ is empty or absent -- there is nothing to grade"

    if not _DECLARED:
        _DECLARED.update(_declarations())

    raises: list[str] = []
    resolves: list[str] = []
    for name in sorted(set(advertised) & set(_DECLARED)):
        try:
            bound = getattr(package, name)
        except Exception:
            raises.append(f"  {name}\n      {_DECLARED[name]}")
            continue
        owner = getattr(bound, "__module__", "?")
        word = getattr(bound, "__name__", type(bound).__name__)
        where = f"{owner}.{word}"
        resolves.append(f"  {name}\n      bound to {where}\n      yet {_DECLARED[name]}")

    assert not (raises or resolves), (
        f"the refusal table and the public surface disagree about "
        f"{len(raises) + len(resolves)} of {len(advertised)} advertised words.\n\n"
        f"(A) {len(raises)} are ADVERTISED AND REFUSED -- take them out of `__all__`:\n"
        + "\n".join(raises)
        + f"\n\n(B) {len(resolves)} are REFUSED AND BOUND -- the row is stale, re-derive the "
        f"census:\n"
        + "\n".join(resolves)
        + "\n\nA word is refused or it is bound. `_adapter.py` is generated by "
        "survey/adapter_surface.py, so neither group is fixed by editing it."
    )


def test_every_declared_refusal_cites_a_location_that_exists() -> None:
    """A DECLARATION MUST BE FOLLOWABLE, or it is not a decision -- it is a stale reading.

    **THIS IS THE CHECK THAT WOULD HAVE CAUGHT THE `Format` OUTAGE, and the two tests above
    would not.** They treat a declared refusal as a decision, which is right; but a refusal
    whose own reason cites a module that does not exist here states nothing checkable, and
    the word is unbound all the same.

    `adcp.types._adapter.__adcp_refused__["Format"]` reads *"NO-DOCUMENT-NO-SUBJECT: upstream
    declares it at `adcp.types.canonical_creative.Format`"*. This repository WITHDREW
    `canonical_creative` (`adcp-client-python-2f52`), so the statement the classification
    followed terminates nowhere -- and "we cannot follow upstream's statement" was recorded as
    "the name has no subject". It does have one: `core/product-format-declaration.json#`, which
    `ProductFormatDeclaration` is bound to, and which the decision index names as `Format`'s
    subject. A stale refusal and a live decision contradicted each other and the stale one won.

    `verdicts/facade-recursion.md` §5 predicted this exactly, about a different word of the
    same nine: *"A statement naming a module that does not exist here cannot be followed …
    it is a ruling about which reading wins when upstream's statement is unfollowable."*
    `UpdateMediaBuySuccessResponse` is in that set, and §5 measured its refusal at 132
    uncollectable files.

    The check is cheap because the reasons already carry their citation: `declares it at
    <dotted path>`. If the module imports, the declaration is followable, whatever it then
    concludes. If it does not, the declaration is about a tree this repository no longer has.
    """
    import pkgutil
    import re

    types_package = importlib.import_module(_TYPES)
    modules = [types_package]
    for found in pkgutil.iter_modules(types_package.__path__):
        try:
            modules.append(importlib.import_module(f"{_TYPES}.{found.name}"))
        except Exception:  # noqa: S112 - an unimportable module declares nothing
            continue

    unfollowable: list[str] = []
    cited = 0
    for module in modules:
        refused = getattr(module, "__adcp_refused__", None)
        if not isinstance(refused, dict):
            continue
        for name, reason in sorted(refused.items()):
            for location in re.findall(r"declares it at ([\w.]+)", reason or ""):
                cited += 1
                owner = location.rsplit(".", 1)[0]
                try:
                    importlib.import_module(owner)
                except Exception as e:
                    unfollowable.append(
                        f"  {module.__name__}.__adcp_refused__[{name!r}]\n"
                        f"      cites {location}\n"
                        f"      and {owner} does not import: {type(e).__name__}"
                    )

    assert cited, "no refusal reason carries a 'declares it at' citation -- the reader is broken"
    assert not unfollowable, (
        f"{len(unfollowable)} of {cited} declared refusals cite a location this repository "
        f"does not have, so each states a reading of a tree that is gone.\n\n"
        + "\n".join(unfollowable)
        + "\n\nA withdrawal is a decision of ours and the census has to say so: 'upstream's "
        "statement cannot be followed' is a different verdict from 'the name has no subject', "
        "and recording the second for the first is how a word with a live document ends up "
        "bound to nothing. Re-derive the census against the tree as it is."
    )


# **RUNNABLE WITHOUT PYTEST, BECAUSE THE CONFTEST GOES DOWN WITH THE PACKAGE.**  Measured
# while writing this: `pytest tests/test_public_words_resolve.py` could not COLLECT, because
# `tests/conftest.py` imports `adcp.server.mcp_tools` and the cascade took the grader with
# the graded -- the same way it took `tests/test_import_layering.py`.  `--noconftest` runs it,
# and so does this, so the gate is readable during exactly the outage it is for:
#
#     PYTHONPATH=.:src python tests/test_public_words_resolve.py
#
# Exit status is the gate: 0 when every word resolves or is declared, 1 otherwise.
if __name__ == "__main__":
    import sys

    failures = 0
    for check in (
        test_every_word_our_source_imports_from_adcp_types_resolves_or_is_declared,
        test_every_word_the_package_advertises_resolves_or_is_declared,
        test_every_declared_refusal_cites_a_location_that_exists,
        test_the_refusal_table_and_the_public_surface_agree,
    ):
        try:
            check()
            print(f"PASS  {check.__name__}")
        except AssertionError as problem:
            failures += 1
            print(f"FAIL  {check.__name__}\n{problem}\n")
    sys.exit(1 if failures else 0)
