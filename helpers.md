# Structured Outputs Parsing Helpers

The SEG API supports extracting JSON from the model with the `response_format` request param, for more details on the API, see [this guide](https://sovereigneg.com/dashboard/docs).

The SDK provides a `client.chat.completions.parse()` method which is a wrapper over the `client.chat.completions.create()` that
provides richer integrations with Python specific types & returns a `ParsedChatCompletion` object, which is a subclass of the standard `ChatCompletion` class.

## Auto-parsing response content with Pydantic models

You can pass a pydantic model to the `.parse()` method and the SDK will automatically convert the model
into a JSON schema, send it to the API and parse the response content back into the given model.

```py
from typing import List
from pydantic import BaseModel
from seg import SEG


class Step(BaseModel):
    explanation: str
    output: str


class MathResponse(BaseModel):
    steps: List[Step]
    final_answer: str


client = SEG()
completion = client.chat.completions.parse(
    model="llama-3.1-8b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
    response_format=MathResponse,
)

message = completion.choices[0].message
if message.parsed:
    print(message.parsed.steps)
    print("answer: ", message.parsed.final_answer)
else:
    print(message.refusal)
```

## Auto-parsing function tool calls

The `.parse()` method will also automatically parse `function` tool calls if:

- You use the `seg.pydantic_function_tool()` helper method
- You mark your tool schema with `"strict": True`

For example:

```py
from enum import Enum
from typing import List, Union
from pydantic import BaseModel
import seg


class Table(str, Enum):
    orders = "orders"
    customers = "customers"
    products = "products"


class Column(str, Enum):
    id = "id"
    status = "status"
    expected_delivery_date = "expected_delivery_date"
    delivered_at = "delivered_at"
    shipped_at = "shipped_at"
    ordered_at = "ordered_at"
    canceled_at = "canceled_at"


class Operator(str, Enum):
    eq = "="
    gt = ">"
    lt = "<"
    le = "<="
    ge = ">="
    ne = "!="


class OrderBy(str, Enum):
    asc = "asc"
    desc = "desc"


class DynamicValue(BaseModel):
    column_name: str


class Condition(BaseModel):
    column: str
    operator: Operator
    value: Union[str, int, DynamicValue]


class Query(BaseModel):
    table_name: Table
    columns: List[Column]
    conditions: List[Condition]
    order_by: OrderBy


client = seg.SEG()
completion = client.chat.completions.parse(
    model="llama-3.1-8b-instruct",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant. The current date is August 6, 2024. You help users query for the data they are looking for by calling the query function.",
        },
        {
            "role": "user",
            "content": "look up all my orders in may of last year that were fulfilled but not delivered on time",
        },
    ],
    tools=[
        seg.pydantic_function_tool(Query),
    ],
)

tool_call = (completion.choices[0].message.tool_calls or [])[0]
print(tool_call.function)
assert isinstance(tool_call.function.parsed_arguments, Query)
print(tool_call.function.parsed_arguments.table_name)
```

### Differences from `.create()`

The `chat.completions.parse()` method imposes some additional restrictions on it's usage that `chat.completions.create()` does not.

- If the completion completes with `finish_reason` set to `length` or `content_filter`, the `LengthFinishReasonError` / `ContentFilterFinishReasonError` errors will be raised.
- Only strict function tools can be passed, e.g. `{'type': 'function', 'function': {..., 'strict': True}}`

# Streaming Helpers

SEG supports streaming responses when interacting with the [Chat Completion](#chat-completions-api) API.

## Chat Completions API

The SDK provides a `.chat.completions.stream()` method that wraps the `.chat.completions.create(stream=True)` stream providing a more granular event API & automatic accumulation of each delta.

It also supports all aforementioned [parsing helpers](#structured-outputs-parsing-helpers).

Unlike `.create(stream=True)`, the `.stream()` method requires usage within a context manager to prevent accidental leakage of the response:

```py
from seg import AsyncSEG

client = AsyncSEG()

async with client.chat.completions.stream(
    model="llama-3.1-8b-instruct",
    messages=[...],
) as stream:
    async for event in stream:
        if event.type == "content.delta":
            print(event.delta, flush=True, end="")
```

When the context manager is entered, a `ChatCompletionStream` / `AsyncChatCompletionStream` instance is returned which, like `.create(stream=True)` is an iterator in the sync client and an async iterator in the async client. The full list of events that are yielded by the iterator are outlined [below](#chat-completions-events).

When the context manager exits, the response will be closed, however the `stream` instance is still available outside
the context manager.

### Chat Completions Events

These events allow you to track the progress of the chat completion generation, access partial results, and handle different aspects of the stream separately.

Below is a list of the different event types you may encounter:

#### ChunkEvent

Emitted for every chunk received from the API.

- `type`: `"chunk"`
- `chunk`: The raw `ChatCompletionChunk` object received from the API
- `snapshot`: The current accumulated state of the chat completion

#### ContentDeltaEvent

Emitted for every chunk containing new content.

- `type`: `"content.delta"`
- `delta`: The new content string received in this chunk
- `snapshot`: The accumulated content so far
- `parsed`: The partially parsed content (if applicable)

#### ContentDoneEvent

Emitted when the content generation is complete. May be fired multiple times if there are multiple choices.

- `type`: `"content.done"`
- `content`: The full generated content
- `parsed`: The fully parsed content (if applicable)

#### RefusalDeltaEvent

Emitted when a chunk contains part of a content refusal.

- `type`: `"refusal.delta"`
- `delta`: The new refusal content string received in this chunk
- `snapshot`: The accumulated refusal content string so far

#### RefusalDoneEvent

Emitted when the refusal content is complete.

- `type`: `"refusal.done"`
- `refusal`: The full refusal content

#### FunctionToolCallArgumentsDeltaEvent

Emitted when a chunk contains part of a function tool call's arguments.

- `type`: `"tool_calls.function.arguments.delta"`
- `name`: The name of the function being called
- `index`: The index of the tool call
- `arguments`: The accumulated raw JSON string of arguments
- `parsed_arguments`: The partially parsed arguments object
- `arguments_delta`: The new JSON string fragment received in this chunk

#### FunctionToolCallArgumentsDoneEvent

Emitted when a function tool call's arguments are complete.

- `type`: `"tool_calls.function.arguments.done"`
- `name`: The name of the function being called
- `index`: The index of the tool call
- `arguments`: The full raw JSON string of arguments
- `parsed_arguments`: The fully parsed arguments object. If you used `seg.pydantic_function_tool()` this will be an instance of the given model.

#### LogprobsContentDeltaEvent

Emitted when a chunk contains new content [log probabilities](https://sovereigneg.com/dashboard/docs).

- `type`: `"logprobs.content.delta"`
- `content`: A list of the new log probabilities received in this chunk
- `snapshot`: A list of the accumulated log probabilities so far

#### LogprobsContentDoneEvent

Emitted when all content [log probabilities](https://sovereigneg.com/dashboard/docs) have been received.

- `type`: `"logprobs.content.done"`
- `content`: The full list of token log probabilities for the content

#### LogprobsRefusalDeltaEvent

Emitted when a chunk contains new refusal [log probabilities](https://sovereigneg.com/dashboard/docs).

- `type`: `"logprobs.refusal.delta"`
- `refusal`: A list of the new log probabilities received in this chunk
- `snapshot`: A list of the accumulated log probabilities so far

#### LogprobsRefusalDoneEvent

Emitted when all refusal [log probabilities](https://sovereigneg.com/dashboard/docs) have been received.

- `type`: `"logprobs.refusal.done"`
- `refusal`: The full list of token log probabilities for the refusal

### Chat Completions stream methods

A handful of helper methods are provided on the stream class for additional convenience,

**`.get_final_completion()`**

Returns the accumulated `ParsedChatCompletion` object

```py
async with client.chat.completions.stream(...) as stream:
    ...

completion = await stream.get_final_completion()
print(completion.choices[0].message)
```

**`.until_done()`**

If you want to wait for the stream to complete, you can use the `.until_done()` method.

```py
async with client.chat.completions.stream(...) as stream:
    await stream.until_done()
    # stream is now finished
```

