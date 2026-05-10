default: fmt lint test

fmt:
    uv run ruff format .
    uv run ruff check --fix .

lint:
    uv run ruff check .
    uv run mypy .

test:
    uv run pytest test/unit

test_int:
    uv run pytest test/integration

run_server:
     uv run --with mcp src/govuk_search_mcp/server.py

run_inspector:
    npx -y @modelcontextprotocol/inspector --server-url http://localhost:8000/mcp

attach_claude:
    claude mcp add --transport http gov-uk-search http://localhost:8000/mcp

detach_claude:
    claude mcp remove gov-uk-search

