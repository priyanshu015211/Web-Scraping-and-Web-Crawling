# Simple Flask Web Scraper

A beginner-friendly web scraping application built with **Python, Flask, Requests and BeautifulSoup**. Enter a public webpage URL and view its title, meta description, headings, paragraphs and links in a simple browser interface. Results can also be downloaded as JSON.

## Features

- Simple Flask web interface
- Extracts page title and meta description
- Extracts headings (`h1`–`h6`) and paragraphs
- Collects up to 100 unique HTTP/HTTPS links
- Displays extraction counts
- Exports scraped results as JSON
- Request timeout, response-size limit and basic URL validation
- Same-domain breadth-first crawling through `POST /crawl` (maximum five pages)
- Logging to the terminal and `logs/app.log`
- Beginner-friendly code separated into app and scraper modules

## Project structure

```text
Web-Scraping-and-Web-Crawling/
├── app.py                 # Flask routes and application setup
├── scraper.py             # Fetching, parsing and extraction logic
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web interface
├── static/
│   └── style.css          # Interface styling
├── tests/
│   └── test_scraper.py    # Basic scraper tests
├── logs/                  # Created automatically at runtime
├── .gitignore
└── README.md
```

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/priyanshu015211/Web-Scraping-and-Web-Crawling.git
cd Web-Scraping-and-Web-Crawling
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser, enter a public webpage URL and select **Scrape page**.

## API endpoint

### `POST /scrape`

Accepts JSON:

```json
{
  "url": "https://example.com"
}
```

Returns the page URL, title, description, headings, paragraphs, links and extraction counts. Invalid URLs and fetch errors return a JSON error message with an appropriate HTTP status code.

### `POST /crawl`

Accepts JSON:

```json
{
  "url": "https://example.com",
  "max_pages": 5
}
```

Crawls up to five pages on the starting hostname and returns a compact summary for each page. A short delay is used between page requests.

## Run tests

```bash
pytest -q
```

## How it works

1. Flask receives the URL from the browser.
2. The scraper validates the URL and requests the page with a timeout.
3. BeautifulSoup parses the returned HTML.
4. Unneeded script, style and SVG elements are removed.
5. Text and links are extracted into a Python dictionary.
6. Flask returns JSON and the browser renders the results.

## Responsible use and limitations

- Only scrape websites you are permitted to access. Check the website's terms and `robots.txt` before scraping.
- Keep request rates low. The crawler is limited to five same-domain pages and waits briefly between requests.
- The scraper handles ordinary static HTML. It does not execute JavaScript, so content rendered only in a browser may not appear.
- Some sites block automated requests or require authentication.
- Basic URL checks are included, but this is an educational local application, not a hardened public scraping service. Do not expose it to untrusted users without additional SSRF protections, network-level egress controls, stricter redirect handling and security review.
- Run Flask's development server only on your own machine. Use a production WSGI server for deployment.

## Technologies

- Python
- Flask
- Requests
- BeautifulSoup4
- HTML and CSS
- Pytest

## Future improvements

- Add same-domain crawling with a maximum depth and page limit
- Add CSV export
- Add a background task queue for longer crawls
- Add persistent storage for scrape history
- Add Playwright support for JavaScript-rendered pages

## License

No license is included by default. Add a license file if you want to specify how others may use, modify and distribute this project.
