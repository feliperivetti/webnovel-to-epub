"""Optional, sequential browser transport for the diagnostic CLI, not API workers."""

import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests


class BrowserTransport:
    def __init__(self, output_dir, channel="msedge", headed=False, wait_seconds=45,
                 pause=False, proxy_url=None):
        # Keep the browser dependency optional for normal scraping and offline tests.
        from playwright.sync_api import sync_playwright

        self.output_dir = Path(output_dir)
        self.wait_seconds = wait_seconds
        self.pause = pause
        self.events = []
        self._playwright = sync_playwright().start()
        options = {"headless": not headed}
        if channel != "chromium":
            options["channel"] = channel
        if proxy_url:
            proxy = urlsplit(proxy_url)
            options["proxy"] = {"server": f"{proxy.scheme}://{proxy.hostname}:{proxy.port}"}
            if proxy.username:
                options["proxy"]["username"] = unquote(proxy.username)
                options["proxy"]["password"] = unquote(proxy.password or "")
        try:
            self.browser = self._playwright.chromium.launch(**options)
            # A new context starts without the user's existing cookies or logins.
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
        except Exception:
            try:
                if hasattr(self, "browser"):
                    self.browser.close()
            finally:
                self._playwright.stop()
            raise

    def request(self, method, url, *args, **kwargs):
        from playwright.sync_api import TimeoutError as BrowserTimeout

        if method.upper() != "GET":
            raise ValueError("Browser diagnostics only supports GET requests")
        number = len(self.events) + 1
        prefix = self.output_dir / f"browser-{number:02d}"
        started = time.perf_counter()
        documents = []

        def observe(response):
            if response.request.is_navigation_request() and response.frame == self.page.main_frame:
                documents.append(response)

        self.page.on("response", observe)
        event = {"requested_url": url, "ready": False}
        self.events.append(event)
        content_selector = "div.fic-header, div.chapter-inner.chapter-content"

        def console_message(message):
            if message.type == "error":
                event.setdefault("console_errors", []).append(message.text[:1000])

        def failed_request(request):
            event.setdefault("failed_requests", []).append({"url": request.url, "failure": request.failure})

        self.page.on("console", console_message)
        self.page.on("requestfailed", failed_request)
        try:
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=kwargs.get("timeout", 15) * 1000)
            except BrowserTimeout:
                event["navigation_timeout"] = True
            # Snapshots are evidence; do not execute or replay a saved challenge.
            prefix.with_name(prefix.name + "-initial.html").write_text(self.page.content(), encoding="utf-8")
            event["initial_title"] = self.page.title()
            print(f"Browser initial title: {event['initial_title']}", flush=True)
            try:
                # Wait for real RoyalRoad content, not an arbitrary fixed delay.
                self.page.wait_for_selector(
                    content_selector,
                    state="attached", timeout=self.wait_seconds * 1000,
                )
                event["ready"] = True
            except BrowserTimeout:
                event["wait_timeout"] = True
            if self.pause:
                print("Browser open for manual inspection. Press Enter in this terminal to continue.", flush=True)
                input()
                event["ready"] = self.page.locator(content_selector).count() > 0
            html = self.page.content()
            prefix.with_name(prefix.name + "-final.html").write_text(html, encoding="utf-8")
            self.page.screenshot(path=str(prefix.with_name(prefix.name + "-final.png")))
            event.update({"final_title": self.page.title(), "final_url": self.page.url,
                          "seconds": round(time.perf_counter() - started, 3)})
            print(f"Browser final title: {event['final_title']} | ready={event['ready']}", flush=True)
            response = requests.Response()
            response.status_code = documents[-1].status if documents else 200
            response.url = self.page.url
            response.encoding = "utf-8"
            response._content = html.encode("utf-8")
            response.headers["Content-Type"] = "text/html; charset=utf-8"
            return response
        except Exception as exc:
            event["error_type"] = type(exc).__name__
            event["error"] = str(exc)
            raise
        finally:
            self.page.remove_listener("response", observe)
            self.page.remove_listener("console", console_message)
            self.page.remove_listener("requestfailed", failed_request)

    def close(self):
        try:
            self.browser.close()
        finally:
            self._playwright.stop()
