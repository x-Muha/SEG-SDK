from __future__ import annotations

import json
from typing import Any, Callable, Iterator, AsyncIterator
from typing_extensions import override

import httpx2
from pydantic import BaseModel

from seg import SEG, AsyncSEG

# High memory use is intentional: valid API payloads must not be rejected by
# arbitrary body, event, or line caps. Keep this above 32 MiB; do not shrink it
# to make a cap pass. This is a regression probe, not an API maximum. Generate
# data in memory and keep the transport and helper cases sequential.
PAYLOAD_SIZE = 32 * 1024 * 1024 + 1


class TextResult(BaseModel):
    value: str


def assert_intact(actual: str | None, expected: str) -> None:
    # Do not dump a 32 MiB string into pytest's assertion diagnostics.
    intact = actual == expected
    assert intact, "The large API payload was truncated or changed"


def response_body(text: str) -> dict[str, Any]:
    return {
        "id": "resp_test",
        "created_at": 0,
        "model": "gpt-4o-mini",
        "object": "response",
        "parallel_tool_calls": True,
        "status": "completed",
        "tool_choice": "auto",
        "tools": [],
        "output": [
            {
                "type": "message",
                "id": "msg_test",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": text, "annotations": []}],
            }
        ],
    }


def sync_client(respond: Callable[[httpx2.Request], httpx2.Response]) -> SEG:
    return SEG(
        api_key="test-key",
        max_retries=0,
        base_url="https://example.test/v1",
        http_client=httpx2.Client(
            transport=httpx2.MockTransport(respond),
        ),
    )


def async_client(respond: Callable[[httpx2.Request], httpx2.Response]) -> AsyncSEG:
    return AsyncSEG(
        api_key="test-key",
        max_retries=0,
        base_url="https://example.test/v1",
        http_client=httpx2.AsyncClient(
            transport=httpx2.MockTransport(respond),
        ),
    )


def sse_body(events: Iterator[dict[str, Any]]) -> Iterator[bytes]:
    for event in events:
        data = json.dumps(event).encode()
        yield b"data: "
        # Fragment the large JSON line across ordinary transport-sized chunks.
        for start in range(0, len(data), 64 * 1024):
            yield data[start : start + 64 * 1024]
        yield b"\n\n"
    yield b"data: [DONE]\n\n"


class AsyncSSE(httpx2.AsyncByteStream):
    def __init__(self, events: Iterator[dict[str, Any]]) -> None:
        self.events = events

    @override
    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in sse_body(self.events):
            yield chunk


def check_chat_stream() -> None:
    value = "x" * PAYLOAD_SIZE
    text = json.dumps({"value": value})

    def events() -> Iterator[dict[str, Any]]:
        for content, finish_reason in [("", None), (text[:-1], None), (text[-1:], "stop")]:
            yield {
                "id": "chatcmpl_test",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": "gpt-4o-mini",
                "choices": [
                    {"index": 0, "finish_reason": finish_reason, "delta": {"role": "assistant", "content": content}}
                ],
            }

    with sync_client(
        lambda _: httpx2.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=sse_body(events()),
        )
    ) as client:
        with client.chat.completions.stream(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            response_format=TextResult,
        ) as stream:
            completion = stream.get_final_completion()
            message = completion.choices[0].message
            assert_intact(message.content, text)
            assert message.parsed is not None
            assert_intact(message.parsed.value, value)


class CompressedStream(httpx2.SyncByteStream):
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.closed = False

    @override
    def __iter__(self) -> Iterator[bytes]:
        # One small network chunk must not inflate into one enormous chunk.
        yield self.data

    @override
    def close(self) -> None:
        self.closed = True


class AsyncCompressedStream(httpx2.AsyncByteStream):
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.closed = False

    @override
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield self.data

    @override
    async def aclose(self) -> None:
        self.closed = True


def compressed_response(stream: CompressedStream | AsyncCompressedStream, encoding: str) -> httpx2.Response:
    # Passing a stream avoids eager decoding in Response's constructor.
    return httpx2.Response(
        200, headers={"content-encoding": encoding, "content-type": "application/json"}, stream=stream
    )
