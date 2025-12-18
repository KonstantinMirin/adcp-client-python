"""Tests for webhook handling (MCP and A2A protocols)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from a2a.types import Artifact, DataPart, Message, Part, Role, Task, TaskState, TaskStatus as A2ATaskStatus, TaskStatusUpdateEvent, TextPart

from adcp.client import ADCPClient
from adcp.exceptions import ADCPWebhookSignatureError
from adcp.types.core import AgentConfig, Protocol, TaskStatus
from adcp.webhooks import extract_webhook_result_data


class TestMCPWebhooks:
    """Test MCP webhook handling (HTTP POST with dict payload)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AgentConfig(
            id="test_agent",
            agent_uri="https://test.example.com",
            protocol=Protocol.MCP,
        )
        self.client = ADCPClient(self.config, webhook_secret="test_secret")

    @pytest.mark.asyncio
    async def test_mcp_webhook_completed_success(self):
        """Test MCP webhook with completed status and valid response."""
        payload = {
            "task_id": "task_123",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "media_buy_id": "mb_123",
                "buyer_ref": "ref_123",
                "packages": []
            },
            "message": "Media buy created successfully",
        }

        result = await self.client.handle_webhook(
            payload, task_type="create_media_buy", operation_id="op_123"
        )

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert result.data is not None
        assert result.metadata["task_id"] == "task_123"
        assert result.metadata["operation_id"] == "op_123"

    @pytest.mark.asyncio
    async def test_mcp_webhook_completed_with_errors(self):
        """Test MCP webhook with completed status but has errors in result."""
        payload = {
            "task_id": "task_456",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "errors": [{"code": "NOT_FOUND", "message": "No matching inventory"}]
            },
            "message": "No matching inventory found",
        }

        result = await self.client.handle_webhook(
            payload, task_type="create_media_buy", operation_id="op_456"
        )

        # Completed status
        assert result.status == TaskStatus.COMPLETED
        # Error is in structured data, not in error field
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_mcp_webhook_failed_status(self):
        """Test MCP webhook with failed status."""
        payload = {
            "task_id": "task_789",
            "task_type": "create_media_buy",
            "status": "failed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "errors": [
                    {
                        "code": "INTERNAL_ERROR",
                        "message": "Database connection failed",
                    }
                ]
            },
            "message": "Task failed due to internal error",
        }

        result = await self.client.handle_webhook(
            payload, task_type="create_media_buy", operation_id="op_789"
        )

        assert result.success is False
        assert result.status == TaskStatus.FAILED
        assert result.data is not None  # Errors in structured data
        assert result.metadata["message"] == "Task failed due to internal error"

    @pytest.mark.asyncio
    async def test_mcp_webhook_working_status(self):
        """Test MCP webhook with working status (async in progress)."""
        payload = {
            "task_id": "task_111",
            "task_type": "create_media_buy",
            "status": "working",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": None,  # Working status may have no result yet
            "message": "Processing request...",
        }

        result = await self.client.handle_webhook(
            payload, task_type="create_media_buy", operation_id="op_111"
        )

        assert result.status == TaskStatus.WORKING
        assert result.success is False  # Not completed yet

    @pytest.mark.asyncio
    async def test_mcp_webhook_input_required_status(self):
        """Test MCP webhook with input-required status."""
        payload = {
            "task_id": "task_222",
            "task_type": "create_media_buy",
            "status": "input-required",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "errors": [
                    {
                        "code": "APPROVAL_REQUIRED",
                        "field": "total_budget",
                        "message": "Budget exceeds auto-approval threshold",
                    }
                ],
            },
            "message": "Campaign budget $150K requires VP approval",
            "context_id": "ctx_abc",
        }

        result = await self.client.handle_webhook(
            payload, task_type="create_media_buy", operation_id="op_222"
        )

        assert result.status == TaskStatus.NEEDS_INPUT
        assert result.success is False
        assert result.data is not None  # Errors in structured data
        assert result.metadata["context_id"] == "ctx_abc"

    @pytest.mark.asyncio
    async def test_mcp_webhook_signature_verification_valid(self):
        """Test signature verification with valid HMAC."""
        payload = {
            "task_id": "task_333",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "media_buy_id": "mb_333",
                "buyer_ref": "ref_333",
                "packages": []
            },
        }

        # Generate valid signature using {timestamp}.{payload} format
        # (matching get_adcp_signed_headers_for_webhook)
        import hashlib
        import hmac

        header_timestamp = "2025-01-15T10:00:00Z"
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=False).encode(
            "utf-8"
        )
        signed_message = f"{header_timestamp}.{payload_bytes.decode('utf-8')}"
        signature = hmac.new(
            "test_secret".encode("utf-8"), signed_message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        result = await self.client.handle_webhook(
            payload,
            task_type="create_media_buy",
            operation_id="op_333",
            signature=signature,
            timestamp=header_timestamp,
        )

        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_mcp_webhook_signature_verification_invalid(self):
        """Test signature verification with invalid HMAC."""
        payload = {
            "task_id": "task_444",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "media_buy_id": "mb_444",
                "buyer_ref": "ref_444",
                "packages": []
            },
        }

        with pytest.raises(ADCPWebhookSignatureError):
            await self.client.handle_webhook(
                payload,
                task_type="create_media_buy",
                operation_id="op_444",
                signature="invalid_signature",
                timestamp="2025-01-15T10:00:00Z",
            )

    @pytest.mark.asyncio
    async def test_mcp_webhook_missing_required_fields(self):
        """Test MCP webhook with missing required fields."""
        payload = {
            # Missing task_id and timestamp
            "status": "completed",
            "result": {"products": []},
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            await self.client.handle_webhook(
                payload, task_type="create_media_buy", operation_id="op_555"
            )


class TestA2AWebhooks:
    """Test A2A webhook handling (Task objects from TaskStatusUpdateEvent)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AgentConfig(
            id="test_agent",
            agent_uri="https://test.example.com",
            protocol=Protocol.A2A,
        )
        self.client = ADCPClient(self.config)

    @pytest.mark.asyncio
    async def test_a2a_webhook_completed_success(self):
        """Test A2A Task with completed status and valid AdCP payload."""
        media_buy_data = {
            "media_buy_id": "mb_123",
            "buyer_ref": "ref_123",
            "packages": []
        }

        task = Task(
            id="task_123",
            context_id="ctx_456",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="artifact_123",
                    parts=[
                        Part(root=DataPart(data=media_buy_data)),
                        Part(root=TextPart(text="Media buy created")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_123"
        )

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert result.data is not None
        assert result.metadata["task_id"] == "task_123"
        assert result.metadata["operation_id"] == "op_123"

    @pytest.mark.asyncio
    async def test_a2a_webhook_completed_with_errors(self):
        """Test A2A Task with completed status but errors in AdCP result."""
        error_data = {
            "errors": [{"code": "NOT_FOUND", "message": "No matching inventory"}],
        }

        task = Task(
            id="task_456",
            context_id="ctx_789",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="test_artifact",
                    parts=[Part(root=DataPart(data=error_data))]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_456"
        )

        assert result.status == TaskStatus.COMPLETED
        assert result.data is not None  # Errors in structured data

    @pytest.mark.asyncio
    async def test_a2a_webhook_failed_status(self):
        """Test A2A Task with failed status."""
        error_data = {
            "errors": [
                {
                    "code": "INTERNAL_ERROR",
                    "message": "Database connection failed",
                }
            ]
        }

        task = Task(
            id="task_789",
            context_id="ctx_111",
            status=A2ATaskStatus(state="failed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(

                    artifact_id="test_artifact",

                    parts=[
                        Part(root=DataPart(data=error_data)),
                        Part(root=TextPart(text="Task failed due to internal error")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_789"
        )

        assert result.success is False
        assert result.status == TaskStatus.FAILED
        assert result.data is not None  # Errors in structured data

    @pytest.mark.asyncio
    async def test_a2a_webhook_working_status(self):
        """Test A2A Task with working status (async in progress)."""
        task = Task(
            id="task_111",
            context_id="ctx_222",
            status=A2ATaskStatus(state="working", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="test_artifact",
                    parts=[
                        Part(root=TextPart(text="Processing request...")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_111"
        )

        assert result.status == TaskStatus.WORKING
        assert result.success is False  # Not completed yet

    @pytest.mark.asyncio
    async def test_a2a_webhook_input_required_status(self):
        """Test A2A Task with input-required status."""
        input_data = {
            "reason": "APPROVAL_REQUIRED",
        }

        task = Task(
            id="task_222",
            context_id="ctx_333",
            status=A2ATaskStatus(
                state="input-required", timestamp=datetime.now(timezone.utc).isoformat()
            ),
            artifacts=[
                Artifact(

                    artifact_id="test_artifact",

                    parts=[
                        Part(root=DataPart(data=input_data)),
                        Part(root=TextPart(text="Campaign budget $150K requires VP approval")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_222"
        )

        assert result.status == TaskStatus.NEEDS_INPUT
        assert result.success is False
        assert result.data is not None  # Errors in structured data

    @pytest.mark.asyncio
    async def test_a2a_webhook_missing_artifacts(self):
        """Test A2A Task with no artifacts array."""
        task = Task(
            id="task_333",
            context_id="ctx_444",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[],  # Empty artifacts
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_333"
        )

        # Should still return result, but with None/empty data
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_a2a_webhook_missing_data_part(self):
        """Test A2A Task with no DataPart in artifacts."""
        task = Task(
            id="task_444",
            context_id="ctx_555",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(

                    artifact_id="test_artifact",

                    parts=[
                        Part(root=TextPart(text="Only text, no data"))  # Only TextPart
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_444"
        )

        # Should still return result, but with None/empty data
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_a2a_webhook_malformed_adcp_data(self):
        """Test A2A Task with minimal data that passes basic validation."""
        # Minimal valid data structure
        minimal_data = {"errors": [{"code": "TEST", "message": "Test error"}]}

        task = Task(
            id="task_555",
            context_id="ctx_666",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="test_artifact",
                    parts=[Part(root=DataPart(data=minimal_data))]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_555"
        )

        # Should handle error response
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_a2a_webhook_taskstatusupdateevent_working(self):
        """Test A2A TaskStatusUpdateEvent with working status (correct intermediate payload)."""
        progress_data = {
            "current_step": "fetching_inventory",
            "percentage": 50,
        }

        # Intermediate status uses TaskStatusUpdateEvent, not Task
        event = TaskStatusUpdateEvent(
            task_id="task_777",
            context_id="ctx_888",
            status=A2ATaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=Message(
                    message_id="msg_777",
                    role=Role.agent,
                    parts=[
                        Part(root=DataPart(data=progress_data)),
                        Part(root=TextPart(text="Processing request...")),
                    ],
                ),
            ),
            final=False,
        )

        result = await self.client.handle_webhook(
            event, task_type="create_media_buy", operation_id="op_777"
        )

        assert result.status == TaskStatus.WORKING
        assert result.success is False
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_a2a_webhook_taskstatusupdateevent_input_required(self):
        """Test A2A TaskStatusUpdateEvent with input-required status."""
        input_data = {
            "reason": "APPROVAL_REQUIRED",
        }

        event = TaskStatusUpdateEvent(
            task_id="task_888",
            context_id="ctx_999",
            status=A2ATaskStatus(
                state=TaskState("input-required"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=Message(
                    message_id="msg_888",
                    role=Role.agent,
                    parts=[
                        Part(root=DataPart(data=input_data)),
                        Part(root=TextPart(text="Campaign budget $150K requires VP approval")),
                    ],
                ),
            ),
            final=False,
        )

        result = await self.client.handle_webhook(
            event, task_type="create_media_buy", operation_id="op_888"
        )

        assert result.status == TaskStatus.NEEDS_INPUT
        assert result.success is False
        assert result.data is not None  # Errors in structured data
        assert result.metadata["context_id"] == "ctx_999"

    @pytest.mark.asyncio
    async def test_a2a_webhook_taskstatusupdateevent_submitted(self):
        """Test A2A TaskStatusUpdateEvent with submitted status."""
        event = TaskStatusUpdateEvent(
            task_id="task_999",
            context_id="ctx_000",
            status=A2ATaskStatus(
                state=TaskState.submitted,
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=Message(
                    message_id="msg_999",
                    role=Role.agent,
                    parts=[
                        Part(root=TextPart(text="Task submitted and queued for processing")),
                    ],
                ),
            ),
            final=False,
        )

        result = await self.client.handle_webhook(
            event, task_type="create_media_buy", operation_id="op_999"
        )

        assert result.status == TaskStatus.SUBMITTED
        assert result.success is False
        assert result.metadata["task_id"] == "task_999"

    @pytest.mark.asyncio
    async def test_a2a_webhook_taskstatusupdateevent_no_message(self):
        """Test A2A TaskStatusUpdateEvent with no status.message (edge case)."""
        event = TaskStatusUpdateEvent(
            task_id="task_1010",
            context_id="ctx_1010",
            status=A2ATaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=None,  # No message
            ),
            final=False,
        )

        result = await self.client.handle_webhook(
            event, task_type="create_media_buy", operation_id="op_1010"
        )

        assert result.status == TaskStatus.WORKING
        assert result.data is None  # No data extracted

    @pytest.mark.asyncio
    async def test_a2a_webhook_signature_not_required(self):
        """Verify signature parameter is ignored for A2A webhooks."""
        task = Task(
            id="task_666",
            context_id="ctx_777",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="test_artifact",
                    parts=[
                        Part(root=DataPart(data={
                            "media_buy_id": "mb_666",
                            "buyer_ref": "ref_666",
                            "packages": []
                        }))
                    ]
                )
            ],
        )

        # Signature should be ignored for A2A webhooks
        result = await self.client.handle_webhook(
            task,
            task_type="create_media_buy",
            operation_id="op_666",
            signature="ignored_signature",
        )

        assert result.status == TaskStatus.COMPLETED


class TestUnifiedInterface:
    """Test unified webhook interface across protocols."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mcp_config = AgentConfig(
            id="mcp_agent",
            agent_uri="https://mcp.example.com",
            protocol=Protocol.MCP,
        )
        self.a2a_config = AgentConfig(
            id="a2a_agent",
            agent_uri="https://a2a.example.com",
            protocol=Protocol.A2A,
        )
        self.mcp_client = ADCPClient(self.mcp_config)
        self.a2a_client = ADCPClient(self.a2a_config)

    @pytest.mark.asyncio
    async def test_type_detection_mcp_dict(self):
        """Verify dict payload routes to MCP handler."""
        payload = {
            "task_id": "task_mcp",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "media_buy_id": "mb_mcp",
                "buyer_ref": "ref_mcp",
                "packages": []
            },
        }

        result = await self.mcp_client.handle_webhook(
            payload, task_type="create_media_buy", operation_id="op_mcp"
        )

        assert result.status == TaskStatus.COMPLETED
        assert result.metadata["task_id"] == "task_mcp"

    @pytest.mark.asyncio
    async def test_type_detection_a2a_task(self):
        """Verify Task object routes to A2A handler."""
        task = Task(
            id="task_a2a",
            context_id="ctx_a2a",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="test_artifact",
                    parts=[Part(root=DataPart(data={
                        "media_buy_id": "mb_a2a",
                        "buyer_ref": "ref_a2a",
                        "packages": []
                    }))]
                )
            ],
        )

        result = await self.a2a_client.handle_webhook(
            task, task_type="create_media_buy", operation_id="op_a2a"
        )

        assert result.status == TaskStatus.COMPLETED
        assert result.metadata["task_id"] == "task_a2a"

    @pytest.mark.asyncio
    async def test_type_detection_a2a_taskstatusupdateevent(self):
        """Verify TaskStatusUpdateEvent object routes to A2A handler."""
        event = TaskStatusUpdateEvent(
            task_id="task_event",
            context_id="ctx_event",
            status=A2ATaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=Message(
                    message_id="msg_event",
                    role=Role.agent,
                    parts=[Part(root=TextPart(text="Processing"))],
                ),
            ),
            final=False,
        )

        result = await self.a2a_client.handle_webhook(
            event, task_type="create_media_buy", operation_id="op_event"
        )

        assert result.status == TaskStatus.WORKING
        assert result.metadata["task_id"] == "task_event"

    @pytest.mark.asyncio
    async def test_consistent_result_format(self):
        """Verify MCP and A2A return identical TaskResult structure."""
        media_buy_data = {
            "media_buy_id": "mb_test",
            "buyer_ref": "ref_test",
            "packages": []
        }

        # MCP webhook
        mcp_payload = {
            "task_id": "task_1",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": media_buy_data,
        }

        # A2A webhook with same data
        a2a_task = Task(
            id="task_2",
            context_id="ctx_2",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="test_artifact",
                    parts=[
                        Part(root=DataPart(data=media_buy_data))
                    ]
                )
            ],
        )

        mcp_result = await self.mcp_client.handle_webhook(
            mcp_payload, task_type="create_media_buy", operation_id="op_1"
        )
        a2a_result = await self.a2a_client.handle_webhook(
            a2a_task, task_type="create_media_buy", operation_id="op_2"
        )

        # Both should return same structure
        assert mcp_result.success == a2a_result.success
        assert mcp_result.status == a2a_result.status
        assert mcp_result.data is not None
        assert a2a_result.data is not None


