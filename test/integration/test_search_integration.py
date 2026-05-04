from datetime import datetime

from govuk_search_mcp.search import run_gov_uk_search


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def test__run_gov_uk_search__simple() -> None:
    response = run_gov_uk_search(query="passport")
    assert len(response.results) == response.count == 10
    assert response.start == 0
    assert response.total >= 10
    assert response.params["q"] == "passport"


def test__run_gov_uk_search__custom_count() -> None:
    response = run_gov_uk_search(query="passport", count=5)
    assert len(response.results) == response.count == 5
    assert response.params["count"] == 5


def test__run_gov_uk_search__custom_start() -> None:
    response_page1 = run_gov_uk_search(query="passport", count=5, start=0)
    response_page2 = run_gov_uk_search(query="passport", count=5, start=5)
    assert response_page2.start == 5
    links_page1 = {r.link for r in response_page1.results}
    links_page2 = {r.link for r in response_page2.results}
    assert links_page1.isdisjoint(links_page2)


def test__run_gov_uk_search__order_updated_newest() -> None:
    response = run_gov_uk_search(query="passport", count=5, order="updated_newest")
    timestamps = [_parse_ts(r.timestamp) for r in response.results]
    # Checking sorting is already applied, i.e. sorting again does not change order
    assert timestamps == sorted(timestamps, reverse=True)


def test__run_gov_uk_search__order_updated_oldest() -> None:
    response = run_gov_uk_search(query="passport", count=5, order="updated_oldest")
    timestamps = [_parse_ts(r.timestamp) for r in response.results]
    # Checking sorting is already applied, i.e. sorting again does not change order
    assert timestamps == sorted(timestamps)


def test__run_gov_uk_search__date_from() -> None:
    date_from = "2023-01-01"
    response = run_gov_uk_search(query="passport", count=5, date_from=date_from)
    cutoff = _parse_ts(f"{date_from}T00:00:00Z")
    for result in response.results:
        assert _parse_ts(result.timestamp) >= cutoff


def test__run_gov_uk_search__date_to() -> None:
    date_to = "2023-12-31"
    response = run_gov_uk_search(query="passport", count=5, date_to=date_to)
    cutoff = _parse_ts(f"{date_to}T23:59:59Z")
    for result in response.results:
        assert _parse_ts(result.timestamp) <= cutoff


def test__run_gov_uk_search__date_range() -> None:
    date_from, date_to = "2022-01-01", "2022-12-31"
    response = run_gov_uk_search(query="passport", count=5, date_from=date_from, date_to=date_to)
    lower = _parse_ts(f"{date_from}T00:00:00Z")
    upper = _parse_ts(f"{date_to}T23:59:59Z")
    for result in response.results:
        assert lower <= _parse_ts(result.timestamp) <= upper
