"""Pydantic models for OSOP data structures and API responses.

Aligned with the official osop-spec JSON Schema (v1.0 + v1.1).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NodeType(str, Enum):
    """The 12 supported OSOP node types."""

    HUMAN = "human"
    AGENT = "agent"
    API = "api"
    CLI = "cli"
    DB = "db"
    GIT = "git"
    DOCKER = "docker"
    CICD = "cicd"
    MCP = "mcp"
    SYSTEM = "system"
    INFRA = "infra"
    DATA = "data"


class EdgeMode(str, Enum):
    """Edge connection modes between nodes (v1.0 + v1.1 switch)."""

    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    LOOP = "loop"
    EVENT = "event"
    FALLBACK = "fallback"
    ERROR = "error"
    TIMEOUT = "timeout"
    SPAWN = "spawn"
    SWITCH = "switch"  # v1.1


class JoinMode(str, Enum):
    """Join mode for parallel fan-in edges (v1.1)."""

    WAIT_ALL = "wait_all"
    WAIT_ANY = "wait_any"
    WAIT_N = "wait_n"


class ExecutionStatus(str, Enum):
    """Execution status of a node or workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"
    TIMED_OUT = "timed_out"


# ---------------------------------------------------------------------------
# Shared Sub-structures
# ---------------------------------------------------------------------------


class IoSpec(BaseModel):
    """An input or output parameter definition."""

    name: str
    schema_ref: str | None = Field(None, alias="schema")
    required: bool = False
    description: str | None = None

    model_config = {"populate_by_name": True}


class RetryPolicy(BaseModel):
    """Retry policy for a node."""

    max_retries: int = 0
    strategy: str = "fixed"
    backoff_sec: float | None = None


class IdempotencyPolicy(BaseModel):
    """Idempotency configuration."""

    enabled: bool = False
    key: str | None = None


class HandoffSpec(BaseModel):
    """Handoff metadata between nodes."""

    summary_for_next_node: str | None = None
    expected_output: str | None = None
    escalation: str | None = None


class ExplainSpec(BaseModel):
    """Explain block — human-readable rationale."""

    why: str | None = None
    what: str | None = None
    result: str | None = None


class SpawnPolicy(BaseModel):
    """Spawn policy for agent orchestration (OSP-0001)."""

    max_children: int | None = None
    child_tools: list[str] | None = None
    can_spawn_children: bool = False


class SecurityNode(BaseModel):
    """Security configuration for a node."""

    permissions: list[str] | None = None
    secrets: list[str] | None = None
    risk_level: str | None = None


class ApprovalGate(BaseModel):
    """Approval gate for a node."""

    required: bool = False
    approver_role: str | None = None


class ObservabilityNode(BaseModel):
    """Observability configuration for a node."""

    log: bool = True
    metrics: list[str] | None = None


class SwitchCase(BaseModel):
    """A switch-case entry (v1.1)."""

    value: Any = None
    to: str


# ---------------------------------------------------------------------------
# Core Graph Types
# ---------------------------------------------------------------------------


class OsopNode(BaseModel):
    """A node in the OSOP workflow graph."""

    # Required
    id: str
    type: NodeType
    purpose: str

    # Optional identity
    name: str | None = None
    subtype: str | None = None
    role: str | None = None
    owner: str | None = None

    # Runtime
    runtime: dict[str, Any] | None = None

    # IO
    inputs: list[IoSpec] | None = None
    outputs: list[IoSpec] | None = None

    # Quality / resilience
    success_criteria: list[str] | None = None
    failure_modes: list[str] | None = None
    retry_policy: RetryPolicy | None = None
    timeout_sec: float | None = None

    # Idempotency
    idempotency: IdempotencyPolicy | None = None

    # Handoff & explain
    handoff: HandoffSpec | None = None
    explain: ExplainSpec | None = None

    # Observability / security / approval
    observability: ObservabilityNode | None = None
    security: SecurityNode | None = None
    approval_gate: ApprovalGate | None = None

    # Agent hierarchy (OSP-0001)
    parent: str | None = None
    spawn_policy: SpawnPolicy | None = None

    # v1.1 — sub-workflow reference
    workflow_ref: str | None = None
    workflow_inputs: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class OsopEdge(BaseModel):
    """An edge connecting two nodes."""

    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    mode: EdgeMode = EdgeMode.SEQUENTIAL
    when: str | None = None
    label: str | None = None
    spawn_count: int | None = None

    # v1.1 — foreach iteration
    for_each: str | None = None
    iterator_var: str | None = None

    # v1.1 — join mode
    join_mode: JoinMode | None = None
    join_count: int | None = None

    # v1.1 — switch/case
    cases: list[SwitchCase] | None = None
    default_to: str | None = None

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Workflow-level Types
# ---------------------------------------------------------------------------


class OsopTrigger(BaseModel):
    """Trigger definition."""

    type: str
    config: dict[str, Any] | None = None


class OsopTestCase(BaseModel):
    """Test case defined within a workflow."""

    id: str
    type: str
    target_node: str | None = None
    run: str | None = None
    input: dict[str, Any] | None = None
    expect: dict[str, Any] | None = None
    mocks: dict[str, Any] | None = None
    failure_injection: dict[str, Any] | None = None


class OsopMessageContract(BaseModel):
    """Message contract between nodes."""

    id: str
    producer: str
    consumer: str
    kind: str
    format: str
    schema_ref: str | None = None
    semantics: dict[str, Any] | None = None


class OsopWorkflow(BaseModel):
    """A complete OSOP workflow definition (v1.0 + v1.1)."""

    # Required
    osop_version: str
    id: str
    name: str

    # Optional identity
    description: str | None = None
    owner: str | None = None
    visibility: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    usage: str | None = None
    workflow_type: dict[str, Any] | None = None
    extends: str | None = None

    # Metadata & schemas
    metadata: dict[str, Any] | None = None
    schemas: dict[str, Any] | None = None

    # Roles & access
    roles: list[str] | None = None

    # Triggers & variables
    triggers: list[OsopTrigger] | None = None
    variables: dict[str, Any] | None = None
    imports: list[str] | None = None
    env: dict[str, str] | None = None

    # Platform & conformance
    platforms: list[str] | None = None
    conformance_level: int | None = None

    # Graph
    nodes: list[OsopNode]
    edges: list[OsopEdge]

    # Contracts & tests
    message_contracts: list[OsopMessageContract] | None = None
    tests: list[OsopTestCase] | None = None

    # Views
    views: list[str] | None = None

    # Security & observability
    security: dict[str, Any] | None = None
    observability: dict[str, Any] | None = None

    # Evolution & ledger
    evolution: dict[str, Any] | None = None
    ledger: dict[str, Any] | None = None

    # v1.1 — workflow-level timeout
    timeout_sec: float | None = None


# ---------------------------------------------------------------------------
# API Response Models (unchanged)
# ---------------------------------------------------------------------------


class ValidationError(BaseModel):
    """A single validation error or warning."""

    level: str
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
