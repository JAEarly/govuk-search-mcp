from unittest.mock import MagicMock, patch

import pytest
import requests

from govuk_search_mcp.content import (
    GovUKAttachment,
    _extract_path,
    _parse_attachment,
    _parse_content,
    _strip_html,
    run_gov_uk_page_fetch,
)

# --- run_gov_uk_page_fetch ---


def run_gov_uk_page_fetch__ok() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "title": "Test Page",
        "description": "A test page",
        "document_type": "press_release",
        "schema_name": "news_article",
        "base_path": "/government/news/test",
        "details": {
            "body": "<p>Body text</p>",
            "attachments": [],
        },
    }
    with patch("govuk_search_mcp.content.requests.get", return_value=mock_response):
        result = run_gov_uk_page_fetch("https://www.gov.uk/government/news/test")
    assert result.title == "Test Page"
    assert result.body == "<p>Body text</p>"
    assert result.attachments == []


def run_gov_uk_page_fetch__plain_text() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "title": "Test Page",
        "description": "A test page",
        "document_type": "press_release",
        "schema_name": "news_article",
        "base_path": "/government/news/test",
        "details": {
            "body": "<p>Body text</p>",
            "attachments": [],
        },
    }
    with patch("govuk_search_mcp.content.requests.get", return_value=mock_response):
        result = run_gov_uk_page_fetch("https://www.gov.uk/government/news/test", plain_text=True)
    assert result.body == "Body text"


