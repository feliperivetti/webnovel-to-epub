import pytest

from src.services.task_manager import TaskManager


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["failed", "completed"])
async def test_late_progress_cannot_reopen_terminal_task(monkeypatch, status):
    monkeypatch.setattr(TaskManager, "_tasks", {})
    task_id = await TaskManager.create_task()
    if status == "failed":
        await TaskManager.fail_task(task_id, "Download failed")
    else:
        await TaskManager.complete_task(task_id, "unused.epub", "unused.epub")
    before = dict(TaskManager.get_task(task_id))
    await TaskManager.update_progress(task_id, 95)
    assert TaskManager.get_task(task_id) == before
