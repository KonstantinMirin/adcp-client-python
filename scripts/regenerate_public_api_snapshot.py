#!/usr/bin/env python3
"""Regenerate tests/fixtures/public_api_snapshot.json.

Run after an intentional addition or removal in `adcp.__all__` or
`adcp.types.__all__`. The snapshot backs
`tests/test_public_api.py::test_public_api_surface_matches_snapshot`.

Usage:
    python scripts/regenerate_public_api_snapshot.py
"""

from __future__ import annotations

import json
from pathlib import Path

import adcp
import adcp.types

SNAPSHOT_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "public_api_snapshot.json"


def main() -> None:
    snapshot = {
        "adcp": sorted(adcp.__all__),
        "adcp.types": sorted(adcp.types.__all__),
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(f"Wrote {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
