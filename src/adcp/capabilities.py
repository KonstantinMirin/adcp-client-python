"""Feature capability resolution for AdCP.

Shared logic for resolving feature support from a capabilities response.
Used by both the client (buyer-side validation) and server (seller-side validation).
"""

from __future__ import annotations

# GetAdcpCapabilitiesResponse is under TYPE_CHECKING to avoid a circular import
# (adcp.types imports from generated_poc which imports from adcp.types.base).
# This is safe because `from __future__ import annotations` makes all annotations
# strings that are never evaluated at runtime.
from typing import TYPE_CHECKING, Any

from adcp.exceptions import ADCPFeatureUnsupportedError

if TYPE_CHECKING:
    from adcp.types.generated_poc.protocol.get_adcp_capabilities_response import (
        GetAdcpCapabilitiesResponse,
    )

# Mapping from AdCP task names to the media_buy.features flag they require.
# Only includes tasks that exist on ADCPClient and ADCPHandler.
# Other features (audience_targeting, catalog_management, etc.) will be added
# here when their corresponding task methods are implemented.
TASK_FEATURE_MAP: dict[str, str] = {
    "sync_event_sources": "conversion_tracking",
    "log_event": "conversion_tracking",
}

# Derived: feature -> list of handler methods that implement it.
# Used by validate_capabilities() to check that sellers implement what they declare.
FEATURE_HANDLER_MAP: dict[str, list[str]] = {}
for _task, _feature in TASK_FEATURE_MAP.items():
    FEATURE_HANDLER_MAP.setdefault(_feature, []).append(_task)


class FeatureResolver:
    """Resolves feature support from a GetAdcpCapabilitiesResponse.

    Supports multiple feature namespaces:

    - Protocol support: ``"media_buy"`` checks ``supported_protocols``
    - Extension support: ``"ext:scope3"`` checks ``extensions_supported``
    - Targeting: ``"targeting.geo_countries"`` checks
      ``media_buy.execution.targeting``
    - Media buy features: ``"audience_targeting"`` checks
      ``media_buy.features``
    - Signals features: ``"catalog_signals"`` checks
      ``signals.features``
    """

    def __init__(self, capabilities: GetAdcpCapabilitiesResponse) -> None:
        self._caps = capabilities

        # Pre-compute the set of valid protocol names so supports() doesn't
        # need a runtime import on every call.
        from adcp.types.generated_poc.protocol.get_adcp_capabilities_response import (
            SupportedProtocol,
        )

        self._valid_protocols = {p.value for p in SupportedProtocol}
        self._declared_protocols = {p.value for p in capabilities.supported_protocols}

    @property
    def capabilities(self) -> GetAdcpCapabilitiesResponse:
        return self._caps

    def supports(self, feature: str) -> bool:
        """Check if a feature is supported."""
        caps = self._caps

        # Extension check: "ext:scope3"
        if feature.startswith("ext:"):
            ext_name = feature[4:]
            if caps.extensions_supported is None:
                return False
            return any(item.root == ext_name for item in caps.extensions_supported)

        # Targeting check: "targeting.geo_countries"
        if feature.startswith("targeting."):
            attr_name = feature[len("targeting."):]
            if caps.media_buy is None or caps.media_buy.execution is None:
                return False
            targeting = caps.media_buy.execution.targeting
            if targeting is None:
                return False
            if attr_name not in type(targeting).model_fields:
                return False
            val = getattr(targeting, attr_name, None)
            # For bool fields, check truthiness. For object fields (like geo_metros),
            # presence means supported.
            return val is not None and val is not False

        # Protocol check: if the string is a known protocol name, resolve it
        # against supported_protocols and stop — don't fall through to features.
        if feature in self._declared_protocols:
            return True
        if feature in self._valid_protocols:
            return False

        # Media buy features check
        if caps.media_buy is not None and caps.media_buy.features is not None:
            if feature in type(caps.media_buy.features).model_fields:
                val = getattr(caps.media_buy.features, feature, None)
                if val is True:
                    return True

        # Signals features check
        if caps.signals is not None and caps.signals.features is not None:
            if feature in type(caps.signals.features).model_fields:
                val = getattr(caps.signals.features, feature, None)
                if val is True:
                    return True

        return False

    def require(
        self,
        *features: str,
        agent_id: str | None = None,
        agent_uri: str | None = None,
    ) -> None:
        """Assert that all listed features are supported.

        Args:
            *features: Feature identifiers to require.
            agent_id: Optional agent ID for error context.
            agent_uri: Optional agent URI for error context.

        Raises:
            ADCPFeatureUnsupportedError: If any features are not supported.
        """
        unsupported = [f for f in features if not self.supports(f)]
        if not unsupported:
            return

        declared = self.get_declared_features()

        raise ADCPFeatureUnsupportedError(
            unsupported_features=unsupported,
            declared_features=declared,
            agent_id=agent_id,
            agent_uri=agent_uri,
        )

    def get_declared_features(self) -> list[str]:
        """Collect all features the response declares as supported."""
        caps = self._caps
        declared: list[str] = []

        # Supported protocols
        for p in caps.supported_protocols:
            declared.append(p.value)

        # Media buy features
        if caps.media_buy is not None and caps.media_buy.features is not None:
            for field_name in type(caps.media_buy.features).model_fields:
                if getattr(caps.media_buy.features, field_name, None) is True:
                    declared.append(field_name)

        # Signals features
        if caps.signals is not None and caps.signals.features is not None:
            for field_name in type(caps.signals.features).model_fields:
                if getattr(caps.signals.features, field_name, None) is True:
                    declared.append(field_name)

        # Targeting features
        if caps.media_buy is not None and caps.media_buy.execution is not None:
            targeting = caps.media_buy.execution.targeting
            if targeting is not None:
                for field_name in type(targeting).model_fields:
                    val = getattr(targeting, field_name, None)
                    if val is not None and val is not False:
                        declared.append(f"targeting.{field_name}")

        # Extensions
        if caps.extensions_supported is not None:
            for item in caps.extensions_supported:
                declared.append(f"ext:{item.root}")

        return declared


