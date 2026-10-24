"""Tasklist: add, complete and list tasks; save and load them as JSON."""
import json
import pathlib

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


def save(path: str = "tasks.json") -> None:
    pathlib.Path(path).write_text(json.dumps(TASKS))


def load(path: str = "tasks.json") -> None:
    TASKS[:] = json.loads(pathlib.Path(path).read_text())
