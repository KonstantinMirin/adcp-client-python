"""Resolving ONE public name imports ONE module, and it is the same object as before.

**THE DEFECT THIS GRADES WAS AN ADOPTER'S FIRST CLASS** (``adcp-client-python-690v``, the
owner's ruling of 2026-11-19).  Measured at ``8b1d8ceee``::

    python -c "pass"                                0.02 s    11.5 MB
    python -c "import adcp"                         0.02 s    13.1 MB   the facade works
    python -c "import adcp; adcp.Product"           4.43 s     145 MB   the first word

``adcp.types.__getattr__`` consulted ``adcp.types.compat`` first, and that module is a flat
namespace over everything -- 1,700 re-exports, so importing it imports all 23 domain
aggregators and through them the 1,051 modules of ``_schemas``.  **Resolving one name
required every module to exist first.**  The fix is the ruling that fixed ``__all__`` one
level up -- *generate, don't derive* -- applied to the lookup: ``codegen/facade.py`` writes
the name -> owning-module table, and the facade reads it.

Three things are asserted here, and the middle one is the only one that matters if they
ever disagree:

1. **the table is this build's**, not a previous one's: ``codegen.facade.owners`` is the
   derivation and the literal is its answer, so they are compared whole.  The same compare
   ``codegen/facade.py`` says is owed for ``__all__`` is here too, beside it.
2. **every routed word resolves to the SAME OBJECT the chain resolves.**  A word that
   starts naming a different class is the worst available outcome
   (``docs/plan/rebuild-plan.md`` §4), and a faster route to the wrong object would look
   like a win in every other measurement.  ``6b690ec84`` is the precedent: ``Policy``
   resolved to the OpenAPI subject instead of the schema one and only a test caught it.
3. **the work count**, in a fresh interpreter, because that is the thing being bought: the
   cold path for one word must not import the flat layers at all.

**THE SUBPROCESSES CARRY ``PYTHONPATH`` ON PURPOSE, and it is a measurement defect to
leave it out.**  The shared ``.venv`` is symlinked across this project's worktrees and its
editable ``.pth`` names ONE of them, so a child spawned with a bare
``[sys.executable, "-c", ...]`` resolves ``adcp`` through whatever checkout installed it
last -- and ``python -I`` ignores ``PYTHONPATH`` entirely, so it can only ever grade that
one.  ``pyproject.toml``'s ``pythonpath = [".", "src"]`` fixes the PARENT and says so in its
own comment; it does not reach a child.  A cold-path probe that grades another lane's tree
measures nothing about this one.
"""

from __future__ import annotations

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

import adcp.types

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

#: How many modules a fresh interpreter may hold after resolving one word.  The flat
#: namespace brought 1,437 (every module of the tree plus pydantic and the stdlib); one
#: document module and its annotations' closure is 547 for ``Product``, 291 for a leaf
#: enumeration.  The budget sits above the heaviest word measured and far below the
#: namespace, so the regression this file exists for -- a consult that pulls the world back
#: in -- fails here rather than in an adopter's first second.
COLD_MODULE_BUDGET = 900

#: The layers that ARE the whole surface: each imports every domain aggregator, so one of
#: them in a cold interpreter means the table was not consulted or did not answer.
FLAT_LAYERS = (
    "adcp.types.compat",
    "adcp.types.legacy_names",
    "adcp.types._adapter",
    "adcp.types._surface._flat",
)

#: One word per kind of row the table carries, so a kind that stops being routed is named
#: rather than averaged away:
#:   Product                   a class at its own document module
#:   TaskStatus                an enumeration, the cheapest kind of word there is
#:   A2UiBoundValue            upstream's spelling, which the owning module spells its own way
#:   accept_proposal_request   a word that names a MODULE of ours
#:   PaginationRequest         the flat spelling of a word a domain path already carries
COLD_WORDS = (
    "Product",
    "TaskStatus",
    "A2UiBoundValue",
    "accept_proposal_request",
    "PaginationRequest",
)

