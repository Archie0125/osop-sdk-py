"""Tests for osop_sdk.report — HTML and text report generation."""

from __future__ import annotations

import pytest

from osop_sdk.report import (
    _kv_table,
    _ms,
    _type_color,
    _usd,
    generate_html_report,
    generate_text_report,
)


# ---------------------------------------------------------------------------
# _type_color()
# ---------------------------------------------------------------------------


class TestTypeColor:
    def test_known_types(self):
        assert _type_color("human") == "#ea580c"
        assert _type_color("agent") == "#7c3aed"
        assert _type_color("api") == "#2563eb"
        assert _type_color("mcp") == "#2563eb"
        assert _type_color("cli") == "#2563eb"
        assert _type_color("db") == "#059669"
        assert _type_color("data") == "#059669"
        assert _type_color("git") == "#475569"
        assert _type_color("docker") == "#475569"
        assert _type_color("cicd") == "#475569"
        assert _type_color("system") == "#475569"
        assert _type_color("infra") == "#475569"

    def test_unknown_type_returns_default(self):
        assert _type_color("unknown") == "#475569"
        assert _type_color("") == "#475569"

    def test_extra_types(self):
        assert _type_color("company") == "#ea580c"
        assert _type_color("department") == "#ea580c"
        assert _type_color("event") == "#475569"
        assert _type_color("gateway") == "#475569"


# ---------------------------------------------------------------------------
# _ms()
# ---------------------------------------------------------------------------


class TestMs:
    def test_none(self):
        assert _ms(None) == "-"

    def test_milliseconds(self):
        assert _ms(0) == "0ms"
        assert _ms(500) == "500ms"
        assert _ms(999) == "999ms"

    def test_seconds(self):
        assert _ms(1000) == "1.0s"
        assert _ms(1500) == "1.5s"
        assert _ms(59999) == "60.0s"

    def test_minutes(self):
        assert _ms(60000) == "1.0m"
        assert _ms(120000) == "2.0m"
        assert _ms(90000) == "1.5m"

    def test_float_input(self):
        assert _ms(500.0) == "500ms"
        assert _ms(1500.5) == "1.5s"


# ---------------------------------------------------------------------------
# _usd()
# ---------------------------------------------------------------------------


class TestUsd:
    def test_none(self):
        assert _usd(None) == "$0"

    def test_zero(self):
        assert _usd(0) == "$0"
        assert _usd(0.0) == "$0"

    def test_small_amount(self):
        assert _usd(0.001) == "$0.0010"
        assert _usd(0.0099) == "$0.0099"

    def test_larger_amount(self):
        assert _usd(0.01) == "$0.010"
        assert _usd(1.234) == "$1.234"
        assert _usd(0.5) == "$0.500"


# ---------------------------------------------------------------------------
# _kv_table()
# ---------------------------------------------------------------------------


class TestKvTable:
    def test_none(self):
        assert _kv_table(None) == ""

    def test_empty_dict(self):
        assert _kv_table({}) == ""

    def test_non_dict(self):
        assert _kv_table("string") == ""
        assert _kv_table([1, 2]) == ""

    def test_simple_dict(self):
        html = _kv_table({"key": "value"})
        assert "<table>" in html
        assert "</table>" in html
        assert "<tr>" in html
        assert "key" in html
        assert "value" in html

    def test_multiple_keys(self):
        html = _kv_table({"a": "1", "b": "2"})
        assert html.count("<tr>") == 2

    def test_nested_dict_value(self):
        html = _kv_table({"config": {"nested": True}})
        assert "config" in html
        # Nested dict is JSON serialized
        assert "nested" in html

    def test_list_value(self):
        html = _kv_table({"items": [1, 2, 3]})
        assert "items" in html
        assert "[1, 2, 3]" in html

    def test_long_value_truncated(self):
        long_val = "x" * 200
        html = _kv_table({"key": long_val})
        assert "..." in html

    def test_html_escaping(self):
        html = _kv_table({"key": "<script>alert(1)</script>"})
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_key_html_escaping(self):
        html = _kv_table({"<b>bold</b>": "value"})
        assert "<b>" not in html
        assert "&lt;b&gt;" in html


