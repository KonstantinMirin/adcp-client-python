"""The adapter writer writes the paths it OWNS, rewrites them, and touches nothing else.

``survey/adapter_surface.py`` writes one module per upstream module its measured demand
names.  Two properties have to hold at once, and ``adcp-client-python-smzq`` is the row for
what happens when only one of them does:

**IT CAN ADD A NAME TO A MODULE IT ALREADY WROTE.**  The writer's claim about itself is
that it is DERIVED -- that the modules beside the table are a function of the same inputs
the table is.  Its guard against clobbering was ``if target.exists(): continue``, which is
true of the writer's own last output, so the instrument could not add a name to its own
module: a schema bump moved the table and left every adapter module at its old contents,
with nothing saying so.  Seven names of ``adcp.types.capabilities`` were refused rows that
the pointer keys now bind, and under that skip not one of them could have reached the file.

**AND A PATH IT DID NOT WRITE IS NEVER WRITTEN.**  Removing the skip alone is worse, and
measurably: five of the paths this writer's demand names hold upstream's own hand-written
machinery, restored byte for byte (``_legacy_assets``, ``_scalar``, ``_str_enum``,
``_wire``, ``error_narrowing``), and ``adcp.types.core`` is a document's module of OURS as
well as the name of a machinery module of theirs.  A run with no ownership reading
overwrites both with generated re-exports.

**THE COMMENT IS NOT THE MECHANISM, WHICH IS THE REASON THIS FILE EXISTS.**  The previous
attempt on that row removed the skip, wrote a comment asserting the exclusion, and only
then checked whether the exclusion was real; it was not.  So each clause below is graded as
BEHAVIOUR over a tree built for the purpose -- bytes written, bytes not written -- and the
population of restored paths is the classification's own rows measured against upstream's
own blobs, never a list spelled here.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from nodeset import claimed

ROOT = Path(__file__).resolve().parent.parent
SURFACE = ROOT / "src" / "adcp" / "types"
TABLE = ROOT / "survey" / "upstream-machinery-9.6.1.tsv"

sys.path.insert(0, str(ROOT / "survey"))

import adapter_surface as writer  # noqa: E402
import upstream_machinery as um  # noqa: E402


def _row(module: str, name: str, target: str, word: str) -> dict:
    """One BOUND row of the join, in the shape :func:`write_modules` consumes.

    Forged rather than drawn from the committed table, because what is graded here is the
    writer's treatment of a path and not the join's choice of a subject; a row of the real
    table would make this test move whenever a binding does.
    """
    return {
        "module": module,
        "name": name,
        "verdict": "BOUND",
        "how": "document+word",
        "identity": "agrees",
        "target": [f"{target}.{word}"],
        "public": [[target, word]],
        "note": "",
        "files": ["src/adcp/forged.py"],
        "pairs": 1,
    }


# --------------------------------------------------------------------------- #
# the population: the classification's rows, and the bytes at those paths now
# --------------------------------------------------------------------------- #
def test_the_classification_column_and_the_live_bytes_say_the_same_thing() -> None:
    """``here_now == restored`` in the table is the same set as blob identity right now.

    Two readings of one question, and the gate is that they agree.  The table's column is
    a RECORD, written when the survey last ran; :func:`upstream_machinery.restored_paths`
    is the same reading taken live, which is what the writer consults before it touches a
    path.  A column gone stale in the dangerous direction -- a module restored after the
    table was written -- would leave that path unprotected by the clause, and nothing else
    in the suite would notice.
    """
    rows = list(
        csv.DictReader(
            [ln for ln in TABLE.read_text().splitlines() if not ln.startswith("#")],
            delimiter="\t",
        )
    )
    claimed("modules of upstream's the classification ranges over", [r["module"] for r in rows])
    recorded = {(ROOT / r["upstream_path"]).resolve() for r in rows if r["here_now"] == "restored"}
    measured = claimed("paths holding upstream's own file, measured", um.restored_paths())
    assert recorded == measured, {
        "the table records a restored path the bytes do not": sorted(
            str(p.relative_to(ROOT)) for p in recorded - measured
        ),
        "upstream's own file is at a path the table does not record": sorted(
            str(p.relative_to(ROOT)) for p in measured - recorded
        ),
    }


def test_every_restored_path_is_refused_by_the_ownership_reading() -> None:
    """Whatever the classification turns out to hold, the writer will not write it.

    Ranges over the measured set rather than over five names, so a module restored later is
    graded by this line without it changing.
    """
    restored = claimed("paths holding upstream's own file", um.restored_paths())
    held = {p: writer.owner(p, restored) for p in restored}
    assert all(held.values()), {
        "a restored path the writer reads as its own": sorted(
            str(p.relative_to(ROOT)) for p, why in held.items() if not why
        )
    }
    assert all("restored" in why for why in held.values()), held


def test_our_own_emitted_domain_module_is_refused_and_says_why() -> None:
    """``adcp.types.core`` is a document's module of ours AND a machinery module of theirs.

    It carries no adapter marker and is not upstream's restored file, so the second clause
    is the one that answers -- and it is the clause the removed ``target.exists()`` skip was
    silently standing in for.
    """
    why = writer.owner(SURFACE / "core.py", um.restored_paths())
    assert why and "a module of ours" in why, why
    assert writer.owner(SURFACE / "_adapter.py", um.restored_paths()) is None, (
        "the writer no longer owns its own flat module, so a run would refuse to rewrite it"
    )


# --------------------------------------------------------------------------- #
# the property the row is named for, demonstrated by writing twice
# --------------------------------------------------------------------------- #
def test_the_writer_adds_a_name_to_a_module_it_already_wrote(tmp_path: Path) -> None:
    """Write one name, then write two: the second run carries both.

    The whole of ``adcp-client-python-smzq``'s first half, as behaviour.  Under the skip the
    second run returned ``(0, 0)`` for the module and left the file at one name -- which is
    asserted here as the thing that no longer happens, by reading the file.
    """
    first, _ = writer.write_modules(
        [_row("adcp.types.forged", "Alpha", "adcp.types.core", "Account")],
        tmp_path,
        "9.6.1",
        restored=frozenset(),
    )
    assert first["adcp.types.forged"] == (1, 0), first
    once = (tmp_path / "forged.py").read_text()
    assert "Alpha" in once and writer.MARKER in once

    second, refused = writer.write_modules(
        [
            _row("adcp.types.forged", "Alpha", "adcp.types.core", "Account"),
            _row("adcp.types.forged", "Beta", "adcp.types.core", "Brand"),
        ],
        tmp_path,
        "9.6.1",
        restored=frozenset(),
    )
    assert not refused, refused
    assert second["adcp.types.forged"] == (2, 0), second
    twice = (tmp_path / "forged.py").read_text()
    assert "Alpha" in twice and "Beta" in twice, twice
    assert '"Beta",' in twice, "the added name reached the module's own __all__"


def test_a_second_run_over_one_demand_reproduces_the_first_byte_for_byte(tmp_path: Path) -> None:
    """Idempotence, which is the other half of the same claim: same inputs, same bytes."""
    rows = [_row("adcp.types.forged", "Alpha", "adcp.types.core", "Account")]
    writer.write_modules(rows, tmp_path, "9.6.1", restored=frozenset())
    once = (tmp_path / "forged.py").read_bytes()
    writer.write_modules(rows, tmp_path, "9.6.1", restored=frozenset())
    assert (tmp_path / "forged.py").read_bytes() == once, (
        "a second run over one demand wrote different bytes"
    )


# --------------------------------------------------------------------------- #
# the fire probe: a run that TARGETS a held path leaves its bytes alone
# --------------------------------------------------------------------------- #
def test_a_run_targeting_a_restored_path_does_not_move_one_byte(tmp_path: Path) -> None:
    """Upstream's own ``_scalar.py``, copied, named by a row, and unchanged afterwards.

    The copy is the real file, so what is graded is the real case; the tree is a temporary
    one, so a broken clause fails the check instead of destroying the surface.
    """
    held = tmp_path / "_scalar.py"
    held.write_bytes((SURFACE / "_scalar.py").read_bytes())
    before = held.read_bytes()
    written, refused = writer.write_modules(
        [_row("adcp.types._scalar", "plain_scalar", "adcp.types.core", "Account")],
        tmp_path,
        "9.6.1",
        restored=frozenset({held.resolve()}),
    )
    assert "adcp.types._scalar" not in written, written
    assert "restored" in refused["adcp.types._scalar"], refused
    assert held.read_bytes() == before, "the writer overwrote upstream's restored machinery"


def test_a_run_targeting_a_module_of_ours_does_not_move_one_byte(tmp_path: Path) -> None:
    """A file with no marker is somebody's; the writer reports it and leaves it alone."""
    ours = tmp_path / "core.py"
    ours.write_text("# Generated by codegen.emit from core/account.json. Do not edit.\n")
    before = ours.read_bytes()
    written, refused = writer.write_modules(
        [_row("adcp.types.core", "Member", "adcp.types.core", "Account")],
        tmp_path,
        "9.6.1",
        restored=frozenset(),
    )
    assert "adcp.types.core" not in written, written
    assert "a module of ours" in refused["adcp.types.core"], refused
    assert ours.read_bytes() == before, "the writer overwrote an emitted module of ours"


def test_a_module_a_loader_serves_is_not_a_file_the_writer_writes(tmp_path: Path) -> None:
    """``adcp.types.domains.**`` is a mirror with no submodule files, and 16 pairs name it.

    The target path's parent is not a directory of the layer, so there is nowhere for a
    file to go; the flattened leaf this writer used to derive would have put
    ``format.py`` beside ``capabilities.py``, at a path no module names.
    """
    written, refused = writer.write_modules(
        [_row("adcp.types.domains.core.format", "Assets", "adcp.types.core", "Account")],
        tmp_path,
        "9.6.1",
        restored=frozenset(),
    )
    assert not written, written
    assert "loader" in refused["adcp.types.domains.core.format"], refused
    assert not (tmp_path / "format.py").exists(), "a nested module was flattened onto a leaf"