_PROBE = """
import sys
import adcp
value = getattr(adcp.types, {word!r})
print(len(sys.modules))
print([m for m in {layers!r} if m in sys.modules])
print(getattr(value, "__module__", None), getattr(value, "__name__", None))
"""


def _cold(word: str) -> tuple[int, list[str], str]:
    """Resolve ``word`` in a fresh interpreter against THIS checkout; report what it cost."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(SRC), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    result = subprocess.run(
        [sys.executable, "-c", _PROBE.format(word=word, layers=FLAT_LAYERS)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=300,
    )
    assert (
        result.returncode == 0
    ), f"resolving {word} in a fresh interpreter failed:\n{result.stderr}"
    count, layers, subject = result.stdout.strip().splitlines()[-3:]
    return int(count), list(ast.literal_eval(layers)), subject


def test_the_committed_table_is_what_a_fresh_derivation_says() -> None:
    """The literal in the facade is ``codegen.facade.owners()``'s answer, whole.

    The derivation is stated in one place and the answer in another, which is what
    "generate, don't derive" buys -- and the only thing that could make the two disagree is
    a tree whose compiler has not been re-run since a layer changed.  A stale row is not an
    outage (``__getattr__`` falls back to the chain) and that is exactly why it needs a
    test: nothing else would ever say so.
    """
    facade = pytest.importorskip("codegen.facade", reason="the generator is not on the path")
    table = facade.owners()
    assert adcp.types._OWNED == table.owned
    assert adcp.types._SPELLED == table.spelled
    assert adcp.types._NAMES_A_MODULE == table.names_a_module
    assert sorted(set(adcp.types.__all__)) == facade.words()


def test_every_routed_word_resolves_to_the_object_the_chain_resolves() -> None:
    """One ``import_module`` plus one ``getattr`` IS what the nine consults would return.

    Asked of ``_searched`` and not of ``adcp.types`` itself: the package's own
    ``__getattr__`` reads the table FIRST, so a comparison against it would compare the
    table with itself and pass on any row at all.
    """
    wrong: list[str] = []
    for word, owner in sorted(adcp.types._WHERE.items()):
        routed = getattr(importlib.import_module(owner), adcp.types._SPELLED.get(word, word))
        if routed is not adcp.types._searched(word):
            wrong.append(f"{word} -> {owner}")
    for word, owner in sorted(adcp.types._NAMES_A_MODULE.items()):
        if importlib.import_module(owner) is not adcp.types._searched(word):
            wrong.append(f"{word} -> {owner} (a module)")
    assert not wrong, (
        f"{len(wrong)} of the {len(adcp.types._WHERE) + len(adcp.types._NAMES_A_MODULE)} routed "
        f"words reach an object the lookup chain does not: {wrong[:10]}"
    )


def test_every_advertised_word_is_routed() -> None:
    """``__all__`` and the table are the same surface, so neither may be short of the other.

    A word in ``__all__`` with no row still resolves -- the chain is the fallback -- and
    pays the 4.4 s this file is about, which is the whole reason the shortfall has to be
    visible.  ``codegen.facade.owners`` REFUSES a word whose owning module cannot be
    decided and reports it, so a failure here is that refusal arriving: read the run's
    ``unrouted`` lines for the reason, and the answer is a decision about that word's
    subject rather than a row invented for it.
    """
    routed = set(adcp.types._WHERE) | set(adcp.types._NAMES_A_MODULE)
    assert not set(adcp.types.__all__) - routed


@pytest.mark.parametrize("word", COLD_WORDS)
def test_resolving_one_word_imports_one_module(word: str) -> None:
    """A fresh interpreter resolving ``word`` imports its module and not the namespace."""
    count, layers, subject = _cold(word)
    assert not layers, (
        f"resolving {word} in a fresh interpreter imported {layers}, each of which is a flat "
        f"namespace over the whole surface -- the table either did not carry the word or did "
        f"not answer for it"
    )
    assert count < COLD_MODULE_BUDGET, (
        f"resolving {word} left {count} modules in sys.modules, over the "
        f"{COLD_MODULE_BUDGET} budget; the flat namespace was 1,437 and one document module "
        f"is 547 ({subject})"
    )
