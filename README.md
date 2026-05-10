# govuk-search-mcp

MCP server for searching [GOV.UK](https://www.gov.uk). Exposes two tools:

- **`search_gov_uk`** — keyword search ranked by relevance
- **`latest_gov_uk`** — most recent publications, newest first

Uses the [GOV.UK Search API](https://github.com/alphagov/search-api/blob/main/docs/using-the-search-api.md).  
The server runs over streamable-http.

## Installation

```bash
pip install govuk-search-mcp
```

Or with `uv`:

```bash
uv add govuk-search-mcp
```

No install needed with `uvx` — see usage below.

## Usage

The server runs over streamable-http. Start it first:

```bash
uvx govuk-search-mcp
# or, if installed via pip/uv:
govuk-search-mcp
```

By default it listens on `http://127.0.0.1:8000/mcp`. Override with env vars:

| Variable       | Default     | Description  |
| -------------- | ----------- | ------------ |
| `FASTMCP_HOST` | `127.0.0.1` | Bind address |
| `FASTMCP_PORT` | `8000`      | Port         |

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gov-uk": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport http gov-uk-search http://localhost:8000/mcp
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
