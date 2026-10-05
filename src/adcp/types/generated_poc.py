"""Tombstone for the removed private generated tree.

The generator used to write its models to ``adcp.types.generated_poc`` and the
public surface re-exported them. It now writes them to ``adcp.types.domains``
directly: the module that defines a class is the module adopters import it
from, so there is no private tree left to re-export.

Every module stem moved unchanged, so the migration is a prefix rename::

    -from adcp.types.generated_poc.media_buy.package_request import PackageRequest
    +from adcp.types.domains.media_buy.package_request import PackageRequest

``adcp.types`` remains the first choice; reach for a domain path only for a name
the flat namespace cannot bind, as ``docs/type-surface.md`` describes.

This file exists so that rename arrives as a sentence instead of a bare
``ModuleNotFoundError``. It is removed in v10.
"""

from __future__ import annotations

raise ImportError(
    "adcp.types.generated_poc was removed in adcp 9.0. The generated models are "
    "defined at adcp.types.domains.<domain>.<schema> — the same module stems, so "
    "rewrite the prefix: adcp.types.generated_poc. -> adcp.types.domains. . Prefer "
    "the flat adcp.types surface where the name you need is bound there. "
    "See docs/type-surface.md."
)