class TestExtractWebhookResultData:
    """Test extract_webhook_result_data utility function."""

    def test_extract_from_mcp_webhook(self):
        """Test extracting result from MCP webhook payload."""
        mcp_payload = {
            "task_id": "task_123",
            "task_type": "create_media_buy",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "media_buy_id": "mb_123",
                "buyer_ref": "ref_123",
                "packages": []
            },
        }

        result = extract_webhook_result_data(mcp_payload)

        assert result is not None
        assert result["media_buy_id"] == "mb_123"
        assert result["buyer_ref"] == "ref_123"
        assert result["packages"] == []

    def test_extract_from_a2a_task_webhook(self):
        """Test extracting result from A2A Task webhook payload."""
        media_buy_data = {
            "media_buy_id": "mb_456",
            "buyer_ref": "ref_456",
            "packages": []
        }

        task = Task(
            id="task_456",
            context_id="ctx_456",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="artifact_456",
                    parts=[
                        Part(root=DataPart(data=media_buy_data)),
                        Part(root=TextPart(text="Media buy created")),
                    ]
                )
            ],
        )

        # Convert to dict (simulating JSON deserialization)
        task_dict = task.model_dump(mode='json')
        result = extract_webhook_result_data(task_dict)

        assert result is not None
        assert result["media_buy_id"] == "mb_456"
        assert result["buyer_ref"] == "ref_456"

    def test_extract_from_a2a_taskstatusupdateevent_webhook(self):
        """Test extracting result from A2A TaskStatusUpdateEvent webhook payload."""
        progress_data = {
            "current_step": "fetching_inventory",
            "percentage": 50,
        }

        event = TaskStatusUpdateEvent(
            task_id="task_777",
            context_id="ctx_777",
            status=A2ATaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=Message(
                    message_id="msg_777",
                    role=Role.agent,
                    parts=[
                        Part(root=DataPart(data=progress_data)),
                        Part(root=TextPart(text="Processing...")),
                    ],
                ),
            ),
            final=False,
        )

        # Convert to dict (simulating JSON deserialization)
        event_dict = event.model_dump(mode='json')
        result = extract_webhook_result_data(event_dict)

        assert result is not None
        assert result["current_step"] == "fetching_inventory"
        assert result["percentage"] == 50

    def test_extract_from_a2a_with_response_wrapper(self):
        """Test extracting result from A2A payload with {"response": {...}} wrapper."""
        wrapped_data = {
            "response": {
                "media_buy_id": "mb_789",
                "buyer_ref": "ref_789",
                "packages": []
            }
        }

        task = Task(
            id="task_789",
            context_id="ctx_789",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="artifact_789",
                    parts=[Part(root=DataPart(data=wrapped_data))]
                )
            ],
        )

        # Convert to dict
        task_dict = task.model_dump(mode='json')
        result = extract_webhook_result_data(task_dict)

        # Should unwrap the response wrapper
        assert result is not None
        assert "response" not in result  # Unwrapped
        assert result["media_buy_id"] == "mb_789"

    def test_extract_from_mcp_with_null_result(self):
        """Test extracting from MCP webhook with None result."""
        mcp_payload = {
            "task_id": "task_111",
            "task_type": "create_media_buy",
            "status": "working",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": None,
        }

        result = extract_webhook_result_data(mcp_payload)

        assert result is None

    def test_extract_from_a2a_with_empty_artifacts(self):
        """Test extracting from A2A Task with empty artifacts array."""
        task = Task(
            id="task_222",
            context_id="ctx_222",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[],
        )

        task_dict = task.model_dump(mode='json')
        result = extract_webhook_result_data(task_dict)

        assert result is None

    def test_extract_from_a2a_with_no_data_part(self):
        """Test extracting from A2A Task with only TextPart (no DataPart)."""
        task = Task(
            id="task_333",
            context_id="ctx_333",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="artifact_333",
                    parts=[Part(root=TextPart(text="Only text, no data"))]
                )
            ],
        )

        task_dict = task.model_dump(mode='json')
        result = extract_webhook_result_data(task_dict)

        assert result is None

    def test_extract_from_a2a_with_multiple_artifacts(self):
        """Test extracting from A2A Task with multiple artifacts (should use last)."""
        old_data = {"media_buy_id": "mb_old"}
        new_data = {"media_buy_id": "mb_new"}

        task = Task(
            id="task_444",
            context_id="ctx_444",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="artifact_old",
                    parts=[Part(root=DataPart(data=old_data))]
                ),
                Artifact(
                    artifact_id="artifact_new",
                    parts=[Part(root=DataPart(data=new_data))]
                ),
            ],
        )

        task_dict = task.model_dump(mode='json')
        result = extract_webhook_result_data(task_dict)

        # Should use last artifact
        assert result is not None
        assert result["media_buy_id"] == "mb_new"

    def test_extract_from_a2a_taskstatusupdateevent_with_no_message(self):
        """Test extracting from A2A TaskStatusUpdateEvent with no status.message."""
        event = TaskStatusUpdateEvent(
            task_id="task_555",
            context_id="ctx_555",
            status=A2ATaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(timezone.utc).isoformat(),
                message=None,
            ),
            final=False,
        )

        event_dict = event.model_dump(mode='json')
        result = extract_webhook_result_data(event_dict)

        assert result is None

    def test_extract_from_mcp_with_missing_result_field(self):
        """Test extracting from MCP webhook without result field."""
        mcp_payload = {
            "task_id": "task_666",
            "task_type": "create_media_buy",
            "status": "working",
            "timestamp": "2025-01-15T10:00:00Z",
            # No result field
        }

        result = extract_webhook_result_data(mcp_payload)

        assert result is None

    def test_extract_from_a2a_with_nested_response_wrapper(self):
        """Test that only single-key {"response": {...}} wrapper is unwrapped."""
        # Data with response wrapper but also other keys (should NOT unwrap)
        data_with_extra_keys = {
            "response": {"media_buy_id": "mb_777"},
            "other_key": "value"
        }

        task = Task(
            id="task_777",
            context_id="ctx_777",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc).isoformat()),
            artifacts=[
                Artifact(
                    artifact_id="artifact_777",
                    parts=[Part(root=DataPart(data=data_with_extra_keys))]
                )
            ],
        )

        task_dict = task.model_dump(mode='json')
        result = extract_webhook_result_data(task_dict)

        # Should NOT unwrap (has multiple keys)
        assert result is not None
        assert "response" in result
        assert "other_key" in result

    def test_extract_from_mcp_with_error_response(self):
        """Test extracting from MCP webhook with error response."""
        mcp_payload = {
            "task_id": "task_888",
            "task_type": "create_media_buy",
            "status": "failed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "errors": [
                    {
                        "code": "INTERNAL_ERROR",
                        "message": "Database connection failed",
                    }
                ]
            },
        }

        result = extract_webhook_result_data(mcp_payload)

        assert result is not None
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == "INTERNAL_ERROR"
