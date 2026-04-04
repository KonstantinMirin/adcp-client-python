"""Base classes for ADCP server implementations.

Defines the ADCPHandler base class and utilities for building ADCP-compliant agents.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from adcp.types import Error


@dataclass
class ToolContext:
    """Context passed to tool handlers.

    Contains metadata about the current request that may be useful
    for logging, authorization, or other cross-cutting concerns.
    """

    request_id: str | None = None
    caller_identity: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NotImplementedResponse(BaseModel):
    """Standard response for operations not supported by this handler."""

    supported: bool = False
    reason: str = "This operation is not supported by this agent"
    error: Error | None = None


def not_supported(
    reason: str = "This operation is not supported by this agent",
) -> NotImplementedResponse:
    """Create a standard 'not supported' response.

    Use this to return from operations that your agent does not implement.

    Args:
        reason: Human-readable explanation of why the operation is not supported

    Returns:
        NotImplementedResponse with supported=False
    """
    return NotImplementedResponse(
        supported=False,
        reason=reason,
        error=Error(
            code="NOT_SUPPORTED",
            message=reason,
        ),
    )


class ADCPHandler(ABC):
    """Base class for ADCP operation handlers.

    Subclass this to implement ADCP operations. All operations have default
    implementations that return 'not supported', allowing you to implement
    only the operations your agent supports.

    For protocol-specific handlers, use:
    - ContentStandardsHandler: For content standards agents
    - SponsoredIntelligenceHandler: For sponsored intelligence agents
    - GovernanceHandler: For governance agents
    """

    _agent_type: str = "this agent"

    def _not_supported(self, operation: str) -> NotImplementedResponse:
        """Create a not-supported response that includes the agent type."""
        return not_supported(f"{operation} is not supported by {self._agent_type}")

    # ========================================================================
    # Core Catalog Operations
    # ========================================================================

    async def get_products(self, params: dict[str, Any], context: ToolContext | None = None) -> Any:
        """Get advertising products.

        Override this to provide product catalog functionality.
        """
        return self._not_supported("get_products")

    async def list_creative_formats(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """List supported creative formats.

        Override this to provide creative format information.
        """
        return self._not_supported("list_creative_formats")

    # ========================================================================
    # Creative Operations
    # ========================================================================

    async def sync_creatives(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Sync creatives.

        Override this to handle creative synchronization.
        """
        return self._not_supported("sync_creatives")

    async def list_creatives(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """List creatives.

        Override this to list synced creatives.
        """
        return self._not_supported("list_creatives")

    async def build_creative(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Build a creative.

        Override this to build creatives from assets.
        """
        return self._not_supported("build_creative")

    async def preview_creative(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Preview a creative rendering.

        Override this to provide creative preview functionality.
        """
        return self._not_supported("preview_creative")

    async def get_creative_delivery(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get creative delivery metrics.

        Override this to provide functionality.
        """
        return self._not_supported("get_creative_delivery")

    # ========================================================================
    # Media Buy Operations
    # ========================================================================

    async def create_media_buy(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Create a media buy.

        Override this to handle media buy creation.
        """
        return self._not_supported("create_media_buy")

    async def update_media_buy(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Update a media buy.

        Override this to handle media buy updates.
        """
        return self._not_supported("update_media_buy")

    async def get_media_buy_delivery(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get media buy delivery metrics.

        Override this to provide delivery reporting.
        """
        return self._not_supported("get_media_buy_delivery")

    async def get_media_buys(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get media buys with status and optional delivery snapshots.

        Override this to provide media buy listing functionality.
        """
        return self._not_supported("get_media_buys")

    # ========================================================================
    # Signal Operations
    # ========================================================================

    async def get_signals(self, params: dict[str, Any], context: ToolContext | None = None) -> Any:
        """Get available signals.

        Override this to provide signal catalog.
        """
        return self._not_supported("get_signals")

    async def activate_signal(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Activate a signal.

        Override this to handle signal activation.
        """
        return self._not_supported("activate_signal")

    # ========================================================================
    # Feedback Operations
    # ========================================================================

    async def provide_performance_feedback(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Provide performance feedback.

        Override this to handle performance feedback ingestion.
        """
        return self._not_supported("provide_performance_feedback")

    # ========================================================================
    # Account Operations
    # ========================================================================

    async def list_accounts(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """List accounts.

        Override this to provide functionality.
        """
        return self._not_supported("list_accounts")

    async def sync_accounts(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Sync accounts.

        Override this to provide functionality.
        """
        return self._not_supported("sync_accounts")

    async def get_account_financials(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get account financials.

        Override this to provide account financial reporting.
        """
        return self._not_supported("get_account_financials")

    async def report_usage(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Report account usage.

        Override this to ingest account usage.
        """
        return self._not_supported("report_usage")

    # ========================================================================
    # Event Operations
    # ========================================================================

    async def log_event(self, params: dict[str, Any], context: ToolContext | None = None) -> Any:
        """Log event.

        Override this to provide functionality.
        """
        return self._not_supported("log_event")

    async def sync_event_sources(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Sync event sources.

        Override this to provide functionality.
        """
        return self._not_supported("sync_event_sources")

    async def sync_audiences(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Sync audiences.

        Override this to provide audience synchronization.
        """
        return self._not_supported("sync_audiences")

    async def sync_catalogs(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Sync catalogs.

        Override this to provide catalog synchronization.
        """
        return self._not_supported("sync_catalogs")

    # ========================================================================
    # V3 Protocol Discovery
    # ========================================================================

    async def get_adcp_capabilities(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get ADCP capabilities.

        Override this to advertise your agent's capabilities.
        """
        return self._not_supported("get_adcp_capabilities")

    # ========================================================================
    # V3 Content Standards Operations
    # ========================================================================

    async def create_content_standards(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Create content standards configuration.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("create_content_standards")

    async def get_content_standards(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get content standards configuration.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("get_content_standards")

    async def list_content_standards(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """List content standards configurations.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("list_content_standards")

    async def update_content_standards(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Update content standards configuration.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("update_content_standards")

    async def calibrate_content(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Calibrate content against standards.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("calibrate_content")

    async def validate_content_delivery(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Validate content delivery against standards.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("validate_content_delivery")

    async def get_media_buy_artifacts(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get artifacts associated with a media buy.

        Override this in ContentStandardsHandler subclasses.
        """
        return self._not_supported("get_media_buy_artifacts")

    # ========================================================================
    # V3 Sponsored Intelligence Operations
    # ========================================================================

    async def si_get_offering(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get sponsored intelligence offering.

        Override this in SponsoredIntelligenceHandler subclasses.
        """
        return self._not_supported("si_get_offering")

    async def si_initiate_session(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Initiate sponsored intelligence session.

        Override this in SponsoredIntelligenceHandler subclasses.
        """
        return self._not_supported("si_initiate_session")

    async def si_send_message(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Send message in sponsored intelligence session.

        Override this in SponsoredIntelligenceHandler subclasses.
        """
        return self._not_supported("si_send_message")

    async def si_terminate_session(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Terminate sponsored intelligence session.

        Override this in SponsoredIntelligenceHandler subclasses.
        """
        return self._not_supported("si_terminate_session")

    # ========================================================================
    # V3 Governance Operations
    # ========================================================================

    async def get_creative_features(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Evaluate governance features for a creative.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("get_creative_features")

    async def sync_plans(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Sync campaign governance plans.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("sync_plans")

    async def check_governance(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Check an action against campaign governance.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("check_governance")

    async def report_plan_outcome(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Report the outcome of a governed action.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("report_plan_outcome")

    async def get_plan_audit_logs(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Retrieve governance audit logs for plans.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("get_plan_audit_logs")

    async def create_property_list(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Create a property list for governance filtering.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("create_property_list")

    async def get_property_list(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get a property list with optional resolution.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("get_property_list")

    async def list_property_lists(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """List property lists.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("list_property_lists")

    async def update_property_list(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Update a property list.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("update_property_list")

    async def delete_property_list(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Delete a property list.

        Override this in GovernanceHandler subclasses.
        """
        return self._not_supported("delete_property_list")

    # ========================================================================
    # V3 TMP Operations
    # ========================================================================

    async def context_match(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Match ad context to buyer packages.

        Override this to provide TMP context matching.
        """
        return self._not_supported("context_match")

    async def identity_match(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Match user identity for package eligibility.

        Override this to provide TMP identity matching.
        """
        return self._not_supported("identity_match")

    # ========================================================================
    # V3 Brand Rights Operations
    # ========================================================================

    async def get_brand_identity(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get brand identity information.

        Override this in BrandHandler subclasses.
        """
        return self._not_supported("get_brand_identity")

    async def get_rights(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Get available rights for licensing.

        Override this in BrandHandler subclasses.
        """
        return self._not_supported("get_rights")

    async def acquire_rights(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Acquire rights for brand content usage.

        Override this in BrandHandler subclasses.
        """
        return self._not_supported("acquire_rights")

    # ========================================================================
    # V3 Compliance Operations
    # ========================================================================

    async def comply_test_controller(
        self, params: dict[str, Any], context: ToolContext | None = None
    ) -> Any:
        """Compliance test controller (sandbox only).

        Override this in ComplianceHandler subclasses.
        """
        return self._not_supported("comply_test_controller")