def run_gov_uk_page_fetch__http_error() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404")
    with patch("govuk_search_mcp.content.requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            run_gov_uk_page_fetch("https://www.gov.uk/guidance/foo")


def run_gov_uk_page_fetch__invalid_url() -> None:
    with pytest.raises(ValueError, match="Not a GOV.UK URL"):
        run_gov_uk_page_fetch("https://example.com/foo")


# --- _strip_html ---


def test__strip_html__removes_tags() -> None:
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test__strip_html__decodes_entities() -> None:
    assert _strip_html("<p>Costs &amp; benefits &gt; zero</p>") == "Costs & benefits > zero"


def test__strip_html__collapses_whitespace() -> None:
    assert _strip_html("<h2>Title</h2><p>Body</p>") == "Title Body"


def test__strip_html__empty_string() -> None:
    assert _strip_html("") == ""


# --- _extract_path ---


def test__extract_path__full_url() -> None:
    assert _extract_path("https://www.gov.uk/guidance/foo") == "/guidance/foo"


def test__extract_path__http_url() -> None:
    assert _extract_path("http://www.gov.uk/guidance/foo") == "/guidance/foo"


def test__extract_path__bare_path_with_slash() -> None:
    assert _extract_path("/guidance/foo") == "/guidance/foo"


def test__extract_path__bare_path_without_slash() -> None:
    assert _extract_path("guidance/foo") == "/guidance/foo"


def test__extract_path__strips_trailing_slash() -> None:
    assert _extract_path("https://www.gov.uk/guidance/foo/") == "/guidance/foo"


def test__extract_path__non_govuk_domain_raises() -> None:
    with pytest.raises(ValueError, match="Not a GOV.UK URL"):
        _extract_path("https://example.com/foo")


def test__extract_path__root_path_raises() -> None:
    with pytest.raises(ValueError, match="No path found"):
        _extract_path("https://www.gov.uk/")


def test__extract_path__subdomain_govuk_ok() -> None:
    assert _extract_path("https://assets.publishing.service.gov.uk/foo") == "/foo"


# --- _parse_content ---


def test__parse_content__null_description_ok() -> None:
    data = {
        "title": "Sub-page",
        "description": None,
        "document_type": "dt",
        "schema_name": "sn",
        "base_path": "/p",
        "details": {"body": "", "attachments": []},
    }
    result = _parse_content(data)
    assert result.description is None


def test__parse_content__news_page_no_attachments() -> None:
    data = {
        "title": "My News",
        "description": "A press release",
        "document_type": "press_release",
        "schema_name": "news_article",
        "base_path": "/government/news/my-news",
        "details": {
            "body": "<p>Some body</p>",
            "attachments": [],
        },
    }
    result = _parse_content(data)
    assert result.title == "My News"
    assert result.description == "A press release"
    assert result.document_type == "press_release"
    assert result.schema_name == "news_article"
    assert result.base_path == "/government/news/my-news"
    assert result.body == "<p>Some body</p>"
    assert result.attachments == []


def test__parse_content__publication_with_attachments() -> None:
    data = {
        "title": "My Publication",
        "description": "",
        "document_type": "policy_paper",
        "schema_name": "publication",
        "base_path": "/government/publications/my-pub",
        "details": {
            "body": "<p>Body</p>",
            "attachments": [
                {
                    "title": "HTML doc",
                    "attachment_type": "html",
                    "url": "/government/publications/my-pub/html-doc",
                },
                {
                    "title": "PDF doc",
                    "attachment_type": "file",
                    "url": "https://assets.publishing.service.gov.uk/media/abc/doc.pdf",
                    "content_type": "application/pdf",
                    "file_size": 100000,
                    "number_of_pages": 10,
                },
            ],
        },
    }
    result = _parse_content(data)
    assert len(result.attachments) == 2
    assert result.attachments[0].attachment_type == "html"
    assert result.attachments[1].content_type == "application/pdf"
    assert result.attachments[1].number_of_pages == 10


def test__parse_content__plain_text() -> None:
    data = {
        "title": "T",
        "description": "",
        "document_type": "dt",
        "schema_name": "sn",
        "base_path": "/p",
        "details": {"body": "<h2>Title</h2><p>Para &amp; more</p>", "attachments": []},
    }
    result = _parse_content(data, plain_text=True)
    assert "<" not in result.body
    assert "Title" in result.body
    assert "Para & more" in result.body


def test__parse_content__body_as_list() -> None:
    data = {
        "title": "T",
        "description": "",
        "document_type": "dt",
        "schema_name": "sn",
        "base_path": "/p",
        "details": {
            "body": [
                {"content": "<p>Part one</p>", "content_type": "text/html"},
                {"content": "<p>Part two</p>", "content_type": "text/html"},
            ],
            "attachments": [],
        },
    }
    result = _parse_content(data)
    assert result.body == "<p>Part one</p>\n<p>Part two</p>"


def test__parse_content__missing_details_ok() -> None:
    data = {
        "title": "T",
        "description": "",
        "document_type": "dt",
        "schema_name": "sn",
        "base_path": "/p",
    }
    result = _parse_content(data)
    assert result.body == ""
    assert result.attachments == []


# --- _parse_attachment ---


def test__parse_attachment__html_relative_url() -> None:
    a = _parse_attachment(
        {
            "title": "HTML doc",
            "attachment_type": "html",
            "url": "/government/publications/foo/bar",
        }
    )
    assert a.url == "https://www.gov.uk/government/publications/foo/bar"
    assert a.content_type is None
    assert a.file_size is None
    assert a.number_of_pages is None


def test__parse_attachment__file_absolute_url() -> None:
    a = _parse_attachment(
        {
            "title": "PDF doc",
            "attachment_type": "file",
            "url": "https://assets.publishing.service.gov.uk/media/abc/doc.pdf",
            "content_type": "application/pdf",
            "file_size": 259611,
            "number_of_pages": 22,
        }
    )
    assert a.url == "https://assets.publishing.service.gov.uk/media/abc/doc.pdf"
    assert a.content_type == "application/pdf"
    assert a.file_size == 259611
    assert a.number_of_pages == 22


def test__parse_attachment__returns_govuk_attachment() -> None:
    a = _parse_attachment({"title": "T", "attachment_type": "html", "url": "/foo"})
    assert isinstance(a, GovUKAttachment)
