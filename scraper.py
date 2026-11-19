"""Small HTML scraper using Requests and BeautifulSoup."""

import ipaddress
import socket
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

USER_AGENT = "BeginnerFlaskScraper/1.0 (learning project)"
TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_LINKS = 100


class ScraperError(Exception):
    """Raised when a URL cannot safely or successfully be scraped."""


def validate_url(url: str) -> str:
    """Validate an HTTP(S) URL and reject localhost/private network targets."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ScraperError("Enter a valid URL beginning with http:// or https://")
    if parsed.username or parsed.password:
        raise ScraperError("URLs containing usernames or passwords are not supported.")

    hostname = parsed.hostname
    if hostname.lower() == "localhost" or hostname.lower().endswith(".localhost"):
        raise ScraperError("Localhost URLs are not allowed.")

    try:
        addresses = {ipaddress.ip_address(hostname)}
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(hostname, None)
            }
        except socket.gaierror as exc:
            raise ScraperError("The hostname could not be resolved.") from exc

    if any(not address.is_global for address in addresses):
        raise ScraperError("Private, local, and non-public network addresses are not allowed.")
    return url


def scrape_page(url: str) -> dict:
    """Fetch a public HTML page and return its main textual elements and links."""
    url = validate_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    try:
        with requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
            stream=True,
            allow_redirects=False,
        ) as response:
            # Do not follow redirects automatically; validate each destination.
            redirects = 0
            while response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                if not location or redirects >= 3:
                    raise ScraperError("Too many or invalid redirects.")
                next_url = validate_url(urljoin(response.url, location))
                response.close()
                response = requests.get(
                    next_url, headers=headers, timeout=TIMEOUT_SECONDS,
                    stream=True, allow_redirects=False
                )
                redirects += 1

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                raise ScraperError("The URL did not return an HTML page.")

            chunks = []
            size = 0
            for chunk in response.iter_content(chunk_size=16_384):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise ScraperError("The page is larger than the 2 MB limit.")
                chunks.append(chunk)
            html = b"".join(chunks)
    except ScraperError:
        raise
    except requests.Timeout as exc:
        raise ScraperError("The website took too long to respond.") from exc
    except requests.RequestException as exc:
        raise ScraperError(f"Could not fetch the page: {exc}") from exc

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else "No title found"
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content", "").strip() if description_tag else ""

    headings = {
        f"h{level}": [tag.get_text(" ", strip=True) for tag in soup.find_all(f"h{level}")]
        for level in range(1, 7)
    }
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paragraphs = [text for text in paragraphs if text]

    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        absolute = urldefrag(urljoin(url, anchor["href"]))[0]
        parsed_link = urlparse(absolute)
        if parsed_link.scheme in {"http", "https"} and absolute not in seen:
            seen.add(absolute)
            links.append({"text": anchor.get_text(" ", strip=True) or "(no link text)", "url": absolute})
        if len(links) >= MAX_LINKS:
            break

    return {
        "url": url,
        "title": title,
        "description": description,
        "headings": headings,
        "paragraphs": paragraphs[:100],
        "links": links,
        "counts": {
            "headings": sum(len(items) for items in headings.values()),
            "paragraphs": len(paragraphs),
            "links": len(links),
        },
    }


def crawl_site(start_url: str, max_pages: int = 5) -> dict:
    """Crawl a small number of same-domain pages (breadth-first).

    This deliberately conservative learning crawler has a hard limit of five
    pages and waits between page requests. Check the site's terms and robots.txt
    before using it.
    """
    start_url = validate_url(start_url)
    if not isinstance(max_pages, int) or not 1 <= max_pages <= 5:
        raise ScraperError("max_pages must be an integer between 1 and 5.")

    start_host = urlparse(start_url).hostname
    queue = deque([start_url])
    visited = set()
    pages = []
    errors = []

    while queue and len(pages) < max_pages:
        current_url = queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)
        try:
            page = scrape_page(current_url)
            pages.append({
                "url": page["url"],
                "title": page["title"],
                "paragraph_count": page["counts"]["paragraphs"],
                "link_count": page["counts"]["links"],
            })
            for item in page["links"]:
                candidate = item["url"]
                parsed = urlparse(candidate)
                if parsed.hostname == start_host and candidate not in visited:
                    queue.append(candidate)
        except ScraperError as exc:
            errors.append({"url": current_url, "error": str(exc)})
        if queue and len(pages) < max_pages:
            time.sleep(0.5)

    return {"start_url": start_url, "pages_crawled": len(pages), "pages": pages, "errors": errors}
