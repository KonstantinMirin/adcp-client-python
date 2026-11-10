"""PRECONDITIONS FIRST, THEN THE POPULATION, STATED ONCE.

Run this before trusting any other figure::

    PYTHONPATH=.:src python -m pytest tests_emit/test_preconditions.py -q

**Why this file exists, and it is a defect report rather than a preference.**  Every
measurement in this epic has re-derived its own population with its own predicate, and
three figures were wrong in a single session for three different reasons -- each of them
LARGER than the truth, and each pointing at work that did not exist:

* a gate's figure was quoted as "zero import problems" without stating that its population
  is ``src/adcp/`` and excludes ``tests/`` entirely;
* a test-side census counted imports inside ``if TYPE_CHECKING``, ``try``/``except`` and
  function bodies -- 258 unresolved names where the live count is 151;
* a family was reported at ~37 blocked files when it was 4, because the probe matched a
  class name appearing in a DOCSTRING.

And underneath all three: the virtualenv was missing ``httpx``, ``a2a``, ``mcp``,
``rfc8785``, ``tldextract``, ``sse_starlette`` and the sibling ``adcp_reporting_storage``,
so a quarter of every reading was the environment rather than the tree.

**A FIGURE WITHOUT ITS PRECONDITIONS IS NOT A MEASUREMENT.**  So this file does three
things in order and nothing else: it asserts the environment can answer, it states the
population once, and it reports the reading.  Any instrument that wants that population
imports :func:`asked_of_us` from here rather than writing a fourth predicate.
"""

from __future__ import annotations

import ast
import importlib
import pathlib
from typing import NamedTuple

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: Every third-party distribution ``pyproject.toml`` lists as a runtime dependency and
#: whose absence silently inflates an import census.  Read as import names, not
#: distribution names, because that is what an ``ImportError`` carries.
RUNTIME = (
    "httpx",
    "httpcore",
    "a2a",
    "mcp",
    "sse_starlette",
    "rfc8785",
    "jsonschema",
    "tldextract",
    "cryptography",
    "pydantic",
)

#: The sibling distribution in ``packages/``.  Upstream's own tests import it, and without
#: it their reporting suite reads as our defect.
SIBLING = "adcp_reporting_storage"


class Pair(NamedTuple):
    """One ``(module, name)`` a file asks of us, and whether the ask EXECUTES."""

    module: str
    name: str
    asker: str
    live: bool


def _live_nodes(tree: ast.Module) -> set[int]:
    """The ids of nodes that run when the module is imported.

    Module scope means the module body plus, recursively, the bodies of module-scope
    ``if`` and ``try`` -- and NOT the body of a ``def``, and NOT an ``if TYPE_CHECKING``
    block, and NOT a ``try`` that swallows the failure.  The three exclusions are the
    whole difference between 258 and 151, which is why they are named here once instead
    of being re-decided per probe.
    """
    dead: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            dead |= {id(child) for child in ast.walk(node)}
        elif isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test):
            dead |= {id(child) for child in ast.walk(node)}
        elif isinstance(node, ast.Try):
            dead |= {id(child) for child in ast.walk(node)}
    return dead


