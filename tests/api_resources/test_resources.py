"""Request/response contract tests for every resource, with HTTP mocked in-process.

Each case checks three things: the SDK hits the right path with the right JSON body and
bearer header, the response is parsed into the right model, and the raw-response wrapper
keeps the headers. Bodies mirror what the SovereignEG gateway returns.
"""

from __future__ import annotations

import json
from typing import Any

import httpx2
import pytest

from seg import SEG, AsyncSEG
from seg.types import Model, Decision, ImagesResponse, CreateEmbeddingResponse, ModerationCreateResponse
from tests.respx2 import MockRouter
from seg.types.chat import ChatCompletion, ChatCompletionChunk

CHAT_COMPLETION: dict[str, Any] = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1_700_000_000,
    "model": "Qwen/Qwen3-0.6B",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": "Hello!", "reasoning_content": "thinking"},
        }
    ],
    "usage": {"prompt_tokens": 15, "completion_tokens": 3, "total_tokens": 18},
}

EMBEDDING: dict[str, Any] = {
    "object": "list",
    "model": "embed-model",
    "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2, 0.3]}],
    "usage": {"prompt_tokens": 4, "total_tokens": 4},
}

IMAGES: dict[str, Any] = {
    "created": 1_700_000_000,
    "data": [{"url": "https://cdn.example/felucca.png"}],
    "size": "1024x1024",
    "usage": {"cost": 0.25},
}

MODERATION: dict[str, Any] = {
    "id": "modr-1",
    "model": "moderation-model",
    "results": [
        {
            "flagged": False,
            "categories": {
                "harassment": False,
                "harassment/threatening": False,
                "hate": False,
                "hate/threatening": False,
                "illicit": False,
                "illicit/violent": False,
                "self-harm": False,
                "self-harm/instructions": False,
                "self-harm/intent": False,
                "sexual": False,
                "sexual/minors": False,
                "violence": False,
                "violence/graphic": False,
            },
            "category_scores": {
                "harassment": 0.0,
                "harassment/threatening": 0.0,
                "hate": 0.0,
                "hate/threatening": 0.0,
                "illicit": 0.0,
                "illicit/violent": 0.0,
                "self-harm": 0.0,
                "self-harm/instructions": 0.0,
                "self-harm/intent": 0.0,
                "sexual": 0.0,
                "sexual/minors": 0.0,
                "violence": 0.0,
                "violence/graphic": 0.0,
            },
            "category_applied_input_types": {
                "harassment": ["text"],
                "harassment/threatening": ["text"],
                "hate": ["text"],
                "hate/threatening": ["text"],
                "illicit": ["text"],
                "illicit/violent": ["text"],
                "self-harm": ["text"],
                "self-harm/instructions": ["text"],
                "self-harm/intent": ["text"],
                "sexual": ["text"],
                "sexual/minors": ["text"],
                "violence": ["text"],
                "violence/graphic": ["text"],
            },
        }
    ],
}

MODEL: dict[str, Any] = {
    "id": "Qwen/Qwen3-0.6B",
    "object": "model",
    "created": 1_700_000_000,
    "owned_by": "sovereigneg",
}

DECISION: dict[str, Any] = {
    "object": "decision",
    "model": "decision-model",
    "answers": [
        {"type": "predicate", "name": "is_complaint", "probability": 0.91},
        {
            "type": "choice",
            "name": "sentiment",
            "choice": "negative",
            "confidence": 1.0,
            "probabilities": [{"value": "positive", "probability": 0.0}, {"value": "negative", "probability": 1.0}],
        },
        {"type": "refusal", "name": "urgency"},
    ],
    "usage": {
        "input_tokens": 40,
        "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
        "output_tokens": 3,
        "output_tokens_details": {"reasoning_tokens": 0},
        "total_tokens": 43,
    },
}

