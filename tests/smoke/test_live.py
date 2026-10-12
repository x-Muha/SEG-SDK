"""Live smoke tests against a real SovereignEG deployment.

They run only when both ``TEST_API_BASE_URL`` and ``SEG_API_KEY`` are set, e.g.

    SEG_API_KEY=sk-... TEST_API_BASE_URL=https://sovereigneg.com/v1 pytest tests/smoke -o addopts=

They cost real tokens, so each case asks for the smallest useful answer.
"""

from __future__ import annotations

import os

import pytest

from seg import SEG, AsyncSEG

BASE_URL = os.environ.get("TEST_API_BASE_URL")
API_KEY = os.environ.get("SEG_API_KEY")

pytestmark = pytest.mark.skipif(
    not BASE_URL or not API_KEY,
    reason="set TEST_API_BASE_URL and SEG_API_KEY to run the live smoke tests",
)

# Any chat model from the catalog works; this one is the cheapest in the public catalog.
CHAT_MODEL = os.environ.get("SEG_SMOKE_CHAT_MODEL", "llama-3.1-8b-instruct")


@pytest.fixture(scope="module")
def client() -> SEG:
    return SEG(base_url=BASE_URL, api_key=API_KEY, max_retries=1)


def test_models_list_and_retrieve(client: SEG) -> None:
    page = client.models.list()
    ids = [model.id for model in page.data]
    assert ids, "the catalog should not be empty"
    assert CHAT_MODEL in ids

    model = client.models.retrieve(CHAT_MODEL)
    assert model.id == CHAT_MODEL


def test_chat_completion(client: SEG) -> None:
    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": "Reply with just the word OK."}],
        max_tokens=200,
    )
    assert completion.choices
    assert completion.usage is not None and completion.usage.total_tokens > 0
    # Reasoning models may spend the budget thinking; the content is still a string when present.
    assert completion.choices[0].message.content is None or isinstance(completion.choices[0].message.content, str)


def test_chat_completion_streaming(client: SEG) -> None:
    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": "Reply with just the word OK."}],
        max_tokens=200,
        stream=True,
    )
    chunks = list(stream)
    assert chunks
    assert any(chunk.choices for chunk in chunks)


def test_raw_response_exposes_request_id(client: SEG) -> None:
    response = client.models.with_raw_response.list()
    assert response.headers.get("X-Request-Id")
    assert response.parse().data


def test_unknown_model_is_a_clean_api_error(client: SEG) -> None:
    from seg import APIStatusError

    with pytest.raises(APIStatusError) as excinfo:
        client.chat.completions.create(
            model="this-model-does-not-exist",
            messages=[{"role": "user", "content": "hi"}],
        )
    assert excinfo.value.status_code in (400, 404)
    assert excinfo.value.request_id


async def test_async_chat_completion() -> None:
    client = AsyncSEG(base_url=BASE_URL, api_key=API_KEY, max_retries=1)
    try:
        completion = await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": "Reply with just the word OK."}],
            max_tokens=200,
        )
        assert completion.choices
    finally:
        await client.close()
