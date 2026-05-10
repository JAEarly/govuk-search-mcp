from datetime import datetime
from typing import Any

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from govuk_search_mcp.server import mcp


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
async def session():
    async with create_connected_server_and_client_session(mcp, raise_exceptions=True) as s:
        yield s


async def _call(session, tool: str, **kwargs) -> dict[str, Any]:
    result = await session.call_tool(tool, arguments=kwargs)
    assert result.structuredContent is not None
    return result.structuredContent


@pytest.mark.anyio
async def test__search_gov_uk__ok(session):
    response = await _call(session, "search_gov_uk", query="passport")
    assert len(response["results"]) == response["count"] == 10
    assert response["start"] == 0
    assert response["total"] >= 10
    assert response["params"]["q"] == "passport"


@pytest.mark.anyio
async def test__search_gov_uk__custom_count(session):
    response = await _call(session, "search_gov_uk", query="passport", count=5)
    assert len(response["results"]) == response["count"] == 5
    assert response["params"]["count"] == 5


@pytest.mark.anyio
async def test__search_gov_uk__pagination(session):
    page1 = await _call(session, "search_gov_uk", query="passport", count=5, start=0)
    page2 = await _call(session, "search_gov_uk", query="passport", count=5, start=5)
    assert page2["start"] == 5
    links1 = {r["link"] for r in page1["results"]}
    links2 = {r["link"] for r in page2["results"]}
    assert links1.isdisjoint(links2)


@pytest.mark.anyio
async def test__search_gov_uk__date_from(session):
    date_from = "2023-01-01"
    response = await _call(session, "search_gov_uk", query="passport", count=5, date_from=date_from)
    cutoff = _parse_ts(f"{date_from}T00:00:00Z")
    for result in response["results"]:
        assert _parse_ts(result["timestamp"]) >= cutoff


@pytest.mark.anyio
async def test__search_gov_uk__date_to(session):
    date_to = "2023-12-31"
    response = await _call(session, "search_gov_uk", query="passport", count=5, date_to=date_to)
    cutoff = _parse_ts(f"{date_to}T23:59:59Z")
    for result in response["results"]:
        assert _parse_ts(result["timestamp"]) <= cutoff


@pytest.mark.anyio
async def test__search_gov_uk__date_range(session):
    date_from, date_to = "2022-01-01", "2022-12-31"
    response = await _call(session, "search_gov_uk", query="passport", count=5, date_from=date_from, date_to=date_to)
    lower = _parse_ts(f"{date_from}T00:00:00Z")
    upper = _parse_ts(f"{date_to}T23:59:59Z")
    for result in response["results"]:
        assert lower <= _parse_ts(result["timestamp"]) <= upper


@pytest.mark.anyio
async def test__latest_gov_uk__ok(session):
    response = await _call(session, "latest_gov_uk")
    assert len(response["results"]) == response["count"] == 10
    assert response["start"] == 0
    assert response["total"] >= 10


@pytest.mark.anyio
async def test__latest_gov_uk__ordered_newest_first(session):
    response = await _call(session, "latest_gov_uk", count=5)
    timestamps = [_parse_ts(r["timestamp"]) for r in response["results"]]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.anyio
async def test__latest_gov_uk__custom_count(session):
    response = await _call(session, "latest_gov_uk", count=3)
    assert len(response["results"]) == response["count"] == 3


@pytest.mark.anyio
async def test__latest_gov_uk__pagination(session):
    page1 = await _call(session, "latest_gov_uk", count=5, start=0)
    page2 = await _call(session, "latest_gov_uk", count=5, start=5)
    assert page2["start"] == 5
    links1 = {r["link"] for r in page1["results"]}
    links2 = {r["link"] for r in page2["results"]}
    assert links1.isdisjoint(links2)


@pytest.mark.anyio
async def test__latest_gov_uk__date_from(session):
    date_from = "2023-01-01"
    response = await _call(session, "latest_gov_uk", count=5, date_from=date_from)
    cutoff = _parse_ts(f"{date_from}T00:00:00Z")
    for result in response["results"]:
        assert _parse_ts(result["timestamp"]) >= cutoff


@pytest.mark.anyio
async def test__latest_gov_uk__date_to(session):
    date_to = "2023-12-31"
    response = await _call(session, "latest_gov_uk", count=5, date_to=date_to)
    cutoff = _parse_ts(f"{date_to}T23:59:59Z")
    for result in response["results"]:
        assert _parse_ts(result["timestamp"]) <= cutoff
