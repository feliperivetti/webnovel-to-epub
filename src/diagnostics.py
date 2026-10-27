"""Inspect the real scrapers without the API, EPUB builder, or chapter placeholders."""

import argparse
import json
import re
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.config import get_settings
from src.services.registry import ScraperRegistry
from src.utils.logger import logger


def create_scraper(url, qty=1, start=1, direct=False):
    """Resolve the same provider as /books/generate; overrides affect this instance only."""
    ScraperRegistry.auto_discover()
    service_cls = ScraperRegistry.get_service(url)
    if service_cls is None:
        raise ValueError(f"Unsupported domain. Available: {ScraperRegistry.get_registered_domains()}")
    service = service_cls()
    try:
        scraper = service.get_book_instance(url, qty, start)
    finally:
        service._session.close()
    if direct:
        scraper.settings = scraper.settings.model_copy(update={
            "PROXY_URL": None, "PROXY_URL_FALLBACK": None,
        })
        scraper._session.proxies.clear()
        # Ignore HTTP(S)_PROXY inherited from the terminal as well.
        scraper._session.trust_env = False
    return scraper


class ScraperDiagnostics:
    """Wrap a scraper's HTTP session, saving evidence even when its parser raises."""

    def __init__(self, scraper, output_dir, timeout=15, html_file=None, selectors=()):
        self.scraper = scraper
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.html_file = Path(html_file) if html_file else None
        self.selectors = selectors
        self.report = {"scraper": scraper.class_name, "requests": [], "steps": [], "ok": False}
        self._secrets = [value for value in (
            scraper.settings.API_JWT_SECRET,
            get_settings().PROXY_URL,
            get_settings().PROXY_URL_FALLBACK,
        ) if value]

    def redact(self, value):
        text = str(value)
        for secret in self._secrets:
            text = text.replace(secret, "[REDACTED]")
        return re.sub(r"(https?://)[^/\s@]+@", r"\1[REDACTED]@", text)

    def say(self, value):
        print(self.redact(value), flush=True)

    @contextmanager
    def capture(self):
        original_request = self.scraper._session.request
        original_formatters = [(handler, handler.formatter) for handler in logger.handlers]
        diagnostics = self

        class RedactingFormatter:
            def __init__(self, formatter):
                self.formatter = formatter

            def format(self, record):
                return diagnostics.redact(self.formatter.format(record))

        for handler, formatter in original_formatters:
            if formatter is not None:
                handler.setFormatter(RedactingFormatter(formatter))

        def observed_request(method, url, *args, **kwargs):
            started = time.perf_counter()
            if self.html_file:
                response = requests.Response()
                response.status_code = 200
                response.url = url
                response._content = self.html_file.read_bytes()
                response.encoding = "utf-8"
                response.headers["Content-Type"] = "text/html; charset=utf-8"
            else:
                kwargs["timeout"] = self.timeout
                try:
                    response = original_request(method, url, *args, **kwargs)
                except requests.RequestException as exc:
                    self.report["requests"].append({
                        "url": self.redact(url), "error": self.redact(exc),
                        "error_type": type(exc).__name__,
                    })
                    raise
            self.inspect_response(response, url, time.perf_counter() - started)
            return response

        self.scraper._session.request = observed_request
        try:
            yield self
        finally:
            self.scraper._session.request = original_request
            for handler, formatter in original_formatters:
                handler.setFormatter(formatter)

    def inspect_response(self, response, requested_url, elapsed):
        number = len(self.report["requests"]) + 1
        filename = f"response-{number:02d}.html"
        # Preserve the body before parsing or raise_for_status can fail.
        (self.output_dir / filename).write_bytes(response.content)
        soup = BeautifulSoup(response.text, "html.parser")
        matches = {}
        for name, selector in getattr(self.scraper, "_selectors", {}).items():
            if isinstance(selector, str):
                matches[name] = len(soup.select(selector))
            else:
                matches[name] = len(soup.find_all(*selector))
        for selector in self.selectors:
            matches[f"custom: {selector}"] = len(soup.select(selector))
        lowered = response.text.lower()
        # These are clues, not proof that a page is blocked.
        hints = [marker for marker in (
            "cf-chl-", "just a moment", "verify you are human", "captcha", "access denied",
            "anubis_challenge", "making sure you&#39;re not a bot",
        ) if marker in lowered]
        entry = {
            "requested_url": self.redact(requested_url), "final_url": self.redact(response.url),
            "status": response.status_code, "content_type": response.headers.get("Content-Type"),
            "bytes": len(response.content), "seconds": round(elapsed, 3),
            "page_title": soup.title.get_text(" ", strip=True) if soup.title else None,
            "redirects": [{"status": r.status_code, "url": self.redact(r.url)} for r in response.history],
            "selectors": matches, "possible_block_markers": hints,
            "html_file": filename, "offline": bool(self.html_file),
        }
        self.report["requests"].append(entry)
        self.say(f"HTTP {response.status_code} | {response.url} | {len(response.content)} bytes | {elapsed:.2f}s")
        self.say(f"  Page title: {entry['page_title']}")
        self.say(f"  Selectors: {matches}")
        if hints:
            self.say(f"  Possible block/challenge (inspect HTML): {', '.join(hints)}")
        self.say(f"  Saved: {self.output_dir / filename}")

    def step(self, name, operation, show_traceback=False):
        try:
            result = operation()
        except Exception as exc:
            self.report["steps"].append({
                "name": name, "ok": False, "error_type": type(exc).__name__,
                "error": self.redact(exc),
            })
            self.say(f"FAIL {name}: {type(exc).__name__}: {exc}")
            if show_traceback:
                self.say(traceback.format_exc())
            return None
        self.report["steps"].append({"name": name, "ok": True, "result": result})
        self.say(f"OK {name}")
        return result

    def metadata(self):
        data = self.scraper.get_book_metadata().model_dump()
        self.say(json.dumps(data, ensure_ascii=False, indent=2))
        return data

    def links(self):
        urls = self.scraper.get_chapters_link()
        if not urls:
            raise ValueError("No chapter URLs found. Inspect the TOC HTML and selectors.")
        for index, url in enumerate(urls, self.scraper._start_chapter):
            self.say(f"  Chapter {index}: {url}")
            if urlparse(url).hostname != urlparse(self.scraper._main_url).hostname:
                self.say("  WARNING: chapter domain differs from the novel domain; check this URL.")
        return urls

    def chapter(self, url, index=1):
        # Call the real parser directly: no placeholder replacement or base-class backoff.
        data = self.scraper.get_chapter_content(url)
        text = BeautifulSoup(data.content, "html.parser").get_text("\n", strip=True)
        if not text:
            raise ValueError(
                f"Empty chapter at {url}. Inspect HTTP status, redirects, and chap_content "
                "selector in report.json; open the saved response HTML."
            )
        html_file = f"chapter-{index:03d}.html"
        text_file = f"chapter-{index:03d}.txt"
        (self.output_dir / html_file).write_text(data.content, encoding="utf-8")
        (self.output_dir / text_file).write_text(text, encoding="utf-8")
        self.say(f"  Title: {data.title} | Text: {len(text)} characters")
        self.say(f"  Preview: {text[:300]}")
        return {"url": url, "title": data.title, "text_characters": len(text),
                "html_file": html_file, "text_file": text_file}

    def fetch(self, url):
        response = self.scraper._session.get(url)
        response.raise_for_status()
        return {"url": response.url, "status": response.status_code}

    def save_report(self):
        self.report["ok"] = bool(self.report["steps"]) and all(s["ok"] for s in self.report["steps"])
        path = self.output_dir / "report.json"
        path.write_text(self.redact(json.dumps(self.report, ensure_ascii=False, indent=2)), encoding="utf-8")
        self.say(f"Report: {path}")
        return self.report["ok"]


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Novel URL (determines which scraper to use)")
    parser.add_argument("--stage", choices=("all", "metadata", "links", "chapter", "fetch"), default="all")
    parser.add_argument("--qty", type=positive_int, default=1, help="Chapters to test sequentially (default: 1)")
    parser.add_argument("--start", type=positive_int, default=1)
    parser.add_argument("--chapter-url", help="Test this exact chapter URL, bypassing link generation")
    parser.add_argument("--direct", action="store_true", help="Ignore configured and system proxies for this run")
    parser.add_argument("--timeout", type=positive_int, default=15, help="HTTP timeout in seconds (default: 15)")
    parser.add_argument("--html", type=Path, help="Parse saved UTF-8 HTML offline; use with an individual stage")
    parser.add_argument("--selector", action="append", default=[], help="Also count matches for this CSS selector")
    parser.add_argument("--output-dir", type=Path, help="Default: diagnostics/<timestamp>")
    parser.add_argument("--traceback", action="store_true", help="Print full tracebacks")
    parser.add_argument("--browser", choices=("chromium", "chrome", "msedge"),
                        help="RoyalRoad diagnostic: load pages with JavaScript in an isolated browser")
    parser.add_argument("--headed", action="store_true", help="Show the diagnostic browser window")
    parser.add_argument("--wait-seconds", type=positive_int, default=45,
                        help="Browser: wait for the actual content selector (default: 45 seconds)")
    parser.add_argument("--pause", action="store_true", help="Browser: wait for Enter for manual inspection")
    args = parser.parse_args(argv)
    if args.html and args.stage == "all":
        parser.error("--html requires --stage metadata, links, chapter, or fetch")
    if args.browser and args.html:
        parser.error("--browser cannot be combined with offline --html")
    if (args.headed or args.pause) and not args.browser:
        parser.error("--headed and --pause require --browser")
    if args.pause and not args.headed:
        parser.error("--pause requires --headed")
    if args.browser and urlparse(args.url).hostname not in ("royalroad.com", "www.royalroad.com"):
        parser.error("--browser currently waits for RoyalRoad selectors; use a RoyalRoad novel URL")
    if args.html and not args.html.is_file():
        parser.error(f"HTML file does not exist: {args.html}")
    if args.chapter_url and args.stage not in ("all", "chapter", "fetch"):
        parser.error("--chapter-url is only used with --stage all, chapter, or fetch")
    if urlparse(args.url).scheme not in ("http", "https") or not urlparse(args.url).hostname:
        parser.error("url must be an absolute HTTP(S) URL")
    if args.chapter_url and urlparse(args.chapter_url).scheme not in ("http", "https"):
        parser.error("--chapter-url must be an absolute HTTP(S) URL")

    output_dir = args.output_dir or Path("diagnostics") / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    try:
        scraper = create_scraper(args.url, args.qty, args.start, args.direct or bool(args.html))
    except ValueError as exc:
        parser.error(str(exc))
    diagnostics = ScraperDiagnostics(scraper, output_dir, args.timeout, args.html, args.selector)
    diagnostics.report["mode"] = "offline" if args.html else "direct" if args.direct else "configured"
    browser = None
    if args.browser:
        try:
            from src.browser_transport import BrowserTransport
            browser = BrowserTransport(
                output_dir, args.browser, args.headed, args.wait_seconds,
                args.pause, None if args.direct else scraper.settings.PROXY_URL,
            )
        except ImportError:
            scraper._session.close()
            parser.error("Install the optional dependency: python -m pip install -r requirements-browser.txt")
        except Exception as exc:
            scraper._session.close()
            diagnostics.report["steps"].append({
                "name": "browser-start", "ok": False,
                "error_type": type(exc).__name__, "error": diagnostics.redact(exc),
            })
            diagnostics.say(f"FAIL browser-start: {type(exc).__name__}: {exc}")
            diagnostics.save_report()
            return 1
        scraper._session.request = browser.request
        diagnostics.report["browser"] = {"channel": args.browser, "headed": args.headed, "pages": browser.events}
    diagnostics.say(f"Scraper: {scraper.class_name} | Mode: {diagnostics.report['mode']}")
    def run_step(name, operation):
        return diagnostics.step(name, operation, args.traceback)
    try:
        with diagnostics.capture():
            if args.stage == "fetch":
                run_step("fetch", lambda: diagnostics.fetch(args.chapter_url or args.url))
            else:
                if args.stage in ("all", "metadata"):
                    run_step("metadata", diagnostics.metadata)
                urls = []
                if args.stage == "links" or (args.stage in ("all", "chapter") and not args.chapter_url and not args.html):
                    urls = run_step("links", diagnostics.links) or []
                if args.stage in ("all", "chapter"):
                    if args.chapter_url or args.html:
                        urls = [args.chapter_url or args.url]
                    for index, url in enumerate(urls, args.start):
                        run_step(f"chapter-{index}", lambda url=url, index=index: diagnostics.chapter(url, index))
    finally:
        scraper._session.close()
        try:
            if browser:
                browser.close()
        finally:
            ok = diagnostics.save_report()
    diagnostics.say("PASS: all selected checks passed." if ok else "FAIL: see report.json and saved HTML.")
    return 0 if ok else 1
