"""Registry API types generated from OpenAPI spec.

DO NOT EDIT — regenerate with:
    python scripts/generate_registry_types.py

Source: schemas/registry-openapi.yaml
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import Field

from adcp.types.base import RegistryBaseModel

__all__ = [
    "KellerType",
    "BrandSource",
    "RegistryApiError",
    "BrandRegistrySource",
    "BrandRegistryItem",
    "ActivityRevision",
    "BrandActivity",
    "PropertyActivity",
    "PropertySource",
    "AuthorizedAgent",
    "AgentContact",
    "PropertyIdentifier",
    "PropertyRegistrySource",
    "PropertyRegistryItem",
    "ValidationResult",
    "AgentType",
    "AgentProtocol",
    "AgentDetailedContact",
    "AgentSource",
    "AgentMember",
    "AgentDiscoveredFrom",
    "AgentHealth",
    "AgentStats",
    "AgentTool",
    "AgentStandardOperations",
    "AgentCreativeCapabilities",
    "AgentCapabilities",
    "ComplianceStatus",
    "AgentLifecycleStage",
    "AgentCompliance",
    "PropertySummary",
    "PublisherDiscoveredFrom",
    "FederatedPublisher",
    "DomainAuthorizedAgent",
    "SalesAgentClaim",
    "DomainLookupResult",
    "PublisherPropertySelector",
    "PolicyCategory",
    "PolicyEnforcement",
    "PolicySourceType",
    "PolicyReviewStatus",
    "PolicySummary",
    "PolicyExemplarPass",
    "PolicyExemplarFail",
    "PolicyExemplars",
    "Policy",
    "PolicyRevision",
    "PolicyHistory",
    "ResolvedBrand",
    "ResolvedPropertyEntry",
    "ResolvedProperty",
    "FederatedAgentWithDetails",
    "FeedEvent",
    "FeedPage",
]


class KellerType(Enum):
    master = "master"
    sub_brand = "sub_brand"
    endorsed = "endorsed"
    independent = "independent"


class BrandSource(Enum):
    brand_json = "brand_json"
    community = "community"
    enriched = "enriched"


class RegistryApiError(RegistryBaseModel):
    error: str


class BrandRegistrySource(Enum):
    hosted = "hosted"
    brand_json = "brand_json"
    community = "community"
    enriched = "enriched"


class BrandRegistryItem(RegistryBaseModel):
    domain: Annotated[str, Field(examples=["acmecorp.com"])]
    brand_name: Annotated[str | None, Field(examples=["Acme Corp"])] = None
    source: BrandRegistrySource
    has_manifest: bool
    verified: bool
    house_domain: str | None = None
    keller_type: KellerType | None = None


class ActivityRevision(RegistryBaseModel):
    revision_number: Annotated[int, Field(examples=[3])]
    editor_name: Annotated[str, Field(examples=["Pinnacle Media"])]
    edit_summary: Annotated[str, Field(examples=["Updated logo and brand colors"])]
    source: Annotated[
        str | None,
        Field(
            description="BrandSource type of the record at the time of this revision (brand_json, enriched, community)"
        ),
    ] = None
    is_rollback: bool
    rolled_back_to: Annotated[
        int | None,
        Field(
            description="ActivityRevision number that was restored; only present when is_rollback is true"
        ),
    ] = None
    created_at: Annotated[str, Field(examples=["2026-03-01T12:34:56Z"])]


class BrandActivity(RegistryBaseModel):
    domain: Annotated[str, Field(examples=["acmecorp.com"])]
    total: Annotated[int, Field(examples=[3])]
    revisions: list[ActivityRevision]


class PropertyActivity(RegistryBaseModel):
    domain: Annotated[str, Field(examples=["examplepub.com"])]
    total: Annotated[int, Field(examples=[3])]
    revisions: list[ActivityRevision]


class PropertySource(Enum):
    adagents_json = "adagents_json"
    hosted = "hosted"
    discovered = "discovered"


class AuthorizedAgent(RegistryBaseModel):
    url: str
    authorized_for: str | None = None


class AgentContact(RegistryBaseModel):
    name: str | None = None
    email: str | None = None


class PropertyIdentifier(RegistryBaseModel):
    type: Annotated[str, Field(examples=["domain"])]
    value: Annotated[str, Field(examples=["examplepub.com"])]


class PropertyRegistrySource(Enum):
    adagents_json = "adagents_json"
    hosted = "hosted"
    community = "community"
    discovered = "discovered"
    enriched = "enriched"


class PropertyRegistryItem(RegistryBaseModel):
    domain: Annotated[str, Field(examples=["examplepub.com"])]
    source: PropertyRegistrySource
    property_count: int
    agent_count: int
    verified: bool


class ValidationResult(RegistryBaseModel):
    valid: bool
    domain: str | None = None
    url: str | None = None
    errors: list[str | dict[str, Any]] | None = None
    warnings: list[str | dict[str, Any]] | None = None
    status_code: int | None = None
    raw_data: dict[str, Any] | None = None


class AgentType(Enum):
    creative = "creative"
    signals = "signals"
    sales = "sales"
    governance = "governance"
    si = "si"
    unknown = "unknown"


class AgentProtocol(Enum):
    mcp = "mcp"
    a2a = "a2a"


class AgentDetailedContact(RegistryBaseModel):
    name: str
    email: str
    website: str


class AgentSource(Enum):
    registered = "registered"
    discovered = "discovered"


class AgentMember(RegistryBaseModel):
    slug: str | None = None
    display_name: str | None = None


class AgentDiscoveredFrom(RegistryBaseModel):
    publisher_domain: str | None = None
    authorized_for: str | None = None


class AgentHealth(RegistryBaseModel):
    online: bool
    checked_at: str
    response_time_ms: float | None = None
    tools_count: int | None = None
    resources_count: int | None = None
    error: str | None = None


class AgentStats(RegistryBaseModel):
    property_count: int | None = None
    publisher_count: int | None = None
    publishers: list[str] | None = None
    creative_formats: int | None = None


class AgentTool(RegistryBaseModel):
    name: str
    description: str


class AgentStandardOperations(RegistryBaseModel):
    can_search_inventory: bool
    can_get_availability: bool
    can_reserve_inventory: bool
    can_get_pricing: bool
    can_create_order: bool
    can_list_properties: bool


class AgentCreativeCapabilities(RegistryBaseModel):
    formats_supported: list[str]
    can_generate: bool
    can_validate: bool
    can_preview: bool


class AgentCapabilities(RegistryBaseModel):
    tools_count: int
    tools: list[AgentTool] | None = None
    standard_operations: AgentStandardOperations | None = None
    creative_capabilities: AgentCreativeCapabilities | None = None


class ComplianceStatus(Enum):
    passing = "passing"
    degraded = "degraded"
    failing = "failing"
    unknown = "unknown"


class AgentLifecycleStage(Enum):
    development = "development"
    testing = "testing"
    production = "production"
    deprecated = "deprecated"


class AgentCompliance(RegistryBaseModel):
    status: ComplianceStatus
    lifecycle_stage: AgentLifecycleStage
    tracks: Annotated[dict[str, str], Field(examples=[{"core": "pass", "products": "fail"}])]
    streak_days: int
    last_checked_at: str | None
    headline: str | None


class PropertySummary(RegistryBaseModel):
    total_count: int
    count_by_type: dict[str, int]
    tags: list[str]
    publisher_count: int


class PublisherDiscoveredFrom(RegistryBaseModel):
    agent_url: str | None = None


class FederatedPublisher(RegistryBaseModel):
    domain: str
    source: AgentSource | None = None
    member: AgentMember | None = None
    agent_count: int | None = None
    last_validated: str | None = None
    discovered_from: PublisherDiscoveredFrom | None = None
    has_valid_adagents: bool | None = None
    discovered_at: str | None = None


class DomainAuthorizedAgent(RegistryBaseModel):
    url: str
    authorized_for: str | None = None
    source: AgentSource | None = None
    member: AgentMember | None = None


class SalesAgentClaim(RegistryBaseModel):
    url: str
    source: AgentSource | None = None
    member: AgentMember | None = None


class DomainLookupResult(RegistryBaseModel):
    domain: Annotated[str, Field(examples=["examplepub.com"])]
    authorized_agents: list[DomainAuthorizedAgent]
    sales_agents_claiming: list[SalesAgentClaim]


class PublisherPropertySelector(RegistryBaseModel):
    publisher_domain: Annotated[str | None, Field(examples=["examplepub.com"])] = None
    property_types: list[str] | None = None
    property_ids: list[str] | None = None
    tags: list[str] | None = None


class PolicyCategory(Enum):
    regulation = "regulation"
    standard = "standard"


class PolicyEnforcement(Enum):
    must = "must"
    should = "should"
    may = "may"


class PolicySourceType(Enum):
    registry = "registry"
    community = "community"


class PolicyReviewStatus(Enum):
    pending = "pending"
    approved = "approved"


class PolicySummary(RegistryBaseModel):
    policy_id: Annotated[str, Field(examples=["gdpr_consent"])]
    version: Annotated[str, Field(examples=["1.0.0"])]
    name: Annotated[str, Field(examples=["GDPR Consent Requirements"])]
    description: Annotated[
        str | None, Field(examples=["Requirements for valid consent under GDPR"])
    ]
    category: PolicyCategory
    enforcement: PolicyEnforcement
    jurisdictions: Annotated[list[str], Field(examples=[["EU", "EEA"]])]
    region_aliases: Annotated[dict[str, list[str]], Field(examples=[{"EU": ["DE", "FR", "IT"]}])]
    policy_categories: Annotated[
        list[str], Field(examples=[["age_restricted", "pharmaceutical_advertising"]])
    ]
    channels: Annotated[list[str] | None, Field(examples=[["display", "video"]])]
    governance_domains: Annotated[list[str], Field(examples=[["campaign", "creative"]])]
    effective_date: Annotated[str | None, Field(examples=["2025-05-25"])]
    sunset_date: str | None
    source_url: Annotated[
        str | None, Field(examples=["https://eur-lex.europa.eu/eli/reg/2016/679/oj"])
    ]
    source_name: Annotated[str | None, Field(examples=["EUR-Lex"])]
    source_type: PolicySourceType
    review_status: PolicyReviewStatus
    created_at: Annotated[str, Field(examples=["2026-03-01T12:00:00.000Z"])]
    updated_at: Annotated[str, Field(examples=["2026-03-01T12:00:00.000Z"])]


class PolicyExemplarPass(RegistryBaseModel):
    scenario: Annotated[str, Field(examples=["Ad for alcohol shown during children's programming"])]
    explanation: Annotated[
        str, Field(examples=["Violates watershed timing rules for alcohol advertising"])
    ]


class PolicyExemplarFail(RegistryBaseModel):
    scenario: Annotated[str, Field(examples=["Ad for alcohol shown during children's programming"])]
    explanation: Annotated[
        str, Field(examples=["Violates watershed timing rules for alcohol advertising"])
    ]


class PolicyExemplars(RegistryBaseModel):
    pass_: Annotated[list[PolicyExemplarPass] | None, Field(alias="pass")] = None
    fail: list[PolicyExemplarFail] | None = None


class Policy(RegistryBaseModel):
    policy_id: Annotated[str, Field(examples=["gdpr_consent"])]
    version: Annotated[str, Field(examples=["1.0.0"])]
    name: Annotated[str, Field(examples=["GDPR Consent Requirements"])]
    description: Annotated[
        str | None, Field(examples=["Requirements for valid consent under GDPR"])
    ]
    category: PolicyCategory
    enforcement: PolicyEnforcement
    jurisdictions: Annotated[list[str], Field(examples=[["EU", "EEA"]])]
    region_aliases: Annotated[dict[str, list[str]], Field(examples=[{"EU": ["DE", "FR", "IT"]}])]
    policy_categories: Annotated[
        list[str], Field(examples=[["age_restricted", "pharmaceutical_advertising"]])
    ]
    channels: Annotated[list[str] | None, Field(examples=[["display", "video"]])]
    governance_domains: Annotated[list[str], Field(examples=[["campaign", "creative"]])]
    effective_date: Annotated[str | None, Field(examples=["2025-05-25"])]
    sunset_date: str | None
    source_url: Annotated[
        str | None, Field(examples=["https://eur-lex.europa.eu/eli/reg/2016/679/oj"])
    ]
    source_name: Annotated[str | None, Field(examples=["EUR-Lex"])]
    policy: Annotated[
        str,
        Field(
            examples=[
                "Data subjects must provide freely given, specific, informed and unambiguous consent..."
            ]
        ),
    ]
    guidance: str | None
    exemplars: PolicyExemplars | None
    ext: dict[str, Any] | None
    source_type: PolicySourceType
    review_status: PolicyReviewStatus
    created_at: Annotated[str, Field(examples=["2026-03-01T12:00:00.000Z"])]
    updated_at: Annotated[str, Field(examples=["2026-03-01T12:00:00.000Z"])]


class PolicyRevision(RegistryBaseModel):
    revision_number: Annotated[int, Field(examples=[2])]
    editor_name: Annotated[str, Field(examples=["Pinnacle Media"])]
    edit_summary: Annotated[str, Field(examples=["Clarified consent requirements for minors"])]
    is_rollback: bool
    rolled_back_to: Annotated[
        int | None,
        Field(
            description="ActivityRevision number that was restored; only present when is_rollback is true"
        ),
    ] = None
    created_at: Annotated[str, Field(examples=["2026-03-01T12:34:56Z"])]


class PolicyHistory(RegistryBaseModel):
    policy_id: Annotated[str, Field(examples=["gdpr_consent"])]
    total: Annotated[int, Field(examples=[3])]
    revisions: list[PolicyRevision]


class ResolvedBrand(RegistryBaseModel):
    canonical_id: Annotated[str, Field(examples=["acmecorp.com"])]
    canonical_domain: Annotated[str, Field(examples=["acmecorp.com"])]
    brand_name: Annotated[str, Field(examples=["Acme Corp"])]
    names: list[dict[str, str]] | None = None
    keller_type: KellerType | None = None
    parent_brand: str | None = None
    house_domain: str | None = None
    house_name: str | None = None
    brand_agent_url: str | None = None
    brand_manifest: dict[str, Any] | None = None
    source: BrandSource


class ResolvedPropertyEntry(RegistryBaseModel):
    id: str | None = None
    type: str | None = None
    name: str | None = None
    identifiers: list[PropertyIdentifier] | None = None
    tags: list[str] | None = None


class ResolvedProperty(RegistryBaseModel):
    publisher_domain: Annotated[str, Field(examples=["examplepub.com"])]
    source: PropertySource
    authorized_agents: list[AuthorizedAgent] | None = None
    properties: list[ResolvedPropertyEntry] | None = None
    contact: AgentContact | None = None
    verified: bool


class FederatedAgentWithDetails(RegistryBaseModel):
    url: str
    name: str
    type: AgentType
    protocol: AgentProtocol | None = None
    description: str | None = None
    mcp_endpoint: str | None = None
    contact: AgentDetailedContact | None = None
    added_date: str | None = None
    source: AgentSource | None = None
    member: AgentMember | None = None
    discovered_from: AgentDiscoveredFrom | None = None
    health: AgentHealth | None = None
    stats: AgentStats | None = None
    capabilities: AgentCapabilities | None = None
    compliance: AgentCompliance | None = None
    publisher_domains: list[str] | None = None
    property_summary: PropertySummary | None = None


# --- Feed types (inline response schemas, not in components/schemas) ---


class FeedEvent(RegistryBaseModel):
    """Single event from the registry change feed."""

    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    actor: str
    created_at: str


class FeedPage(RegistryBaseModel):
    """Page of events from the registry change feed."""

    events: list[FeedEvent] = Field(default_factory=list)
    cursor: str | None = None
    has_more: bool
