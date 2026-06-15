# GOV.UK Search MCP Server

MCP server for searching [GOV.UK](https://www.gov.uk). Exposes three tools:

- **`search_gov_uk`** — keyword search ranked by relevance
- **`latest_gov_uk`** — most recent publications, newest first
- **`fetch_gov_uk_page`** — fetches the content and attachments on a specific gov UK page

Uses the [GOV.UK Search API](https://github.com/alphagov/search-api/blob/main/docs/using-the-search-api.md).  
The server runs over streamable-http.

## Usage (Deployed)

### Installation

Install with `pip`:

```bash
pip install govuk-search-mcp
```

or with `uv`:

```bash
uv add govuk-search-mcp
```

or skip installation and use `uvx` (see below).

### Run Server

The server runs over streamable-http.

If installed via pip/uv:

```bash
govuk-search-mcp
```

Or if using `uvx`:

```bash
uvx govuk-search-mcp
```

By default the server listens on `http://127.0.0.1:8000/mcp`. Override with env vars:

| Variable       | Default     | Description  |
| -------------- | ----------- | ------------ |
| `FASTMCP_HOST` | `127.0.0.1` | Bind address |
| `FASTMCP_PORT` | `8000`      | Port         |

## Usage (Local)

If running locally, use just commands to run local code version (not release version).

```bash
# Start server using local code
just run_server
# Start inspector to manually test
just run_inspector
# Attach to claude code
just attach_claude
# Detach from calude code
just detach_claude
```

## Tools

### `search_gov_uk`

Search GOV.UK by keyword.

| Parameter   | Type   | Default | Description                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `query`     | string | —       | Search terms                            |
| `count`     | int    | 10      | Max results (0–1500)                    |
| `start`     | int    | 0       | Pagination offset                       |
| `date_from` | string | —       | Earliest date, `YYYY-MM-DD` (inclusive) |
| `date_to`   | string | —       | Latest date, `YYYY-MM-DD` (inclusive)   |

### `latest_gov_uk`

Get most recently updated GOV.UK publications.

| Parameter   | Type   | Default | Description                             |
| ----------- | ------ | ------- | --------------------------------------- |
| `count`     | int    | 10      | Max results (0–1500)                    |
| `start`     | int    | 0       | Pagination offset                       |
| `date_from` | string | —       | Earliest date, `YYYY-MM-DD` (inclusive) |
| `date_to`   | string | —       | Latest date, `YYYY-MM-DD` (inclusive)   |

## Development

```bash
uv sync
just test        # unit tests
just test_int    # integration tests (hits live GOV.UK API)
just lint        # ruff + mypy
```
