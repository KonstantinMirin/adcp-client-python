"""Types the AdCP ``signals`` schemas declare.

Importing from the domain says which variant you mean, where the flat
``adcp.types`` namespace can only bind one class per name:

    from adcp.types.domains.signals import <Type>

A type this domain declares in more than one schema carries the defining
file in its name (``CreativeFromListCreativesResponse``); everything else
keeps the name codegen gave it.

Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.
Generation date: 2026-10-03 04:37:13 UTC
"""

# ruff: noqa: E501, I001
from __future__ import annotations

from adcp.types.generated_poc.signals.activate_signal_request import Action, ActivateSignalRequest
from adcp.types.generated_poc.signals.activate_signal_response import (
    ActivateSignalResponse,
    ActivateSignalResponse1,
    ActivateSignalResponse2,
)
from adcp.types.generated_poc.signals.get_signals_async_response_submitted import (
    GetSignalsSubmitted,
)
from adcp.types.generated_poc.signals.get_signals_async_response_working import GetSignalsWorking
from adcp.types.generated_poc.signals.get_signals_request import (
    Country as CountryFromGetSignalsRequest,
    DiscoveryMode,
    Field1,
    GetSignalsRequest,
)
from adcp.types.generated_poc.signals.get_signals_response import (
    AiActRiskClass,
    Art9Basis,
    CacheScope,
    Channel,
    Country as CountryFromGetSignalsResponse,
    DataSource,
    DataSubjectRights,
    GetSignalsResponse,
    IncompleteItem,
    MatchKey,
    Method,
    Methodology,
    Modeling,
    Onboarder,
    ParentMatchBehavior,
    PreOnboardingPrecisionLevel,
    Range,
    RefreshCadence,
    Right,
    Scope,
    SeedSource,
    Signal,
    Taxonomy,
    TrainingDataJurisdiction,
    Type,
    Value,
    ValueMapping,
)

# Explicit exports
__all__ = [
    "Action",
    "ActivateSignalRequest",
    "ActivateSignalResponse",
    "ActivateSignalResponse1",
    "ActivateSignalResponse2",
    "AiActRiskClass",
    "Art9Basis",
    "CacheScope",
    "Channel",
    "CountryFromGetSignalsRequest",
    "CountryFromGetSignalsResponse",
    "DataSource",
    "DataSubjectRights",
    "DiscoveryMode",
    "Field1",
    "GetSignalsRequest",
    "GetSignalsResponse",
    "GetSignalsSubmitted",
    "GetSignalsWorking",
    "IncompleteItem",
    "MatchKey",
    "Method",
    "Methodology",
    "Modeling",
    "Onboarder",
    "ParentMatchBehavior",
    "PreOnboardingPrecisionLevel",
    "Range",
    "RefreshCadence",
    "Right",
    "Scope",
    "SeedSource",
    "Signal",
    "Taxonomy",
    "TrainingDataJurisdiction",
    "Type",
    "Value",
    "ValueMapping",
]
