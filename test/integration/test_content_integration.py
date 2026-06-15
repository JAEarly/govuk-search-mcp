from govuk_search_mcp.content import run_gov_uk_page_fetch

PUBLICATION_URL = "https://www.gov.uk/government/publications/ai-opportunities-action-plan-government-response"
NEWS_URL = "https://www.gov.uk/government/news/children-and-parents-to-pilot-social-media-bans-time-limits-and-curfews-at-home-as-government-tests-next-steps-to-give-uk-kids-their-childhood-back"


def test__run_gov_uk_page_fetch__publication_has_body() -> None:
    result = run_gov_uk_page_fetch(PUBLICATION_URL)
    assert result.title != ""
    assert result.body != ""
    assert result.document_type != ""


def test__run_gov_uk_page_fetch__publication_has_attachments() -> None:
    result = run_gov_uk_page_fetch(PUBLICATION_URL)
    assert len(result.attachments) > 0
    for a in result.attachments:
        assert a.title != ""
        assert a.url.startswith("https://")
        assert a.attachment_type in ("html", "file")


def test__run_gov_uk_page_fetch__publication_has_pdf_attachment() -> None:
    result = run_gov_uk_page_fetch(PUBLICATION_URL)
    pdf_attachments = [a for a in result.attachments if a.attachment_type == "file"]
    assert len(pdf_attachments) > 0
    pdf = pdf_attachments[0]
    assert pdf.content_type == "application/pdf"
    assert pdf.file_size is not None and pdf.file_size > 0
    assert pdf.number_of_pages is not None and pdf.number_of_pages > 0


def test__run_gov_uk_page_fetch__news_has_body() -> None:
    result = run_gov_uk_page_fetch(NEWS_URL)
    assert result.title != ""
    assert result.body != ""
    assert result.document_type != ""


def test__run_gov_uk_page_fetch__news_has_no_attachments() -> None:
    result = run_gov_uk_page_fetch(NEWS_URL)
    assert result.attachments == []


def test__run_gov_uk_page_fetch__bare_path() -> None:
    result = run_gov_uk_page_fetch("/government/publications/ai-opportunities-action-plan-government-response")
    assert result.title != ""
    assert len(result.attachments) > 0
