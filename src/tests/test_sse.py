"""API -> real scraper -> EPUB -> SSE -> download, with only external HTTP simulated."""

import json
from pathlib import Path

import pytest

from src.services.task_manager import TaskManager
from src.tests.epub_checks import assert_expected_epub, inspect_epub, load_expected
from src.tests.offline_flow import CASES, COVER_BYTES, offline_client, terminal_event


@pytest.fixture(scope="module", params=CASES, ids=CASES)
def offline_epub(request, tmp_path_factory):
    source = request.param
    output_dir = tmp_path_factory.mktemp(f"offline-{source}")
    with offline_client(source, output_dir) as (client, scenario):
        started = client.post("/books/generate", params={"url": scenario.novel_url, "qty": 1, "start": 1})
        assert started.status_code == 202, started.text
        task_id = started.json()["task_id"]
        task = TaskManager.get_task(task_id)
        assert task and task["status"] == "completed", task
        server_file = Path(task["file_path"])
        assert server_file.is_file()

        event = terminal_event(client, started.json()["status_url"])
        assert event["status"] == "completed" and event["progress"] == 100
        download = client.get(event["download_url"])
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/epub+zip"
        assert "attachment" in download.headers["content-disposition"]
        assert TaskManager.get_task(task_id) is None
        assert not server_file.exists()
        assert set(scenario.seen) == scenario.response_urls, "Some fixture responses were never requested"
        epub_path = output_dir / "download.epub"
        epub_path.write_bytes(download.content)
        actual = inspect_epub(epub_path, COVER_BYTES)
        assert actual["chapter_count"] == 1  # The request explicitly asks for one chapter.
        (output_dir / "actual.json").write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
        yield {"source": source, "actual": actual, "epub_path": epub_path}


def test_full_sse_flow(offline_epub):
    """Always runs, even while the manual expected.json values are placeholders."""
    assert offline_epub["epub_path"].is_file()


def test_epub_matches_manual_expectations(offline_epub):
    expected = load_expected(offline_epub["source"])
    assert_expected_epub(offline_epub["actual"], expected)
