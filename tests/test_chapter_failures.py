"""Chapter failures use real scrapers, retries, task state, SSE and EPUB generation."""

import json
from pathlib import Path

import pytest

from src.services.task_manager import TaskManager
from tests.epub_checks import inspect_epub
from tests.offline_flow import CASES, COVER_BYTES, offline_client, terminal_event


@pytest.mark.parametrize("source", CASES)
@pytest.mark.parametrize("failure", ["404", "timeout", "empty"])
def test_all_chapters_failed_produces_no_epub(source, failure, tmp_path):
    outcomes = {number: [failure] for number in (1, 2, 3)}
    with offline_client(source, tmp_path, chapter_count=3, outcomes=outcomes) as (client, scenario):
        started = client.post("/books/generate", params={"url": scenario.novel_url, "qty": 3, "start": 1})
        assert started.status_code == 202
        task_id = started.json()["task_id"]
        task = TaskManager.get_task(task_id)
        assert task["status"] == "failed"
        assert "All 3 selected chapters failed" in task["error"]
        assert task["file_path"] is None and task["filename"] is None
        event = terminal_event(client, started.json()["status_url"])
        assert event["status"] == "failed"
        assert event["error"] == task["error"]
        assert "download_url" not in event
        assert client.get(f"/books/download/{task_id}").status_code == 404
        assert not list(tmp_path.glob("*.epub"))
        assert set(scenario.calls) == {1, 2, 3}
        metric = json.loads((tmp_path / "benchmarks.jsonl").read_text().splitlines()[-1])
        assert metric["status"] == "failed"


@pytest.mark.parametrize("source", CASES)
@pytest.mark.parametrize("start,quantity,failed_numbers,expected_numbers", [
    (1, 3, (2,), [1, 2, 3]),
    (1, 3, (1, 2), [1, 2, 3]),
    (2, 2, (2,), [2, 3]),
])
def test_partial_failure_keeps_warning_pages_in_order(source, start, quantity, failed_numbers, expected_numbers, tmp_path):
    outcomes = {number: ["404"] for number in failed_numbers}
    with offline_client(source, tmp_path, chapter_count=3, outcomes=outcomes) as (client, scenario):
        started = client.post("/books/generate", params={"url": scenario.novel_url, "qty": quantity, "start": start})
        assert started.status_code == 202
        task_id = started.json()["task_id"]
        task = TaskManager.get_task(task_id)
        assert task["status"] == "completed", task
        server_file = Path(task["file_path"])
        event = terminal_event(client, started.json()["status_url"])
        assert event["status"] == "completed" and event["progress"] == 100
        downloaded = client.get(event["download_url"])
        assert downloaded.status_code == 200
        assert downloaded.headers["content-type"] == "application/epub+zip"
        assert not server_file.exists() and TaskManager.get_task(task_id) is None
        path = tmp_path / "partial.epub"
        path.write_bytes(downloaded.content)
        # Strict success checks must still reject error pages unless explicitly allowed.
        with pytest.raises(AssertionError):
            inspect_epub(path, COVER_BYTES)
        actual = inspect_epub(path, COVER_BYTES, allow_error_pages=True)
        assert actual["chapter_count"] == len(expected_numbers)
        assert [chapter["file"] for chapter in actual["chapters"]] == [
            f"chap_{index}.xhtml" for index in range(1, len(expected_numbers) + 1)
        ]
        for number, chapter in zip(expected_numbers, actual["chapters"]):
            if number in failed_numbers:
                assert chapter["title"] == f"Error Chapter {number}"
                assert chapter["text"] == "Content could not be downloaded."
            else:
                assert chapter["title"] == f"Fixture chapter {number}"
                assert f"Offline chapter marker {number}." in chapter["text"]
                assert "Content could not be downloaded." not in chapter["text"]


@pytest.mark.parametrize("source", CASES)
@pytest.mark.parametrize("failure", ["429", "timeout"])
def test_temporary_chapter_failure_recovers_without_warning_page(source, failure, tmp_path):
    with offline_client(source, tmp_path, chapter_count=3, outcomes={2: [failure, "ok"]}) as (client, scenario):
        started = client.post("/books/generate", params={"url": scenario.novel_url, "qty": 3, "start": 1})
        assert started.status_code == 202
        task_id = started.json()["task_id"]
        assert TaskManager.get_task(task_id)["status"] == "completed"
        event = terminal_event(client, started.json()["status_url"])
        assert event["status"] == "completed"
        downloaded = client.get(event["download_url"])
        assert downloaded.status_code == 200
        path = tmp_path / "recovered.epub"
        path.write_bytes(downloaded.content)
        actual = inspect_epub(path, COVER_BYTES)
        assert scenario.calls == {1: 1, 2: 2, 3: 1}
        assert actual["chapter_count"] == 3
        assert [chapter["title"] for chapter in actual["chapters"]] == [f"Fixture chapter {n}" for n in (1, 2, 3)]
        for number, chapter in enumerate(actual["chapters"], 1):
            assert f"Offline chapter marker {number}." in chapter["text"]
