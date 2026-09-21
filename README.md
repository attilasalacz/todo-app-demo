# Todo App Demo

A small Streamlit todo app designed for demonstrations of coding-agent workflows.
Todos can be added, completed, and deleted, and are saved locally in
`data/todos.json`.

## Run locally

Requirements:

- Python 3.11 or newer

Create a virtual environment, install the app, and start Streamlit:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
streamlit run app.py
```

Streamlit opens the app at [http://localhost:8501](http://localhost:8501).

## Develop and test

Install the development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the same checks used by continuous integration:

```bash
ruff check .
pytest
```

The GitHub Actions workflow runs these checks for every push and pull request.
This project intentionally has no deployment step because it is intended to run
locally.
