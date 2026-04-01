"""OSOP Python SDK — programmatic access to OSOP workflow operations."""

__version__ = "0.1.0"

from osop_sdk.client import AsyncOsopClient, OsopClient
from osop_sdk.report import generate_html_report, generate_text_report
from osop_sdk.models import (
    ExecutionNodeResult,
    ExecutionResult,
    OsopEdge,
    OsopNode,
    OsopWorkflow,
    RenderResult,
    TestCaseResult,
    TestResult,
    ValidationError,
    ValidationResult,
)

__all__ = [
    "__version__",
    "OsopClient",
    "AsyncOsopClient",
    "OsopWorkflow",
    "OsopNode",
    "OsopEdge",
    "ValidationResult",
    "ValidationError",
    "ExecutionResult",
    "ExecutionNodeResult",
    "RenderResult",
    "TestResult",
    "TestCaseResult",
    "generate_html_report",
    "generate_text_report",
]
