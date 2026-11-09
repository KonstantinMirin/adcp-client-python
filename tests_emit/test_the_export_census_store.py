"""The export census store: what a hit hands back, and how long an entry lives.

``codegen/store.py`` argues its own correctness -- the key covers the compiler's source, the
bundle and the set asked for; the write is atomic; every failure path falls through to
computing, so "the worst it can do is cost the walk it was there to save".  What that
argument does NOT cover is the two things a store gets wrong in the world rather than on
paper, and they are what is graded here:

**1. A HIT IS THE WALK'S OWN ANSWER.**  §1's domain-scope collision rule decides every
public name of the surface, so a store that changed one name would change what a consumer
imports -- and it would do it silently, because a name derived from a stale census is a
perfectly good identifier.  So the first check asks for one domain's census twice, cold and
then over the entry the cold ask wrote, and asserts the two answers are equal BY NAME.

**2. AN ENTRY NOTHING HAS ASKED FOR IS DROPPED, AND BY THE RUN THAT ASKS.**  The compile
store beside this one had no prune at all and reached 103 entries of 842,068,270 bytes --
55 GB on a root filesystem at 96% -- of which 98 had been neither written nor read in eight
hours, and they were removed by hand.  A retention rule that needs a human is the defect and
not the fix, so the rule is graded at both ends: in isolation over a store planted by hand,
and WIRED, over a real ask in a child process whose only unusual input is ``ADCP_CACHE``.

**And the hazard the key cannot answer for is graded too.**  A runtime perturbation changes
what the walk does without changing a byte of source, so the digest does not move and a
perturbed process would be handed -- or worse, would WRITE -- a census no compiler anybody
runs derived.  ``store.perturbed()`` is the declaration that closes that, and the last check
is that inside it the planted entry is neither read nor written.
``tests/test_no_cached_compile_under_a_perturbation.py`` holds the other half: that every
perturbing caller in this suite makes the declaration.
"""

from __future__ import annotations

import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

import fresh
import pytest
from nodeset import claimed

from codegen import emit, store

REPO = Path(__file__).resolve().parents[1]
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
BUNDLE = fresh.BUNDLE

#: One §1 DOMAIN, because what these checks grade is the STORE and not a census: the domain
#: set a one-document run of ``core`` asks for costs ~110 s and this one costs 0.85 s.
#: Named rather than counted, and it is a domain that EXPORTS something, which is what makes
#: a child's own return code readable as "the ask succeeded" and what keeps the equality
#: below from holding over two empty answers.
A_CHEAP_DOMAIN = frozenset({"aao"})

#: What the child does: ask for a domain's census, through the same public function
#: ``emit.emit`` calls, with the store's location coming from ``ADCP_CACHE`` alone.  It
#: prints the key it asked under, so the parent NAMES the new entry rather than inferring it
#: from whatever is left in the directory.
_THE_ASK = """
import sys
sys.path.insert(0, "tests")
from pathlib import Path
from codegen import emit, store
bundle = Path({bundle!r})
domains = frozenset({domains!r})
emit.domain_exports(bundle, domains)
print(store.key(bundle, sorted(domains)))
"""


