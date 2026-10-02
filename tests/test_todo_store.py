import json

import pytest

from todo_store import (
    DuplicateTodoError,
    TodoStoreError,
    add_todo,
    delete_todo,
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
