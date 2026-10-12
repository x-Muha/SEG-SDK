# Changelog

## 0.1.0 (unreleased)

First release of the SovereignEG (SEG) Python SDK.

### Features

- `SEG` and `AsyncSEG` clients with bearer-token auth (`SEG_API_KEY`), configurable base URL
  (`SEG_BASE_URL`, default `https://sovereigneg.com/v1`), retries, timeouts, and raw/streaming
  response wrappers.
- Resources: `chat.completions` (including `parse` and `stream` helpers for structured outputs
  and tools), `embeddings`, `images.generate`, `moderations`, `models`, and `decisions`.
- Module-level client (`seg.api_key = ...; seg.chat.completions.create(...)`).
- HTTPX2 transport with optional aiohttp support (`seg-sdk[aiohttp]`).
