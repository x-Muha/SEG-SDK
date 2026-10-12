# Repository Guidance

This is the hand-maintained Python SDK for the SovereignEG (SEG) API, published on PyPI as
`seg-sdk` and imported as `seg`. It started as a fork of a generated OpenAI-style client and was
trimmed to the endpoints the SEG backend actually serves. There is no code generator any more:
edit the source directly.

## Scope

The SEG gateway serves these routes, and the SDK must not grow beyond them without a matching
backend change:

| Client resource           | Route                                      |
| ------------------------- | ------------------------------------------ |
| `client.chat.completions` | `POST /v1/chat/completions` (+ streaming)  |
| `client.embeddings`       | `POST /v1/embeddings`                      |
| `client.images.generate`  | `POST /v1/images/generations`              |
| `client.moderations`      | `POST /v1/moderations`                     |
| `client.models`           | `GET /v1/models`, `GET /v1/models/{id}`    |
| `client.decisions`        | `POST /v1/decisions`                       |

Authentication is a single `Authorization: Bearer sk-...` header from `api_key` /
`SEG_API_KEY`. The default base URL is `https://sovereigneg.com/v1` (`SEG_BASE_URL` overrides it).

## Working rules

- Keep the sync and async clients, and their `with_raw_response` / `with_streaming_response`
  wrappers, in step whenever a method changes.
- Mock HTTP in tests with the `respx2_mock` fixture; do not add tests that need a mock server.
  Live calls belong only in `tests/smoke/` and must skip when `TEST_API_BASE_URL` is unset.
- Run `./scripts/lint` and `./scripts/test` before finishing. Pyright runs in strict mode.
- Do not rename the import package (`seg`), the client classes (`SEG`, `AsyncSEG`), or the
  environment variables without an explicit request.
- Follow `CONTRIBUTING.md` for the checklist when adding an endpoint.

## Security requirements

- Never commit real API keys, bearer tokens, or `.env` files. Read credentials from the
  environment and use clearly fake values (`sk-test`, `My API Key`) in tests and examples.
- Keep `Authorization` redaction in debug logging intact (`src/seg/_utils/_logs.py`).
- Review dependency changes in `pyproject.toml` and `uv.lock`; the lock is regenerated with
  `uv lock` and verified in CI with `uv lock --check`.
- Pin third-party GitHub Actions to full commit SHAs. The publish workflow keeps the build job
  without `id-token: write`; only the upload-only job gets it.
- Report suspected vulnerabilities privately as described in `SECURITY.md`.

## Python version policy

`requires-python` in `pyproject.toml` is the technical minimum and `PYTHON_VERSION_POLICY.md` is
the human-readable policy. When changing the minimum, update `pyproject.toml`, `.python-version`,
the classifiers, the README, the CI matrix, and the lock file together.

## Large-payload compatibility

Large JSON bodies and long streams are normal API behaviour, not hostile input. Do not add fixed
size limits on bodies, events, or lines; prefer incremental processing. `tests/test_large_payload_contract.py`
protects this with synthetic payloads generated in memory; do not shrink them.
