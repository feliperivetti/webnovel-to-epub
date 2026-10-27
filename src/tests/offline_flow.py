"""Shared HTTP-only simulation for success and chapter-failure API flows."""

import base64
import json
import tempfile
import time
from collections import Counter
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin

import pytest
import requests
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sse_starlette.sse import AppStatus

from src.classes import base_book, centralnovel_book, novelsbr_book
from src.config import get_settings
from src.main import app, verify_internal_token
from src.routes import book_routes
from src.services.metrics_service import MetricsService
from src.services.task_manager import TaskManager


FIXTURES = Path(__file__).parent / "fixtures"
CASES = {
    "panda": {
        "prefix": "pandanovel", "cover": "https://novelphoenix.com/server-1/shadow-slave.jpg",
        "title_selector": "span.chapter-title", "content_selector": "div#content",
    },
    "centralnovel": {
        "prefix": "centralnovel",
        "cover": ("https://i2.wp.com/centralnovel.com/wp-content/uploads/2023/03/"
                  "Shadow-Slave-capa-central.png?resize=370,500"),
        "title_selector": "div.cat-series", "content_selector": "div.epcontent.entry-content",
    },
    "novelsbr": {
        "prefix": "novelsbr", "cover": "https://novels-br.com/s3/escravo-das-sombras.jpeg",
        "title_selector": "h2.chapter-title", "content_selector": "div.chapter-content",
    },
}
COVER_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGP4DwQACfsD/fteaysAAAAASUVORK5CYII="
)


class OfflineHTTP:
    def __init__(self, source, chapter_count=1, outcomes=None):
        self.source = source
        self.case = CASES[source]
        prefix = self.case["prefix"]
        provenance = json.loads((FIXTURES / "sources.json").read_text(encoding="utf-8"))
        self.novel_url = provenance[f"{prefix}_toc"]["requested_url"]
        self.chapter_url = provenance[f"{prefix}_chap"]["requested_url"]
        self.main_html = (FIXTURES / f"{prefix}_toc.html").read_bytes()
        self.chapter_html = (FIXTURES / f"{prefix}_chap.html").read_text(encoding="utf-8")
        if source == "panda":
            urls = {n: f"https://novelphoenix.com/novel/shadow-slave/chapter-{n}" for n in range(1, 4)}
        elif source == "centralnovel":
            urls = {n: f"https://centralnovel.com/shadow-slave-capitulo-{n}/" for n in range(1, 4)}
        else:
            soup = BeautifulSoup(self.main_html, "lxml")
            urls = {n: urljoin(self.novel_url, a["href"]) for n, a in enumerate(
                soup.select("#volumes div.accordion-body ol li a.custom-link"), 1
            )}
        self.chapter_urls = {n: urls[n] for n in range(1, chapter_count + 1)}
        self.url_to_number = {url: number for number, url in self.chapter_urls.items()}
        self.outcomes = outcomes or {}
        self.calls = Counter()
        self.seen = []
        self.unexpected = []
        self.response_urls = {self.novel_url, self.case["cover"], *self.chapter_urls.values()}

    def chapter_response(self, number, *, empty=False):
        if number == 1 and not self.outcomes and not empty:
            return self.chapter_html.encode("utf-8")
        soup = BeautifulSoup(self.chapter_html, "lxml")
        soup.select_one(self.case["title_selector"]).string = f"Fixture chapter {number}"
        content = soup.select_one(self.case["content_selector"])
        if empty:
            content.clear()
            paragraph = soup.new_tag("p")
            paragraph.string = " \n "
            content.append(paragraph)
        else:
            paragraph = soup.new_tag("p")
            paragraph.string = f"Offline chapter marker {number}."
            content.append(paragraph)
        return str(soup).encode("utf-8")

    def request(self, method, url, **kwargs):
        prepared = requests.Request(method, url, params=kwargs.get("params")).prepare()
        url = prepared.url
        self.seen.append(url)
        if method.upper() != "GET" or url not in self.response_urls:
            self.unexpected.append(f"{method} {url}")
            raise AssertionError(f"Unexpected external request: {method} {url}")
        status = 200
        if url in self.url_to_number:
            number = self.url_to_number[url]
            attempt = self.calls[number]
            self.calls[number] += 1
            sequence = self.outcomes.get(number, ["ok"])
            outcome = sequence[min(attempt, len(sequence) - 1)]
            if outcome == "timeout":
                raise requests.Timeout(f"Simulated timeout for chapter {number}")
            if outcome in ("404", "403", "429"):
                status = int(outcome)
                body = b"<html><body>Simulated HTTP error</body></html>"
            else:
                body = self.chapter_response(number, empty=outcome == "empty")
            content_type = "text/html; charset=utf-8"
        elif url == self.novel_url:
            body, content_type = self.main_html, "text/html; charset=utf-8"
        else:
            body, content_type = COVER_BYTES, "image/png"
        response = requests.Response()
        response.status_code = status
        response.url = url
        response.request = prepared
        response._content = body
        response.encoding = "utf-8"
        response.headers["Content-Type"] = content_type
        return response


@contextmanager
def offline_client(source, output_dir, *, chapter_count=1, outcomes=None):
    scenario = OfflineHTTP(source, chapter_count, outcomes)

    def offline_request(session, method, url, *args, **kwargs):
        return scenario.request(method, url, **kwargs)

    def forbid_send(*args, **kwargs):
        raise AssertionError("External networking is forbidden in offline flow tests")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(requests.sessions.Session, "request", offline_request)
        patch.setattr(requests.sessions.Session, "send", forbid_send)
        patch.setattr(MetricsService, "FILE_PATH", str(output_dir / "benchmarks.jsonl"))
        patch.setattr(TaskManager, "_tasks", {})
        patch.setattr(AppStatus, "should_exit_event", None)
        patch.setattr(AppStatus, "should_exit", False)
        patch.setattr(book_routes, "tempfile", SimpleNamespace(
            NamedTemporaryFile=partial(tempfile.NamedTemporaryFile, dir=output_dir),
        ))
        # Skip retry delays without replacing the retry code or globally patching time.sleep.
        clock = SimpleNamespace(time=time.time, perf_counter=time.perf_counter, sleep=lambda seconds: None)
        for module in (base_book, centralnovel_book, novelsbr_book):
            patch.setattr(module, "time", clock)
        for name, value in (("PROXY_URL", None), ("PROXY_URL_FALLBACK", None), ("DEBUG", False)):
            patch.setattr(get_settings(), name, value)
        patch.setitem(app.dependency_overrides, verify_internal_token,
                      lambda: {"sub": "offline-test", "tier": "test", "action": "generate-epub"})
        try:
            with TestClient(app) as client:
                yield client, scenario
            assert not scenario.unexpected, scenario.unexpected
        finally:
            for task in TaskManager._tasks.values():
                if task.get("file_path"):
                    path = Path(task["file_path"])
                    if path.is_relative_to(output_dir):
                        path.unlink(missing_ok=True)


def terminal_event(client, status_url):
    stream = client.get(status_url)
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    events = [json.loads(line[5:].strip()) for line in stream.text.splitlines() if line.startswith("data:")]
    assert events
    return events[-1]
