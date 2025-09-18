# Repository Guidelines

This project implements an AWS S3 MCP server using the FastMCP v2 Python framework. Keep code Python-only under `src/`, with tests in `tests/`.

## Project Structure & Module Organization
- `PRD.md`, `TASKS.md`, `CLAUDE.md`: Planning and notes.
- `src/`: Application code
  - `src/server.py`: FastMCP entrypoint (`FastMCP("S3")` + tools)
  - `src/aws/s3.py`: S3 adapters (list/get/put/delete, pagination, presigned URLs)
- `tests/`: Pytest suites (`tests/unit/**`, `tests/integration/**`)
- `config/`: Non-secret config and `.env.example`
- `scripts/`: Local helpers (e.g., data seeding, tooling)

## Build, Test, and Development Commands
- Install (recommended): `uv sync` (or `pip install -e .[dev]`)
- Run server (STDIO): `uv run fastmcp run src/server.py`
- Run server (HTTP): `uv run python -m src.server -- --transport http --port 8000`
- Tests: `uv run pytest -q`
- Coverage: `uv run pytest --cov=src --cov-report=term-missing`
- Static checks: `uv run pre-commit run --all-files`

## Coding Style & Naming Conventions
- Python 3.10+ with type hints; docstrings for tools/resources.
- Format: Black; Lint: Ruff; Types: mypy (when practical).
- Indentation 4 spaces; modules `snake_case`, classes `PascalCase`, functions/vars `snake_case`.
- Tool names and resource URIs should be short and action-oriented (e.g., `s3_list_objects`).

## Testing Guidelines
- Framework: Pytest.
- Layout: unit tests isolate logic in `src/aws/`; integration uses LocalStack or a dev AWS account.
- Naming: `tests/unit/test_*.py`, `tests/integration/test_*.py`.
- Coverage target ≥80% for `src/aws` and tool handlers.
- Mark real-AWS tests with `@pytest.mark.aws` and skip by default.

## Commit & Pull Request Guidelines
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- PRs must include: description, linked issues, test evidence (logs or screenshots for HTTP), and updated docs/examples.
- CI must pass: tests, coverage threshold, pre-commit hooks.

## Security & Configuration Tips
- Configure via env: `AWS_PROFILE`, `AWS_REGION`, optional `AWS_ENDPOINT_URL` (LocalStack).
- Never commit credentials; provide `.env.example`; ignore `.env`.
- Apply least-privilege IAM; restrict to required buckets/prefixes.
- Default integration tests to LocalStack; require an explicit flag to hit real AWS (`USE_REAL_AWS=1`).

## FastMCP Notes
- Define tools with `@mcp.tool` or `mcp.tool()`; expose S3 operations as tools and common buckets as resources.
- Prefer STDIO in Claude Desktop; use `mcp.run(transport="http", port=8000)` for web deployments.