def validate_capabilities(
    handler: Any,
    capabilities: GetAdcpCapabilitiesResponse,
) -> list[str]:
    """Check that a handler implements the methods required by its declared features.

    Compares the features declared in a capabilities response against the handler's
    method implementations. Returns warnings for features that are declared but
    whose corresponding handler methods are not overridden from the base class.

    This is a development-time check — call it at startup to catch misconfigurations.

    Args:
        handler: An ADCPHandler instance (or any object with handler methods).
        capabilities: The capabilities response the handler will serve.

    Returns:
        List of warning strings. Empty if everything is consistent.
    """
    # Late import to avoid circular dependency: server.base imports from adcp.types
    # which may transitively import from this module.
    from adcp.server.base import ADCPHandler

    resolver = FeatureResolver(capabilities)
    warnings: list[str] = []

    for feature, handler_methods in FEATURE_HANDLER_MAP.items():
        if not resolver.supports(feature):
            continue

        for method_name in handler_methods:
            if not hasattr(handler, method_name):
                warnings.append(
                    f"Feature '{feature}' is declared but handler has no "
                    f"'{method_name}' method"
                )
                continue

            # Walk MRO to check if any class between the leaf and ADCPHandler
            # overrides the method (handles mixin / intermediate-class patterns).
            if isinstance(handler, ADCPHandler):
                overridden = any(
                    method_name in cls.__dict__
                    for cls in type(handler).__mro__
                    if cls is not ADCPHandler and not issubclass(ADCPHandler, cls)
                )
                if not overridden:
                    warnings.append(
                        f"Feature '{feature}' is declared but '{method_name}' "
                        f"is not overridden from ADCPHandler"
                    )

    return warnings
