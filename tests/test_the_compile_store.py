"""The two properties of the compile store that are not about any compile's ANSWER.

``tests/compiled.py`` argues its own correctness: the key covers the compiler's source, a
write is atomic, and "every failure path falls through to compiling ... the worst it can
do is cost 280 s".  Both checks here are about what that argument does NOT cover -- how
many copies of one answer the store holds, and for how long -- so neither of them grades a
compile and neither can move a verdict.

**1. ONE BUNDLE IS HELD UNDER ONE KEY.**  ``adcp-client-python-q3a`` measured two.  The
key carried the bundle path AS THE CALLER SPELLED IT, and the two entry points spell it
differently -- ``./check`` says ``Path("schemas/cache/3.2")`` and every module under
``tests/`` says ``REPO / "schemas" / "cache" / "3.2"`` -- so at trunk ``3f757728`` the same
bundle, the same 1,054 documents and the same compiler gave ``fc2222b39088cb00...`` and
``b7e473ca16f94ddc...``: two keys, two 842 MB pickles, and the one of them the store
actually held was the fast loop's.  A lane that warmed the store with ``./check`` had not
warmed the entry the gate reads, which is a reading of the loop ``./check`` exists to BE,
so the claim is graded at the entry points' own values and not at a copy of their literals.

**2. AN ENTRY NOTHING HAS ASKED FOR IS DROPPED, AND BY THE RUN THAT ASKS.**  The store had
no prune at all: 103 entries of 842,068,270 bytes each, 55 GB, on a root filesystem at 96%
with 81 GB free, of which 98 had been neither written nor read in eight hours -- compiler
revisions that no longer exist, and they were pruned by hand to get the disk back.  A
retention rule that needs a human to run it is the defect and not the fix, so the second
check is that ASKING FOR A COMPILE prunes: a child process whose only unusual input is
``ADCP_CACHE`` asks for one document, and the entry nothing had asked for is gone when it
returns.

The rule itself is stated where it lives (``compiled.KEPT_SECONDS``) and is graded here at
both ends -- in isolation, over a store planted by hand, and wired, over a real ask.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import compiled
import fresh
from nodeset import claimed

from codegen import bundle

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: One portable document, because what the wiring check grades is the STORE and not a
#: compile: a whole-population entry is 842,068,270 bytes and 97 s, and this one is 7,381
#: bytes and 0.53 s.  Named rather than counted, so a reader of a red mark knows what the
#: child asked for, and it is a document that EMITS, which is why the child's own return
#: code is readable as "the ask succeeded".
A_CHEAP_POPULATION = ("core/pagination-request.json",)

#: What the child does: ask the store for a compile, through the same public function
#: every caller uses, with the store's location coming from ``ADCP_CACHE`` alone.  It
#: prints the key it asked under so the parent names the new entry rather than inferring
#: it from what is left over.
_THE_ASK = """
import sys
sys.path.insert(0, "tests")
from pathlib import Path
import compiled
population = {population!r}
compiled.compiled(Path({bundle!r}), population)
print(compiled.digest(Path({bundle!r}), population))
"""


def _as_check_spells_it() -> Path:
    """``./check``'s own ``BUNDLE``, read by IMPORTING the entry point.

    Imported rather than re-spelled here, because a copy of the literal would be a third
    place the bundle's path is written down and the defect being graded is exactly two
    places disagreeing about it.  ``./check`` is a python module behind a shell preamble
    that is itself a string expression, so it imports; everything it does on import is
    bind constants and define functions, and ``main`` runs under ``__main__`` alone.
    """
    loader = importlib.machinery.SourceFileLoader("check_entry_point", str(REPO / "check"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None, loader.path
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module.BUNDLE


def test_one_bundle_is_held_under_one_key_however_a_caller_spells_its_path() -> None:
    """The fast loop and the gate ask the store for ONE entry, which is q3a's finding.

    The spellings are the two live entry points' own values plus one that is neither: a
    path out of the suite's directory and back in, which is this bundle named a third way.
    Every one of them is asserted to NAME this bundle first -- that is the check's
    precondition and it is also what keeps the keys comparable, since a spelling pointing
    somewhere else would be entitled to its own key.

    The population is the whole portable set, read once and handed to every spelling, so
    the only thing varying across the keys is how the path is written.  It is the whole set
    rather than a cheap one because that is the entry the 842 MB is in and the one the two
    lanes were each warming separately.

    ``./check``'s spelling is RELATIVE, so this reads it with the checkout as the working
    directory -- what ``./check`` itself requires of a caller, and what the suite already
    requires of one (``tests/test_required_with_no_declaration.py``'s ``SOURCE`` is the
    same relative literal).  The precondition
    above is what reports a working directory that is not the checkout, rather than letting
    it arrive as a difference between keys.
    """
    spellings = {
        "./check": _as_check_spells_it(),
        "tests/fresh.py": fresh.BUNDLE,
        "out of the suite's directory and back": REPO / "tests" / ".." / "schemas" / "cache" / "3.2",
    }
    labels = claimed("spellings a caller reaches the store with", set(spellings))
    assert {Path(path).resolve() for path in spellings.values()} == {BUNDLE}, (
        f"a spelling here does not name {BUNDLE}, and the working directory is "
        f"{Path.cwd()}: { {label: str(path) for label, path in spellings.items()} }"
    )

    population = sorted(claimed("the bundle's portable documents", bundle.portable(BUNDLE)))
    keys = {label: compiled.digest(spellings[label], population) for label in sorted(labels)}
    held = claimed("keys this one compile would be held under", set(keys.values()))
    assert len(held) == 1, (
        "one bundle, one population and one compiler are held under more than one key, so "
        "the store carries a copy of one 842 MB answer per spelling and a lane that warms "
        f"it with ./check has not warmed the entry the suite reads: {keys}"
    )


def test_the_store_drops_only_what_nothing_has_asked_for_inside_the_window(
    tmp_path: Path,
) -> None:
    """The retention rule, over a store planted by hand, reported BY NAME.

    Six cells, and the last two are what make the rule safe rather than merely bounded:

    * an entry asked for just now stays;
    * an entry asked for inside the window stays;
    * an entry nothing has asked for since before the window opened goes -- those are the
      98 of 103 the hand prune removed;
    * a staging file a killed writer left behind goes, under the same rule and not a second
      one: it is named for a key, and nothing has asked for it either;
    * **the entry being asked for RIGHT NOW stays, with an ancient mtime**, which is the
      one deletion that could take an entry out from under the reader that is mid-ask.  Its
      mtime is set old deliberately: the rule may not depend on the asking process having
      touched the file first;
    * **and a staging file of THAT SAME KEY still goes**, because the exemption is the
      entry and not the key.  The live store holds one such file of 842,068,270 bytes from a
      writer killed at 09:10, so this is the difference between a rule that bounds the store
      and one that leaks an 842 MB file per killed writer forever.

    The survivors are asserted as a SET OF NAMES: a rule that dropped the wrong three of
    six would be invisible in a count.
    """
    store = tmp_path / "emit-cache"
    store.mkdir()
    now = time.time()
    stale = now - compiled.KEPT_SECONDS - 60
    asked_for_now = "a" * 64
    planted = {
        f"{asked_for_now}.pickle": stale,
        f"{asked_for_now}.4242.tmp": stale,
        f"{'b' * 64}.pickle": now,
        f"{'c' * 64}.pickle": now - compiled.KEPT_SECONDS / 2,
        f"{'d' * 64}.pickle": stale,
        f"{'e' * 64}.12345.tmp": stale,
    }
    claimed("entries planted in the store", planted)
    for name, mtime in planted.items():
        held = store / name
        held.write_bytes(b"the prune reads this file's mtime and never its bytes")
        os.utime(held, (mtime, mtime))

    compiled._prune(store, keep=asked_for_now)

    assert {path.name for path in store.iterdir()} == {
        f"{asked_for_now}.pickle",
        f"{'b' * 64}.pickle",
        f"{'c' * 64}.pickle",
    }, sorted(path.name for path in store.iterdir())


def test_asking_for_a_compile_prunes_the_store_and_nobody_runs_anything(
    tmp_path: Path,
) -> None:
    """The wiring: a child whose only unusual input is ``ADCP_CACHE`` prunes on its way.

    This is the half the rule cannot cover.  ``tests/fresh.py``'s tree store is bounded
    because ``_materialised`` calls its ``_prune`` on every ask; the compile store reached
    55 GB because nothing called anything, and a rule nothing calls is the same amount of
    disk as no rule.  So the ask here is a real one, through the public function, in a
    CHILD: this process has already bound ``compiled.STORE`` to the shared store, and
    pointing it elsewhere in-process would grade a store no lane uses.

    Three readings, and the third is what says the prune did not simply empty the
    directory: the stale entry is gone, the entry asked for inside the window is still
    there, and the compile the child asked for is held under the key it printed.
    """
    root = tmp_path / "cache"
    store = root / "emit-cache"
    store.mkdir(parents=True)
    now = time.time()
    stale = store / f"{'0' * 64}.pickle"
    recent = store / f"{'1' * 64}.pickle"
    planted = {stale: now - compiled.KEPT_SECONDS - 60, recent: now}
    claimed("entries the child did not ask for", planted)
    for held, mtime in planted.items():
        held.write_bytes(b"an entry of a compiler revision that no longer exists")
        os.utime(held, (mtime, mtime))

    done = subprocess.run(
        [sys.executable, "-c", _THE_ASK.format(population=list(A_CHEAP_POPULATION), bundle=str(BUNDLE))],
        capture_output=True,
        text=True,
        env={**os.environ, "ADCP_CACHE": str(root), "PYTHONPATH": os.pathsep.join((str(REPO), str(REPO / "src")))},
        cwd=REPO,
        check=False,
    )
    assert done.returncode == 0, f"{done.stdout[-2000:]}\n{done.stderr[-4000:]}"

    assert not stale.exists(), (
        "the child asked the store for a compile and the entry nothing has asked for in "
        f"{compiled.KEPT_SECONDS / 3600:.0f} h is still there, so the store is bounded by "
        "whoever remembers to prune it by hand"
    )
    assert recent.exists(), "an entry inside the window was dropped"
    asked_under = store / f"{done.stdout.strip()}.pickle"
    assert asked_under.exists(), sorted(path.name for path in store.iterdir())
