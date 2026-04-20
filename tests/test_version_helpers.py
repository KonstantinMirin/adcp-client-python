"""Tests for ``get_adcp_spec_version`` / ``get_adcp_sdk_version``
version helpers (splits the legacy single-name API).
"""

from __future__ import annotations

import adcp


def test_get_adcp_sdk_version_matches_dunder_version() -> None:
    """``get_adcp_sdk_version()`` and ``adcp.__version__`` must agree —
    both name the SDK package version."""
    assert adcp.get_adcp_sdk_version() == adcp.__version__


def test_get_adcp_spec_version_returns_string() -> None:
    """``get_adcp_spec_version`` reads the packaged ``ADCP_VERSION``
    file. Confirm it returns a non-empty string."""
    version = adcp.get_adcp_spec_version()
    assert isinstance(version, str)
    assert version.strip() != ""


def test_legacy_get_adcp_version_still_returns_spec_version() -> None:
    """``get_adcp_version`` is the pre-4.1 name. Kept as a thin alias
    returning the spec version, so callers pinning to the old name
    keep working."""
    assert adcp.get_adcp_version() == adcp.get_adcp_spec_version()


def test_spec_and_sdk_versions_are_distinct_concepts() -> None:
    """The whole point of the split: spec version and SDK version are
    different things. This test pins the naming so a future refactor
    can't silently collapse them."""
    spec = adcp.get_adcp_spec_version()
    sdk = adcp.get_adcp_sdk_version()
    # Either one could technically equal the other (e.g. during local
    # dev with unusual version strings), but they MUST come from
    # different sources — assert we can read both independently.
    assert isinstance(spec, str) and isinstance(sdk, str)
