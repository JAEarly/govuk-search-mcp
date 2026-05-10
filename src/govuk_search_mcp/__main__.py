from govuk_search_mcp.server import mcp


def main() -> None:
    """Entry point for GOV.UK Search MCP Server."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
