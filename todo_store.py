"""JSON-backed storage operations for the todo app."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal, NotRequired, TypedDict
from uuid import uuid4


class Todo(TypedDict):
    id: str
    title: str
    completed: bool
    created_at: str
    due_date: NotRequired[str | None]


TodoFilter = Literal["All", "Active", "Completed"]
TODO_FILTERS: tuple[TodoFilter, ...] = ("All", "Active", "Completed")


class TodoStoreError(RuntimeError):
    """Raised when todo data cannot be read or written."""


class DuplicateTodoError(ValueError):
    """Raised when a todo with the same title already exists."""


def load_todos(path: Path) -> list[Todo]:
    """Load todos from *path*, returning an empty list when it does not exist."""
    if not path.exists():
        return []

    try:
        raw_todos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TodoStoreError(f"Could not read todo data from {path}.") from exc

    if not isinstance(raw_todos, list) or not all(_is_todo(item) for item in raw_todos):
        raise TodoStoreError(f"Todo data in {path} has an invalid format.")

    return raw_todos


def add_todo(path: Path, title: str, due_date: date | None = None) -> Todo:
    """Create and persist a todo with an optional due date."""
    normalized_title = title.strip()
    if not normalized_title:
        raise ValueError("Todo title cannot be empty.")

    todos = load_todos(path)
    if any(_title_key(todo["title"]) == _title_key(normalized_title) for todo in todos):
        raise DuplicateTodoError(f"A todo titled {normalized_title!r} already exists.")

    todo: Todo = {
        "id": str(uuid4()),
        "title": normalized_title,
        "completed": False,
        "created_at": datetime.now(UTC).isoformat(),
        "due_date": due_date.isoformat() if due_date else None,
    }
    todos.append(todo)
    _save_todos(path, todos)
    return todo


def set_completed(path: Path, todo_id: str, completed: bool) -> bool:
    """Set completion state. Return whether a matching todo was found."""
    todos = load_todos(path)
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = completed
            _save_todos(path, todos)
            return True
    return False


def delete_todo(path: Path, todo_id: str) -> bool:
    """Delete a todo. Return whether a matching todo was found."""
    todos = load_todos(path)
    remaining = [todo for todo in todos if todo["id"] != todo_id]
    if len(remaining) == len(todos):
        return False
    _save_todos(path, remaining)
    return True


def filter_todos(todos: list[Todo], view: TodoFilter) -> list[Todo]:
    """Return the todos visible in *view*, preserving their order."""
    if view == "All":
        return list(todos)
    if view == "Active":
        return [todo for todo in todos if not todo["completed"]]
    if view == "Completed":
        return [todo for todo in todos if todo["completed"]]
    raise ValueError(f"Unknown todo filter: {view!r}.")


def _title_key(title: str) -> str:
    return title.strip().casefold()


def _save_todos(path: Path, todos: list[Todo]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(todos, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    except OSError as exc:
        raise TodoStoreError(f"Could not save todo data to {path}.") from exc


def _is_todo(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        isinstance(value.get("id"), str)
        and isinstance(value.get("title"), str)
        and isinstance(value.get("completed"), bool)
        and isinstance(value.get("created_at"), str)
        and _is_optional_iso_date(value.get("due_date"))
    )


def _is_optional_iso_date(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
