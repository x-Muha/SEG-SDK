## Setting up the environment

This repository uses [uv](https://docs.astral.sh/uv/) to manage dependencies. Install uv, then run:

```sh
./scripts/bootstrap
```

This creates a `.venv` with the locked development dependencies (ruff, pyright, mypy, pytest).

## Repository layout

- `src/seg/_client.py` — the `SEG` and `AsyncSEG` clients (auth, base URL, retries, options).
- `src/seg/resources/` — one module per API resource: `chat`, `embeddings`, `images`, `moderations`, `models`, `decisions`.
- `src/seg/types/` — Pydantic response models and `TypedDict` request params.
- `src/seg/lib/` — hand-written helpers (structured-output parsing, chat streaming events).
- `src/seg/_base_client.py` and the other `_` modules — HTTP plumbing shared by every resource.
- `tests/` — unit tests; HTTP calls are mocked in-process with `respx2`, so no server is needed.
- `tests/smoke/` — live tests that run only when `TEST_API_BASE_URL` and `SEG_API_KEY` are set.
- `examples/` — runnable scripts; run them with `uv run python examples/demo.py`.

## Adding or changing an endpoint

1. Add the request params `TypedDict` and response model under `src/seg/types/`, and export them from `src/seg/types/__init__.py`.
2. Add the method to the resource in `src/seg/resources/` for both the sync and async classes, plus the `WithRawResponse` and `WithStreamingResponse` wrappers at the bottom of the file.
3. If it is a new resource, register it in `src/seg/_client.py` (client property and the four wrapper classes), `src/seg/resources/__init__.py`, `src/seg/_module_client.py`, and `src/seg/__init__.py`.
4. Add a mocked test in `tests/api_resources/` and, where it matters, a live case in `tests/smoke/`.
5. Document it in `api.md` and, if user facing, the README.

Keep the backend as the source of truth: the SovereignEG gateway serves `/v1/chat/completions`,
`/v1/embeddings`, `/v1/images/generations`, `/v1/moderations`, `/v1/models`, and `/v1/decisions`.
Do not add client methods for endpoints the backend does not expose.

## Running checks

```sh
./scripts/lint     # ruff, pyright, mypy, import check
./scripts/format   # ruff format + autofix
./scripts/test     # pytest (Pydantic v2), then the Pydantic v1 environment
./scripts/build    # build the sdist and wheel into dist/
```

To run the live smoke tests against an API (set `SEG_SMOKE_CHAT_MODEL` if the default chat model,
`llama-3.1-8b-instruct`, is not in that deployment's catalog):

```sh
SEG_API_KEY=sk-... TEST_API_BASE_URL=https://sovereigneg.com/v1 uv run pytest tests/smoke -o addopts=
```

For a local Docker backend prefer `http://127.0.0.1:8000/v1` over `localhost`: on Windows, httpx tries
IPv6 first and the initial request to `localhost` can take a couple of seconds.

## Using the repository from source

```sh
pip install git+ssh://git@github.com/x-Muha/SEG-SDK.git
# or, for a local checkout
pip install -e /path/to/seg-sdk
```

## Releasing

1. Bump `version` in `pyproject.toml` and `__version__` in `src/seg/_version.py`, and add a `CHANGELOG.md` entry.
2. Run `uv lock` so the lock file records the new version, then run the checks above.
3. Tag and publish a GitHub release; the `Publish PyPI` workflow builds the distributions and uploads
   `seg-sdk` through PyPI Trusted Publishing (configure the PyPI project to trust the `publish` environment first).

## Security

Never commit real API keys. Read `SEG_API_KEY` from the environment and use clearly fake values in
tests and examples. See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.
