# OSOP Python SDK

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/osop-sdk)](https://pypi.org/project/osop-sdk/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)

**Serves both SOP Doc and The Loop.** Build workflow tools in Python.

Parse .osop files, validate, render, execute. Build custom SOP Doc viewers or integrate The Loop into Python applications. Sync and async clients.

Website: [osop.ai](https://osop.ai) | GitHub: [github.com/osop/osop-sdk-py](https://github.com/osop/osop-sdk-py)

## Installation

```bash
pip install osop-sdk
```

## Quick Start

```python
from osop_sdk import OsopClient

client = OsopClient(base_url="http://localhost:8080")

# Validate a workflow
result = client.validate(file_path="deploy.osop.yaml")
print(result.valid)  # True

# Run a workflow in dry-run mode
execution = client.run(
    file_path="deploy.osop.yaml",
    inputs={"environment": "staging"},
    dry_run=True,
)
print(execution.status)  # "completed"

# Render a Mermaid diagram
diagram = client.render(file_path="deploy.osop.yaml", format="mermaid")
print(diagram.content)

# Run test cases
test_result = client.test(file_path="deploy.osop.yaml")
print(f"{test_result.passed}/{test_result.total} passed")
```

### Async Usage

```python
from osop_sdk import AsyncOsopClient

async def main():
    client = AsyncOsopClient(base_url="http://localhost:8080")
    result = await client.validate(file_path="workflow.osop.yaml")
    print(result.valid)
```

## API Reference

### `OsopClient` / `AsyncOsopClient`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `base_url` | `str` | Yes | OSOP server base URL |
| `api_key` | `str` | No | API key for authentication |
| `timeout` | `float` | No | Request timeout in seconds (default: 30.0) |

#### Methods

| Method | Description |
|--------|-------------|
| `validate(content=, file_path=, strict=)` | Validate a workflow against the schema |
| `run(content=, file_path=, inputs=, dry_run=, timeout_seconds=)` | Execute a workflow |
| `render(content=, file_path=, format=, direction=)` | Render a workflow diagram |
| `test(content=, file_path=, filter=, verbose=)` | Run workflow test cases |

## Development

```bash
git clone https://github.com/osop/osop-sdk-py.git
cd osop-sdk-py
pip install -e ".[dev]"
pytest
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
