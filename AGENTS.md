# okama-macro — Development rules for AI agents

## Project overview

`okama-macro` is the consolidated Python library for macro-economic data-source
clients used by the okama project. It exposes:

- the normalized public API `okama_macro.get()` and
  `okama_macro.list_series()`;
- raw source clients under `okama_macro.sources`;
- shared HTTP and frame-normalization infrastructure.

The package supports Python 3.11–3.14 and both pandas 2.x and 3.x. The source of
truth for package metadata and dependencies is `pyproject.toml`.

## Repository structure

- `okama_macro/registry.py` — public series registry and normalization layer.
- `okama_macro/sources/` — one module or subpackage per upstream source.
- `okama_macro/_http.py` — shared HTTP, retry, proxy, TLS, and redaction logic.
- `okama_macro/_frame.py` — shared date-window and pandas helpers.
- `tests/` — offline unit and contract tests.
- `docs/audits/` — independent source-comparison and data-quality audits.
- `.github/workflows/ci.yml` — test matrix for supported Python versions.
- `.github/workflows/publish-to-pypi.yml` — Trusted Publishing release workflow.

## Environment and commands

Use Poetry for dependency and environment management:

```bash
poetry install
poetry run pytest -q
poetry run ruff check .
poetry build
```

Add dependencies with `poetry add`; never use `pip install` to modify project
dependencies. `poetry.lock` is intentionally untracked and must not be
committed.

## Test-Driven Development

All changes to executable production code must follow TDD:

1. **RED** — write the smallest test that describes the required behavior.
2. Run that test and verify it fails for the intended reason.
3. **GREEN** — implement the minimum production change that makes it pass.
4. Run the focused test, then the full suite.
5. **REFACTOR** — improve the implementation while keeping all tests green.

Do not write production code before observing the failing test. Bug fixes need
a regression test that reproduces the defect. Refactors must preserve behavior
and remain covered by existing or newly added tests.

TDD is not required for documentation, comments, docstrings, images, or
workflow-only changes that do not alter runtime behavior. Validate those
changes directly instead.

## Public series contract

Every series returned by `okama_macro.get()` must satisfy the registry contract:

- values are decimal fractions, never percentages or index levels;
- CPI series are monthly and use first-of-month `DatetimeIndex` dates;
- rate series normally contain observations only, without implicit padding;
- `UK_BR.RATE` is the documented exception because its Bank of England client
  safely forward-fills a change-date series;
- indexes are ascending, values have float dtype, and `Series.name` equals the
  registry key;
- `first_date` and `last_date` clipping is consistent across sources;
- unknown keys raise a clear `ValueError`.

Raw clients under `okama_macro.sources` return data in source-native units and
shapes. Perform public-contract normalization in `registry.py`, not in callers.
Do not silently change units, padding, date semantics, or historical depth.

## Adding or changing a source

- Prefer the shared `_http` transport for generic HTTP clients. Preserve
  specialized source transport when it provides required WAF, TLS, fallback,
  proxy, or User-Agent behavior.
- Fail loudly on malformed or unexpectedly empty upstream responses. Do not
  silently substitute another source unless the composition is an explicit,
  documented registry rule.
- Use realistic offline fixtures that preserve the upstream payload's real sort
  order and structure.
- Contract tests must cover units, date/index type, monotonic ordering, window
  semantics, and padding direction where padding exists.
- For a new consumed series or a material parser change, compare the output
  against an independent source over the overlapping history and record the
  result under `docs/audits/`.
- If an intentional data change affects expected output, inspect and explain
  every resulting fixture or audit delta; never blindly regenerate baselines.

## Python style

- Write code comments, docstrings, documentation, and commit messages in
  English.
- Add type hints to new and changed function parameters and return values.
- Use modern syntax compatible with the minimum Python version in
  `pyproject.toml`: built-in generics and `X | None` unions.
- Ruff configuration in `pyproject.toml` is authoritative. Fix all findings;
  use only targeted `# noqa: <CODE>` comments with a rationale when unavoidable.
- Preserve source-specific compatibility code unless a test proves it can be
  removed safely.

## Required verification

After changing executable Python code:

```bash
poetry run pytest -q
poetry run ruff check .
```

Also inspect every caller when changing a function signature or public return
contract. For packaging changes, additionally run:

```bash
poetry build
poetry run twine check dist/*
```

Do not report success from an exit code alone; confirm the pytest summary and
the ruff/build output.

## Releases

- Bump the version in `pyproject.toml` before creating a release.
- A published GitHub Release with tag `v<version>` triggers
  `publish-to-pypi.yml`.
- PyPI publishing uses GitHub OIDC Trusted Publishing through the `pypi`
  environment. Do not add long-lived PyPI tokens to the repository.
- Run the full test matrix and validate wheel and source-distribution metadata
  before publishing.
- Release notes must name the affected public functions or source methods when
  describing features and bug fixes.
- PyPI versions are immutable; never reuse or move a published version tag.

## Project hygiene

- Track tasks in GitHub Issues and history in git; do not add task status,
  commit hashes, or work logs to this file.
- Keep temporary exports and generated scratch artifacts out of the repository.
- Never hardcode API keys, proxy credentials, or other secrets. Use documented
  environment variables such as `FRED_API_KEY` and `PROXY_*`.