QUESTIONS: list[Any] = [
    {"type": "predicate", "name": "is_complaint", "instructions": "Is the customer complaining?"},
    {
        "type": "choice",
        "name": "sentiment",
        "instructions": "Overall sentiment?",
        "choices": [{"value": "positive"}, {"value": "negative"}],
    },
    {
        "type": "score",
        "name": "urgency",
        "instructions": "How urgent?",
        "levels": [{"label": "low"}, {"label": "high"}],
    },
]


def _sent_json(route: Any) -> Any:
    return json.loads(route.calls.last.request.content)


def _sse(*events: dict[str, Any]) -> bytes:
    body = b"".join(f"data: {json.dumps(event)}\n\n".encode() for event in events)
    return body + b"data: [DONE]\n\n"


class TestChatCompletions:
    def test_create(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.post("/chat/completions").mock(return_value=httpx2.Response(200, json=CHAT_COMPLETION))

        completion = client.chat.completions.create(
            model="Qwen/Qwen3-0.6B",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=300,
            temperature=0.2,
        )

        assert isinstance(completion, ChatCompletion)
        assert completion.choices[0].message.content == "Hello!"
        assert completion.usage is not None and completion.usage.total_tokens == 18
        # The gateway's extra field survives parsing.
        assert completion.choices[0].message.model_dump().get("reasoning_content") == "thinking"

        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer My API Key"
        assert request.headers["Content-Type"] == "application/json"
        assert _sent_json(route) == {
            "model": "Qwen/Qwen3-0.6B",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 300,
            "temperature": 0.2,
        }

    def test_create_streaming(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.post("/chat/completions").mock(
            return_value=httpx2.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                content=_sse(
                    {
                        "id": "c",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "m",
                        "choices": [
                            {"index": 0, "delta": {"role": "assistant", "content": "O"}, "finish_reason": None}
                        ],
                    },
                    {
                        "id": "c",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": "m",
                        "choices": [{"index": 0, "delta": {"content": "K"}, "finish_reason": "stop"}],
                    },
                ),
            )
        )

        stream = client.chat.completions.create(
            model="Qwen/Qwen3-0.6B",
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )
        chunks = list(stream)

        assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)
        assert "".join(chunk.choices[0].delta.content or "" for chunk in chunks) == "OK"
        assert _sent_json(route)["stream"] is True

    def test_raw_response(self, client: SEG, respx2_mock: MockRouter) -> None:
        respx2_mock.post("/chat/completions").mock(
            return_value=httpx2.Response(
                200, json=CHAT_COMPLETION, headers={"X-Request-Id": "req_abc", "X-RateLimit-Remaining-Requests": "59"}
            )
        )

        response = client.chat.completions.with_raw_response.create(
            model="Qwen/Qwen3-0.6B", messages=[{"role": "user", "content": "hi"}]
        )

        assert response.request_id == "req_abc"
        assert response.headers["X-RateLimit-Remaining-Requests"] == "59"
        assert response.parse().id == "chatcmpl-123"

    async def test_async_create(self, async_client: AsyncSEG, respx2_mock: MockRouter) -> None:
        respx2_mock.post("/chat/completions").mock(return_value=httpx2.Response(200, json=CHAT_COMPLETION))

        completion = await async_client.chat.completions.create(
            model="Qwen/Qwen3-0.6B", messages=[{"role": "user", "content": "hi"}]
        )

        assert completion.choices[0].message.content == "Hello!"


