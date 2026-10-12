# Changelog

## 0.1.1

### Changes

- Renamed the Decisions answer models to `PredicateAnswer`, `ChoiceAnswer`, `ScoreAnswer`,
  `RefusalAnswer`, `ChoiceProbability`, and `ScoreProbability` (previously generator-style
  `AnswerAnswerResource*` names) and exported them from `seg.types`.
- Image generation `usage` now accepts the gateway's cost-only block (`cost` in EGP) without
  requiring token counts.
- Fixed the module-level client building `.../v1models` when `seg.base_url` had no trailing slash.
- `Model` now mirrors the SovereignEG catalog (`display_name`, `provider`, `modality`,
  `context_window`, `pricing`, `status`, ...) with `created` and `owned_by` optional, so strict
  response validation no longer rejects `models.list()` / `models.retrieve()`.
- Moderation responses no longer require the `illicit` categories or
  `category_applied_input_types`, which the SovereignEG moderation endpoint does not return.
- `Decision` gained the `object` field; docs and examples now use `llama-3.1-8b-instruct`.

## 0.1.0

First release of the SovereignEG (SEG) Python SDK.

### Features

- `SEG` and `AsyncSEG` clients with bearer-token auth (`SEG_API_KEY`), configurable base URL
  (`SEG_BASE_URL`, default `https://sovereigneg.com/v1`), retries, timeouts, and raw/streaming
  response wrappers.
- Resources: `chat.completions` (including `parse` and `stream` helpers for structured outputs
  and tools), `embeddings`, `images.generate`, `moderations`, `models`, and `decisions`.
- Module-level client (`seg.api_key = ...; seg.chat.completions.create(...)`).
- HTTPX2 transport with optional aiohttp support (`seg-sdk[aiohttp]`).
