"""Tests for ``python -m adcp.migrate v3-to-v4``.

The migration is one-shot tooling — once a codebase runs through it,
the output is reviewed in ``git diff`` and tests never run against
migrated code again. But the migration itself is code that rewrites
other people's code: bugs here corrupt their source tree. These tests
pin the behaviour tightly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adcp.migrate import v3_to_v4

# ---------------------------------------------------------------------------
# Dry-run scans — file contents unchanged, report lists findings
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body)
    return path


def test_renames_all_nine_asset_content_types(tmp_path: Path) -> None:
    """All 9 ``<Type>Asset`` → ``<Type>Content`` names are detected."""
    source = "\n".join(
        [
            "from adcp.types import (",
            "    AudioAsset, CssAsset, HtmlAsset, ImageAsset, JavascriptAsset,",
            "    TextAsset, UrlAsset, VideoAsset, WebhookAsset,",
            ")",
            "x = AudioAsset(duration_seconds=30)",
        ]
    )
    _write(tmp_path, "user_code.py", source)

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    assert report.scanned_files == 1
    # 9 import-line hits + 1 call-site hit for AudioAsset = 10 applied findings
    applied_names = {f.before for f in report.applied}
    assert applied_names == set(v3_to_v4.ASSET_CONTENT_RENAMES.keys())
    # Every applied rename carries the target name.
    for f in report.applied:
        assert f.after == v3_to_v4.ASSET_CONTENT_RENAMES[f.before]


def test_apply_rewrites_files_in_place(tmp_path: Path) -> None:
    """With ``--apply`` the file contents are rewritten."""
    path = _write(
        tmp_path,
        "code.py",
        "from adcp.types import AudioAsset, VideoAsset\n"
        "audio = AudioAsset(duration_seconds=30)\n"
        "video = VideoAsset(width=1920, height=1080)\n",
    )

    report = v3_to_v4.run(tmp_path, apply_changes=True)

    assert report.rewritten_files == 1
    rewritten = path.read_text()
    assert "AudioAsset" not in rewritten
    assert "VideoAsset" not in rewritten
    assert "AudioContent" in rewritten
    assert "VideoContent" in rewritten


def test_dry_run_does_not_modify_files(tmp_path: Path) -> None:
    """Default mode (no ``--apply``) leaves files untouched."""
    original = "from adcp.types import AudioAsset\n" "audio = AudioAsset(duration_seconds=30)\n"
    path = _write(tmp_path, "code.py", original)

    v3_to_v4.run(tmp_path, apply_changes=False)

    assert path.read_text() == original


def test_word_boundary_protects_against_partial_matches(tmp_path: Path) -> None:
    """``MyAudioAsset`` or ``AudioAssetExtra`` must NOT be rewritten —
    they're the seller's own types and coincidentally contain the
    renamed substring."""
    source = (
        "class MyAudioAsset: pass\n"
        "class AudioAssetExtra: pass\n"
        "class AudioAsset_Custom: pass\n"
        "from adcp.types import AudioAsset\n"
    )
    path = _write(tmp_path, "code.py", source)

    v3_to_v4.run(tmp_path, apply_changes=True)

    rewritten = path.read_text()
    assert "class MyAudioAsset: pass" in rewritten
    assert "class AudioAssetExtra: pass" in rewritten
    assert "class AudioAsset_Custom: pass" in rewritten
    # Only the bare import rewrote.
    assert "from adcp.types import AudioContent" in rewritten


# ---------------------------------------------------------------------------
# Flagged findings — reported with migration-guide anchor, not rewritten
# ---------------------------------------------------------------------------


def test_flags_removed_types_with_migration_anchor(tmp_path: Path) -> None:
    """Removed types (BrandManifest, DeliverTo, Pricing, etc.) are
    flagged — NOT rewritten, since replacement depends on context."""
    source = (
        "from adcp import BrandManifest, DeliverTo, Pricing\n"
        "manifest = BrandManifest(name='x')\n"
    )
    _write(tmp_path, "code.py", source)

    report = v3_to_v4.run(tmp_path, apply_changes=True)

    # Source is unchanged — removed types aren't auto-rewritten.
    rewritten = (tmp_path / "code.py").read_text()
    assert "BrandManifest" in rewritten
    assert "DeliverTo" in rewritten

    # Every flagged finding carries the migration anchor + hint.
    by_name = {f.before: f for f in report.flagged if f.kind == "flag_removed"}
    assert "BrandManifest" in by_name
    assert by_name["BrandManifest"].hint is not None
    assert "BrandReference" in by_name["BrandManifest"].hint
    assert by_name["BrandManifest"].migration_anchor == "brandmanifest--brandreference"


def test_flags_numbered_assets_imports(tmp_path: Path) -> None:
    """Direct ``Assets81`` imports are unstable across spec revisions —
    flag, don't rewrite (the semantic alias depends on what the caller
    was doing with the numbered class)."""
    _write(
        tmp_path,
        "code.py",
        "from adcp.types.generated_poc.bundled.x import Assets81, Assets149\n",
    )

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    numbered = [f for f in report.flagged if f.kind == "flag_numbered"]
    names = {f.before for f in numbered}
    assert names == {"Assets81", "Assets149"}


def test_bare_assets_is_not_flagged_as_numbered(tmp_path: Path) -> None:
    """``Assets`` (no digits) is the legitimate base alias. The numbered
    flag must not fire on it."""
    _write(tmp_path, "code.py", "from adcp.types import Assets\nx = Assets\n")

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    numbered = [f for f in report.flagged if f.kind == "flag_numbered"]
    assert numbered == []


def test_flags_generated_poc_imports(tmp_path: Path) -> None:
    """``adcp.types.generated_poc`` is a private module — flag imports
    from it and point at the public alias path."""
    _write(
        tmp_path,
        "code.py",
        "from adcp.types.generated_poc.core.account import Account\n",
    )

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    private = [f for f in report.flagged if f.kind == "flag_private"]
    assert len(private) == 1
    assert private[0].before == "adcp.types.generated_poc"


def test_flags_removed_attribute_accesses(tmp_path: Path) -> None:
    """``.brand_manifest`` on ResolvedBrand was removed — flag the
    attribute access with a hint."""
    _write(
        tmp_path,
        "code.py",
        "result = await registry.lookup_brand('x')\n" "manifest = result.brand_manifest\n",
    )

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    attr = [f for f in report.flagged if f.kind == "flag_attribute"]
    assert len(attr) == 1
    assert attr[0].before == ".brand_manifest"


# ---------------------------------------------------------------------------
# Skips + file-iteration safety
# ---------------------------------------------------------------------------


def test_skips_common_build_and_dep_dirs(tmp_path: Path) -> None:
    """.venv, .git, node_modules etc. MUST be skipped — scanning
    dependency code would generate thousands of false-positive hits."""
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "bad.py").write_text("from adcp.types import AudioAsset\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "bad.py").write_text("AudioAsset\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "bad.py").write_text("AudioAsset\n")
    (tmp_path / "user.py").write_text("from adcp.types import AudioAsset\n")

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    # Only user.py scanned.
    assert report.scanned_files == 1
    assert {f.path for f in report.applied} == {str(tmp_path / "user.py")}


def test_empty_directory_yields_empty_report(tmp_path: Path) -> None:
    report = v3_to_v4.run(tmp_path, apply_changes=False)
    assert report.scanned_files == 0
    assert report.applied == []
    assert report.flagged == []


def test_non_python_files_ignored(tmp_path: Path) -> None:
    _write(tmp_path, "README.md", "AudioAsset is mentioned here\n")
    _write(tmp_path, "config.yaml", "key: AudioAsset\n")

    report = v3_to_v4.run(tmp_path, apply_changes=False)

    assert report.scanned_files == 0


def test_single_file_path_scans_one_file(tmp_path: Path) -> None:
    """Running against a single .py file scans just that file."""
    path = _write(tmp_path, "user.py", "from adcp.types import AudioAsset\n")

    report = v3_to_v4.run(path, apply_changes=False)

    assert report.scanned_files == 1
    assert len(report.applied) == 1


# ---------------------------------------------------------------------------
# CLI entry + JSON report
# ---------------------------------------------------------------------------


def test_cli_exits_nonzero_on_flagged_findings(tmp_path: Path) -> None:
    """CI gate: any flagged finding (manual review required) → exit 1."""
    _write(tmp_path, "code.py", "from adcp import BrandManifest\n")

    rc = v3_to_v4.main([str(tmp_path)])

    assert rc == 1  # flagged finding


def test_cli_exits_zero_on_renames_only(tmp_path: Path) -> None:
    """Mechanical renames alone don't gate CI — they're a clean apply."""
    _write(tmp_path, "code.py", "from adcp.types import AudioAsset\n")

    rc = v3_to_v4.main([str(tmp_path)])

    assert rc == 0


def test_cli_exits_zero_on_empty_tree(tmp_path: Path) -> None:
    rc = v3_to_v4.main([str(tmp_path)])
    assert rc == 0


def test_cli_exits_nonzero_on_missing_path() -> None:
    rc = v3_to_v4.main(["/nonexistent/path-that-does-not-exist-xyz"])
    assert rc == 2


def test_cli_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--json`` emits a structured report parseable by CI / editors."""
    _write(
        tmp_path,
        "code.py",
        "from adcp.types import AudioAsset\n" "from adcp import BrandManifest\n",
    )

    v3_to_v4.main([str(tmp_path), "--json"])
    out = capsys.readouterr().out

    payload = json.loads(out)
    assert payload["scanned_files"] == 1
    assert payload["rewritten_files"] == 0
    assert len(payload["applied"]) == 1
    assert payload["applied"][0]["before"] == "AudioAsset"
    assert payload["applied"][0]["after"] == "AudioContent"
    removed = [f for f in payload["flagged"] if f["kind"] == "flag_removed"]
    assert any(f["before"] == "BrandManifest" for f in removed)


def test_cli_apply_rewrites_and_reports(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The happy end-to-end path: scan + rewrite + human-readable summary."""
    path = _write(tmp_path, "code.py", "from adcp.types import AudioAsset\n")

    v3_to_v4.main([str(tmp_path), "--apply"])
    out = capsys.readouterr().out

    assert "Rewrote 1 files" in out or "Rewrote 1 file" in out
    assert path.read_text() == "from adcp.types import AudioContent\n"


def test_unreadable_file_does_not_crash(tmp_path: Path) -> None:
    """Non-UTF-8 binary files in the tree are skipped silently —
    they're obviously not Python source the migration cares about."""
    path = tmp_path / "binary.py"
    path.write_bytes(b"\xff\xfe\x00 not valid utf-8")

    # Doesn't raise.
    report = v3_to_v4.run(tmp_path, apply_changes=False)
    assert report.scanned_files == 1
    assert report.applied == []