# ---------------------------------------------------------------------------
# generate_html_report() — spec-only mode
# ---------------------------------------------------------------------------

MINIMAL_OSOP_YAML = """\
osop_version: "1.0"
id: "test-wf"
name: "Test Workflow"
description: "A test workflow"
nodes:
  - id: "n1"
    type: "human"
    name: "Start"
    purpose: "begin"
  - id: "n2"
    type: "agent"
    name: "Process"
    purpose: "do work"
edges:
  - from: "n1"
    to: "n2"
    mode: "sequential"
"""


class TestGenerateHtmlReportSpecOnly:
    def test_returns_html_string(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_title(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "Test Workflow" in html

    def test_contains_description(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "A test workflow" in html

    def test_contains_node_names(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "Start" in html
        assert "Process" in html

    def test_contains_node_count(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "2 nodes" in html
        assert "1 edges" in html

    def test_contains_node_type_colors(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "#ea580c" in html  # human color
        assert "#7c3aed" in html  # agent color

    def test_custom_title(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, title="Custom Title")
        assert "Custom Title" in html

    def test_contains_css(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "<style>" in html

    def test_contains_footer(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "osop.ai" in html

    def test_contains_workflow_id_in_meta(self):
        html = generate_html_report(MINIMAL_OSOP_YAML)
        assert "test-wf" in html


# ---------------------------------------------------------------------------
# generate_html_report() — execution mode (with log)
# ---------------------------------------------------------------------------

OSOPLOG_YAML = """\
osoplog_version: "1.0"
run_id: "abc12345-6789-0000-0000-000000000000"
workflow_id: "test-wf"
mode: "live"
status: "COMPLETED"
trigger:
  type: "manual"
  actor: "user"
  timestamp: "2024-01-01T00:00:00Z"
started_at: "2024-01-01T00:00:00Z"
ended_at: "2024-01-01T00:01:00Z"
duration_ms: 60000
runtime:
  agent: "claude-code"
  model: "opus"
cost:
  total_usd: 0.05
  breakdown:
    - node_id: "n1"
      cost_usd: 0.02
    - node_id: "n2"
      cost_usd: 0.03
node_records:
  - node_id: "n1"
    node_type: "human"
    attempt: 1
    status: "COMPLETED"
    started_at: "2024-01-01T00:00:00Z"
    ended_at: "2024-01-01T00:00:30Z"
    duration_ms: 30000
    inputs:
      prompt: "hello"
    outputs:
      response: "world"
  - node_id: "n2"
    node_type: "agent"
    attempt: 1
    status: "COMPLETED"
    started_at: "2024-01-01T00:00:30Z"
    ended_at: "2024-01-01T00:01:00Z"
    duration_ms: 30000
    ai_metadata:
      model: "opus"
      prompt_tokens: 100
      completion_tokens: 50
result_summary: "Workflow completed successfully."
"""


class TestGenerateHtmlReportWithLog:
    def test_shows_completed_status(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "COMPLETED" in html

    def test_shows_duration(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "1.0m" in html  # 60000ms

    def test_shows_cost(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "$0.050" in html

    def test_shows_node_count(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "2 nodes" in html

    def test_shows_run_id(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "abc12345" in html

    def test_shows_agent(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "claude-code" in html

    def test_shows_result_summary(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "Workflow completed successfully." in html

    def test_shows_ai_metadata(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "opus" in html
        assert "100" in html  # prompt_tokens

    def test_shows_node_duration(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "30.0s" in html  # 30000ms


# ---------------------------------------------------------------------------
# generate_html_report() — failure handling
# ---------------------------------------------------------------------------

OSOPLOG_FAILED_YAML = """\
osoplog_version: "1.0"
run_id: "fail-run-id"
workflow_id: "test-wf"
mode: "live"
status: "FAILED"
started_at: "2024-01-01T00:00:00Z"
ended_at: "2024-01-01T00:00:10Z"
duration_ms: 10000
node_records:
  - node_id: "n1"
    node_type: "human"
    attempt: 1
    status: "COMPLETED"
    started_at: "2024-01-01T00:00:00Z"
    ended_at: "2024-01-01T00:00:05Z"
    duration_ms: 5000
  - node_id: "n2"
    node_type: "agent"
    attempt: 1
    status: "FAILED"
    started_at: "2024-01-01T00:00:05Z"
    ended_at: "2024-01-01T00:00:10Z"
    duration_ms: 5000
    error:
      code: "TIMEOUT"
      message: "Node timed out after 5s"
"""


class TestGenerateHtmlReportFailure:
    def test_shows_failed_status(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_FAILED_YAML)
        assert "FAILED" in html

    def test_shows_error_banner(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_FAILED_YAML)
        assert "TIMEOUT" in html
        assert "Node timed out after 5s" in html

    def test_failed_node_open_by_default(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_FAILED_YAML)
        # Failed nodes get open attribute and "er" class
        assert 'class="n er"' in html
        assert " open" in html


# ---------------------------------------------------------------------------
# generate_html_report() — retry handling
# ---------------------------------------------------------------------------

OSOPLOG_RETRY_YAML = """\
osoplog_version: "1.0"
run_id: "retry-run"
workflow_id: "test-wf"
mode: "live"
status: "COMPLETED"
started_at: "2024-01-01T00:00:00Z"
ended_at: "2024-01-01T00:01:00Z"
duration_ms: 60000
node_records:
  - node_id: "n2"
    node_type: "agent"
    attempt: 1
    status: "FAILED"
    started_at: "2024-01-01T00:00:00Z"
    ended_at: "2024-01-01T00:00:10Z"
    duration_ms: 10000
    error:
      code: "RATE_LIMIT"
      message: "Too many requests"
  - node_id: "n2"
    node_type: "agent"
    attempt: 2
    status: "COMPLETED"
    started_at: "2024-01-01T00:00:15Z"
    ended_at: "2024-01-01T00:00:30Z"
    duration_ms: 15000
  - node_id: "n1"
    node_type: "human"
    attempt: 1
    status: "COMPLETED"
    started_at: "2024-01-01T00:00:00Z"
    ended_at: "2024-01-01T00:00:05Z"
    duration_ms: 5000
"""


class TestGenerateHtmlReportRetry:
    def test_shows_retried_ok(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_RETRY_YAML)
        assert "retried ok" in html

    def test_shows_retry_attempt(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, OSOPLOG_RETRY_YAML)
        assert "Attempt 1" in html


# ---------------------------------------------------------------------------
# generate_text_report()
# ---------------------------------------------------------------------------


class TestGenerateTextReport:
    def test_spec_only(self):
        text = generate_text_report(MINIMAL_OSOP_YAML)
        assert "Test Workflow" in text
        assert "2 nodes" in text
        assert "1 edges" in text

    def test_spec_lists_node_names(self):
        text = generate_text_report(MINIMAL_OSOP_YAML)
        assert "Start" in text
        assert "Process" in text

    def test_with_log(self):
        text = generate_text_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "COMPLETED" in text
        assert "1.0m" in text

    def test_with_ansi(self):
        text = generate_text_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML, ansi=True)
        assert "\x1b[" in text  # ANSI escape codes present

    def test_without_ansi(self):
        text = generate_text_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML, ansi=False)
        assert "\x1b[" not in text

    def test_shows_result_summary(self):
        text = generate_text_report(MINIMAL_OSOP_YAML, OSOPLOG_YAML)
        assert "Workflow completed successfully." in text

    def test_failure_report(self):
        text = generate_text_report(MINIMAL_OSOP_YAML, OSOPLOG_FAILED_YAML)
        assert "FAILED" in text
        assert "TIMEOUT" in text


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestReportEdgeCases:
    def test_empty_yaml(self):
        html = generate_html_report("")
        assert "<!DOCTYPE html>" in html

    def test_no_nodes(self):
        yaml_str = "osop_version: '1.0'\nid: empty\nname: Empty\n"
        html = generate_html_report(yaml_str)
        assert "0 nodes" in html

    def test_no_log(self):
        html = generate_html_report(MINIMAL_OSOP_YAML, None)
        assert "2 nodes" in html
