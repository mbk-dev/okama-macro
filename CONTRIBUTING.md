# Contributing to okama-macro

Thanks for helping improve `okama-macro`. Bug reports, source corrections,
documentation fixes, and focused feature proposals are welcome.

## Before you start

- Search the existing issues before opening a new one.
- Use the bug or feature-request form so the report includes the context needed
  to reproduce or evaluate it.
- Never include API keys, proxy credentials, or other secrets in an issue,
  fixture, log, commit, or pull request.
- For a new consumed series or a material parser change, plan an independent
  source comparison and record the result under `docs/audits/`.

## Development setup

The project supports Python 3.11–3.14 and uses Poetry:

```bash
git clone https://github.com/mbk-dev/okama-macro.git
cd okama-macro
poetry install
```

Do not commit `poetry.lock`; it is intentionally untracked in this repository.

## Making changes

- Follow test-driven development for executable production code: add the
  smallest failing test, implement the change, then refactor with the test
  passing.
- Keep public normalization in `okama_macro/registry.py`; raw clients should
  preserve source-native units and shapes.
- Add type hints to new and changed function parameters and return values.
- Write code comments, docstrings, documentation, and commit messages in
  English.
- Keep fixtures offline, realistic, and faithful to upstream payload ordering
  and structure.

Documentation-only changes do not require a new test, but links, examples, and
the documentation build should still be checked directly.

## Verification

Run the project checks before submitting a change:

```bash
poetry run pytest -q
poetry run ruff check .
```

For documentation changes:

```bash
poetry install --with docs
poetry run mkdocs build --strict
```

For packaging changes, also run:

```bash
poetry build
poetry run twine check dist/*
```

When a function signature or public return contract changes, inspect every
caller and explain any intentional data or fixture delta.

## Reporting source-data problems

Include the public series key or raw source method, requested date window,
Python and pandas versions, and a minimal reproducible example. If the problem
is a value mismatch, link to the original publisher or an independent source
and state the exact observation date and expected value.
