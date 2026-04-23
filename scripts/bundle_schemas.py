#!/usr/bin/env python3
"""Mirror ``schemas/cache/`` into ``src/adcp/_schemas/`` so the packaged
wheel ships the JSON schemas that ``adcp.validation.schema_loader`` needs.

The canonical copy lives in ``schemas/cache/`` (populated by
``scripts/sync_schemas.py``). That tree is outside the package, so
setuptools can't include it via ``package-data``. This script copies it
into the package right before build / regenerate, keeping both trees in
lockstep so editable installs and wheel builds both resolve schemas.

Runs as part of ``make regenerate-schemas`` after ``sync_schemas.py`` and
before ``generate_types.py``.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SRC_CACHE = REPO_ROOT / "schemas" / "cache"
DEST = REPO_ROOT / "src" / "adcp" / "_schemas"


def main() -> int:
    if not SRC_CACHE.is_dir():
        print(f"error: {SRC_CACHE} does not exist — run sync_schemas.py first", file=sys.stderr)
        return 1

    if DEST.exists():
        shutil.rmtree(DEST)

    shutil.copytree(
        SRC_CACHE,
        DEST,
        ignore=shutil.ignore_patterns("*.md", ".hashes.json"),
    )

    count = sum(1 for _ in DEST.rglob("*.json"))
    print(f"Bundled {count} schemas into {DEST.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
