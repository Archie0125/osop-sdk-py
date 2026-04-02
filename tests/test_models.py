"""Tests for osop_sdk.models — Pydantic models, enums, serialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from osop_sdk.models import (
    ApprovalGate,
    EdgeMode,
    ExecutionNodeResult,
    ExecutionResult,
    ExecutionStatus,
    ExplainSpec,
    HandoffSpec,
    IdempotencyPolicy,
    IoSpec,
    JoinMode,
    NodeType,
    ObservabilityNode,
    OsopEdge,
    OsopNode,
    OsopTestCase,
    OsopTrigger,
    OsopWorkflow,
    RenderResult,
    RetryPolicy,
    SecurityNode,
    SpawnPolicy,
    SwitchCase,
    TestCaseResult,
    TestResult,
    ValidationError,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# NodeType enum
# ---------------------------------------------------------------------------


class TestNodeType:
    def test_has_12_values(self):
        assert len(NodeType) == 12

    def test_all_values_present(self):
        expected = {
            "human", "agent", "api", "cli", "db", "git",
            "docker", "cicd", "mcp", "system", "infra", "data",
        }
        actual = {m.value for m in NodeType}
        assert actual == expected

    def test_str_enum(self):
        assert NodeType.HUMAN == "human"
        assert str(NodeType.AGENT) == "agent"

    def test_from_value(self):
        assert NodeType("cli") is NodeType.CLI


# ---------------------------------------------------------------------------
# EdgeMode enum
# ---------------------------------------------------------------------------


class TestEdgeMode:
    def test_has_10_values(self):
        assert len(EdgeMode) == 10

    def test_all_values_present(self):
        expected = {
            "sequential", "conditional", "parallel", "loop", "event",
            "fallback", "error", "timeout", "spawn", "switch",
        }
        actual = {m.value for m in EdgeMode}
        assert actual == expected

    def test_switch_is_v11(self):
        """switch was added in v1.1."""
        assert EdgeMode.SWITCH == "switch"


# ---------------------------------------------------------------------------
# JoinMode enum
# ---------------------------------------------------------------------------


class TestJoinMode:
    def test_has_3_values(self):
        assert len(JoinMode) == 3

    def test_values(self):
        assert JoinMode.WAIT_ALL == "wait_all"
        assert JoinMode.WAIT_ANY == "wait_any"
        assert JoinMode.WAIT_N == "wait_n"


# ---------------------------------------------------------------------------
# ExecutionStatus enum
# ---------------------------------------------------------------------------


class TestExecutionStatus:
    def test_has_7_values(self):
        assert len(ExecutionStatus) == 7

    def test_values(self):
        expected = {
            "pending", "running", "completed", "failed",
            "skipped", "waiting_approval", "timed_out",
        }
        actual = {s.value for s in ExecutionStatus}
        assert actual == expected


# ---------------------------------------------------------------------------
# IoSpec
# ---------------------------------------------------------------------------


class TestIoSpec:
    def test_minimal(self):
        io = IoSpec(name="prompt")
        assert io.name == "prompt"
        assert io.schema_ref is None
        assert io.required is False
        assert io.description is None

    def test_full(self):
        io = IoSpec(name="prompt", required=True, description="User prompt")
        assert io.required is True
        assert io.description == "User prompt"

    def test_schema_alias(self):
        io = IoSpec(**{"name": "x", "schema": "string"})
        assert io.schema_ref == "string"

    def test_populate_by_name(self):
        io = IoSpec(name="x", schema_ref="integer")
        assert io.schema_ref == "integer"


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------


class TestRetryPolicy:
    def test_defaults(self):
        rp = RetryPolicy()
        assert rp.max_retries == 0
        assert rp.strategy == "fixed"
        assert rp.backoff_sec is None

    def test_custom(self):
        rp = RetryPolicy(max_retries=3, strategy="exponential", backoff_sec=2.0)
        assert rp.max_retries == 3
        assert rp.strategy == "exponential"
        assert rp.backoff_sec == 2.0


# ---------------------------------------------------------------------------
# Other sub-structures
# ---------------------------------------------------------------------------


class TestSubStructures:
    def test_idempotency_defaults(self):
        ip = IdempotencyPolicy()
        assert ip.enabled is False
        assert ip.key is None

    def test_handoff_spec(self):
        h = HandoffSpec(summary_for_next_node="done", expected_output="json")
        assert h.summary_for_next_node == "done"

    def test_explain_spec(self):
        e = ExplainSpec(why="perf", what="cache", result="faster")
        assert e.why == "perf"

    def test_spawn_policy_defaults(self):
        sp = SpawnPolicy()
        assert sp.can_spawn_children is False
        assert sp.max_children is None

    def test_security_node(self):
        s = SecurityNode(permissions=["read"], risk_level="low")
        assert s.permissions == ["read"]

    def test_approval_gate_defaults(self):
        ag = ApprovalGate()
        assert ag.required is False

    def test_observability_node_defaults(self):
        ob = ObservabilityNode()
        assert ob.log is True
        assert ob.metrics is None


# ---------------------------------------------------------------------------
# SwitchCase
# ---------------------------------------------------------------------------


class TestSwitchCase:
    def test_creation(self):
        sc = SwitchCase(value="yes", to="node_a")
        assert sc.value == "yes"
        assert sc.to == "node_a"

    def test_default_value_none(self):
        sc = SwitchCase(to="fallback")
        assert sc.value is None


# ---------------------------------------------------------------------------
# OsopNode
# ---------------------------------------------------------------------------


class TestOsopNode:
    def test_required_fields(self):
        node = OsopNode(id="n1", type=NodeType.HUMAN, purpose="review code")
        assert node.id == "n1"
        assert node.type == NodeType.HUMAN
        assert node.purpose == "review code"

    def test_optional_fields_default_none(self):
        node = OsopNode(id="n1", type=NodeType.AGENT, purpose="analyze")
        assert node.name is None
        assert node.subtype is None
        assert node.role is None
        assert node.owner is None
        assert node.runtime is None
        assert node.inputs is None
        assert node.outputs is None
        assert node.retry_policy is None
        assert node.timeout_sec is None
        assert node.handoff is None
        assert node.explain is None
        assert node.parent is None
        assert node.spawn_policy is None
        assert node.workflow_ref is None
        assert node.workflow_inputs is None

    def test_with_optional_fields(self):
        node = OsopNode(
            id="n2",
            type=NodeType.AGENT,
            purpose="generate code",
            name="Code Generator",
            subtype="llm",
            role="developer",
            owner="team-a",
            timeout_sec=60.0,
            parent="coordinator",
        )
        assert node.name == "Code Generator"
        assert node.subtype == "llm"
        assert node.role == "developer"
        assert node.owner == "team-a"
        assert node.timeout_sec == 60.0
        assert node.parent == "coordinator"

    def test_with_io_specs(self):
        node = OsopNode(
            id="n3",
            type=NodeType.API,
            purpose="fetch data",
            inputs=[IoSpec(name="url")],
            outputs=[IoSpec(name="response", required=True)],
        )
        assert len(node.inputs) == 1
        assert len(node.outputs) == 1
        assert node.outputs[0].required is True

    def test_with_retry_policy(self):
        node = OsopNode(
            id="n4",
            type=NodeType.CLI,
            purpose="deploy",
            retry_policy=RetryPolicy(max_retries=3, strategy="exponential"),
        )
        assert node.retry_policy.max_retries == 3

    def test_v11_workflow_ref(self):
        node = OsopNode(
            id="sub1",
            type=NodeType.SYSTEM,
            purpose="run sub-workflow",
            workflow_ref="workflows/deploy.osop",
            workflow_inputs={"env": "prod"},
        )
        assert node.workflow_ref == "workflows/deploy.osop"
        assert node.workflow_inputs == {"env": "prod"}

    def test_missing_required_raises(self):
        with pytest.raises(PydanticValidationError):
            OsopNode(id="n1", type=NodeType.HUMAN)  # missing purpose

    def test_invalid_type_raises(self):
        with pytest.raises(PydanticValidationError):
            OsopNode(id="n1", type="not_a_type", purpose="x")

    def test_serialization_roundtrip(self):
        node = OsopNode(
            id="rt",
            type=NodeType.MCP,
            purpose="search",
            name="Search Node",
            spawn_policy=SpawnPolicy(max_children=5, can_spawn_children=True),
        )
        data = node.model_dump()
        restored = OsopNode.model_validate(data)
        assert restored.id == node.id
        assert restored.spawn_policy.max_children == 5
        assert restored.spawn_policy.can_spawn_children is True


# ---------------------------------------------------------------------------
# OsopEdge
# ---------------------------------------------------------------------------


class TestOsopEdge:
    def test_creation_with_aliases(self):
        edge = OsopEdge(**{"from": "a", "to": "b"})
        assert edge.from_node == "a"
        assert edge.to_node == "b"

    def test_default_mode_sequential(self):
        edge = OsopEdge(**{"from": "a", "to": "b"})
        assert edge.mode == EdgeMode.SEQUENTIAL

    def test_populate_by_name(self):
        edge = OsopEdge(from_node="x", to_node="y", mode=EdgeMode.PARALLEL)
        assert edge.from_node == "x"
        assert edge.to_node == "y"
        assert edge.mode == EdgeMode.PARALLEL

    def test_with_condition(self):
        edge = OsopEdge(
            **{"from": "a", "to": "b"},
            mode=EdgeMode.CONDITIONAL,
            when="status == 'ok'",
            label="on success",
        )
        assert edge.when == "status == 'ok'"
        assert edge.label == "on success"

    def test_spawn_count(self):
        edge = OsopEdge(**{"from": "a", "to": "b"}, mode=EdgeMode.SPAWN, spawn_count=3)
        assert edge.spawn_count == 3

    def test_v11_for_each(self):
        edge = OsopEdge(
            **{"from": "a", "to": "b"},
            for_each="items",
            iterator_var="item",
        )
        assert edge.for_each == "items"
        assert edge.iterator_var == "item"

    def test_v11_join_mode(self):
        edge = OsopEdge(
            **{"from": "a", "to": "b"},
            join_mode=JoinMode.WAIT_ALL,
            join_count=3,
        )
        assert edge.join_mode == JoinMode.WAIT_ALL
        assert edge.join_count == 3

    def test_v11_switch_cases(self):
        edge = OsopEdge(
            **{"from": "a", "to": "b"},
            mode=EdgeMode.SWITCH,
            cases=[
                SwitchCase(value="yes", to="approve"),
                SwitchCase(value="no", to="reject"),
            ],
            default_to="review",
        )
        assert edge.mode == EdgeMode.SWITCH
        assert len(edge.cases) == 2
        assert edge.cases[0].to == "approve"
        assert edge.default_to == "review"

    def test_optional_fields_default_none(self):
        edge = OsopEdge(**{"from": "a", "to": "b"})
        assert edge.when is None
        assert edge.label is None
        assert edge.spawn_count is None
        assert edge.for_each is None
        assert edge.iterator_var is None
        assert edge.join_mode is None
        assert edge.join_count is None
        assert edge.cases is None
        assert edge.default_to is None

    def test_serialization_with_alias(self):
        edge = OsopEdge(**{"from": "a", "to": "b", "mode": "parallel"})
        data = edge.model_dump(by_alias=True)
        assert data["from"] == "a"
        assert data["to"] == "b"
        assert data["mode"] == "parallel"

    def test_roundtrip(self):
        edge = OsopEdge(from_node="x", to_node="y", mode=EdgeMode.LOOP, when="i < 10")
        data = edge.model_dump()
        restored = OsopEdge.model_validate(data)
        assert restored.from_node == "x"
        assert restored.when == "i < 10"


# ---------------------------------------------------------------------------
# OsopWorkflow
# ---------------------------------------------------------------------------


def _minimal_workflow(**overrides):
    """Helper to build a minimal valid workflow dict."""
    base = {
        "osop_version": "1.0",
        "id": "test-wf",
        "name": "Test Workflow",
        "nodes": [
            {"id": "n1", "type": "human", "purpose": "start"},
        ],
        "edges": [
        ],
    }
    base.update(overrides)
    return base


class TestOsopWorkflow:
    def test_minimal_required_fields(self):
        wf = OsopWorkflow.model_validate(_minimal_workflow())
        assert wf.osop_version == "1.0"
        assert wf.id == "test-wf"
        assert wf.name == "Test Workflow"
        assert len(wf.nodes) == 1
        assert len(wf.edges) == 0

    def test_optional_fields_default_none(self):
        wf = OsopWorkflow.model_validate(_minimal_workflow())
        assert wf.description is None
        assert wf.owner is None
        assert wf.visibility is None
        assert wf.tags is None
        assert wf.status is None
        assert wf.metadata is None
        assert wf.schemas is None
        assert wf.roles is None
        assert wf.triggers is None
        assert wf.variables is None
        assert wf.imports is None
        assert wf.env is None
        assert wf.platforms is None
        assert wf.conformance_level is None
        assert wf.message_contracts is None
        assert wf.tests is None
        assert wf.views is None
        assert wf.security is None
        assert wf.observability is None
        assert wf.evolution is None
        assert wf.ledger is None
        assert wf.timeout_sec is None

    def test_with_all_optional_fields(self):
        wf = OsopWorkflow.model_validate(_minimal_workflow(
            description="A test workflow",
            owner="team-a",
            visibility="public",
            tags=["test", "demo"],
            status="active",
            usage="testing purposes",
            metadata={"version": "1.0"},
            schemas={"input": {"type": "object"}},
            roles=["admin", "viewer"],
            triggers=[{"type": "webhook"}],
            variables={"env": "dev"},
            imports=["common.osop"],
            env={"NODE_ENV": "test"},
            platforms=["linux", "macos"],
            conformance_level=2,
            views=["default"],
            security={"auth": "required"},
            observability={"tracing": True},
            evolution={"deprecated_nodes": []},
            ledger={"last_run": "2024-01-01"},
            timeout_sec=600.0,
        ))
        assert wf.description == "A test workflow"
        assert wf.tags == ["test", "demo"]
        assert wf.conformance_level == 2
        assert wf.timeout_sec == 600.0
        assert wf.env == {"NODE_ENV": "test"}

    def test_with_edges(self):
        data = _minimal_workflow(
            nodes=[
                {"id": "n1", "type": "human", "purpose": "start"},
                {"id": "n2", "type": "agent", "purpose": "process"},
            ],
            edges=[
                {"from": "n1", "to": "n2", "mode": "sequential"},
            ],
        )
        wf = OsopWorkflow.model_validate(data)
        assert len(wf.edges) == 1
        assert wf.edges[0].from_node == "n1"
        assert wf.edges[0].to_node == "n2"

    def test_with_triggers(self):
        data = _minimal_workflow(
            triggers=[{"type": "cron", "config": {"schedule": "0 * * * *"}}],
        )
        wf = OsopWorkflow.model_validate(data)
        assert len(wf.triggers) == 1
        assert wf.triggers[0].type == "cron"
        assert wf.triggers[0].config["schedule"] == "0 * * * *"

    def test_with_test_cases(self):
        data = _minimal_workflow(
            tests=[{
                "id": "t1",
                "type": "unit",
                "target_node": "n1",
                "expect": {"status": "completed"},
            }],
        )
        wf = OsopWorkflow.model_validate(data)
        assert len(wf.tests) == 1
        assert wf.tests[0].id == "t1"

    def test_v11_timeout_sec(self):
        wf = OsopWorkflow.model_validate(_minimal_workflow(timeout_sec=120.5))
        assert wf.timeout_sec == 120.5

    def test_missing_required_raises(self):
        with pytest.raises(PydanticValidationError):
            OsopWorkflow.model_validate({"osop_version": "1.0", "id": "x"})

    def test_serialization_roundtrip(self):
        data = _minimal_workflow(
            description="roundtrip test",
            tags=["a", "b"],
            nodes=[
                {"id": "n1", "type": "human", "purpose": "start"},
                {"id": "n2", "type": "cli", "purpose": "build"},
            ],
            edges=[{"from": "n1", "to": "n2"}],
        )
        wf = OsopWorkflow.model_validate(data)
        dumped = wf.model_dump()
        restored = OsopWorkflow.model_validate(dumped)
        assert restored.id == wf.id
        assert restored.description == "roundtrip test"
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1


# ---------------------------------------------------------------------------
# API Response Models
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_valid(self):
        vr = ValidationResult(valid=True)
        assert vr.valid is True
        assert vr.errors == []
        assert vr.warnings == []

    def test_with_errors(self):
        vr = ValidationResult(
            valid=False,
            errors=[ValidationError(level="error", message="missing id", path="/id")],
        )
        assert vr.valid is False
        assert len(vr.errors) == 1
        assert vr.errors[0].path == "/id"


class TestExecutionResult:
    def test_minimal(self):
        er = ExecutionResult(
            workflow_name="wf",
            status=ExecutionStatus.COMPLETED,
            started_at="2024-01-01T00:00:00Z",
        )
        assert er.workflow_name == "wf"
        assert er.status == ExecutionStatus.COMPLETED
        assert er.dry_run is False
        assert er.nodes == []

    def test_with_nodes(self):
        er = ExecutionResult(
            workflow_name="wf",
            status=ExecutionStatus.COMPLETED,
            started_at="2024-01-01T00:00:00Z",
            nodes=[
                ExecutionNodeResult(node_id="n1", status=ExecutionStatus.COMPLETED),
            ],
        )
        assert len(er.nodes) == 1


class TestRenderResult:
    def test_creation(self):
        rr = RenderResult(format="mermaid", content="graph TD; A-->B")
        assert rr.format == "mermaid"
        assert "A-->B" in rr.content


class TestTestResult:
    def test_creation(self):
        tr = TestResult(
            total=2,
            passed=1,
            failed=1,
            cases=[
                TestCaseResult(name="test1", passed=True),
                TestCaseResult(name="test2", passed=False, message="assertion failed"),
            ],
        )
        assert tr.total == 2
        assert tr.passed == 1
        assert tr.failed == 1
        assert tr.cases[1].message == "assertion failed"
