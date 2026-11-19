"""Every published name either resolves, or carries a recorded decision (#5wr6).

``tests/fixtures/public_api_snapshot.json`` records 8,118 names the package
published and what each resolved to. ``tests/test_public_api.py`` compares it
against the live surface -- but its FIRST assertion is that the snapshot's
namespace set equals the live one, and that assertion has been failing on
``FINDINGS-126.md`` row R16 (``brand_discovery``, ``manifest``,
``manifest_schema`` recorded, ``common`` live) since before this week. So it
dies in its own setup and **never reaches the name comparison**: 3,962 recorded
names do not resolve and nothing in the repo noticed. That is the gap this file
closes, and it is why this is a separate file rather than another assertion in
that one -- a check that shares a failure with an unrelated pre-existing one is a
check nobody reads.

The obligation, in three outcomes:

* **it resolves** -- nothing owed;
* **it does not resolve and is declared** -- fine, and
  ``tests/fixtures/public_api_declarations.json`` says which kind and why;
* **it does not resolve and is declared nowhere** -- RED. This is the whole point.

**THE DECLARATIONS ARE A FROZEN LIST AND NOT A RULE.** Each cluster records the
rule it was assigned by, for audit, but this gate reads only the name lists. A
name that stops resolving tomorrow is RED even where a cluster's rule would have
had an opinion about it -- a rule evaluated here would silence the next removal
automatically, which is the failure the obligation exists to prevent.

**AND THE SNAPSHOT IS A CHECK, NEVER AN INPUT** (owner, 2026-11-19). Nothing here
writes it, and nothing here emits a binding: it says WHICH names existed, not what
they should alias to.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def accountability():
    """The engine, the snapshot and the declarations, imported once.

    Module-scoped because resolving 8,118 names realises the whole generated
    pydantic graph, and three tests asking for it separately would pay for it
    three times.
    """
    import sys
    from pathlib import Path

    repo = Path(__file__).parent.parent
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from scripts import public_api_accountability as engine

    snapshot = engine.load_snapshot()
    declarations = engine.load_declarations()
    return engine, snapshot, declarations, engine.sweep(snapshot)


def test_every_published_name_resolves_or_is_declared(accountability) -> None:
    """A recorded name that neither resolves nor carries a declaration is RED.

    The remedy is never to delete the row from the snapshot. It is to work out
    what happened to the name and record it::

        python scripts/public_api_accountability.py                     # the cluster table
        python scripts/public_api_accountability.py --unaccounted       # just these names
        python scripts/public_api_accountability.py --propose /tmp/p.json

    ``--propose`` gathers the evidence -- is the recorded document still emitted,
    does any class in the tree carry the word, what did the class actually look
    like at ``639134c75^`` -- and suggests a cluster. **A proposal is not a
    declaration**: read it, decide, and move the row into the declarations file
    yourself. A name you cannot place stays red.
    """
    engine, _snapshot, declarations, resolution = accountability
    declared = engine.declared_names(declarations)

    unaccounted = sorted(key for key, ok in resolution.items() if not ok and key not in declared)
    assert not unaccounted, (
        f"{len(unaccounted)} published name(s) neither resolve nor carry a declaration:\n"
        + "\n".join(f"  {namespace}.{name}" for namespace, name in unaccounted[:40])
        + (f"\n  ... and {len(unaccounted) - 40} more" if len(unaccounted) > 40 else "")
        + "\n\nA published name vanishing is invisible until an adopter's import fails, so "
        "it is red here instead. Record WHY in tests/fixtures/public_api_declarations.json "
        "-- retired, renamed to X, a generator numbering artefact, never a document's -- or "
        "restore the name. Do NOT regenerate the snapshot: it is the specification, and "
        "refreshing it to match the tree destroys the only thing that can detect this. "
        "`python scripts/public_api_accountability.py --propose <path>` gathers the evidence."
    )


def test_a_declaration_is_removed_once_its_name_resolves_again(accountability) -> None:
    """A declared name that resolves again is a stale declaration, so the file shrinks.

    Without this the file is an allowlist that only grows, and a name restored by
    one lane keeps its "retired" note for the next reader to trust. Declarations
    ratchet DOWN, like every other allowlist in this repo.
    """
    engine, _snapshot, declarations, resolution = accountability
    declared = engine.declared_names(declarations)

    stale = sorted(key for key in declared if resolution.get(key) is True)
    assert not stale, (
        f"{len(stale)} name(s) resolve again and their declaration is now stale:\n"
        + "\n".join(
            f"  {namespace}.{name} (declared by {declared[(namespace, name)]['id']})"
            for namespace, name in stale[:40]
        )
        + "\n\nDelete the row: a declaration kept past its name reads as a live decision."
    )


def test_a_declaration_names_a_name_the_snapshot_records(accountability) -> None:
    """The file declares nothing the snapshot does not record.

    A row for a name no recording namespace carries is dead weight at best, and at
    worst a note about a word this package never published -- which would make the
    file's own counts a fiction.
    """
    _engine, snapshot, declarations, _resolution = accountability

    phantom = []
    for cluster in declarations.get("clusters", ()):
        for namespace, names in cluster.get("names", {}).items():
            recorded = snapshot.get(namespace, {}).get("resolves", {})
            phantom += [(cluster["id"], namespace, name) for name in names if name not in recorded]
    assert not phantom, "declarations name words the snapshot does not record:\n" + "\n".join(
        f"  {cluster}: {namespace}.{name}" for cluster, namespace, name in phantom[:40]
    )


def test_the_declarations_file_is_well_formed(accountability) -> None:
    """One cluster per name, every kind defined, every cluster reasoned.

    A name two clusters claim has two reasons and therefore none; a kind the file
    does not define is a word without a meaning; and a cluster with no reason is
    the thing this whole obligation exists to refuse -- a name silenced without a
    judgement behind it.
    """
    engine, _snapshot, declarations, _resolution = accountability

    duplicates = engine.duplicate_declarations(declarations)
    assert not duplicates, "name(s) claimed by more than one cluster:\n" + "\n".join(
        f"  {ns}.{name}: {ids}" for ns, name, ids in duplicates[:20]
    )

    kinds = declarations.get("kinds", {})
    assert kinds, "the declarations file defines no kinds"
    for cluster in declarations.get("clusters", ()):
        where = cluster.get("id", "<unnamed cluster>")
        assert cluster.get("kind") in kinds, f"{where}: kind {cluster.get('kind')!r} is undefined"
        for field in ("rule", "reason", "stated_in"):
            assert cluster.get(field), f"{where}: no {field}"
        assert cluster.get("names"), f"{where}: declares no names"


def test_the_unaccounted_count_is_zero_and_the_declared_count_is_stated(accountability) -> None:
    """The file's own ``counts`` agree with the file, so a quoted figure is checkable.

    The cluster table on ``adcp-client-python-5wr6`` quotes these numbers. A count
    that drifts from the lists under it is how a stale figure gets re-quoted as a
    measurement -- which is the failure ``./check``'s own docstring warns about.
    """
    _engine, snapshot, declarations, resolution = accountability

    recorded = sum(len(entry["resolves"]) for entry in snapshot.values())
    declared = sum(
        len(names)
        for cluster in declarations.get("clusters", ())
        for names in cluster["names"].values()
    )
    counts = declarations.get("counts", {})
    assert counts.get("recorded_names") == recorded, (
        f"counts.recorded_names is {counts.get('recorded_names')}, the snapshot holds {recorded}"
    )
    assert counts.get("declared_here") == declared, (
        f"counts.declared_here is {counts.get('declared_here')}, the clusters hold {declared}"
    )
    assert counts.get("clusters") == len(declarations.get("clusters", ())), (
        "counts.clusters disagrees with the cluster list"
    )

    from collections import Counter

    by_kind = Counter()
    for cluster in declarations.get("clusters", ()):
        by_kind[cluster["kind"]] += sum(len(names) for names in cluster["names"].values())
    measured = dict(sorted(by_kind.items()))
    assert counts.get("by_kind") == measured, (
        f"counts.by_kind is {counts.get('by_kind')}, the clusters hold {measured}"
    )

    # The two halves must partition the recording: a declared name that resolves is
    # caught above, so here declared + resolving == recorded is the same statement
    # as "nothing is unaccounted", said as a count rather than a list.
    assert declared + sum(1 for ok in resolution.values() if ok) == recorded
    assert counts.get("unaccounted") == 0, (
        "counts.unaccounted is not 0; it is a STATED figure, and the obligation is that "
        "it stays 0 by a name being understood, never by the snapshot being refreshed"
    )
