# API reference

All methods are available on `seg.SEG` (sync) and `seg.AsyncSEG` (async). Every method accepts
`extra_headers`, `extra_query`, `extra_body`, and `timeout` keyword arguments, and can be prefixed
with `.with_raw_response` or `.with_streaming_response`.

## Shared Types

```python
from seg.types import (
    ChatModel,
    ComparisonFilter,
    CompoundFilter,
    CustomToolInputFormat,
    ErrorObject,
    FunctionDefinition,
    FunctionParameters,
    Metadata,
    Reasoning,
    ReasoningEffort,
    ResponseFormatJSONObject,
    ResponseFormatJSONSchema,
    ResponseFormatText,
)
```

## Chat

### Completions

Types:

```python
from seg.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionAudio,
    ChatCompletionAudioParam,
    ChatCompletionChunk,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartImage,
    ChatCompletionContentPartText,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionFunctionTool,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionModality,
    ChatCompletionNamedToolChoiceParam,
    ChatCompletionPredictionContentParam,
    ChatCompletionReasoningEffort,
    ChatCompletionRole,
    ChatCompletionStreamOptionsParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionTokenLogprob,
    ChatCompletionToolParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
    ParsedChatCompletion,
)
```

Methods:

- <code title="post /chat/completions">client.chat.completions.<a href="./src/seg/resources/chat/completions/completions.py">create</a>(\*\*<a href="src/seg/types/chat/completion_create_params.py">params</a>) -> <a href="./src/seg/types/chat/chat_completion.py">ChatCompletion</a> | Stream[<a href="./src/seg/types/chat/chat_completion_chunk.py">ChatCompletionChunk</a>]</code>
- <code title="post /chat/completions">client.chat.completions.<a href="./src/seg/resources/chat/completions/completions.py">parse</a>(\*\*params, response_format=PydanticModel) -> <a href="./src/seg/types/chat/parsed_chat_completion.py">ParsedChatCompletion</a></code>
- <code title="post /chat/completions">client.chat.completions.<a href="./src/seg/resources/chat/completions/completions.py">stream</a>(\*\*params) -> ChatCompletionStreamManager</code>

`stream=True` on `create` returns a `Stream[ChatCompletionChunk]` (or `AsyncStream`). See
[helpers.md](helpers.md) for `parse` and `stream`.

## Embeddings

Types:

```python
from seg.types import CreateEmbeddingResponse, Embedding, EmbeddingModel
```

Methods:

- <code title="post /embeddings">client.embeddings.<a href="./src/seg/resources/embeddings.py">create</a>(\*\*<a href="src/seg/types/embedding_create_params.py">params</a>) -> <a href="./src/seg/types/create_embedding_response.py">CreateEmbeddingResponse</a></code>

## Images

Types:

```python
from seg.types import (
    Image,
    ImageModel,
    ImagesResponse,
    ImageGenStreamEvent,
    ImageGenCompletedEvent,
    ImageGenPartialImageEvent,
)
```

Methods:

- <code title="post /images/generations">client.images.<a href="./src/seg/resources/images.py">generate</a>(\*\*<a href="src/seg/types/image_generate_params.py">params</a>) -> <a href="./src/seg/types/images_response.py">ImagesResponse</a></code>

The response `usage` block includes `cost`, the amount charged in EGP.

## Moderations

Types:

```python
from seg.types import (
    Moderation,
    ModerationImageURLInputParam,
    ModerationModel,
    ModerationMultiModalInputParam,
    ModerationTextInputParam,
    ModerationCreateResponse,
)
```

Methods:

- <code title="post /moderations">client.moderations.<a href="./src/seg/resources/moderations.py">create</a>(\*\*<a href="src/seg/types/moderation_create_params.py">params</a>) -> <a href="./src/seg/types/moderation_create_response.py">ModerationCreateResponse</a></code>

## Models

Types:

```python
from seg.types import Model
```

`Model` carries the catalog metadata (`display_name`, `provider`, `modality`, `context_window`,
`max_output_tokens`, `pricing`, `status`, ...); fields the backend does not return are `None`.

Methods:

- <code title="get /models/{model}">client.models.<a href="./src/seg/resources/models.py">retrieve</a>(model) -> <a href="./src/seg/types/model.py">Model</a></code>
- <code title="get /models">client.models.<a href="./src/seg/resources/models.py">list</a>() -> <a href="./src/seg/types/model.py">SyncPage[Model]</a></code>

## Decisions

Types:

```python
from seg.types import (
    Answer,
    ChoiceAnswer,
    Decision,
    PredicateAnswer,
    RefusalAnswer,
    ScoreAnswer,
    DecisionInputImageParam,
    DecisionInputMessageParam,
    DecisionInputPartUnionParam,
    DecisionInputTextParam,
)
```

Methods:

- <code title="post /decisions">client.decisions.<a href="./src/seg/resources/decisions.py">create</a>(\*\*<a href="src/seg/types/decision_create_params.py">params</a>) -> <a href="./src/seg/types/decision.py">Decision</a></code>

Questions are `predicate` (a probability), `choice` (pick one of 2 to 255 values), or `score`
(rate against 2 to 10 ordered levels). Answers come back in the order the questions were asked;
a question the model declines returns a `refusal` answer.
