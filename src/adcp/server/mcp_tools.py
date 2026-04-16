"""MCP server integration helpers.

Provides utilities for registering ADCP handlers with MCP servers.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from adcp.server.base import ADCPHandler, ToolContext

logger = logging.getLogger(__name__)

# Tool definitions for all ADCP operations
ADCP_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    # Core Catalog Operations
    {
        "name": "get_products",
        "description": "Get advertising products from the catalog",
        "inputSchema": {
            "type": "object",
            "properties": {
                "context": {"type": "object"},
                "filters": {"type": "object"},
                "pagination": {"type": "object"},
                "fields": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "list_creative_formats",
        "description": "List supported creative formats",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "format_id": {"type": "string"},
                "pagination": {"type": "object"},
            },
        },
    },
    # Creative Operations
    {
        "name": "sync_creatives",
        "description": "Sync creatives to the agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "creatives": {"type": "array"},
            },
            "required": ["creatives"],
        },
    },
    {
        "name": "list_creatives",
        "description": "List synced creatives",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filters": {"type": "object"},
                "pagination": {"type": "object"},
                "fields": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "build_creative",
        "description": "Build a creative from assets",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format_id": {"type": "string"},
                "assets": {"type": "array"},
            },
            "required": ["format_id", "assets"],
        },
    },
    {
        "name": "preview_creative",
        "description": "Preview a creative rendering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format_id": {"type": "string"},
                "creative_manifest": {"type": "object"},
                "output_format": {"type": "string"},
            },
        },
    },
    {
        "name": "get_creative_delivery",
        "description": "Get creative delivery metrics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "media_buy_ids": {"type": "array", "items": {"type": "string"}},
                "creative_ids": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    # Media Buy Operations
    {
        "name": "create_media_buy",
        "description": "Create a media buy from products",
        "inputSchema": {
            "type": "object",
            "properties": {
                "packages": {"type": "array"},
                "proposal_id": {"type": "string"},
            },
        },
    },
    {
        "name": "update_media_buy",
        "description": "Update an existing media buy",
        "inputSchema": {
            "type": "object",
            "properties": {
                "media_buy_id": {"type": "string"},
                "packages": {"type": "array"},
            },
            "required": ["media_buy_id"],
        },
    },
    {
        "name": "get_media_buy_delivery",
        "description": "Get delivery metrics for a media buy",
        "inputSchema": {
            "type": "object",
            "properties": {
                "media_buy_id": {"type": "string"},
                "metrics": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["media_buy_id"],
        },
    },
    {
        "name": "get_media_buys",
        "description": "List media buys with status and optional delivery snapshots",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "object"},
                "media_buy_ids": {"type": "array", "items": {"type": "string"}},
                "status_filter": {"type": "array", "items": {"type": "string"}},
                "pagination": {"type": "object"},
            },
        },
    },
    # Signal Operations
    {
        "name": "get_signals",
        "description": "Get available signals",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filters": {"type": "object"},
                "pagination": {"type": "object"},
            },
        },
    },
    {
        "name": "activate_signal",
        "description": "Activate a signal for use",
        "inputSchema": {
            "type": "object",
            "properties": {
                "signal_id": {"type": "string"},
                "activation_key": {"type": "string"},
            },
            "required": ["signal_id"],
        },
    },
    # Account Operations
    {
        "name": "list_accounts",
        "description": "List accounts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filters": {"type": "object"},
                "pagination": {"type": "object"},
            },
        },
    },
    {
        "name": "sync_accounts",
        "description": "Sync accounts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "accounts": {"type": "array"},
            },
            "required": ["accounts"],
        },
    },
    {
        "name": "get_account_financials",
        "description": "Get account financials",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "object"},
                "date_range": {"type": "object"},
            },
        },
    },
    {
        "name": "report_usage",
        "description": "Report usage for billing or metering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "object"},
                "usage": {"type": "array"},
            },
            "required": ["usage"],
        },
    },
    # Event Operations
    {
        "name": "log_event",
        "description": "Log event",
        "inputSchema": {
            "type": "object",
            "properties": {
                "events": {"type": "array"},
            },
            "required": ["events"],
        },
    },
    {
        "name": "sync_event_sources",
        "description": "Sync event sources",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_sources": {"type": "array"},
            },
            "required": ["event_sources"],
        },
    },
    {
        "name": "sync_audiences",
        "description": "Sync audiences",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "object"},
                "audiences": {"type": "array"},
            },
            "required": ["audiences"],
        },
    },
    {
        "name": "sync_catalogs",
        "description": "Sync catalogs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account": {"type": "object"},
                "catalogs": {"type": "array"},
            },
            "required": ["catalogs"],
        },
    },
    # Governance Sync
    {
        "name": "sync_governance",
        "description": "Register governance agents for accounts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "accounts": {"type": "array"},
            },
            "required": ["accounts"],
        },
    },
    # Feedback Operations
    {
        "name": "provide_performance_feedback",
        "description": "Provide performance feedback",
        "inputSchema": {
            "type": "object",
            "properties": {
                "media_buy_id": {"type": "string"},
                "feedback": {"type": "object"},
            },
            "required": ["media_buy_id", "feedback"],
        },
    },
    # V3 Protocol Discovery
    {
        "name": "get_adcp_capabilities",
        "description": "Get ADCP capabilities supported by this agent",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    # V3 Content Standards
    {
        "name": "create_content_standards",
        "description": "Create content standards configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "rules": {"type": "array"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_content_standards",
        "description": "Get content standards configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content_standards_id": {"type": "string"},
            },
            "required": ["content_standards_id"],
        },
    },
    {
        "name": "list_content_standards",
        "description": "List content standards configurations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pagination": {"type": "object"},
            },
        },
    },
    {
        "name": "update_content_standards",
        "description": "Update content standards configuration",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content_standards_id": {"type": "string"},
                "rules": {"type": "array"},
            },
            "required": ["content_standards_id"],
        },
    },
    {
        "name": "calibrate_content",
        "description": "Calibrate content against standards",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content_standards_id": {"type": "string"},
                "content": {"type": "object"},
            },
            "required": ["content_standards_id", "content"],
        },
    },
    {
        "name": "validate_content_delivery",
        "description": "Validate content delivery against standards",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content_standards_id": {"type": "string"},
                "delivery": {"type": "object"},
            },
            "required": ["content_standards_id", "delivery"],
        },
    },
    {
        "name": "get_media_buy_artifacts",
        "description": "Get artifacts associated with a media buy",
        "inputSchema": {
            "type": "object",
            "properties": {
                "media_buy_id": {"type": "string"},
            },
            "required": ["media_buy_id"],
        },
    },
    # V3 Governance
    {
        "name": "get_creative_features",
        "description": "Evaluate governance features for a creative",
        "inputSchema": {
            "type": "object",
            "properties": {
                "creative_manifest": {"type": "object"},
                "account": {"type": "object"},
                "context": {"type": "object"},
            },
            "required": ["creative_manifest"],
        },
    },
    {
        "name": "sync_plans",
        "description": "Sync campaign governance plans",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plans": {"type": "array"},
            },
            "required": ["plans"],
        },
    },
    {
        "name": "check_governance",
        "description": "Check an action against campaign governance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "media_buy_id": {"type": "string"},
                "phase": {"type": "string"},
                "caller": {"type": "string"},
                "tool": {"type": "string"},
                "payload": {"type": "object"},
                "governance_context": {"type": "object"},
            },
            "required": ["plan_id", "caller"],
        },
    },
    {
        "name": "report_plan_outcome",
        "description": "Report the outcome of a governed action",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "outcome": {"type": "string"},
                "check_id": {"type": "string"},
                "seller_response": {"type": "object"},
                "delivery": {"type": "object"},
                "error": {"type": "object"},
            },
            "required": ["plan_id", "outcome"],
        },
    },
    {
        "name": "get_plan_audit_logs",
        "description": "Retrieve governance audit logs for one or more plans",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_ids": {"type": "array", "items": {"type": "string"}},
                "portfolio_plan_ids": {"type": "array", "items": {"type": "string"}},
                "include_entries": {"type": "boolean"},
            },
        },
    },
    # V3 Sponsored Intelligence
    {
        "name": "si_get_offering",
        "description": "Get sponsored intelligence offering",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "si_initiate_session",
        "description": "Initiate sponsored intelligence session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "budget": {"type": "number"},
            },
        },
    },
    {
        "name": "si_send_message",
        "description": "Send message in sponsored intelligence session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["session_id", "message"],
        },
    },
    {
        "name": "si_terminate_session",
        "description": "Terminate sponsored intelligence session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
            },
            "required": ["session_id"],
        },
    },
    # V3 Governance (Property Lists)
    {
        "name": "create_property_list",
        "description": "Create a property list for governance filtering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "base_properties": {"type": "array"},
                "filters": {"type": "object"},
                "brand_manifest": {"type": "object"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_property_list",
        "description": "Get a property list with optional resolution",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string"},
                "resolve": {"type": "boolean"},
                "pagination": {"type": "object"},
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "list_property_lists",
        "description": "List property lists",
        "inputSchema": {
            "type": "object",
            "properties": {
                "principal": {"type": "string"},
                "pagination": {"type": "object"},
            },
        },
    },
    {
        "name": "update_property_list",
        "description": "Update a property list",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "filters": {"type": "object"},
                "brand_manifest": {"type": "object"},
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "delete_property_list",
        "description": "Delete a property list",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string"},
            },
            "required": ["list_id"],
        },
    },
    # V3 Governance (Collection Lists)
    {
        "name": "create_collection_list",
        "description": "Create a collection list for governance filtering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "base_collections": {"type": "array"},
                "filters": {"type": "object"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_collection_list",
        "description": "Get a collection list with optional resolution",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string"},
                "resolve": {"type": "boolean"},
                "pagination": {"type": "object"},
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "list_collection_lists",
        "description": "List collection lists",
        "inputSchema": {
            "type": "object",
            "properties": {
                "principal": {"type": "string"},
                "pagination": {"type": "object"},
            },
        },
    },
    {
        "name": "update_collection_list",
        "description": "Update a collection list",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "filters": {"type": "object"},
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "delete_collection_list",
        "description": "Delete a collection list",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string"},
            },
            "required": ["list_id"],
        },
    },
    # V3 TMP
    {
        "name": "context_match",
        "description": (
            "Evaluate publisher placement context against buyer packages"
            " and return matching offers. Called at ad-request time."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_rid": {"type": "string"},
                "placement_id": {"type": "string"},
                "property_type": {"type": "string"},
                "request_id": {"type": "string"},
                "type": {"type": "string"},
                "artifact_refs": {"type": "array"},
                "context_signals": {"type": "object"},
                "geo": {"type": "object"},
                "package_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["property_rid", "placement_id", "property_type", "request_id", "type"],
        },
    },
    {
        "name": "identity_match",
        "description": (
            "Evaluate user identity token against active packages"
            " for eligibility. Requires consent in regulated regions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "type": {"type": "string"},
                "user_token": {"type": "string"},
                "uid_type": {"type": "string"},
                "package_ids": {"type": "array", "items": {"type": "string"}},
                "consent": {"type": "object"},
            },
            "required": ["request_id", "type", "user_token", "uid_type", "package_ids"],
        },
    },
    # V3 Brand Rights
    {
        "name": "get_brand_identity",
        "description": "Get brand identity information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "string"}},
                "use_case": {"type": "string"},
            },
            "required": ["brand_id"],
        },
    },
    {
        "name": "get_rights",
        "description": "Get available rights for licensing",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "uses": {"type": "array", "items": {"type": "string"}},
                "brand_id": {"type": "string"},
                "right_type": {"type": "string"},
                "countries": {"type": "array", "items": {"type": "string"}},
                "include_excluded": {"type": "boolean"},
                "pagination": {"type": "object"},
            },
            "required": ["query", "uses"],
        },
    },
    {
        "name": "acquire_rights",
        "description": (
            "Acquire rights for brand content usage."
            " Binding contractual action with financial obligations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "rights_id": {"type": "string"},
                "pricing_option_id": {"type": "string"},
                "buyer": {"type": "object"},
                "campaign": {"type": "object"},
                "revocation_webhook": {"type": "object"},
                "idempotency_key": {"type": "string"},
            },
            "required": [
                "rights_id",
                "pricing_option_id",
                "buyer",
                "campaign",
                "revocation_webhook",
            ],
        },
    },
    # V3 Compliance
    {
        "name": "comply_test_controller",
        "description": (
            "Compliance test controller. Sandbox only,"
            " not for production use."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "enum": [
                        "list_scenarios",
                        "force_creative_status",
                        "force_account_status",
                        "force_media_buy_status",
                        "force_session_status",
                        "simulate_delivery",
                        "simulate_budget_spend",
                    ],
                },
                "params": {"type": "object"},
                "context": {"type": "object"},
            },
            "required": ["scenario"],
        },
    },
]


# Protocol discovery tool included for all handler types
_PROTOCOL_TOOLS: set[str] = {"get_adcp_capabilities"}

# Tools specific to each specialized handler type
_HANDLER_TOOLS: dict[str, set[str]] = {
    "GovernanceHandler": {
        "get_creative_features",
        "sync_plans",
        "check_governance",
        "report_plan_outcome",
        "get_plan_audit_logs",
        "create_property_list",
        "get_property_list",
        "list_property_lists",
        "update_property_list",
        "delete_property_list",
        "create_collection_list",
        "get_collection_list",
        "list_collection_lists",
        "update_collection_list",
        "delete_collection_list",
    },
    "ContentStandardsHandler": {
        "create_content_standards",
        "get_content_standards",
        "list_content_standards",
        "update_content_standards",
        "calibrate_content",
        "validate_content_delivery",
        "get_media_buy_artifacts",
    },
    "SponsoredIntelligenceHandler": {
        "si_get_offering",
        "si_initiate_session",
        "si_send_message",
        "si_terminate_session",
    },
    "TmpHandler": {
        "context_match",
        "identity_match",
    },
    "BrandHandler": {
        "get_brand_identity",
        "get_rights",
        "acquire_rights",
    },
    "ComplianceHandler": {
        "comply_test_controller",
    },
    "ADCPHandler": {tool["name"] for tool in ADCP_TOOL_DEFINITIONS},
}

# Validate that all handler tool names reference real tools
_ALL_TOOL_NAMES = {t["name"] for t in ADCP_TOOL_DEFINITIONS}
for _handler_name, _tools in _HANDLER_TOOLS.items():
    _unknown = _tools - _ALL_TOOL_NAMES
    assert not _unknown, f"{_handler_name} references unknown tools: {_unknown}"


# ============================================================================
# Pydantic schema generation — spec-accurate input schemas
# ============================================================================

def _generate_pydantic_schemas() -> dict[str, dict[str, Any]]:
    """Generate JSON schemas from Pydantic request models.

    Maps tool names to their corresponding request Pydantic types,
    then generates JSON Schema via model_json_schema(). This produces
    spec-accurate schemas with proper field types, descriptions,
    required fields, and nested definitions.

    Falls back to hand-crafted schemas for tools without a matching
    Pydantic request type.
    """
    try:
        from pydantic import TypeAdapter

        from adcp.types import (
            AcquireRightsRequest,
            ActivateSignalRequest,
            BuildCreativeRequest,
            CalibrateContentRequest,
            CheckGovernanceRequest,
            ComplyTestControllerRequest,
            ContextMatchRequest,
            CreateCollectionListRequest,
            CreateContentStandardsRequest,
            CreateMediaBuyRequest,
            CreatePropertyListRequest,
            DeleteCollectionListRequest,
            DeletePropertyListRequest,
            GetAccountFinancialsRequest,
            GetAdcpCapabilitiesRequest,
            GetBrandIdentityRequest,
            GetCollectionListRequest,
            GetContentStandardsRequest,
            GetCreativeDeliveryRequest,
            GetCreativeFeaturesRequest,
            GetMediaBuyArtifactsRequest,
            GetMediaBuyDeliveryRequest,
            GetMediaBuysRequest,
            GetPlanAuditLogsRequest,
            GetProductsRequest,
            GetPropertyListRequest,
            GetRightsRequest,
            GetSignalsRequest,
            IdentityMatchRequest,
            ListAccountsRequest,
            ListCollectionListsRequest,
            ListContentStandardsRequest,
            ListCreativeFormatsRequest,
            ListCreativesRequest,
            ListPropertyListsRequest,
            LogEventRequest,
            PreviewCreativeRequest,
            ProvidePerformanceFeedbackRequest,
            ReportPlanOutcomeRequest,
            ReportUsageRequest,
            SiGetOfferingRequest,
            SiInitiateSessionRequest,
            SiSendMessageRequest,
            SiTerminateSessionRequest,
            SyncAccountsRequest,
            SyncAudiencesRequest,
            SyncCatalogsRequest,
            SyncCreativesRequest,
            SyncEventSourcesRequest,
            SyncPlansRequest,
            UpdateCollectionListRequest,
            UpdateContentStandardsRequest,
            UpdateMediaBuyRequest,
            UpdatePropertyListRequest,
            ValidateContentDeliveryRequest,
        )
    except ImportError:
        return {}

    # Map tool names to their Pydantic request types
    _tool_to_request: dict[str, Any] = {
        # Catalog
        "get_products": GetProductsRequest,
        "list_creative_formats": ListCreativeFormatsRequest,
        # Creative
        "sync_creatives": SyncCreativesRequest,
        "list_creatives": ListCreativesRequest,
        "build_creative": BuildCreativeRequest,
        "preview_creative": PreviewCreativeRequest,
        "get_creative_delivery": GetCreativeDeliveryRequest,
        # Media Buy
        "create_media_buy": CreateMediaBuyRequest,
        "update_media_buy": UpdateMediaBuyRequest,
        "get_media_buy_delivery": GetMediaBuyDeliveryRequest,
        "get_media_buys": GetMediaBuysRequest,
        # Signals
        "get_signals": GetSignalsRequest,
        "activate_signal": ActivateSignalRequest,
        # Account
        "list_accounts": ListAccountsRequest,
        "sync_accounts": SyncAccountsRequest,
        "get_account_financials": GetAccountFinancialsRequest,
        "report_usage": ReportUsageRequest,
        # Events & Catalogs
        "log_event": LogEventRequest,
        "sync_event_sources": SyncEventSourcesRequest,
        "sync_audiences": SyncAudiencesRequest,
        "sync_catalogs": SyncCatalogsRequest,
        # Feedback
        "provide_performance_feedback": ProvidePerformanceFeedbackRequest,
        # Protocol Discovery
        "get_adcp_capabilities": GetAdcpCapabilitiesRequest,
        # Compliance
        "comply_test_controller": ComplyTestControllerRequest,
        # Content Standards
        "create_content_standards": CreateContentStandardsRequest,
        "get_content_standards": GetContentStandardsRequest,
        "list_content_standards": ListContentStandardsRequest,
        "update_content_standards": UpdateContentStandardsRequest,
        "calibrate_content": CalibrateContentRequest,
        "validate_content_delivery": ValidateContentDeliveryRequest,
        "get_media_buy_artifacts": GetMediaBuyArtifactsRequest,
        # Governance
        "get_creative_features": GetCreativeFeaturesRequest,
        "sync_plans": SyncPlansRequest,
        "check_governance": CheckGovernanceRequest,
        "report_plan_outcome": ReportPlanOutcomeRequest,
        "get_plan_audit_logs": GetPlanAuditLogsRequest,
        # Property Lists
        "create_property_list": CreatePropertyListRequest,
        "get_property_list": GetPropertyListRequest,
        "list_property_lists": ListPropertyListsRequest,
        "update_property_list": UpdatePropertyListRequest,
        "delete_property_list": DeletePropertyListRequest,
        # Collection Lists
        "create_collection_list": CreateCollectionListRequest,
        "get_collection_list": GetCollectionListRequest,
        "list_collection_lists": ListCollectionListsRequest,
        "update_collection_list": UpdateCollectionListRequest,
        "delete_collection_list": DeleteCollectionListRequest,
        # Sponsored Intelligence
        "si_get_offering": SiGetOfferingRequest,
        "si_initiate_session": SiInitiateSessionRequest,
        "si_send_message": SiSendMessageRequest,
        "si_terminate_session": SiTerminateSessionRequest,
        # Brand
        "get_brand_identity": GetBrandIdentityRequest,
        "get_rights": GetRightsRequest,
        "acquire_rights": AcquireRightsRequest,
        # TMP
        "context_match": ContextMatchRequest,
        "identity_match": IdentityMatchRequest,
    }

    schemas: dict[str, dict[str, Any]] = {}
    for tool_name, request_type in _tool_to_request.items():
        try:
            # Handle union types (e.g. PreviewCreativeRequest, ComplyTestControllerRequest)
            if isinstance(request_type, type) and hasattr(request_type, "model_json_schema"):
                schema = request_type.model_json_schema()
            else:
                # Union types need TypeAdapter
                adapter = TypeAdapter(request_type)
                schema = adapter.json_schema()

            schema.pop("title", None)

            # Union types produce anyOf with $ref at root — these can't
            # be represented as flat MCP schemas. Keep hand-crafted.
            if "anyOf" in schema or "$ref" in schema:
                continue

            # Only strip $defs if no $ref references exist in the schema.
            # If nested properties use $ref, keep $defs so references resolve.
            schema_str = json.dumps(schema)
            if '"$ref"' not in schema_str:
                schema.pop("$defs", None)

            schemas[tool_name] = schema
        except Exception:
            logger.debug(
                "Pydantic schema generation failed for %s, using hand-crafted schema",
                tool_name,
                exc_info=True,
            )

    return schemas


# Generate schemas once at import time
_PYDANTIC_SCHEMAS = _generate_pydantic_schemas()


def _apply_pydantic_schemas() -> None:
    """Replace hand-crafted inputSchemas with Pydantic-generated ones."""
    for tool_def in ADCP_TOOL_DEFINITIONS:
        name = tool_def["name"]
        if name in _PYDANTIC_SCHEMAS:
            tool_def["inputSchema"] = _PYDANTIC_SCHEMAS[name]


_apply_pydantic_schemas()


def get_tools_for_handler(handler: ADCPHandler | type[ADCPHandler]) -> list[dict[str, Any]]:
    """Return tool definitions filtered by handler type.

    Walks the MRO to find the matching handler base class, so subclasses
    (e.g. MyGovernanceAgent(GovernanceHandler)) get the correct tool set.
    ADCPHandler gets all tools. Unknown handlers get only protocol discovery
    (minimum privilege).

    Args:
        handler: The handler instance or class

    Returns:
        Filtered list of tool definitions
    """
    cls = handler if isinstance(handler, type) else type(handler)
    for base in cls.__mro__:
        if base.__name__ in _HANDLER_TOOLS:
            allowed = _HANDLER_TOOLS[base.__name__] | _PROTOCOL_TOOLS
            return [tool for tool in ADCP_TOOL_DEFINITIONS if tool["name"] in allowed]

    return [tool for tool in ADCP_TOOL_DEFINITIONS if tool["name"] in _PROTOCOL_TOOLS]


def create_tool_caller(
    handler: ADCPHandler,
    method_name: str,
) -> Callable[[dict[str, Any]], Any]:
    """Create a tool caller function for an ADCP handler method.

    Args:
        handler: The ADCP handler instance
        method_name: Name of the method to call

    Returns:
        Async callable that invokes the handler method
    """
    method = getattr(handler, method_name)

    async def call_tool(params: dict[str, Any]) -> Any:
        context = ToolContext()
        result = await method(params, context)
        # Convert Pydantic models to JSON-safe dicts for MCP serialization
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json", exclude_none=True)
        return result

    return call_tool


class MCPToolSet:
    """Collection of MCP tools from an ADCP handler.

    Provides tool definitions and handlers for registering with an MCP server.
    """

    def __init__(self, handler: ADCPHandler):
        """Create tool set from handler.

        Args:
            handler: ADCP handler instance
        """
        self.handler = handler
        self._filtered_definitions = get_tools_for_handler(handler)
        self._tools: dict[str, Callable[[dict[str, Any]], Any]] = {}

        # Create tool callers only for filtered tools
        for tool_def in self._filtered_definitions:
            name = tool_def["name"]
            self._tools[name] = create_tool_caller(handler, name)

    @property
    def tool_definitions(self) -> list[dict[str, Any]]:
        """Get MCP tool definitions filtered by handler type."""
        return list(self._filtered_definitions)

    async def call_tool(self, name: str, params: dict[str, Any]) -> Any:
        """Call a tool by name.

        Args:
            name: Tool name
            params: Tool parameters

        Returns:
            Tool result

        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return await self._tools[name](params)

    def get_tool_names(self) -> list[str]:
        """Get list of available tool names."""
        return list(self._tools.keys())


def create_mcp_tools(handler: ADCPHandler) -> MCPToolSet:
    """Create MCP tools from an ADCP handler.

    This is the main entry point for MCP server integration.

    Example with mcp library:
        from mcp.server import Server
        from adcp.server import ContentStandardsHandler, create_mcp_tools

        class MyHandler(ContentStandardsHandler):
            # ... implement methods

        handler = MyHandler()
        tools = create_mcp_tools(handler)

        server = Server("my-content-agent")

        @server.list_tools()
        async def list_tools():
            return tools.tool_definitions

        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            return await tools.call_tool(name, arguments)

    Args:
        handler: ADCP handler instance

    Returns:
        MCPToolSet with tool definitions and handlers
    """
    return MCPToolSet(handler)
