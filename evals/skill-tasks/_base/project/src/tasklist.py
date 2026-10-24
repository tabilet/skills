"""Tasklist: add and list tasks in memory."""

TASKS: list[dict] = []


def add(title: str) -> dict:
    task = {"id": len(TASKS) + 1, "title": title, "done": False}
    TASKS.append(task)
    return task


def complete(task_id: int) -> None:
    for task in TASKS:
        if task["id"] == task_id:
            task["done"] = True


def listing() -> list[dict]:
    return list(TASKS)
