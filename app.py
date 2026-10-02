"""Streamlit user interface for the todo app."""

from pathlib import Path

import streamlit as st

from todo_store import (
    DuplicateTodoError,
    TodoStoreError,
    add_todo,
    delete_todo,
    load_todos,
    set_completed,
)

DATA_FILE = Path("data/todos.json")

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

    for todo in todos:
        checkbox_column, title_column, delete_column = st.columns([1, 8, 1])
        with checkbox_column:
            completed = st.checkbox(
                f"Complete {todo['title']}",
                value=todo["completed"],
                key=f"completed-{todo['id']}",
                label_visibility="collapsed",
            )
        with title_column:
            if todo["completed"]:
                st.markdown(f"~~{todo['title']}~~")
            else:
                st.write(todo["title"])
            if todo.get("due_date"):
                st.caption(f"Due {todo['due_date']}")
        with delete_column:
            should_delete = st.button(
                "🗑️",
                key=f"delete-{todo['id']}",
                help=f"Delete {todo['title']}",
            )

        if completed != todo["completed"]:
            set_completed(DATA_FILE, todo["id"], completed)
            st.rerun()
        if should_delete:
            delete_todo(DATA_FILE, todo["id"])
            st.rerun()
