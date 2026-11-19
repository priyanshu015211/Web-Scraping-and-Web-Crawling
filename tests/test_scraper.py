from unittest.mock import Mock, patch

import pytest

from scraper import ScraperError, crawl_site, scrape_page, validate_url


def test_rejects_non_http_scheme():
    with pytest.raises(ScraperError):
        validate_url("file:///etc/passwd")


def test_rejects_localhost():
    with pytest.raises(ScraperError):
        validate_url("http://localhost:5000")


def test_extracts_page_content():
    response = Mock()
    response.is_redirect = False
    response.is_permanent_redirect = False
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    response.url = "https://example.com"
    response.iter_content.return_value = [b"""<html><head><title>Example title</title>
      <meta name='description' content='A test page'></head><body>
      <h1>Hello</h1><p>Sample paragraph</p><a href='/about'>About</a>
      </body></html>"""]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)

    with patch("scraper.validate_url", return_value="https://example.com"), \
         patch("scraper.requests.get", return_value=response):
        result = scrape_page("https://example.com")

    assert result["title"] == "Example title"
    assert result["description"] == "A test page"
    assert result["headings"]["h1"] == ["Hello"]
    assert result["paragraphs"] == ["Sample paragraph"]
    assert result["links"][0]["url"] == "https://example.com/about"


def test_crawler_stays_on_same_domain_and_respects_page_limit():
    first = {
        "url": "https://example.com", "title": "Home",
        "counts": {"paragraphs": 1, "links": 2},
        "links": [
            {"url": "https://example.com/about"},
            {"url": "https://other.example/about"},
        ],
    }
    second = {
        "url": "https://example.com/about", "title": "About",
        "counts": {"paragraphs": 2, "links": 0}, "links": [],
    }
    with patch("scraper.validate_url", return_value="https://example.com"), \
         patch("scraper.scrape_page", side_effect=[first, second]):
        result = crawl_site("https://example.com", max_pages=2)

    assert result["pages_crawled"] == 2
    assert [page["title"] for page in result["pages"]] == ["Home", "About"]


def test_crawler_rejects_large_page_limit():
    with pytest.raises(ScraperError):
        crawl_site("https://example.com", max_pages=20)
