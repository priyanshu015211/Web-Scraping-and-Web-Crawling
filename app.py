"""Flask web interface for the beginner-friendly web scraper."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from scraper import ScraperError, crawl_site, scrape_page

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

# Log to both the terminal and a rotating file.
(BASE_DIR / "logs").mkdir(exist_ok=True)
file_handler = RotatingFileHandler(
    BASE_DIR / "logs" / "app.log", maxBytes=1_000_000, backupCount=3
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s: %(message)s"
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/scrape")
def scrape():
    payload = request.get_json(silent=True) or request.form
    url = (payload.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Please enter a URL."}), 400

    try:
        result = scrape_page(url)
        app.logger.info("Scraped %s successfully", result["url"])
        return jsonify(result)
    except ScraperError as exc:
        app.logger.warning("Scrape failed for %s: %s", url, exc)
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Unexpected scraping error for %s", url)
        return jsonify({"error": "An unexpected error occurred. Check the application log."}), 500


@app.post("/crawl")
def crawl():
    payload = request.get_json(silent=True) or request.form
    url = (payload.get("url") or "").strip()
    try:
        max_pages = int(payload.get("max_pages", 5))
        result = crawl_site(url, max_pages=max_pages)
        app.logger.info("Crawled %s pages starting at %s", result["pages_crawled"], url)
        return jsonify(result)
    except (ValueError, TypeError):
        return jsonify({"error": "max_pages must be a number between 1 and 5."}), 400
    except ScraperError as exc:
        app.logger.warning("Crawl failed for %s: %s", url, exc)
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Unexpected crawling error for %s", url)
        return jsonify({"error": "An unexpected error occurred. Check the application log."}), 500


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "The submitted request is too large."}), 413


if __name__ == "__main__":
    # Debug mode is convenient locally. Do not enable it on a public server.
    app.run(host="127.0.0.1", port=5000, debug=True)
