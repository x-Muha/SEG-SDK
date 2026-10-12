# SEG Python SDK

[![PyPI version](https://img.shields.io/pypi/v/seg-sdk.svg?label=pypi%20(seg-sdk))](https://pypi.org/project/seg-sdk/)

The official Python library for the [SovereignEG](https://sovereigneg.com) (SEG) API, a MENA-first,
OpenAI-compatible AI inference platform. It provides typed synchronous and asynchronous clients for
chat completions, embeddings, image generation, moderation, model listing, and decisions, built on
[httpx2](https://httpx2.pydantic.dev/) and [Pydantic](https://docs.pydantic.dev/).

## Installation

```sh
pip install seg-sdk
```

Requires Python 3.10 or newer. The distribution is `seg-sdk`; the import name is `seg`.

## Usage

Create an API key in the [SovereignEG dashboard](https://sovereigneg.com/keys) and export it:

```sh
export SEG_API_KEY="sk-..."
```

```python
from seg import SEG

client = SEG()  # reads SEG_API_KEY from the environment

completion = client.chat.completions.create(
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
    max_tokens=300,
)
print(completion.choices[0].message.content)
```

Pick a model from `client.models.list()`; the catalog depends on your plan. Reasoning models may spend the
`max_tokens` budget thinking before answering, and expose that thinking as extra fields on the message
(`reasoning` / `reasoning_details`, or `reasoning_content` depending on the serving provider).

### Client options

| Option            | Environment variable | Default                       |
| ----------------- | -------------------- | ----------------------------- |
| `api_key`         | `SEG_API_KEY`        | required                      |
| `base_url`        | `SEG_BASE_URL`       | `https://sovereigneg.com/v1`  |
| `timeout`         |                      | 10 minutes                    |
| `max_retries`     |                      | 2                             |
| `default_headers` |                      | none                          |
| `http_client`     |                      | an `httpx2.Client`            |

`api_key` may also be a callable that returns the key; it is called before every request, which is
useful for keys that rotate.

```python
from seg import SEG

client = SEG(api_key="sk-...", base_url="http://127.0.0.1:8000/v1", timeout=30.0, max_retries=3)
```

Every option can also be set at module level for quick scripts:

```python
import seg

seg.api_key = "sk-..."
print(seg.models.list().data[0].id)
```

## Async usage

Import `AsyncSEG` and `await` each call:

```python
import asyncio
from seg import AsyncSEG

client = AsyncSEG()


async def main() -> None:
    completion = await client.chat.completions.create(
        model="llama-3.1-8b-instruct",
        messages=[{"role": "user", "content": "Say hello"}],
    )
    print(completion.choices[0].message.content)


asyncio.run(main())
```

Install `seg-sdk[aiohttp]` and pass `http_client=DefaultAioHttpClient()` to use aiohttp instead of httpx2.

## Streaming

Pass `stream=True` to receive Server-Sent Events as they are produced:

```python
stream = client.chat.completions.create(
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Count from 1 to 5."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

The async client works the same way with `async for`.

## Structured outputs and tools

`client.chat.completions.parse()` turns a Pydantic model into a JSON schema, sends it as
`response_format`, and parses the reply back into your model. `seg.pydantic_function_tool()` does
the same for tool calls. See [helpers.md](helpers.md) for the full guide, including streaming helpers.

```python
from pydantic import BaseModel
from seg import SEG


class Answer(BaseModel):
    city: str
    country: str


client = SEG()
completion = client.chat.completions.parse(
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Where is the Great Pyramid?"}],
    response_format=Answer,
)
print(completion.choices[0].message.parsed)
```

## Other resources

```python
# Embeddings
client.embeddings.create(model="<embedding-model>", input="Cairo at night")

# Image generation
client.images.generate(model="<image-model>", prompt="A felucca on the Nile at sunset")

# Moderation
client.moderations.create(input="Some user text")

# Models
client.models.list()
client.models.retrieve("llama-3.1-8b-instruct")

# Decisions: typed questions about one input
client.decisions.create(
    model="<decision-model>",
    input="The package arrived late and the box was damaged.",
    questions=[
        {
            "type": "predicate",
            "name": "is_complaint",
            "instructions": "Is the customer complaining?",
        },
        {
            "type": "choice",
            "name": "sentiment",
            "instructions": "Overall sentiment?",
            "choices": [{"value": "positive"}, {"value": "neutral"}, {"value": "negative"}],
        },
    ],
)
```

The complete list of methods, parameters, and return types is in [api.md](api.md).

## Errors

Connection failures raise `seg.APIConnectionError`; non-2xx responses raise a subclass of
`seg.APIStatusError` carrying `status_code`, `request_id`, and the decoded error `body`.

| Status code | Error type                 |
| ----------- | -------------------------- |
| 400         | `BadRequestError`          |
| 401         | `AuthenticationError`      |
| 403         | `PermissionDeniedError`    |
| 404         | `NotFoundError`            |
| 422         | `UnprocessableEntityError` |
| 429         | `RateLimitError`           |
| >=500       | `InternalServerError`      |
| N/A         | `APIConnectionError`       |

```python
import seg
from seg import SEG

client = SEG()
try:
    client.chat.completions.create(model="missing-model", messages=[{"role": "user", "content": "hi"}])
except seg.RateLimitError:
    print("Slow down")
except seg.APIStatusError as e:
    print(e.status_code, e.request_id, e.body)
```

Every response carries an `X-Request-Id` header, and inference responses (chat, embeddings, images,
moderations, decisions) also carry rate-limit headers such as `X-RateLimit-Remaining-Requests`; read them
through `with_raw_response`.

### Retries and timeouts

Connection errors, 408, 409, 429, and 5xx responses are retried twice with exponential backoff by
default. Requests time out after 10 minutes. Both can be changed per client or per request:

```python
client = SEG(max_retries=0, timeout=20.0)
client.with_options(max_retries=5, timeout=60.0).chat.completions.create(...)
```

## Advanced

### Raw responses and headers

```python
response = client.chat.completions.with_raw_response.create(
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "hi"}],
)
print(response.headers.get("X-Request-Id"))
completion = response.parse()  # the parsed ChatCompletion
```

`with_streaming_response` does the same without reading the body eagerly; use it inside a `with` block.

### Undocumented requests and parameters

`client.get`, `client.post`, and friends send arbitrary requests. Every method also accepts
`extra_query`, `extra_body`, and `extra_headers` for parameters the SDK does not know about yet.

### Custom HTTP client

```python
import httpx2
from seg import SEG, DefaultHttpxClient

client = SEG(
    base_url="http://localhost:8000/v1",
    http_client=DefaultHttpxClient(
        proxy="http://my.proxy:3128", transport=httpx2.HTTPTransport(local_address="0.0.0.0")
    ),
)
```

Use the client as a context manager (`with SEG() as client:`) or call `client.close()` to release
connections.

### Logging

Set `SEG_LOG=debug` to log each request's method, response status, retries, and request id. Headers,
bodies, and the API key are never written to the log.

## Supported API surface

| Resource                   | Endpoint                     |
| -------------------------- | ---------------------------- |
| `client.chat.completions`  | `POST /v1/chat/completions`  |
| `client.embeddings`        | `POST /v1/embeddings`        |
| `client.images.generate`   | `POST /v1/images/generations`|
| `client.moderations`       | `POST /v1/moderations`       |
| `client.models`            | `GET /v1/models`, `GET /v1/models/{id}` |
| `client.decisions`         | `POST /v1/decisions`         |

## Versioning

This package follows [SemVer](https://semver.org/). Changes that only affect static types, internal
modules (prefixed with `_`), or that fix bugs are not considered breaking.

## Requirements

Python 3.10 or higher.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. This SDK is derived from the [openai-python](https://github.com/openai/openai-python)
client, Copyright OpenAI, used under the same license; see [NOTICE](NOTICE) for attributions.
