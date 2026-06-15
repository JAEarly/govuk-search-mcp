import html
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

GOV_UK_CONTENT_API_URL = "https://www.gov.uk/api/content"


@dataclass(frozen=True)
class GovUKAttachment:
    title: str
    attachment_type: str
    url: str
    content_type: str | None
    file_size: int | None
    number_of_pages: int | None


@dataclass(frozen=True)
class GovUKPageContent:
    title: str
    description: str | None
    document_type: str
    schema_name: str
    base_path: str
    body: str
    attachments: list[GovUKAttachment]


def run_gov_uk_page_fetch(url: str, plain_text: bool = False, timeout: int = 10) -> GovUKPageContent:
    """
    Fetch structured content for a GOV.UK page via the Content API.

    Args:
        url: Full GOV.UK URL or path (e.g. https://www.gov.uk/guidance/foo or /guidance/foo).
        plain_text: If True, strip HTML tags from the body and return plain text.
        timeout: Request timeout in seconds.

    Returns:
        Structured page content with body text and attachment metadata.

    Raises:
        ValueError: If the URL is not a GOV.UK URL or the path cannot be extracted.
        requests.HTTPError: If the API returns a non-2xx status.
    """
    path = _extract_path(url)
    api_url = f"{GOV_UK_CONTENT_API_URL}{path}"
    response = requests.get(api_url, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return _parse_content(data, plain_text=plain_text)


def _extract_path(url: str) -> str:
    """
    Extract the path component from a GOV.UK URL or bare path.

    Args:
        url: Full URL or path string.

    Returns:
        Path string starting with /.

    Raises:
        ValueError: If the URL is not a gov.uk URL or has no path.
    """
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        if not parsed.netloc.endswith("gov.uk"):
            raise ValueError(f"Not a GOV.UK URL: {url!r}")
        path = parsed.path
    else:
        path = url if url.startswith("/") else f"/{url}"
    if not path or path == "/":
        raise ValueError(f"No path found in URL: {url!r}")
    return path.rstrip("/")


def _strip_html(body: str) -> str:
    """
    Strip HTML tags from a string and decode HTML entities.

    Args:
        body: HTML string.

    Returns:
        Plain text string.
    """
    text = re.sub(r"<[^>]+>", " ", body)
    text = html.unescape(text)
    return re.sub(r" {2,}", " ", text).strip()


def _parse_content(data: dict[str, Any], plain_text: bool = False) -> GovUKPageContent:
    """
    Parse raw Content API JSON into typed dataclasses.

    Args:
        data: Decoded JSON response from the GOV.UK Content API.
        plain_text: If True, strip HTML tags from the body.

    Returns:
        Structured page content.
    """
    details = data.get("details", {})

    body = details.get("body", "")
    if isinstance(body, list):
        body = "\n".join(part.get("content", "") for part in body if isinstance(part, dict))

    if plain_text:
        body = _strip_html(body)

    raw_attachments = details.get("attachments", [])
    attachments = [_parse_attachment(a) for a in raw_attachments]

    return GovUKPageContent(
        title=data.get("title", ""),
        description=data.get("description", ""),
        document_type=data.get("document_type", ""),
        schema_name=data.get("schema_name", ""),
        base_path=data.get("base_path", ""),
        body=body,
        attachments=attachments,
    )


def _parse_attachment(a: dict[str, Any]) -> GovUKAttachment:
    """
    Parse a single attachment dict from the Content API.

    Args:
        a: Raw attachment dict.

    Returns:
        Typed GovUKAttachment.
    """
    url = a.get("url", "")
    if url and not url.startswith("http"):
        url = f"https://www.gov.uk{url}"
    return GovUKAttachment(
        title=a.get("title", ""),
        attachment_type=a.get("attachment_type", ""),
        url=url,
        content_type=a.get("content_type"),
        file_size=a.get("file_size"),
        number_of_pages=a.get("number_of_pages"),
    )