@pytest.fixture
def a_store_of_its_own(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """``store.STORE`` pointed at this test's own directory, and the memo cleared.

    Both are needed and neither is a perturbation of the WALK: "cold" has to be a fact about
    a directory this test owns rather than about what another lane happened to warm, and
    ``lru_cache`` would otherwise answer the second ask so the disk layer would never be
    read.  ``monkeypatch`` puts ``store.STORE`` back, because a module global left pointing
    at a deleted ``tmp_path`` would turn every later test in this process into a cold walk.
    """
    monkeypatch.setattr(store, "STORE", tmp_path / "domain-exports")
    emit.domain_exports.cache_clear()
    return tmp_path / "domain-exports"


def _planted(store_dir: Path, entries: dict[str, float]) -> None:
    """Write each named file with the mtime given.  The prune reads the mtime and never the
    bytes, so the bytes say that."""
    for name, mtime in entries.items():
        held = store_dir / name
        held.write_bytes(b"the prune reads this file's mtime and never its bytes")
        os.utime(held, (mtime, mtime))


def test_the_census_a_hit_hands_back_is_the_one_the_walk_computed(
    a_store_of_its_own: Path,
) -> None:
    """Cold and warm answer the same thing, asserted as the (domain, name) pairs.

    This is the property the whole design rests on and the one a reader of a public name
    cares about: §1's census decides what ``adcp.types.<domain>`` exports, so an answer that
    moved between a cold store and a warm one would move a class's import path without
    anybody's gate going red.

    The store is pointed at ``tmp_path`` rather than the shared one, so "cold" is a fact
    about this directory and not about what another lane happened to warm; and the in-process
    memo is cleared between the two asks, because ``lru_cache`` would otherwise answer the
    second one and the disk layer would never be read at all.

    Asserted by NAME and not by count: a census that dropped one symbol and gained another
    is identical in a count, and the name is what a consumer types.
    """
    cold = emit.domain_exports(BUNDLE, A_CHEAP_DOMAIN)

    emit.domain_exports.cache_clear()
    warm = emit.domain_exports(BUNDLE, A_CHEAP_DOMAIN)

    pairs = claimed(
        "the (domain, name) pairs this domain's census holds",
        {(known, symbol) for known, held in cold.items() for symbol in held},
    )
    assert {(known, symbol) for known, held in warm.items() for symbol in held} == pairs
    assert warm == cold, f"cold {cold}\nwarm {warm}"
    assert (a_store_of_its_own / f"{store.key(BUNDLE, sorted(A_CHEAP_DOMAIN))}.pickle").exists(), (
        "the cold ask wrote no entry, so the 'warm' half above was a second cold walk and "
        "this check compares the walk with itself"
    )


def test_a_perturbed_caller_neither_reads_the_store_nor_writes_it(
    a_store_of_its_own: Path,
) -> None:
    """``store.perturbed()``: the one hazard the key cannot answer for.

    A runtime perturbation moves no byte of ``codegen/``, so the digest cannot see it.  Both
    directions are graded here with one planted entry, because both are defects and only one
    of them is loud:

    * READING -- the entry is planted with a census no walk produced, and the answer inside
      the block has to be the WALK's.  Served the plant instead, a perturbing test measures
      the unperturbed compiler and passes while measuring nothing;
    * WRITING -- the plant is asserted unchanged on the way out.  A perturbed process that
      wrote its census under the honest key would make every later run export names a
      compiler nobody runs derived, which is the staleness the key exists to prevent.

    The plant is a census shaped like a real one and holding a name no document of the bundle
    exports, so "the answer is the plant" and "the answer is the walk's" cannot be confused.
    """
    a_store_of_its_own.mkdir(parents=True)
    entry = a_store_of_its_own / f"{store.key(BUNDLE, sorted(A_CHEAP_DOMAIN))}.pickle"
    plant = {"aao": {"NoWalkOfThisBundleEverDerivedThisName": frozenset({"aao/nothing.json"})}}
    entry.write_bytes(pickle.dumps(plant))
    planted = claimed("the names planted under the honest key", set(plant["aao"]))

    with store.perturbed():
        answer = emit.domain_exports(BUNDLE, A_CHEAP_DOMAIN)

    assert {s for held in answer.values() for s in held}.isdisjoint(planted), (
        f"a perturbed caller was served the store's entry: {answer}"
    )
    assert pickle.loads(entry.read_bytes()) == plant, (
        "a perturbed caller overwrote the entry under the honest key, so every later run "
        "would export names a compiler no source describes derived"
    )


def test_the_store_drops_only_what_nothing_has_asked_for_inside_the_window(
    tmp_path: Path,
) -> None:
    """The retention rule, over a store planted by hand, reported BY NAME.

    Six cells, and the last two are what make the rule safe rather than merely bounded:

    * an entry asked for just now stays;
    * an entry asked for inside the window stays;
    * an entry nothing has asked for since before the window opened goes -- those are the 98
      of 103 the compile store's hand prune removed;
    * a staging file a killed writer left behind goes, under the same rule and not a second
      one: it is named for a key, and nothing has asked for it either;
    * **the entry being asked for RIGHT NOW stays, with an ancient mtime**, which is the one
      deletion that could take an entry out from under the reader that is mid-ask.  Its mtime
      is set old deliberately: the rule may not depend on the asking process having touched
      the file first;
    * **and a staging file of THAT SAME KEY still goes**, because the exemption is the entry
      and not the key.  The compile store held one such file of 842,068,270 bytes from a
      killed writer, so this is the difference between a rule that bounds the store and one
      that leaks a file per killed writer forever.

    The survivors are asserted as a SET OF NAMES: a rule that dropped the wrong three of six
    would be invisible in a count.
    """
    store_dir = tmp_path / "domain-exports"
    store_dir.mkdir()
    now = time.time()
    stale = now - store.KEPT_SECONDS - 60
    asked_for_now = "a" * 64
    planted = {
        f"{asked_for_now}.pickle": stale,
        f"{asked_for_now}.4242.tmp": stale,
        f"{'b' * 64}.pickle": now,
        f"{'c' * 64}.pickle": now - store.KEPT_SECONDS / 2,
        f"{'d' * 64}.pickle": stale,
        f"{'e' * 64}.12345.tmp": stale,
    }
    claimed("entries planted in the store", planted)
    _planted(store_dir, planted)

    store._prune(store_dir, keep=asked_for_now)

    assert {path.name for path in store_dir.iterdir()} == {
        f"{asked_for_now}.pickle",
        f"{'b' * 64}.pickle",
        f"{'c' * 64}.pickle",
    }, sorted(path.name for path in store_dir.iterdir())


def test_asking_for_a_census_prunes_the_store_and_nobody_runs_anything(
    tmp_path: Path,
) -> None:
    """The wiring: a child whose only unusual input is ``ADCP_CACHE`` prunes on its way.

    This is the half the rule itself cannot cover.  ``tests/fresh.py``'s tree store is
    bounded because every ask calls its prune; the compile store reached 55 GB because
    nothing called anything, and a rule nothing calls is the same amount of disk as no rule.
    So the ask here is a real one, through the same function ``emit.emit`` calls, in a CHILD:
    this process has already bound ``store.STORE``, and pointing it elsewhere in-process
    would grade a store no lane uses.

    Three readings, and the third is what says the prune did not simply empty the directory:
    the stale entry is gone, the entry asked for inside the window is still there, and the
    census the child asked for is held under the key it printed.
    """
    root = tmp_path / "cache"
    store_dir = root / "domain-exports"
    store_dir.mkdir(parents=True)
    now = time.time()
    stale = store_dir / f"{'0' * 64}.pickle"
    recent = store_dir / f"{'1' * 64}.pickle"
    planted = {stale.name: now - store.KEPT_SECONDS - 60, recent.name: now}
    claimed("entries the child did not ask for", planted)
    _planted(store_dir, planted)

    done = subprocess.run(
        [
            sys.executable,
            "-c",
            _THE_ASK.format(bundle=str(BUNDLE), domains=sorted(A_CHEAP_DOMAIN)),
        ],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "ADCP_CACHE": str(root),
            "PYTHONPATH": os.pathsep.join((str(REPO), str(REPO / "src"))),
        },
        cwd=REPO,
        check=False,
    )
    assert done.returncode == 0, f"{done.stdout[-2000:]}\n{done.stderr[-4000:]}"

    assert not stale.exists(), (
        "the child asked the store for a census and the entry nothing has asked for in "
        f"{store.KEPT_SECONDS / 3600:.0f} h is still there, so the store is bounded by "
        "whoever remembers to prune it by hand"
    )
    assert recent.exists(), "an entry inside the window was dropped"
    asked_under = store_dir / f"{done.stdout.strip()}.pickle"
    assert asked_under.exists(), sorted(path.name for path in store_dir.iterdir())
