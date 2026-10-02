from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from todo_store import add_todo, load_todos

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


@pytest.fixture
def data_file(tmp_path, monkeypatch):
    path = tmp_path / "todos.json"
    monkeypatch.setenv("TODO_DATA_FILE", str(path))
    return path


def run_app() -> AppTest:
    return AppTest.from_file(str(APP_PATH), default_timeout=10).run()


def button(at: AppTest, label: str):
    return next(b for b in at.button if b.label == label)


def test_add_todo_flow_persists_and_renders_todo(data_file):
    at = run_app()

    at.text_input[0].input("  Buy milk  ")
    button(at, "Add todo").click().run()

    assert not at.exception
    assert [todo["title"] for todo in load_todos(data_file)] == ["Buy milk"]
    assert [checkbox.label for checkbox in at.checkbox] == ["Buy milk"]


def test_add_duplicate_todo_shows_warning(data_file):
    add_todo(data_file, "Buy milk")
    at = run_app()

    at.text_input[0].input("buy milk")
    button(at, "Add todo").click().run()

    assert len(load_todos(data_file)) == 1
    assert [warning.value for warning in at.warning] == ["“buy milk” is already on your list."]


def test_complete_todo_flow_persists_completion(data_file):
    todo = add_todo(data_file, "Ship demo")
    at = run_app()

    at.checkbox(key=f"completed-{todo['id']}").check().run()

    assert not at.exception
    assert load_todos(data_file)[0]["completed"] is True
    assert at.checkbox(key=f"completed-{todo['id']}").value is True


def test_delete_todo_flow_removes_todo(data_file):
    keep = add_todo(data_file, "Keep")
    add_todo(data_file, "Remove")
    at = run_app()

    button(at, "Delete Remove").click().run()

    assert not at.exception
    assert load_todos(data_file) == [keep]
    assert [checkbox.label for checkbox in at.checkbox] == ["Keep"]


def test_controls_have_accessible_names_with_todo_title(data_file):
    add_todo(data_file, "Walk dog")
    at = run_app()

    checkbox = at.checkbox[0]
    assert checkbox.label == "Walk dog"
    assert checkbox.proto.label_visibility.value == checkbox.proto.label_visibility.VISIBLE
    assert "Delete Walk dog" in [b.label for b in at.button]


def test_filter_flow_shows_matching_todos_and_empty_states(data_file):
    done = add_todo(data_file, "Done")
    at = run_app()
    at.checkbox(key=f"completed-{done['id']}").check().run()

    at.radio(key="todo-filter").set_value("Active").run()
    assert at.checkbox.len == 0
    assert [info.value for info in at.info] == ["No active todos. Everything is done!"]

    at.radio(key="todo-filter").set_value("Completed").run()
    assert [checkbox.label for checkbox in at.checkbox] == ["~~Done~~"]

    button(at, "Delete Done").click().run()
    assert load_todos(data_file) == []
