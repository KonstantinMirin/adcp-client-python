"""Types the AdCP ``manifest_schema`` schemas declare.

Importing from the domain says which variant you mean, where the flat
``adcp.types`` namespace can only bind one class per name:

    from adcp.types.domains.manifest_schema import <Type>

A type this domain declares in more than one schema carries the defining
file in its name (``CreativeFromListCreativesResponse``); everything else
keeps the name codegen gave it.

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-03 04:37:13 UTC
"""

# ruff: noqa: E501, I001
from __future__ import annotations

from adcp.types.generated_poc.manifest_schema import (
    AdcpManifest,
    DefaultUnknownRecovery,
    ErrorCodePolicy,
    ErrorCodes,
    IdempotencyRequirement,
    LegacyFallback,
    LegacyFallback1,
    LegacyFallback2,
    Mode,
    Protocol,
    SchemaPath,
    Specialisms,
    TaskResultResolution,
    ToolName,
    Tools,
)

# Explicit exports
__all__ = [
    "AdcpManifest",
    "DefaultUnknownRecovery",
    "ErrorCodePolicy",
    "ErrorCodes",
    "IdempotencyRequirement",
    "LegacyFallback",
    "LegacyFallback1",
    "LegacyFallback2",
    "Mode",
    "Protocol",
    "SchemaPath",
    "Specialisms",
    "TaskResultResolution",
    "ToolName",
    "Tools",
]
