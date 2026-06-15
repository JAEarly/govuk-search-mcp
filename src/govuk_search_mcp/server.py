from mcp.server.fastmcp import FastMCP
from requests import HTTPError

from govuk_search_mcp.content import GovUKPageContent, run_gov_uk_page_fetch
from govuk_search_mcp.search import GovUKSearchResponse, run_gov_uk_search

mcp = FastMCP("GovUK Search", stateless_http=True, json_response=True)


@mcp.tool()
def search_gov_uk(
    query: str,
    count: int = 10,
    start: int = 0,
    date_from: str | None = None,
    date_to: str | None = None,
) -> GovUKSearchResponse:
    """
    Run a query against the GOV.UK search API.

    Args:
        query: Content to search for.
        count: Maximum number of items to return. May be below this if insufficient results found. Max = 1500.
        start: Result offset. E.g. count=1, start=1 returns the second result.
        date_from: Earliest date for results (YYYY-MM-DD, inclusive, 00:00).
        date_to: Latest date for results (YYYY-MM-DD, inclusive, 23:59).

    Returns:
        Parsed search response containing result list and metadata.
    """
    try:
        return run_gov_uk_search(
            query=query,
            count=count,
            start=start,
            order="relevance",
            date_from=date_from,
            date_to=date_to,
        )
    except HTTPError as e:
        raise ValueError(f"GOV.UK Search API error: {e.response.status_code} {e.response.reason}")


@mcp.tool()
def latest_gov_uk(
    count: int = 10,
    start: int = 0,
    date_from: str | None = None,
    date_to: str | None = None,
) -> GovUKSearchResponse:
    """
    Get the most recent publications from the GOV.UK search API.

    Args:
        count: Maximum number of items to return. May be below this if insufficient results found. Max = 1500.
        start: Result offset. E.g. count=1, start=1 returns the second result.
        date_from: Earliest date for results (YYYY-MM-DD, inclusive, 00:00).
        date_to: Latest date for results (YYYY-MM-DD, inclusive, 23:59).

    Returns:
        Parsed search response containing result list and metadata.
    """
    try:
        return run_gov_uk_search(
            query="",
            count=count,
            start=start,
            order="updated_newest",
            date_from=date_from,
            date_to=date_to,
        )
    except HTTPError as e:
        raise ValueError(f"GOV.UK Search API error: {e.response.status_code} {e.response.reason}")


@mcp.tool()
def fetch_gov_uk_page(url: str, plain_text: bool = False) -> GovUKPageContent:
    """
    Fetch the full content of a GOV.UK page, including body text and attachment metadata.

    Use this to read the body of a GOV.UK page returned by search_gov_uk or latest_gov_uk,
    and to discover any attached documents (HTML or PDF) linked from that page.

    Args:
        url: Full GOV.UK URL (e.g. https://www.gov.uk/guidance/foo) or bare path (/guidance/foo).
        plain_text: If True, strip HTML tags from the body and return plain text instead of HTML.

    Returns:
        Page content including body text, document type, and list of attachments with URLs.
    """
    try:
        return run_gov_uk_page_fetch(url, plain_text=plain_text)
    except ValueError as e:
        raise ValueError(str(e))
    except HTTPError as e:
        raise ValueError(f"GOV.UK Content API error: {e.response.status_code} {e.response.reason}")


# TODO(jearly): Add icons and/or prompts?
