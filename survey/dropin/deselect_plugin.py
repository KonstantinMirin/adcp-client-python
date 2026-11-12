"""The DELETE set, removed from the drop-in run at collection -- §8a's mechanism.

**WHY THIS IS A DESELECTION AND NOT AN EXCISION, and the reason is §8a's own rule.**
``survey/regenerate.py --audit`` classifies every file of a drop-in tree as
``upstream verbatim``, ``ours verbatim``, one of the two plus a declared marker, or an
EDIT -- and "an edit in a disposable tree is a fork beginning, which §8a says can only be
deleted and regenerated".  The DELETE set is 147 test FUNCTIONS spread over 65 of
upstream's test files; cutting them out would turn all 65 into ``UPSTREAM EDITED`` and the
audit that makes the tree checkable would report a fork of 65 files.  Deselecting them at
collection removes them from the DENOMINATOR -- which is the whole of what is wanted,
because the complaint was that a pass-count over assertions about their generator is a
figure that cannot be earned -- and leaves every retained file byte-identical to upstream's.

**THE LIST IS DERIVED AND NEVER WRITTEN.**  ``survey/upstream_test_character.py
--delete-tsv`` is its only source: it classifies by AST, over the ``test`` expression of
each ``assert`` and over ``pytest.raises`` bodies, and a row exists only where the claim
itself names upstream's representation.  ``survey/regenerate.py`` re-runs that classifier
against the tree it has just laid, so the table a run deselects by is a derivation over the
files that are THERE -- the same discipline ``population()`` already follows -- and not a
record of what some earlier tree held.

**A ROW THAT MATCHES NOTHING IN A FILE THIS RUN COLLECTED IS AN ERROR AND NOT A SHRUG.**  A
renamed test would silently stop deselecting and the denominator would move without anyone
saying so, so an unmatched row fails the run -- the same reading
``drop_their_generator_tests`` takes of its declared population.

**AND THE CHECK IS SCOPED TO THE FILES THIS RUN COLLECTED, because the suite is run in four
chunks.**  ``survey/regenerate.py`` partitions the 577 behavioural files into
``chunk-00``/``-01``/``-02``/``-r159`` and each command collects its own chunk, so most of
the table names a file the current command was never given.  A row whose FILE was not
collected is out of this run's scope and says nothing; a row whose file WAS collected and
whose test was not is the stale row the gate is for.  Reading it the other way made the
first chunk refuse the whole table.

**AND IT DESELECTS A FUNCTION, NOT AN ITEM.**  The table's key is ``(path, function)``; a
parametrised function is one row here and many items in a junit, so every parametrisation
of a deselected function goes together.  Measured on upstream 9.6.1: 147 functions, 659
collected items.

Installed by ``survey/regenerate.py`` into the tree root beside ``deselect.tsv`` and loaded
with ``-p deselect``.  Nothing here imports ``adcp``: a plugin that imported the package
under test would decide at collection time what the run exists to measure.
"""

from __future__ import annotations

import pathlib

#: Beside this file, written by the build from the classifier's own output.
TABLE = pathlib.Path(__file__).resolve().parent / "deselect.tsv"


def _rows(table: pathlib.Path) -> dict[tuple[str, str], tuple[str, str]]:
    """``(path, test) -> (layer, reason)``, read off the one derived table.

    **ONE TABLE, TWO LAYERS** (``adcp-client-python-l1r3``).  ``survey/regenerate.py``
    merges the character classifier's DELETE rows and
    ``survey/dropin/deselect.py``'s invented-default rows into a single
    ``deselect.tsv`` with a ``layer`` column, because a built tree used to read only the
    first and the second declined nothing.  Each row keeps its own layer's reason text, so
    the table stays checkable row by row.
    """
    found: dict[tuple[str, str], tuple[str, str]] = {}
    if not table.is_file():
        return found
    for line in table.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("path\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        found[(parts[0], parts[1])] = (parts[2], parts[3])
    return found


def pytest_collection_modifyitems(config, items):  # noqa: ANN001, ANN201 -- pytest's own
    """Deselect every collected item whose ``(path, function)`` the table names.

    ``item.nodeid`` is ``<path>::<function>[<params>]`` for a plain test and carries a class
    segment for a method, so the function is the LAST ``::`` segment with its parametrisation
    stripped -- read off the nodeid rather than off ``item.function`` because a parametrised
    item's function object is shared by every parametrisation and says nothing about which
    row collected it.
    """
    table = _rows(TABLE)
    if not table:
        return
    keep, dropped, matched, collected_files = [], [], set(), set()
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        path, _, rest = nodeid.partition("::")
        name = rest.split("::")[-1].split("[")[0] if rest else ""
        collected_files.add(path)
        key = (path, name)
        if key in table:
            dropped.append(item)
            matched.add(key)
        else:
            keep.append(item)
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = keep

    # Only a row whose FILE this command collected can be stale; the rest belong to the
    # other chunks and this run has nothing to say about them.
    stale = sorted(
        key for key in set(table) - matched if key[0] in collected_files
    )
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        by_layer: dict[str, int] = {}
        for key in matched:
            by_layer[table[key][0]] = by_layer.get(table[key][0], 0) + 1
        detail = ", ".join(f"{n} {layer}" for layer, n in sorted(by_layer.items()))
        reporter.write_line(
            f"deselect: {len(dropped)} items over {len(matched)} test functions"
            + (f" ({detail})" if detail else "")
        )
        for path, name in stale[:10]:
            reporter.write_line(f"deselect: STALE ROW -- {path}::{name} matched nothing")
    if stale:
        raise SystemExit(
            f"{len(stale)} rows of {TABLE} match no collected test: the derived table is "
            f"stale against this tree and the denominator it defines would be wrong. "
            f"First: {', '.join(f'{p}::{t}' for p, t in stale[:5])}"
        )
