"""Public types grouped by the AdCP schema domain that declares them.

The AdCP bundle is organised by domain — ``core/``, ``creative/``,
``media_buy/`` and the rest — and codegen mirrors that layout. These modules
re-export each domain faithfully, so a type name several domains define is
unambiguous by module path rather than by a mangled name:

    from adcp.types.domains.creative import QuerySummary
    from adcp.types.domains.core import QuerySummary

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-03 04:37:13 UTC
"""

from __future__ import annotations

#: Every domain module in this package.
DOMAINS = (
    "a2ui",
    "aao",
    "account",
    "adagents",
    "brand",
    "collection",
    "compliance",
    "content_standards",
    "core",
    "creative",
    "enums",
    "error_details",
    "extensions",
    "formats",
    "governance",
    "manifest",
    "manifest_schema",
    "media_buy",
    "pricing_options",
    "property",
    "protocol",
    "registries",
    "signals",
    "sponsored_intelligence",
    "trusted_match",
)

__all__ = ["DOMAINS"]
