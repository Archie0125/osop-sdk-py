"""Pydantic models for OSOP data structures and API responses."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """The 12 supported OSOP node types."""

    START = "start"
    END = "end"
    STEP = "step"
    DECISION = "decision"
    FORK = "fork"
    JOIN = "join"
    LOOP = "loop"
    RETRY = "retry"
    APPROVAL = "approval"
    WEBHOOK = "webhook"
    TIMER = "timer"
    SUBPROCESS = "subprocess"


class EdgeMode(str, Enum):
    """Edge connection modes between nodes."""

    DEFAULT = "default"
    CONDITIONAL = "conditional"
    ERROR = "error"
    TIMEOUT = "timeout"


class ExecutionStatus(str, Enum):
    """Execution status of a node or workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"
    TIMED_OUT = "timed_out"


class OsopInput(BaseModel):
    """An input parameter definition."""

    name: str
    type: str = "string"
    required: bool = False
    default: Any = None
    description: str | None = None


class OsopOutput(BaseModel):
    """An output parameter definition."""

    name: str
    type: str = "string"
    description: str | None = None


class OsopNode(BaseModel):
    """A node in the OSOP workflow graph."""

    id: str
    type: NodeType
    description: str | None = None
    action: str | None = None
    condition: str | None = None
    inputs: list[OsopInput] | None = None
    outputs: list[OsopOutput] | None = None

    # Retry
    max_attempts: int | None = None
    backoff: str | None = None
    delay: str | None = None

    # Approval
    approvers: list[str] | None = None

    # Webhook
    url: str | None = None
    method: str | None = None
    headers: dict[str, str] | None = None

    # Timer
    duration: str | None = None
    cron: str | None = None

    # Loop
    for_each: str | None = None
    while_condition: str | None = Field(None, alias="while")
    max_iterations: int | None = None

    # Subprocess
    workflow: str | None = None

    # Common
    timeout: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class OsopEdge(BaseModel):
    """An edge connecting two nodes."""

    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    mode: EdgeMode = EdgeMode.DEFAULT
    condition: str | None = None
    description: str | None = None

    model_config = {"populate_by_name": True}


class OsopMetadata(BaseModel):
    """Workflow metadata."""

    owner: str | None = None
    tags: list[str] | None = None


class OsopWorkflow(BaseModel):
    """A complete OSOP workflow definition."""

    osop: str
    name: str
    description: str
    metadata: OsopMetadata | None = None
    inputs: list[OsopInput] | None = None
    nodes: list[OsopNode]
    edges: list[OsopEdge]


# --- API Response Models ---


class ValidationError(BaseModel):
    """A single validation error or warning."""

    level: str  # "error" or "warning"
    message: str
    path: str | None = None
    line: int | None = None
    column: int | None = None


class ValidationResult(BaseModel):
    """Result of a validate operation."""

    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)


class ExecutionNodeResult(BaseModel):
    """Result of a single node's execution."""

    node_id: str
    status: ExecutionStatus
    started_at: str | None = None
    completed_at: str | None = None
    outputs: dict[str, Any] | None = None
    error: str | None = None


class ExecutionResult(BaseModel):
    """Result of a workflow execution."""

    workflow_name: str
    status: ExecutionStatus
    dry_run: bool = False
    started_at: str
    completed_at: str | None = None
    nodes: list[ExecutionNodeResult] = Field(default_factory=list)
    outputs: dict[str, Any] | None = None
    error: str | None = None


class RenderResult(BaseModel):
    """Result of a render operation."""

    format: str
    content: str


class TestCaseResult(BaseModel):
    """Result of a single test case."""

    name: str
    passed: bool
    message: str | None = None
    expected: Any = None
    actual: Any = None


class TestResult(BaseModel):
    """Result of running all test cases."""

    total: int
    passed: int
    failed: int
    cases: list[TestCaseResult] = Field(default_factory=list)