class TestEmbeddings:
    def test_create(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.post("/embeddings").mock(return_value=httpx2.Response(200, json=EMBEDDING))

        result = client.embeddings.create(model="embed-model", input="Cairo at night")

        assert isinstance(result, CreateEmbeddingResponse)
        assert result.data[0].embedding == [0.1, 0.2, 0.3]
        body = _sent_json(route)
        assert body["model"] == "embed-model"
        assert body["input"] == "Cairo at night"
        # The SDK asks for base64 floats by default to shrink the payload; the gateway may ignore it.
        assert body.get("encoding_format", "base64") == "base64"

    async def test_async_create(self, async_client: AsyncSEG, respx2_mock: MockRouter) -> None:
        respx2_mock.post("/embeddings").mock(return_value=httpx2.Response(200, json=EMBEDDING))

        result = await async_client.embeddings.create(model="embed-model", input=["a", "b"])

        assert result.usage.total_tokens == 4


class TestImages:
    def test_generate(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.post("/images/generations").mock(return_value=httpx2.Response(200, json=IMAGES))

        result = client.images.generate(model="image-model", prompt="A felucca on the Nile", size="1024x1024")

        assert isinstance(result, ImagesResponse)
        assert result.data is not None and result.data[0].url == "https://cdn.example/felucca.png"
        assert _sent_json(route) == {"model": "image-model", "prompt": "A felucca on the Nile", "size": "1024x1024"}

    def test_unsupported_methods_are_gone(self, client: SEG) -> None:
        assert not hasattr(client.images, "edit")
        assert not hasattr(client.images, "create_variation")


class TestModerations:
    def test_create(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.post("/moderations").mock(return_value=httpx2.Response(200, json=MODERATION))

        result = client.moderations.create(input="Some user text")

        assert isinstance(result, ModerationCreateResponse)
        assert result.results[0].flagged is False
        assert _sent_json(route) == {"input": "Some user text"}


class TestModels:
    def test_list(self, client: SEG, respx2_mock: MockRouter) -> None:
        respx2_mock.get("/models").mock(return_value=httpx2.Response(200, json={"object": "list", "data": [MODEL]}))

        page = client.models.list()

        assert [model.id for model in page.data] == ["Qwen/Qwen3-0.6B"]
        assert all(isinstance(model, Model) for model in page)

    def test_retrieve(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.get("/models/Qwen/Qwen3-0.6B").mock(return_value=httpx2.Response(200, json=MODEL))

        model = client.models.retrieve("Qwen/Qwen3-0.6B")

        assert model.owned_by == "sovereigneg"
        assert route.calls.last.request.url.path.endswith("/models/Qwen/Qwen3-0.6B")

    def test_delete_is_gone(self, client: SEG) -> None:
        assert not hasattr(client.models, "delete")


class TestDecisions:
    def test_create(self, client: SEG, respx2_mock: MockRouter) -> None:
        route = respx2_mock.post("/decisions").mock(return_value=httpx2.Response(200, json=DECISION))

        decision = client.decisions.create(
            model="decision-model",
            input="The package arrived late and the box was damaged.",
            questions=QUESTIONS,
            safety_identifier="end-user-42",
        )

        assert isinstance(decision, Decision)
        predicate, choice, refusal = decision.answers
        assert predicate.type == "predicate" and predicate.probability == 0.91
        assert choice.type == "choice" and choice.choice == "negative"
        assert refusal.type == "refusal" and refusal.name == "urgency"
        assert decision.usage.total_tokens == 43

        body = _sent_json(route)
        assert body["model"] == "decision-model"
        assert body["safety_identifier"] == "end-user-42"
        assert [question["type"] for question in body["questions"]] == ["predicate", "choice", "score"]

    async def test_async_create(self, async_client: AsyncSEG, respx2_mock: MockRouter) -> None:
        respx2_mock.post("/decisions").mock(return_value=httpx2.Response(200, json=DECISION))

        decision = await async_client.decisions.create(model="decision-model", input="text", questions=QUESTIONS)

        assert len(decision.answers) == 3


class TestRemovedResources:
    @pytest.mark.parametrize(
        "name",
        [
            "responses",
            "files",
            "batches",
            "fine_tuning",
            "audio",
            "vector_stores",
            "webhooks",
            "admin",
            "completions",
            "beta",
            "realtime",
        ],
    )
    def test_removed_resource_is_absent(self, client: SEG, name: str) -> None:
        assert not hasattr(client, name)
