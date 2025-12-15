"""Webhook creation and signing utilities for AdCP agents."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from a2a.types import (
    Artifact,
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

from adcp.types import GeneratedTaskStatus
from adcp.types.generated_poc.core.async_response_data import AdcpAsyncResponseData


def create_mcp_webhook_payload(
    task_id: str,
    task_type: str,
    status: GeneratedTaskStatus,
    timestamp: datetime | None = None,
    result: AdcpAsyncResponseData | dict[str, Any] | None = None,
    operation_id: str | None = None,
    message: str | None = None,
    context_id: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """
    Create MCP webhook payload dictionary.

    This function helps agent implementations construct properly formatted
    webhook payloads for sending to clients.

    Args:
        task_id: Unique identifier for the task
        task_type: Type of AdCP operation (e.g., "get_products", "create_media_buy")
        status: Current task status
        timestamp: When the webhook was generated (defaults to current UTC time)
        result: Task-specific payload (AdCP response data)
        operation_id: Publisher-defined operation identifier (deprecated from payload,
            should be in URL routing, but included for backward compatibility)
        message: Human-readable summary of task state
        context_id: Session/conversation identifier
        domain: AdCP domain this task belongs to

    Returns:
        Dictionary matching McpWebhookPayload schema, ready to be sent as JSON

    Examples:
        Create a completed webhook with results:
        >>> from adcp.webhooks import create_mcp_webhook_payload
        >>> from adcp.types import GeneratedTaskStatus
        >>>
        >>> payload = create_mcp_webhook_payload(
        ...     task_id="task_123",
        ...     task_type="get_products",
        ...     status=GeneratedTaskStatus.completed,
        ...     result={"products": [...]},
        ...     message="Found 5 products"
        ... )

        Create a failed webhook with error:
        >>> payload = create_mcp_webhook_payload(
        ...     task_id="task_456",
        ...     task_type="create_media_buy",
        ...     status=GeneratedTaskStatus.failed,
        ...     result={"errors": [{"code": "INVALID_INPUT", "message": "..."}]},
        ...     message="Validation failed"
        ... )

        Create a working status update:
        >>> payload = create_mcp_webhook_payload(
        ...     task_id="task_789",
        ...     task_type="sync_creatives",
        ...     status=GeneratedTaskStatus.working,
        ...     message="Processing 3 of 10 creatives"
        ... )
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # Convert status enum to string value
    status_value = status.value if hasattr(status, "value") else str(status)

    # Build payload matching McpWebhookPayload schema
    payload: dict[str, Any] = {
        "task_id": task_id,
        "task_type": task_type,
        "status": status_value,
        "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
    }

    # Add optional fields only if provided
    if result is not None:
        payload["result"] = result

    if operation_id is not None:
        payload["operation_id"] = operation_id

    if message is not None:
        payload["message"] = message

    if context_id is not None:
        payload["context_id"] = context_id

    if domain is not None:
        payload["domain"] = domain

    return payload


