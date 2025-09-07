# Contributing

Thanks for your interest in contributing!

## Development setup

```bash
git clone https://github.com/YanYablonovskiy/networkx-arxiv-generators
cd networkx-arxiv-generators
python -m venv .venv && source .venv/bin/activate
pip install -e .[test,lint,docs]
```

## Guidelines

- Follow NetworkX API patterns: functions like `model_name(..., seed=None)` returning a `Graph`/`DiGraph`.
- Document each algorithm with:
  - Full reference (authors, title, venue, year, DOI/arXiv).
  - Parameter constraints and complexity, where applicable.
  - Reproducible examples (with `seed`).
- Add unit tests and type hints.
- Run `ruff`, `black`, `mypy`, and `pytest` locally before pushing.

## Adding a new generator

- Create a module in `src/nx_arxivgen/generators/`.
- Add it to `__all__` in `src/nx_arxivgen/__init__.py`.
- Write tests in `tests/`.
- Update README and docs if needed.