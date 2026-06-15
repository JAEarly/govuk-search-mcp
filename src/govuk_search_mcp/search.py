from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, get_args

import requests

GOV_UK_SEARCH_API_URL = "https://www.gov.uk/api/search.json"

Order = Literal["relevance", "updated_newest", "updated_oldest"]
SearchParams = dict[str, str | int | list[str]]


@dataclass(frozen=True)
class GovUKSearchResponse:
    count: int
    start: int
    total: int
    params: SearchParams
    results: list[GovUKSearchResult]


@dataclass(frozen=True)
class GovUKSearchResult:
    title: str
    description: str
    format: str
    link: str
    timestamp: str
    organisations: list[GovUKOrganisation]


@dataclass(frozen=True)
class GovUKOrganisation:
    title: str
    slug: str
    parents: list[str]


# TODO(jearly): Support filter and reject
def run_gov_uk_search(
    query: str,
    count: int = 10,
    start: int = 0,
    order: Order = "relevance",
    timeout: int = 10,
    date_from: str | None = None,
    date_to: str | None = None,
) -> GovUKSearchResponse:
    """
    Run a query against the GOV.UK search API.

    Args:
        query: Content to search for.
        count: Maximum number of items to return. May be below this if insufficient results found. Max = 1500.
        start: Result offset. E.g. count=1, start=1 returns the second result.
        order: Sort order. One of "relevance", "updated_newest", "updated_oldest".
        timeout: Request timeout in seconds.
        date_from: Earliest date for results (YYYY-MM-DD, inclusive, 00:00).
        date_to: Latest date for results (YYYY-MM-DD, inclusive, 23:59).

    Returns:
        Parsed search response containing result list and metadata.

    Raises:
        ValueError: If any argument fails validation.
        requests.HTTPError: If the API returns a non-2xx status.
    """
    _validate_args(count, start, order, date_from, date_to)
    params = _build_params(query, count, start, order, date_from, date_to)
    api_response = requests.get(GOV_UK_SEARCH_API_URL, params=params, timeout=timeout)
    api_response.raise_for_status()
    data = api_response.json()
    response = _parse_results(data, params)
    return response


def _validate_args(
    count: int,
    start: int,
    order: Order,
    date_from: str | None,
    date_to: str | None,
) -> None:
    """
    Validate search arguments before building the API request.

    Args:
        count: Number of results to return. Must be 0–1500.
        start: Result offset. Must be non-negative.
        order: Sort order. Must be a valid Order literal.
        date_from: Earliest result date (YYYY-MM-DD). Must parse as a valid date.
        date_to: Latest result date (YYYY-MM-DD). Must parse as a valid date and not precede date_from.

    Raises:
        ValueError: If any argument is out of range, malformed, or logically inconsistent.
    """
    if count > 1500:
        raise ValueError(f"{count=} is too high. Limit is 1500.")
    if count < 0:
        raise ValueError(f"{count=} cannot be a negative number.")
    if start < 0:
        raise ValueError(f"{start=} cannot be a negative number.")
    if date_from is not None:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"{date_from=} is not a valid date. Expected format: YYYY-MM-DD.")
    if date_to is not None:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"{date_to=} is not a valid date. Expected format: YYYY-MM-DD.")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError(f"{date_to=} comes before {date_from=}. Swap these around?")
    if order not in get_args(Order):
        raise ValueError(f"Invalid {order=}. Expected one of {get_args(Order)}")


def _build_params(
    query: str,
    count: int = 10,
    start: int = 0,
    order: Order = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
) -> SearchParams:
    """
    Build the query parameter dict for the GOV.UK search API.

    Args:
        query: Search query string.
        count: Maximum number of results to request.
        start: Result offset.
        order: Sort order.
        date_from: Earliest result date (YYYY-MM-DD).
        date_to: Latest result date (YYYY-MM-DD).

    Returns:
        Dict of query parameters ready to pass to requests.get.
    """
    params: SearchParams = {
        "q": query,
        "count": count,
        "start": start,
        "fields": [
            "title",
            "description",
            "format",
            "link",
            "organisations",
            "public_timestamp",
        ],
    }
    if (order_param := _order_to_param(order)) is not None:
        params["order"] = order_param
    if (dates_param := _dates_to_param(date_from, date_to)) is not None:
        params["filter_public_timestamp"] = dates_param
    return params


def _order_to_param(order: Order) -> str | None:
    """
    Convert an Order to the required parameter to pass to the API.

    API can sort based on (most) field names, and uses -<field_name> to sort in descending order.
    In our case we constrain to just sorted by newest/oldest updated, which uses the public_timestamp field.
    Default sorting approach for the API is relevance, so in that case we don't need to pass a param and return None.

    Args:
        order: Sort order to convert.

    Returns:
        API sort parameter string, or None if order is "relevance" (API default).
    """
    match order:
        case "relevance":
            return None
        case "updated_newest":
            return "-public_timestamp"
        case "updated_oldest":
            return "public_timestamp"


def _dates_to_param(
    date_from: str | None = None,
    date_to: str | None = None,
) -> str | None:
    """
    Convert optional date bounds into a single filter string for the API.

    Args:
        date_from: Earliest date for results (YYYY-MM-DD, inclusive, 00:00).
        date_to: Latest date for results (YYYY-MM-DD, inclusive, 23:59).

    Returns:
        Comma-separated filter string (e.g. "from:2024-01-01,to:2024-12-31"), or None if both dates are absent.
    """
    str_parts = []
    if date_from is not None:
        str_parts.append(f"from:{date_from}")
    if date_to is not None:
        str_parts.append(f"to:{date_to}")
    return ",".join(str_parts) if len(str_parts) > 0 else None


def _parse_results(data: dict[str, Any], params: SearchParams) -> GovUKSearchResponse:
    """
    Parse raw API response JSON into typed dataclasses.

    Args:
        data: Decoded JSON response body from the GOV.UK search API.
        params: Original query parameters used for the request, stored on the response.

    Returns:
        Structured search response with typed results and organisations.
    """
    results = []
    for r in data["results"]:
        orgs = []
        for o in r["organisations"]:
            org = GovUKOrganisation(
                title=o.get("title", "Missing Title"),
                slug=o.get("slug", "Missing Slug"),
                parents=o.get("parent_organisations", "Missing Parents"),
            )
            orgs.append(org)
        result = GovUKSearchResult(
            title=r["title"],
            description=r["description"],
            format=r["format"],
            link=f"https://www.gov.uk{r['link']}",
            timestamp=r["public_timestamp"],
            organisations=orgs,
        )
        results.append(result)
    response = GovUKSearchResponse(
        count=len(data["results"]),
        start=data["start"],
        total=data["total"],
        params=params,
        results=results,
    )
    return response