def get_adcp_signed_headers_for_webhook(
    headers: dict[str, Any], secret: str, timestamp: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Generate AdCP-compliant signed headers for webhook delivery.

    This function creates a cryptographic signature that proves the webhook
    came from an authorized agent and protects against replay attacks by
    including a timestamp in the signed message.

    The function adds two headers to the provided headers dict:
    - X-AdCP-Signature: HMAC-SHA256 signature in format "sha256=<hex_digest>"
    - X-AdCP-Timestamp: ISO 8601 timestamp used in signature generation

    The signing algorithm:
    1. Constructs message as "{timestamp}.{json_payload}"
    2. JSON-serializes payload with compact separators (no sorted keys for performance)
    3. UTF-8 encodes the message
    4. HMAC-SHA256 signs with the shared secret
    5. Hex-encodes and prefixes with "sha256="

    Args:
        headers: Existing headers dictionary to add signature headers to
        secret: Shared secret key for HMAC signing
        timestamp: ISO 8601 timestamp string (e.g., "2025-01-15T10:00:00Z")
        payload: Webhook payload dictionary (will be JSON-serialized)

    Returns:
        The modified headers dictionary with signature headers added

    Examples:
        Sign and send an MCP webhook:
        >>> from adcp.webhooks import create_mcp_webhook_payload, get_adcp_signed_headers_for_webhook
        >>> from datetime import datetime, timezone
        >>>
        >>> payload = create_mcp_webhook_payload(
        ...     task_id="task_123",
        ...     task_type="get_products",
        ...     status="completed",
        ...     result={"products": [...]}
        ... )
        >>> headers = {"Content-Type": "application/json"}
        >>> timestamp = datetime.now(timezone.utc).isoformat()
        >>> signed_headers = get_adcp_signed_headers_for_webhook(
        ...     headers, secret="my-webhook-secret", timestamp=timestamp, payload=payload
        ... )
        >>>
        >>> # Send webhook with signed headers
        >>> import httpx
        >>> response = await httpx.post(
        ...     webhook_url,
        ...     json=payload,
        ...     headers=signed_headers
        ... )

        Headers will contain:
        >>> print(signed_headers)
        {
            "Content-Type": "application/json",
            "X-AdCP-Signature": "sha256=a1b2c3...",
            "X-AdCP-Timestamp": "2025-01-15T10:00:00Z"
        }
    """
    # Serialize payload to JSON with consistent formatting
    # Note: sort_keys=False for performance (key order doesn't affect signature)
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=False).encode(
        "utf-8"
    )

    # Construct signed message: timestamp.payload
    # Including timestamp prevents replay attacks
    signed_message = f"{timestamp}.{payload_bytes.decode('utf-8')}"

    # Generate HMAC-SHA256 signature over timestamp + payload
    signature_hex = hmac.new(
        secret.encode("utf-8"),
        signed_message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Add AdCP-compliant signature headers
    headers["X-AdCP-Signature"] = f"sha256={signature_hex}"
    headers["X-AdCP-Timestamp"] = timestamp

    return headers


def create_a2a_webhook_payload(
    task_id: str,
    status: GeneratedTaskStatus,
    context_id: str,
    timestamp: datetime | None = None,
    result: AdcpAsyncResponseData | dict[str, Any] | None = None,
    message: str | None = None,
) -> Task | TaskStatusUpdateEvent:
    """
    Create A2A webhook payload (Task or TaskStatusUpdateEvent).

    Per A2A specification:
    - Terminated statuses (completed, failed): Returns Task with artifacts[].parts[]
    - Intermediate statuses (working, input-required, submitted): Returns TaskStatusUpdateEvent
      with status.message.parts[]

    This function helps agent implementations construct properly formatted A2A webhook
    payloads for sending to clients.

    Args:
        task_id: Unique identifier for the task
        status: Current task status
        context_id: Session/conversation identifier (required by A2A protocol)
        timestamp: When the webhook was generated (defaults to current UTC time)
        result: Task-specific payload (AdCP response data)
        message: Human-readable summary of task state

    Returns:
        Task object for terminated statuses, TaskStatusUpdateEvent for intermediate statuses

    Examples:
        Create a completed Task webhook:
        >>> from adcp.webhooks import create_a2a_webhook_payload
        >>> from adcp.types import GeneratedTaskStatus
        >>>
        >>> task = create_a2a_webhook_payload(
        ...     task_id="task_123",
        ...     status=GeneratedTaskStatus.completed,
        ...     result={"products": [...]},
        ...     message="Found 5 products"
        ... )
        >>> # task is a Task object with artifacts containing the result

        Create a working status update:
        >>> event = create_a2a_webhook_payload(
        ...     task_id="task_456",
        ...     status=GeneratedTaskStatus.working,
        ...     message="Processing 3 of 10 items"
        ... )
        >>> # event is a TaskStatusUpdateEvent with status.message

        Send A2A webhook via HTTP POST:
        >>> import httpx
        >>> from a2a.types import Task
        >>>
        >>> payload = create_a2a_webhook_payload(...)
        >>> # Serialize to dict for JSON
        >>> if isinstance(payload, Task):
        ...     payload_dict = payload.model_dump(mode='json')
        ... else:
        ...     payload_dict = payload.model_dump(mode='json')
        >>>
        >>> response = await httpx.post(webhook_url, json=payload_dict)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # Convert datetime to ISO string for A2A protocol
    timestamp_str = timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp

    # Map GeneratedTaskStatus to A2A status state string
    status_value = status.value if hasattr(status, "value") else str(status)

    # Map AdCP status to A2A status state
    # Note: A2A uses "input-required" (hyphenated) while AdCP uses "input_required" (underscore)
    status_mapping = {
        "completed": "completed",
        "failed": "failed",
        "working": "working",
        "submitted": "submitted",
        "input_required": "input-required",
    }
    a2a_status_state = status_mapping.get(status_value, status_value)

    # Build parts for the message/artifact
    parts: list[Part] = []

    # Add DataPart if result provided
    if result is not None:
        # Convert AdcpAsyncResponseData to dict if it's a Pydantic model
        if hasattr(result, "model_dump"):
            result_dict: dict[str, Any] = result.model_dump(mode="json")
        else:
            result_dict = result

        data_part = DataPart(data=result_dict)
        parts.append(Part(root=data_part))

    # Determine if this is a terminated status (Task) or intermediate (TaskStatusUpdateEvent)
    is_terminated = status in [GeneratedTaskStatus.completed, GeneratedTaskStatus.failed]

    # Convert string to TaskState enum
    task_state_enum = TaskState(a2a_status_state)

    if is_terminated:
        # Create Task object with artifacts for terminated statuses
        task_status = TaskStatus(state=task_state_enum, timestamp=timestamp_str)

        # Build artifact with parts
        # Note: Artifact requires artifact_id, use task_id as prefix
        if parts:
            artifact = Artifact(
                artifact_id=f"{task_id}_result",
                parts=parts,
            )
            artifacts = [artifact]
        else:
            artifacts = []

        return Task(
            id=task_id,
            status=task_status,
            artifacts=artifacts,
            context_id=context_id,
        )
    else:
        # Create TaskStatusUpdateEvent with status.message for intermediate statuses
        # Build message with parts
        if parts:
            message_obj = Message(
                message_id=f"{task_id}_msg",
                role=Role.agent,  # Agent is responding
                parts=parts,
            )
        else:
            message_obj = None

        task_status = TaskStatus(state=task_state_enum, timestamp=timestamp_str, message=message_obj)

        return TaskStatusUpdateEvent(
            task_id=task_id,
            status=task_status,
            context_id=context_id,
            final=False,  # Intermediate statuses are not final
        )