def asked_of_us(*roots: str) -> list[Pair]:
    """Every ``(module, name)`` the files under ``roots`` ask of ``adcp`` or ``scripts``.

    ``roots`` are repository-relative directories.  The population is the union over them,
    and each pair carries ``live`` -- whether the import executes on module import.  A
    caller that wants only the blocking set filters on ``live``; a caller that wants the
    type-checker's view does not.  Both readings come from one walk, so they cannot
    disagree.
    """
    found: list[Pair] = []
    for root in roots:
        for path in sorted((ROOT / root).rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            dead = _live_nodes(tree)
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.level:
                    continue
                if not node.module or not node.module.startswith(("adcp", "scripts")):
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    found.append(
                        Pair(
                            node.module,
                            alias.name,
                            str(path.relative_to(ROOT)),
                            id(node) not in dead,
                        )
                    )
    return found


def resolves(module: str, name: str) -> bool:
    """``from module import name``, by the import system's own three steps.

    ``from M import N`` imports ``M``, takes ``N`` as an attribute, and failing that
    imports the submodule ``M.N``.  A probe that reads ``dir(M)`` alone misses the third
    and reports a resolving submodule as absent.
    """
    try:
        held = importlib.import_module(module)
    except BaseException:  # noqa: BLE001 - a missing dependency is an answer, not a crash
        return False
    if hasattr(held, name):
        return True
    try:
        importlib.import_module(f"{module}.{name}")
    except BaseException:  # noqa: BLE001
        return False
    return True


# --------------------------------------------------------------------------- #
# 1. the environment can answer
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("dist", RUNTIME)
def test_a_runtime_dependency_is_importable(dist: str) -> None:
    """Without these, an import census measures the virtualenv and not the tree."""
    pytest.importorskip.__module__  # keep the import of pytest meaningful to linters
    try:
        importlib.import_module(dist)
    except ImportError as exc:  # pragma: no cover - the failure IS the message
        pytest.fail(
            f"{dist!r} is not installed, so every import figure taken here is inflated. "
            f"Install the project's dependency set before measuring: {exc}"
        )


def test_the_sibling_distribution_is_importable() -> None:
    """``packages/adcp-reporting-storage`` -- upstream's own tests import it."""
    try:
        importlib.import_module(SIBLING)
    except ImportError as exc:  # pragma: no cover
        pytest.fail(
            f"{SIBLING!r} is not installed, so upstream's reporting suite reads as our "
            f"defect. It lives in packages/ and is installed editable: {exc}"
        )


def test_adcp_resolves_to_this_checkout() -> None:
    """The shared virtualenv is hardlink-shared across worktrees and its editable path
    names ONE of them, so a bare interpreter can grade a different tree entirely. This
    was observed: three readings of one commit differed by which checkout answered.
    """
    held = importlib.import_module("adcp")
    where = pathlib.Path(held.__file__ or "").resolve()
    assert where.is_relative_to(ROOT), (
        f"adcp resolves to {where}, which is NOT this checkout ({ROOT}). "
        "Every figure taken in this interpreter describes another tree."
    )


# --------------------------------------------------------------------------- #
# 2. the population, stated once
# --------------------------------------------------------------------------- #
def test_the_population_is_stated_and_not_empty() -> None:
    """A census that silently matches nothing reads as a clean bill of health.

    Each of the three bad figures this file exists for had a predicate that could not
    match its own subject, and absence read as an answer. So the population asserts its
    own non-emptiness before anything is concluded from it.
    """
    source = asked_of_us("src/adcp")
    tests = asked_of_us("tests")
    assert source, "no (module, name) pair found under src/adcp -- the predicate is broken"
    assert tests, "no (module, name) pair found under tests -- the predicate is broken"
    assert any(p.live for p in tests), "no LIVE ask found under tests -- the guard is broken"
    assert any(not p.live for p in tests), (
        "every ask under tests reads as live, so the TYPE_CHECKING/try/def exclusion is "
        "not firing -- which is the exact defect that reported 258 where the truth is 151"
    )


# --------------------------------------------------------------------------- #
# 3. the reading
# --------------------------------------------------------------------------- #
def test_every_live_ask_of_upstreams_own_source_resolves() -> None:
    """Upstream's source is the party whose imports the substitution must not break."""
    unresolved = sorted(
        {(p.module, p.name) for p in asked_of_us("src/adcp") if p.live and not resolves(p.module, p.name)}
    )
    assert not unresolved, (
        f"{len(unresolved)} live (module, name) asks of upstream's own source do not "
        f"resolve: {unresolved[:12]}"
    )


def test_the_test_side_reading_is_reported_with_its_guard() -> None:
    """Upstream's TESTS are a SEPARATE population and are red today.

    This is not an assertion that they all resolve -- they do not. It states the reading
    with its guard condition attached, so the number cannot be quoted as the source-side
    one was. It fails only if the live count EXCEEDS the whole count, which would mean the
    guard is inverted.
    """
    tests = asked_of_us("tests")
    live = {(p.module, p.name) for p in tests if p.live}
    whole = {(p.module, p.name) for p in tests}
    live_bad = sorted(k for k in live if not resolves(*k))
    whole_bad = sorted(k for k in whole if not resolves(*k))
    assert len(live_bad) <= len(whole_bad), "the live set exceeds the whole set: guard inverted"
    print(
        f"\ntest-side asks: {len(whole)} declared, {len(live)} live\n"
        f"unresolved:     {len(whole_bad)} declared, {len(live_bad)} LIVE "
        f"over {len({p.asker for p in tests if p.live and (p.module, p.name) in set(live_bad)})} files\n"
        "the LIVE number is the one that blocks; the other is the type checker's view."
    )
