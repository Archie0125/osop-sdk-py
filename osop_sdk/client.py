"""OSOP API client for Python."""

from __future__ import annotations

from typing import Any

import httpx

from osop_sdk.models import (
    ExecutionResult,
    RenderResult,
    TestResult,
    ValidationResult,
)


class OsopClient:
    """Synchronous client for the OSOP API.

    Args:
        base_url: Base URL of the OSOP server.
        api_key: Optional API key for authentication.
        timeout: Request timeout in seconds. Default: 30.0.

    Example::

        client = OsopClient(base_url="http://localhost:8080")
        result = client.validate(file_path="workflow.osop.yaml")
        print(result.valid)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        headers: dict[str, str] = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
        )

    def validate(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate an OSOP workflow against the schema."""
        data = self._request("/api/v1/validate", {
            "content": content,
            "file_path": file_path,
            "strict": strict,
        })
        return ValidationResult.model_validate(data)

    def run(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        inputs: dict[str, Any] | None = None,
        dry_run: bool = False,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """Execute an OSOP workflow with the given inputs."""
        data = self._request("/api/v1/run", {
            "content": content,
            "file_path": file_path,
            "inputs": inputs or {},
            "dry_run": dry_run,
            "timeout_seconds": timeout_seconds,
        })
        return ExecutionResult.model_validate(data)

    def render(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        format: str = "mermaid",
        direction: str = "TB",
    ) -> RenderResult:
        """Render an OSOP workflow as a visual diagram."""
        data = self._request("/api/v1/render", {
            "content": content,
            "file_path": file_path,
            "format": format,
            "direction": direction,
        })
        return RenderResult.model_validate(data)

    def test(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        filter: str | None = None,
        verbose: bool = False,
    ) -> TestResult:
        """Run test cases defined in an OSOP workflow."""
        data = self._request("/api/v1/test", {
            "content": content,
            "file_path": file_path,
            "filter": filter,
            "verbose": verbose,
        })
        return TestResult.model_validate(data)

    def _request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(path, json=body)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> OsopClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncOsopClient:
    """Asynchronous client for the OSOP API.

    Args:
        base_url: Base URL of the OSOP server.
        api_key: Optional API key for authentication.
        timeout: Request timeout in seconds. Default: 30.0.

    Example::

        async with AsyncOsopClient(base_url="http://localhost:8080") as client:
            result = await client.validate(file_path="workflow.osop.yaml")
            print(result.valid)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        headers: dict[str, str] = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
        )

    async def validate(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate an OSOP workflow against the schema."""
        data = await self._request("/api/v1/validate", {
            "content": content,
            "file_path": file_path,
            "strict": strict,
        })
        return ValidationResult.model_validate(data)

    async def run(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        inputs: dict[str, Any] | None = None,
        dry_run: bool = False,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """Execute an OSOP workflow with the given inputs."""
        data = await self._request("/api/v1/run", {
            "content": content,
            "file_path": file_path,
            "inputs": inputs or {},
            "dry_run": dry_run,
            "timeout_seconds": timeout_seconds,
        })
        return ExecutionResult.model_validate(data)

    async def render(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        format: str = "mermaid",
        direction: str = "TB",
    ) -> RenderResult:
        """Render an OSOP workflow as a visual diagram."""
        data = await self._request("/api/v1/render", {
            "content": content,
            "file_path": file_path,
            "format": format,
            "direction": direction,
        })
        return RenderResult.model_validate(data)

    async def test(
        self,
        *,
        content: str | None = None,
        file_path: str | None = None,
        filter: str | None = None,
        verbose: bool = False,
    ) -> TestResult:
        """Run test cases defined in an OSOP workflow."""
        data = await self._request("/api/v1/test", {
            "content": content,
            "file_path": file_path,
            "filter": filter,
            "verbose": verbose,
        })
        return TestResult.model_validate(data)

    async def _request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post(path, json=body)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncOsopClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
