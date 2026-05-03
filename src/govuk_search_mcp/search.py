from dataclasses import dataclass
from typing import Literal, get_args

import requests

GOV_UK_SEARCH_API_URL = "https://www.gov.uk/api/search.json"

Order = Literal["relevance", "updated_newest", "updated_oldest"]


@dataclass(frozen=True)
class GovUKSearchResponse:
    count: int
    start: int
    total: int
    params: dict[str, str | int | list[str]]
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
    """
    if count > 1500:
        raise ValueError(f"Requested count of {count} is too high. Limit is 1500.")

    params: dict[str, str | int | list[str]] = {
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

    # Include data range if from or to is provided
    if date_from is not None:
        if date_to is not None:
            params["filter_public_timestamp"] = f"from:{date_from},to:{date_to}"
        else:
            params["filter_public_timestamp"] = f"from:{date_from}"
    elif date_to is not None:
        params["filter_public_timestamp"] = f"to:{date_to}"

    # Include order - only applied for updated newest or oldest. API defaults to relevance so no need to apply.
    # API expects field_name or -field_name, so use public timestamp.
    match order:
        case "relevance":
            pass
        case "updated_newest":
            params["order"] = "-public_timestamp"
        case "updated_oldest":
            params["order"] = "public_timestamp"
        case _:
            raise ValueError(f"Invalid order {order}. Expected one of {get_args(Order)}")

    # Make request and parse results
    api_response = requests.get(GOV_UK_SEARCH_API_URL, params=params, timeout=timeout)
    api_response.raise_for_status()
    data = api_response.json()
    results = []
    for r in data["results"]:
        orgs = []
        for o in r["organisations"]:
            org = GovUKOrganisation(
                title=o["title"],
                slug=o["slug"],
                parents=o["parent_organisations"],
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


if __name__ == "__main__":
    response = run_gov_uk_search(query="passport", count=1, start=1)
    print(response)
