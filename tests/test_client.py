"""Tests for osop_sdk.client — sync and async HTTP clients."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from osop_sdk.client import AsyncOsopClient, OsopClient
from osop_sdk.models import (
    ExecutionResult,
    ExecutionStatus,
    RenderResult,
    TestResult,
    ValidationResult,
)

BASE_URL = "http://localhost:8080"


# ---------------------------------------------------------------------------
# OsopClient — constructor
# ---------------------------------------------------------------------------


class TestOsopClientConstructor:
    def test_base_url_stored(self):
        client = OsopClient(base_url=BASE_URL)
        assert client._base_url == BASE_URL
        client.close()

    def test_base_url_trailing_slash_stripped(self):
        client = OsopClient(base_url="http://localhost:8080/")
        assert client._base_url == "http://localhost:8080"
        client.close()

    def test_timeout_stored(self):
        client = OsopClient(base_url=BASE_URL, timeout=10.0)
        assert client._timeout == 10.0
        client.close()

    def test_default_timeout(self):
        client = OsopClient(base_url=BASE_URL)
        assert client._timeout == 30.0
        client.close()

    def test_api_key_sets_auth_header(self):
        client = OsopClient(base_url=BASE_URL, api_key="sk-test-123")
        assert client._client.headers["Authorization"] == "Bearer sk-test-123"
        client.close()

    def test_no_api_key_no_auth_header(self):
        client = OsopClient(base_url=BASE_URL)
        assert "Authorization" not in client._client.headers
        client.close()

    def test_accept_header_set(self):
        client = OsopClient(base_url=BASE_URL)
        assert client._client.headers["Accept"] == "application/json"
        client.close()


# ---------------------------------------------------------------------------
# OsopClient — context manager
# ---------------------------------------------------------------------------


class TestOsopClientContextManager:
    def test_enter_returns_self(self):
        client = OsopClient(base_url=BASE_URL)
        with client as c:
            assert c is client

    def test_exit_closes_client(self):
        client = OsopClient(base_url=BASE_URL)
        with client:
            pass
        assert client._client.is_closed


# ---------------------------------------------------------------------------
# OsopClient — validate()
# ---------------------------------------------------------------------------


class TestOsopClientValidate:
    def test_validate_valid(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.validate(content="osop_version: '1.0'")
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    def test_validate_invalid(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={
                "valid": False,
                "errors": [{"level": "error", "message": "missing id"}],
                "warnings": [],
            },
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.validate(content="bad yaml")
        assert result.valid is False
        assert len(result.errors) == 1

    def test_validate_with_file_path(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.validate(file_path="workflow.osop.yaml")
        assert result.valid is True

    def test_validate_strict(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.validate(content="x", strict=True)
        request = httpx_mock.get_requests()[0]
        import json
        body = json.loads(request.content)
        assert body["strict"] is True


# ---------------------------------------------------------------------------
# OsopClient — run()
# ---------------------------------------------------------------------------


class TestOsopClientRun:
    def test_run_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/run",
            json={
                "workflow_name": "test-wf",
                "status": "completed",
                "dry_run": False,
                "started_at": "2024-01-01T00:00:00Z",
                "nodes": [],
            },
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.run(content="yaml content")
        assert isinstance(result, ExecutionResult)
        assert result.status == ExecutionStatus.COMPLETED

    def test_run_dry_run(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/run",
            json={
                "workflow_name": "test-wf",
                "status": "completed",
                "dry_run": True,
                "started_at": "2024-01-01T00:00:00Z",
                "nodes": [],
            },
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.run(content="yaml", dry_run=True)
        assert result.dry_run is True

    def test_run_with_inputs(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/run",
            json={
                "workflow_name": "test-wf",
                "status": "completed",
                "dry_run": False,
                "started_at": "2024-01-01T00:00:00Z",
                "nodes": [],
            },
        )
        with OsopClient(base_url=BASE_URL) as client:
            client.run(content="yaml", inputs={"key": "value"})
        import json
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["inputs"] == {"key": "value"}


# ---------------------------------------------------------------------------
# OsopClient — render()
# ---------------------------------------------------------------------------


class TestOsopClientRender:
    def test_render_mermaid(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/render",
            json={"format": "mermaid", "content": "graph TD; A-->B"},
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.render(content="yaml")
        assert isinstance(result, RenderResult)
        assert result.format == "mermaid"
        assert "A-->B" in result.content

    def test_render_sends_format(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/render",
            json={"format": "dot", "content": "digraph {}"},
        )
        with OsopClient(base_url=BASE_URL) as client:
            client.render(content="yaml", format="dot", direction="LR")
        import json
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["format"] == "dot"
        assert body["direction"] == "LR"


# ---------------------------------------------------------------------------
# OsopClient — test()
# ---------------------------------------------------------------------------


class TestOsopClientTest:
    def test_test_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/test",
            json={"total": 2, "passed": 2, "failed": 0, "cases": []},
        )
        with OsopClient(base_url=BASE_URL) as client:
            result = client.test(content="yaml")
        assert isinstance(result, TestResult)
        assert result.total == 2
        assert result.failed == 0

    def test_test_with_filter(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/test",
            json={"total": 1, "passed": 1, "failed": 0, "cases": []},
        )
        with OsopClient(base_url=BASE_URL) as client:
            client.test(content="yaml", filter="unit", verbose=True)
        import json
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["filter"] == "unit"
        assert body["verbose"] is True


# ---------------------------------------------------------------------------
# OsopClient — error handling
# ---------------------------------------------------------------------------


class TestOsopClientErrors:
    def test_http_404(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            status_code=404,
        )
        with OsopClient(base_url=BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                client.validate(content="yaml")
            assert exc_info.value.response.status_code == 404

    def test_http_500(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/run",
            status_code=500,
        )
        with OsopClient(base_url=BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                client.run(content="yaml")
            assert exc_info.value.response.status_code == 500

    def test_http_401_unauthorized(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            status_code=401,
        )
        with OsopClient(base_url=BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                client.validate(content="yaml")
            assert exc_info.value.response.status_code == 401


# ---------------------------------------------------------------------------
# OsopClient — API key header
# ---------------------------------------------------------------------------


class TestOsopClientApiKey:
    def test_api_key_sent_in_request(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        with OsopClient(base_url=BASE_URL, api_key="my-secret-key") as client:
            client.validate(content="yaml")
        request = httpx_mock.get_requests()[0]
        assert request.headers["Authorization"] == "Bearer my-secret-key"

    def test_no_api_key_no_header_in_request(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        with OsopClient(base_url=BASE_URL) as client:
            client.validate(content="yaml")
        request = httpx_mock.get_requests()[0]
        assert "Authorization" not in request.headers


# ---------------------------------------------------------------------------
# AsyncOsopClient — constructor
# ---------------------------------------------------------------------------


class TestAsyncOsopClientConstructor:
    def test_base_url_stored(self):
        client = AsyncOsopClient(base_url=BASE_URL)
        assert client._base_url == BASE_URL

    def test_api_key_sets_auth_header(self):
        client = AsyncOsopClient(base_url=BASE_URL, api_key="async-key")
        assert client._client.headers["Authorization"] == "Bearer async-key"

    def test_no_api_key_no_auth_header(self):
        client = AsyncOsopClient(base_url=BASE_URL)
        assert "Authorization" not in client._client.headers

    def test_timeout_stored(self):
        client = AsyncOsopClient(base_url=BASE_URL, timeout=15.0)
        assert client._timeout == 15.0


# ---------------------------------------------------------------------------
# AsyncOsopClient — context manager
# ---------------------------------------------------------------------------


class TestAsyncOsopClientContextManager:
    @pytest.mark.asyncio
    async def test_aenter_returns_self(self):
        client = AsyncOsopClient(base_url=BASE_URL)
        async with client as c:
            assert c is client

    @pytest.mark.asyncio
    async def test_aexit_closes_client(self):
        client = AsyncOsopClient(base_url=BASE_URL)
        async with client:
            pass
        assert client._client.is_closed


# ---------------------------------------------------------------------------
# AsyncOsopClient — validate()
# ---------------------------------------------------------------------------


class TestAsyncOsopClientValidate:
    @pytest.mark.asyncio
    async def test_validate_valid(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        async with AsyncOsopClient(base_url=BASE_URL) as client:
            result = await client.validate(content="yaml")
        assert isinstance(result, ValidationResult)
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_validate_with_errors(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={
                "valid": False,
                "errors": [{"level": "error", "message": "bad"}],
                "warnings": [],
            },
        )
        async with AsyncOsopClient(base_url=BASE_URL) as client:
            result = await client.validate(content="bad")
        assert result.valid is False
        assert len(result.errors) == 1


# ---------------------------------------------------------------------------
# AsyncOsopClient — run()
# ---------------------------------------------------------------------------


class TestAsyncOsopClientRun:
    @pytest.mark.asyncio
    async def test_run_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/run",
            json={
                "workflow_name": "wf",
                "status": "completed",
                "dry_run": False,
                "started_at": "2024-01-01T00:00:00Z",
                "nodes": [],
            },
        )
        async with AsyncOsopClient(base_url=BASE_URL) as client:
            result = await client.run(content="yaml")
        assert isinstance(result, ExecutionResult)
        assert result.status == ExecutionStatus.COMPLETED


# ---------------------------------------------------------------------------
# AsyncOsopClient — render()
# ---------------------------------------------------------------------------


class TestAsyncOsopClientRender:
    @pytest.mark.asyncio
    async def test_render(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/render",
            json={"format": "mermaid", "content": "graph TD"},
        )
        async with AsyncOsopClient(base_url=BASE_URL) as client:
            result = await client.render(content="yaml")
        assert isinstance(result, RenderResult)


# ---------------------------------------------------------------------------
# AsyncOsopClient — test()
# ---------------------------------------------------------------------------


class TestAsyncOsopClientTestMethod:
    @pytest.mark.asyncio
    async def test_test(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/test",
            json={"total": 1, "passed": 1, "failed": 0, "cases": []},
        )
        async with AsyncOsopClient(base_url=BASE_URL) as client:
            result = await client.test(content="yaml")
        assert isinstance(result, TestResult)
        assert result.passed == 1


# ---------------------------------------------------------------------------
# AsyncOsopClient — error handling
# ---------------------------------------------------------------------------


class TestAsyncOsopClientErrors:
    @pytest.mark.asyncio
    async def test_http_error(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            status_code=500,
        )
        async with AsyncOsopClient(base_url=BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.validate(content="yaml")

    @pytest.mark.asyncio
    async def test_api_key_sent(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/api/v1/validate",
            json={"valid": True, "errors": [], "warnings": []},
        )
        async with AsyncOsopClient(base_url=BASE_URL, api_key="async-secret") as client:
            await client.validate(content="yaml")
        request = httpx_mock.get_requests()[0]
        assert request.headers["Authorization"] == "Bearer async-secret"
