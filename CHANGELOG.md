# Changelog

## 0.1.2

### Changes

- `ChatModel`, `ImageModel`, `EmbeddingModel`, and `ModerationModel` now list the SovereignEG
  catalog ids (e.g. `llama-3.1-8b-instruct`, `flux-1-schnell`, `embeddinggemma-300m`,
  `sovereigneg-basic-keyword-check`) instead of OpenAI names. Regenerate them from
  `GET /v1/models` with `scripts/update_model_types.py`.
- `Model` gained `image_options`, `weights_type`, `benchmarks`, and `card_url`. Gateway-internal
  routing fields (`engines`, `healthy_backends`, `total_backends`, `source`, `provider_slug`)
  stay untyped and are still reachable via `model.model_extra` / `model.to_dict()`.
- `CompletionUsage` gained `cost`, `cost_details` (new `CostDetails` type), and `is_byok`;
  `CompletionTokensDetails.image_tokens` and `PromptTokensDetails.video_tokens` are now typed.
- `ImagesResponse` gained `runtime_ms`.
- `Embedding` now decodes `base64` vectors during validation, so clients created with
  `_strict_response_validation=True` no longer fail on the base64 the SDK requests by default
  (or on an explicit `encoding_format="base64"`); every client sends the same request.
- `AllModels` and `ResponsesModel` are now simply `Union[str, ChatModel]`; the OpenAI-only extra
  ids are gone.
- Docstrings for images, moderations, and embeddings describe the SovereignEG gateway
  (catalog image models, the built-in keyword moderation scorer) instead of OpenAI models.
- Docstring links now point at https://sovereigneg.com/dashboard/docs; the previous
  `developers.sovereigneg.com` links did not resolve.

### Removed

- The legacy `seg.Completion`, `seg.ChatCompletion`, `seg.Audio`, `seg.FineTune`, and similar
  placeholder symbols, which only raised a migration error for an API this package never had.

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
