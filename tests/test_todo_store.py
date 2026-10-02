import json
from datetime import date

import pytest

from todo_store import (
    DuplicateTodoError,
    TodoStoreError,
    add_todo,
    delete_todo,
    filter_todos,
    load_todos,
    set_completed,
)


def test_load_todos_returns_empty_list_for_missing_file(tmp_path):
    assert load_todos(tmp_path / "todos.json") == []


def test_add_todo_trims_title_and_persists_it(tmp_path):
    data_file = tmp_path / "nested" / "todos.json"

    created = add_todo(data_file, "  Write tests  ")

    assert created["title"] == "Write tests"
    assert created["completed"] is False
    assert load_todos(data_file) == [created]


def test_add_todo_rejects_blank_title(tmp_path):
    with pytest.raises(ValueError, match="cannot be empty"):
        add_todo(tmp_path / "todos.json", "   ")


def test_set_completed_updates_matching_todo(tmp_path):
    data_file = tmp_path / "todos.json"
    created = add_todo(data_file, "Ship demo")

    assert set_completed(data_file, created["id"], True) is True
    assert load_todos(data_file)[0]["completed"] is True


def test_set_completed_returns_false_for_unknown_id(tmp_path):
    assert set_completed(tmp_path / "todos.json", "missing", True) is False


def test_delete_todo_removes_matching_todo(tmp_path):
    data_file = tmp_path / "todos.json"
    keep = add_todo(data_file, "Keep")
    remove = add_todo(data_file, "Remove")

    assert delete_todo(data_file, remove["id"]) is True
    assert load_todos(data_file) == [keep]


def test_delete_todo_returns_false_for_unknown_id(tmp_path):
    assert delete_todo(tmp_path / "todos.json", "missing") is False


def test_load_todos_rejects_invalid_json(tmp_path):
    data_file = tmp_path / "todos.json"
    data_file.write_text("{not json", encoding="utf-8")

    with pytest.raises(TodoStoreError, match="Could not read"):
        load_todos(data_file)


def test_load_todos_rejects_invalid_schema(tmp_path):
    data_file = tmp_path / "todos.json"
    data_file.write_text(json.dumps([{"title": "Incomplete"}]), encoding="utf-8")

    with pytest.raises(TodoStoreError, match="invalid format"):
        load_todos(data_file)


def test_add_todo_rejects_exact_duplicate_title(tmp_path):
    data_file = tmp_path / "todos.json"
    first = add_todo(data_file, "Buy milk")

    with pytest.raises(DuplicateTodoError, match="already exists"):
        add_todo(data_file, "Buy milk")

    assert load_todos(data_file) == [first]


def test_add_todo_rejects_duplicate_ignoring_case_and_whitespace(tmp_path):
    data_file = tmp_path / "todos.json"
    first = add_todo(data_file, "Buy milk")

    with pytest.raises(DuplicateTodoError):
        add_todo(data_file, "buy milk")
    with pytest.raises(DuplicateTodoError):
        add_todo(data_file, "  BUY MILK  ")

    assert load_todos(data_file) == [first]


def test_add_todo_allows_distinct_titles(tmp_path):
    data_file = tmp_path / "todos.json"
    add_todo(data_file, "Buy milk")
    add_todo(data_file, "Buy bread")

    assert [todo["title"] for todo in load_todos(data_file)] == ["Buy milk", "Buy bread"]


def test_add_todo_without_due_date_stores_null(tmp_path):
    data_file = tmp_path / "todos.json"

    created = add_todo(data_file, "No deadline")

    assert created["due_date"] is None
    assert json.loads(data_file.read_text(encoding="utf-8"))[0]["due_date"] is None


def test_add_todo_with_due_date_persists_iso_string_and_reloads(tmp_path):
    data_file = tmp_path / "todos.json"

    created = add_todo(data_file, "File taxes", date(2026, 4, 15))

    assert created["due_date"] == "2026-04-15"
    assert json.loads(data_file.read_text(encoding="utf-8"))[0]["due_date"] == "2026-04-15"
    assert load_todos(data_file) == [created]


def test_load_todos_accepts_legacy_record_without_due_date(tmp_path):
    data_file = tmp_path / "todos.json"
    legacy = {
        "id": "legacy-1",
        "title": "Old todo",
        "completed": False,
        "created_at": "2025-01-01T00:00:00+00:00",
    }
    data_file.write_text(json.dumps([legacy]), encoding="utf-8")

    todos = load_todos(data_file)

    assert todos == [legacy]
    assert todos[0].get("due_date") is None
    assert set_completed(data_file, "legacy-1", True) is True


def test_load_todos_rejects_invalid_due_date(tmp_path):
    data_file = tmp_path / "todos.json"
    record = {
        "id": "bad",
        "title": "Bad date",
        "completed": False,
        "created_at": "2025-01-01T00:00:00+00:00",
        "due_date": "not-a-date",
    }
    data_file.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(TodoStoreError, match="invalid format"):
        load_todos(data_file)


def _make_todo(todo_id: str, completed: bool):
    return {
        "id": todo_id,
        "title": todo_id,
        "completed": completed,
        "created_at": "2025-01-01T00:00:00+00:00",
    }


@pytest.mark.parametrize(
    ("view", "expected_ids"),
    [("All", ["a", "b", "c"]), ("Active", ["a", "c"]), ("Completed", ["b"])],
)
def test_filter_todos_returns_matching_todos_in_order(view, expected_ids):
    todos = [_make_todo("a", False), _make_todo("b", True), _make_todo("c", False)]

    assert [todo["id"] for todo in filter_todos(todos, view)] == expected_ids


@pytest.mark.parametrize("view", ["All", "Active", "Completed"])
def test_filter_todos_handles_empty_list(view):
    assert filter_todos([], view) == []


def test_filter_todos_rejects_unknown_view():
    with pytest.raises(ValueError, match="Unknown todo filter"):
        filter_todos([], "Archived")
