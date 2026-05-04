from unittest.mock import MagicMock, patch

import pytest
import requests

from govuk_search_mcp.search import (
    Order,
    SearchParams,
    _build_params,
    _dates_to_param,
    _order_to_param,
    _parse_results,
    _validate_args,
    run_gov_uk_search,
)


def test__run_gov_uk_search__ok() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": "Passport guidance",
                "description": "How to renew your passport",
                "format": "guide",
                "link": "/passport",
                "public_timestamp": "2024-06-01T00:00:00Z",
                "organisations": [],
            }
        ],
        "start": 0,
        "total": 1,
    }
    with patch("govuk_search_mcp.search.requests.get", return_value=mock_response):
        response = run_gov_uk_search("passport", count=1)
    assert response.count == 1
    assert response.results[0].title == "Passport guidance"


def test__run_gov_uk_search__http_error() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("503")
    with patch("govuk_search_mcp.search.requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            run_gov_uk_search("passport")


def test__validate_args__ok() -> None:
    _validate_args(count=10, start=0, order="relevance", date_from=None, date_to=None)


def test__validate_args__count_too_high() -> None:
    with pytest.raises(ValueError, match=r"count=1501 is too high\. Limit is 1500\."):
        _validate_args(count=1501, start=0, order="relevance", date_from=None, date_to=None)


def test__validate_args__count_at_limit_ok() -> None:
    _validate_args(count=1500, start=0, order="relevance", date_from=None, date_to=None)


def test__validate_args__count_negative() -> None:
    with pytest.raises(ValueError, match=r"count=-1 cannot be a negative number\."):
        _validate_args(count=-1, start=0, order="relevance", date_from=None, date_to=None)


def test__validate_args__start_negative() -> None:
    with pytest.raises(ValueError, match=r"start=-1 cannot be a negative number\."):
        _validate_args(count=10, start=-1, order="relevance", date_from=None, date_to=None)


def test__validate_args__date_range_inverted() -> None:
    with pytest.raises(ValueError, match=r"date_to='2024-01-01' comes before date_from='2024-12-31'"):
        _validate_args(count=10, start=0, order="relevance", date_from="2024-12-31", date_to="2024-01-01")


def test__validate_args__date_from_invalid_format() -> None:
    with pytest.raises(ValueError, match=r"date_from='01-01-2024' is not a valid date\. Expected format: YYYY-MM-DD\."):
        _validate_args(count=10, start=0, order="relevance", date_from="01-01-2024", date_to=None)


def test__validate_args__date_to_invalid_format() -> None:
    with pytest.raises(ValueError, match=r"date_to='not-a-date' is not a valid date\. Expected format: YYYY-MM-DD\."):
        _validate_args(count=10, start=0, order="relevance", date_from=None, date_to="not-a-date")


def test__validate_args__order_invalid() -> None:
    with pytest.raises(ValueError, match=r"order='foobar'"):
        _validate_args(count=10, start=0, order="foobar", date_from=None, date_to=None)  # type: ignore[arg-type]


def test__validate_args__date_range_same_day_ok() -> None:
    _validate_args(count=10, start=0, order="relevance", date_from="2024-06-15", date_to="2024-06-15")


def test__validate_args__date_from_only_ok() -> None:
    _validate_args(count=10, start=0, order="relevance", date_from="2024-01-01", date_to=None)


def test__validate_args__date_to_only_ok() -> None:
    _validate_args(count=10, start=0, order="relevance", date_from=None, date_to="2024-12-31")


def test__build_params__core_fields() -> None:
    params = _build_params("passport", count=5, start=2)
    assert params["q"] == "passport"
    assert params["count"] == 5
    assert params["start"] == 2
    assert "fields" in params


def test__build_params__order_absent_for_relevance() -> None:
    params = _build_params("passport", order="relevance")
    assert "order" not in params


def test__build_params__order_present_for_non_relevance() -> None:
    params = _build_params("passport", order="updated_newest")
    assert "order" in params


def test__build_params__date_filter_absent_without_dates() -> None:
    params = _build_params("passport")
    assert "filter_public_timestamp" not in params


def test__build_params__date_filter_present_with_dates() -> None:
    params = _build_params("passport", date_from="2024-01-01", date_to="2024-12-31")
    assert "filter_public_timestamp" in params


@pytest.mark.parametrize(
    "order,expected",
    [
        ("relevance", None),
        ("updated_newest", "-public_timestamp"),
        ("updated_oldest", "public_timestamp"),
    ],
)
def test__order_to_param__okay(order: Order, expected: str | None) -> None:
    assert _order_to_param(order) == expected


@pytest.mark.parametrize(
    "date_from,date_to,expected",
    [
        (None, None, None),
        ("2024-01-01", None, "from:2024-01-01"),
        (None, "2024-12-31", "to:2024-12-31"),
        ("2024-01-01", "2024-12-31", "from:2024-01-01,to:2024-12-31"),
    ],
)
def test__dates_to_param(date_from: str | None, date_to: str | None, expected: str | None) -> None:
    assert _dates_to_param(date_from, date_to) == expected


def test__parse_results__single_result_with_organisation() -> None:
    org_a = {"title": "Home Office", "slug": "home-office", "parent_organisations": ["cabinet-office"]}
    result_a = {
        "title": "Passport guidance",
        "description": "How to renew your passport",
        "format": "guide",
        "link": "/passport",
        "public_timestamp": "2024-06-01T00:00:00Z",
        "organisations": [org_a],
    }
    data = {
        "results": [result_a],
        "start": 0,
        "total": 1,
    }
    params: SearchParams = {"q": "passport", "count": 10, "start": 0}
    response = _parse_results(data, params)

    assert response.count == 1
    assert response.start == 0
    assert response.total == 1
    assert response.params == params
    result = response.results[0]
    assert result.title == "Passport guidance"
    assert result.description == "How to renew your passport"
    assert result.format == "guide"
    assert result.link == "https://www.gov.uk/passport"
    assert result.timestamp == "2024-06-01T00:00:00Z"
    org = result.organisations[0]
    assert org.title == "Home Office"
    assert org.slug == "home-office"
    assert org.parents == ["cabinet-office"]


def test__parse_results__empty_results() -> None:
    data = {"results": [], "start": 0, "total": 0}
    response = _parse_results(data=data, params={})
    assert response.count == 0
    assert response.results == []


def test__parse_results__multiple_results() -> None:
    result_a = {
        "title": "A",
        "description": "",
        "format": "guide",
        "link": "/a",
        "public_timestamp": "2024-06-01T00:00:00Z",
        "organisations": [],
    }
    result_b = {
        "title": "B",
        "description": "",
        "format": "guide",
        "link": "/b",
        "public_timestamp": "2024-06-01T00:00:00Z",
        "organisations": [],
    }
    data = {
        "results": [result_a, result_b],
        "start": 0,
        "total": 2,
    }

    response = _parse_results(data, {})
    assert response.count == 2
    assert response.results[0].title == "A"
    assert response.results[0].link == "https://www.gov.uk/a"
    assert response.results[1].title == "B"
    assert response.results[1].link == "https://www.gov.uk/b"
