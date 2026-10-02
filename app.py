"""Streamlit user interface for the todo app."""

from pathlib import Path

import streamlit as st

from todo_store import (
    TODO_FILTERS,
    DuplicateTodoError,
    TodoStoreError,
    add_todo,
    delete_todo,
    filter_todos,
    load_todos,
    set_completed,
)

DATA_FILE = Path("data/todos.json")
EMPTY_FILTER_MESSAGES = {
    "Active": "No active todos. Everything is done!",
    "Completed": "No completed todos yet.",
}

st.set_page_config(page_title="Todo App Demo", page_icon="✅", layout="centered")
st.title("Todo App")
st.caption("A small project for demonstrating coding-agent workflows.")

with st.form("new_todo", clear_on_submit=True):
    title = st.text_input(
        "New todo",
        placeholder="What needs to be done?",
        label_visibility="collapsed",
    )
    due_date = st.date_input("Due date (optional)", value=None)
    submitted = st.form_submit_button("Add todo", type="primary", use_container_width=True)

if submitted:
    try:
        add_todo(DATA_FILE, title, due_date)
        st.rerun()
    except DuplicateTodoError:
        st.warning(f"“{title.strip()}” is already on your list.")
    except ValueError:
        st.warning("Enter a todo before adding it.")
    except TodoStoreError as exc:
        st.error(str(exc))

try:
    todos = load_todos(DATA_FILE)
except TodoStoreError as exc:
    st.error(str(exc))
    todos = []

if not todos:
    st.info("No todos yet. Add one above to get started.")
else:
    completed_count = sum(todo["completed"] for todo in todos)
    st.write(f"**{completed_count} of {len(todos)} completed**")

    view = st.radio("Show", TODO_FILTERS, horizontal=True, key="todo-filter")
    visible_todos = filter_todos(todos, view)
    if not visible_todos:
        st.info(EMPTY_FILTER_MESSAGES[view])

    for todo in visible_todos:
        title_column, delete_column = st.columns([3, 1], vertical_alignment="center")
        with title_column:
            # The visible label is the todo title, so it is also the checkbox's accessible name.
            completed = st.checkbox(
                f"~~{todo['title']}~~" if todo["completed"] else todo["title"],
                value=todo["completed"],
                key=f"completed-{todo['id']}",
                help=f"Mark {todo['title']} as {'active' if todo['completed'] else 'complete'}",
            )
            if todo.get("due_date"):
                st.caption(f"Due {todo['due_date']}")
        with delete_column:
            should_delete = st.button(
                f"Delete {todo['title']}",
                key=f"delete-{todo['id']}",
                icon=":material/delete:",
                type="tertiary",
            )

        if completed != todo["completed"]:
            set_completed(DATA_FILE, todo["id"], completed)
            st.rerun()
        if should_delete:
            delete_todo(DATA_FILE, todo["id"])
            st.rerun()
