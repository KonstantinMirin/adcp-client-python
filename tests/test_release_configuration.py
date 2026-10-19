"""Release automation owns the SDK version and the SDK 9 beta channel."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.normalize_pyproject_prerelease import pep440_prerelease

ROOT = Path(__file__).parent.parent


def test_worktree_version_matches_normalized_release_manifest() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    project_section = re.search(
        r'^\[project\]\s*$.*?^version\s*=\s*"([^"]+)"',
        pyproject,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert project_section is not None
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())
    expected = {pep440_prerelease(manifest["."])}
    # On the next draft-spec line, pyproject.toml carries next's own release
    # version once next has released; until then it still carries main's.
    next_manifest = ROOT / ".release-please-manifest.next.json"
    if next_manifest.exists():
        expected.add(pep440_prerelease(json.loads(next_manifest.read_text())["."]))
    assert project_section.group(1) in expected


def test_release_please_keeps_sdk_9_on_the_beta_channel() -> None:
    """The breaking SDK 9 surface must remain beta until the reviewed GA exit.

    The adopting commit's ``Release-As: 9.0.0-beta.1`` footer selects the
    first beta. Subsequent fixes increment the beta, and GitHub releases
    are marked as prereleases rather than presented as stable releases.
    """
    config = json.loads((ROOT / "release-please-config.json").read_text())
    package = config["packages"]["."]
    assert package["versioning"] == "prerelease"
    assert package["prerelease-type"] == "beta"
    assert package["prerelease"] is True


def test_release_please_keeps_next_on_the_alpha_channel() -> None:
    """The next draft-spec line releases only ``10.0.0-alpha.N`` pre-releases.

    The adopting commit on next ends with ``Release-As: 10.0.0-alpha.0``;
    later commits increment the alpha number. next's workflow uses its own
    config and manifest so that merging main into next never changes them.
    """
    config_path = ROOT / "release-please-config.next.json"
    if not config_path.exists():
        return  # main does not carry next's release configuration.
    config = json.loads(config_path.read_text())
    package = config["packages"]["."]
    assert package["versioning"] == "prerelease"
    assert package["prerelease-type"] == "alpha"
    assert package["prerelease"] is True
    assert package["changelog-path"] != "CHANGELOG.md"
    workflow = (ROOT / ".github/workflows/release-please-next.yml").read_text()
    assert "target-branch: next" in workflow
    assert "config-file: release-please-config.next.json" in workflow
    assert "manifest-file: .release-please-manifest.next.json" in workflow
    assert "--target-branch next" in workflow
    assert "release-publish.yml --ref next" in workflow
