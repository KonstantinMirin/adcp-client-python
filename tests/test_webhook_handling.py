"""Tests for webhook handling (MCP and A2A protocols)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from a2a.types import Artifact, DataPart, Message, Part, Role, Task, TaskStatus as A2ATaskStatus, TextPart

from adcp.client import ADCPClient
from adcp.exceptions import ADCPWebhookSignatureError
from adcp.types import GetProductsResponse
from adcp.types.core import AgentConfig, Protocol, TaskStatus


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
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "products": [
                    {
                        "product_id": "prod_1",
                        "name": "Banner Ad",
                        "description": "Standard banner",
                    }
                ]
            },
            "message": "Found 1 product",
        }

        result = await self.client.handle_webhook(
            payload, task_type="get_products", operation_id="op_123"
        )

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert isinstance(result.data, GetProductsResponse)
        assert len(result.data.products) == 1
        assert result.data.products[0].product_id == "prod_1"
        assert result.metadata["task_id"] == "task_123"
        assert result.metadata["operation_id"] == "op_123"

    @pytest.mark.asyncio
    async def test_mcp_webhook_completed_with_errors(self):
        """Test MCP webhook with completed status but errors in result."""
        payload = {
            "task_id": "task_456",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "products": [],
                "errors": [{"code": "NOT_FOUND", "message": "No products found"}],
            },
            "message": "No products matched criteria",
        }

        result = await self.client.handle_webhook(
            payload, task_type="get_products", operation_id="op_456"
        )

        # Completed with errors is still considered completed
        assert result.status == TaskStatus.COMPLETED
        # But error is extracted from result.errors
        assert result.error is None  # Error extraction happens in fallback path

    @pytest.mark.asyncio
    async def test_mcp_webhook_failed_status(self):
        """Test MCP webhook with failed status."""
        payload = {
            "task_id": "task_789",
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
            payload, task_type="get_products", operation_id="op_789"
        )

        assert result.success is False
        assert result.status == TaskStatus.FAILED
        assert result.error == "Database connection failed"
        assert result.metadata["message"] == "Task failed due to internal error"

    @pytest.mark.asyncio
    async def test_mcp_webhook_working_status(self):
        """Test MCP webhook with working status (async in progress)."""
        payload = {
            "task_id": "task_111",
            "status": "working",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "current_step": "fetching_inventory",
                "percentage": 50,
            },
            "message": "Processing request...",
        }

        result = await self.client.handle_webhook(
            payload, task_type="get_products", operation_id="op_111"
        )

        assert result.status == TaskStatus.WORKING
        assert result.success is False  # Not completed yet
        assert result.data is not None  # Contains progress info

    @pytest.mark.asyncio
    async def test_mcp_webhook_input_required_status(self):
        """Test MCP webhook with input-required status."""
        payload = {
            "task_id": "task_222",
            "status": "input-required",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "reason": "BUDGET_APPROVAL",
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
        assert result.error == "Budget exceeds auto-approval threshold"
        assert result.metadata["context_id"] == "ctx_abc"

    @pytest.mark.asyncio
    async def test_mcp_webhook_signature_verification_valid(self):
        """Test signature verification with valid HMAC."""
        payload = {
            "task_id": "task_333",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {"products": []},
        }

        # Generate valid signature
        import hashlib
        import hmac

        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        signature = hmac.new(
            "test_secret".encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()

        result = await self.client.handle_webhook(
            payload, task_type="get_products", operation_id="op_333", signature=signature
        )

        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_mcp_webhook_signature_verification_invalid(self):
        """Test signature verification with invalid HMAC."""
        payload = {
            "task_id": "task_444",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {"products": []},
        }

        with pytest.raises(ADCPWebhookSignatureError):
            await self.client.handle_webhook(
                payload,
                task_type="get_products",
                operation_id="op_444",
                signature="invalid_signature",
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
                payload, task_type="get_products", operation_id="op_555"
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
        products_data = {
            "products": [
                {
                    "product_id": "prod_1",
                    "name": "Banner Ad",
                    "description": "Standard banner",
                }
            ]
        }

        task = Task(
            id="task_123",
            context_id="ctx_456",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[
                Artifact(
                    parts=[
                        Part(root=DataPart(data=products_data)),
                        Part(root=TextPart(text="Found 1 product")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_123"
        )

        assert result.success is True
        assert result.status == TaskStatus.COMPLETED
        assert isinstance(result.data, GetProductsResponse)
        assert len(result.data.products) == 1
        assert result.data.products[0].product_id == "prod_1"
        assert result.metadata["task_id"] == "task_123"
        assert result.metadata["operation_id"] == "op_123"

    @pytest.mark.asyncio
    async def test_a2a_webhook_completed_with_errors(self):
        """Test A2A Task with completed status but errors in AdCP result."""
        products_data = {
            "products": [],
            "errors": [{"code": "NOT_FOUND", "message": "No products found"}],
        }

        task = Task(
            id="task_456",
            context_id="ctx_789",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[Artifact(parts=[Part(root=DataPart(data=products_data))])],
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_456"
        )

        assert result.status == TaskStatus.COMPLETED

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
            status=A2ATaskStatus(state="failed", timestamp=datetime.now(timezone.utc)),
            artifacts=[
                Artifact(
                    parts=[
                        Part(root=DataPart(data=error_data)),
                        Part(root=TextPart(text="Task failed due to internal error")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_789"
        )

        assert result.success is False
        assert result.status == TaskStatus.FAILED
        assert result.error == "Database connection failed"

    @pytest.mark.asyncio
    async def test_a2a_webhook_working_status(self):
        """Test A2A Task with working status (async in progress)."""
        progress_data = {
            "current_step": "fetching_inventory",
            "percentage": 50,
        }

        task = Task(
            id="task_111",
            context_id="ctx_222",
            status=A2ATaskStatus(state="working", timestamp=datetime.now(timezone.utc)),
            artifacts=[
                Artifact(
                    parts=[
                        Part(root=DataPart(data=progress_data)),
                        Part(root=TextPart(text="Processing request...")),
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_111"
        )

        assert result.status == TaskStatus.WORKING
        assert result.success is False  # Not completed yet

    @pytest.mark.asyncio
    async def test_a2a_webhook_input_required_status(self):
        """Test A2A Task with input-required status."""
        input_data = {
            "reason": "BUDGET_APPROVAL",
            "errors": [
                {
                    "code": "APPROVAL_REQUIRED",
                    "field": "total_budget",
                    "message": "Budget exceeds auto-approval threshold",
                }
            ],
        }

        task = Task(
            id="task_222",
            context_id="ctx_333",
            status=A2ATaskStatus(
                state="input-required", timestamp=datetime.now(timezone.utc)
            ),
            artifacts=[
                Artifact(
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
        assert result.error == "Budget exceeds auto-approval threshold"

    @pytest.mark.asyncio
    async def test_a2a_webhook_missing_artifacts(self):
        """Test A2A Task with no artifacts array."""
        task = Task(
            id="task_333",
            context_id="ctx_444",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[],  # Empty artifacts
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_333"
        )

        # Should still return result, but with None/empty data
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_a2a_webhook_missing_data_part(self):
        """Test A2A Task with no DataPart in artifacts."""
        task = Task(
            id="task_444",
            context_id="ctx_555",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[
                Artifact(
                    parts=[
                        Part(root=TextPart(text="Only text, no data"))  # Only TextPart
                    ]
                )
            ],
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_444"
        )

        # Should still return result, but with None/empty data
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_a2a_webhook_malformed_adcp_data(self):
        """Test A2A Task with invalid AdCP data structure."""
        # Invalid product structure (missing required fields)
        invalid_data = {"products": [{"invalid": "structure"}]}

        task = Task(
            id="task_555",
            context_id="ctx_666",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[Artifact(parts=[Part(root=DataPart(data=invalid_data))])],
        )

        result = await self.client.handle_webhook(
            task, task_type="get_products", operation_id="op_555"
        )

        # Should fallback to untyped result when parsing fails
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_a2a_webhook_signature_not_required(self):
        """Verify signature parameter is ignored for A2A webhooks."""
        task = Task(
            id="task_666",
            context_id="ctx_777",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[
                Artifact(parts=[Part(root=DataPart(data={"products": []}))])
            ],
        )

        # Signature should be ignored for A2A webhooks
        result = await self.client.handle_webhook(
            task,
            task_type="get_products",
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
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {"products": []},
        }

        result = await self.mcp_client.handle_webhook(
            payload, task_type="get_products", operation_id="op_mcp"
        )

        assert result.status == TaskStatus.COMPLETED
        assert result.metadata["task_id"] == "task_mcp"

    @pytest.mark.asyncio
    async def test_type_detection_a2a_task(self):
        """Verify Task object routes to A2A handler."""
        task = Task(
            id="task_a2a",
            context_id="ctx_a2a",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[Artifact(parts=[Part(root=DataPart(data={"products": []}))])],
        )

        result = await self.a2a_client.handle_webhook(
            task, task_type="get_products", operation_id="op_a2a"
        )

        assert result.status == TaskStatus.COMPLETED
        assert result.metadata["task_id"] == "task_a2a"

    @pytest.mark.asyncio
    async def test_consistent_result_format(self):
        """Verify MCP and A2A return identical TaskResult structure."""
        # MCP webhook
        mcp_payload = {
            "task_id": "task_1",
            "status": "completed",
            "timestamp": "2025-01-15T10:00:00Z",
            "result": {
                "products": [{"product_id": "prod_1", "name": "Test", "description": "Test"}]
            },
        }

        # A2A webhook with same data
        a2a_task = Task(
            id="task_2",
            context_id="ctx_2",
            status=A2ATaskStatus(state="completed", timestamp=datetime.now(timezone.utc)),
            artifacts=[
                Artifact(
                    parts=[
                        Part(
                            root=DataPart(
                                data={
                                    "products": [
                                        {"product_id": "prod_1", "name": "Test", "description": "Test"}
                                    ]
                                }
                            )
                        )
                    ]
                )
            ],
        )

        mcp_result = await self.mcp_client.handle_webhook(
            mcp_payload, task_type="get_products", operation_id="op_1"
        )
        a2a_result = await self.a2a_client.handle_webhook(
            a2a_task, task_type="get_products", operation_id="op_2"
        )

        # Both should return same structure
        assert mcp_result.success == a2a_result.success
        assert mcp_result.status == a2a_result.status
        assert isinstance(mcp_result.data, GetProductsResponse)
        assert isinstance(a2a_result.data, GetProductsResponse)
        assert len(mcp_result.data.products) == len(a2a_result.data.products)
