from __future__ import annotations

from typing import Any

import httpx2
import pytest

import seg
from seg import SEG, AsyncSEG, APIStatusError, APITimeoutError, APIConnectionError
from seg._constants import DEFAULT_TIMEOUT


def model_list(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(200, json={"object": "list", "data": []}, request=request)


def sse_response(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(
        200,
        headers={"content-type": "text/event-stream"},
        content=(
            b'data: {"type":"response.completed","response":{"id":"resp_test","object":"response",'
            b'"created_at":0,"model":"gpt-4o","output":[],"parallel_tool_calls":false,'
            b'"tool_choice":"auto","tools":[]}}\n\ndata: [DONE]\n\n'
        ),
        request=request,
    )


async def test_httpx2_helpers_supply_sdk_defaults_and_accept_native_proxy() -> None:
    sync_client = seg.DefaultHttpx2Client(proxy="http://127.0.0.1:8080", trust_env=False)
    async_client = seg.DefaultAsyncHttpx2Client(proxy="http://127.0.0.1:8080", trust_env=False)
    try:
        assert type(sync_client).__module__ == "httpx2"
        assert type(async_client).__module__ == "httpx2"
        assert sync_client.timeout.as_dict() == {"connect": 5.0, "read": 600, "write": 600, "pool": 600}
        assert async_client.timeout.as_dict() == {"connect": 5.0, "read": 600, "write": 600, "pool": 600}
        assert sync_client.follow_redirects
        assert async_client.follow_redirects
    finally:
        sync_client.close()
        await async_client.aclose()


def test_direct_sync_injection_and_module_configuration() -> None:
    direct = httpx2.Client(transport=httpx2.MockTransport(model_list), trust_env=False)
    with SEG(api_key="test", base_url="https://example.test/v1", http_client=direct, max_retries=0) as client:
        assert client.timeout == DEFAULT_TIMEOUT
        assert client.models.list().object == "list"

    seg.api_key = "test"
    seg.base_url = httpx2.URL("https://example.test/v1")
    seg.http_client = seg.DefaultHttpx2Client(transport=httpx2.MockTransport(model_list), trust_env=False)
    try:
        response = seg.models.with_raw_response.list()
    finally:
        seg._reset_client()
        seg.http_client = None

    assert type(response.http_response).__module__ == "httpx2"


async def test_httpx2_urls_and_response_casts() -> None:
    class ResponseSubclass(httpx2.Response):
        pass

    def model(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            request=request,
            json={"id": "gpt-4o", "object": "model", "created": 1, "owned_by": "seg"},
        )

    with SEG(
        api_key="test",
        base_url=httpx2.URL("https://example.test/v1"),
        http_client=httpx2.Client(transport=httpx2.MockTransport(model), trust_env=False),
        max_retries=0,
    ) as client:
        client.base_url = httpx2.URL("https://example.test/v1")
        response = client.get("/models", cast_to=httpx2.Response)
        legacy_raw = client.models.with_raw_response.retrieve("gpt-4o")
        with client.models.with_streaming_response.retrieve("gpt-4o") as streaming_raw:
            streaming_response = streaming_raw.parse(to=httpx2.Response)

        with pytest.raises(ValueError, match="Subclasses of HTTP response classes"):
            client.get("/models", cast_to=ResponseSubclass)

    async def handler(request: httpx2.Request) -> httpx2.Response:
        return model(request)

    async with AsyncSEG(
        api_key="test",
        base_url=httpx2.URL("https://example.test/v1"),
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler), trust_env=False),
        max_retries=0,
    ) as async_client:
        async_client.base_url = httpx2.URL("https://example.test/v1")
        async_response = await async_client.get("/models", cast_to=httpx2.Response)
        async_legacy_raw = await async_client.models.with_raw_response.retrieve("gpt-4o")
        async with async_client.models.with_streaming_response.retrieve("gpt-4o") as async_streaming_raw:
            async_streaming_response = await async_streaming_raw.parse(to=httpx2.Response)

        with pytest.raises(ValueError, match="Subclasses of HTTP response classes"):
            await async_client.get("/models", cast_to=ResponseSubclass)

    assert isinstance(response, httpx2.Response)
    assert isinstance(legacy_raw.parse(to=httpx2.Response), httpx2.Response)
    assert isinstance(streaming_response, httpx2.Response)
    assert isinstance(async_response, httpx2.Response)
    assert isinstance(async_legacy_raw.parse(to=httpx2.Response), httpx2.Response)
    assert isinstance(async_streaming_response, httpx2.Response)


async def test_httpx2_native_timeouts_set_numeric_read_timeout_header() -> None:
    sync_requests: list[httpx2.Request] = []
    async_requests: list[httpx2.Request] = []

    def sync_handler(request: httpx2.Request) -> httpx2.Response:
        sync_requests.append(request)
        return model_list(request)

    async def async_handler(request: httpx2.Request) -> httpx2.Response:
        async_requests.append(request)
        return model_list(request)

    with SEG(
        api_key="test",
        base_url="https://example.test/v1",
        timeout=httpx2.Timeout(30.0, read=12.0),
        http_client=httpx2.Client(transport=httpx2.MockTransport(sync_handler), trust_env=False),
        max_retries=0,
    ) as client:
        client.models.list()
        client.models.list(timeout=httpx2.Timeout(30.0, read=7.0))

    async with AsyncSEG(
        api_key="test",
        base_url="https://example.test/v1",
        timeout=httpx2.Timeout(30.0, read=13.0),
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(async_handler), trust_env=False),
        max_retries=0,
    ) as async_client:
        await async_client.models.list()
        await async_client.models.list(timeout=httpx2.Timeout(30.0, read=8.0))

    assert [request.headers["x-stainless-read-timeout"] for request in sync_requests] == ["12.0", "7.0"]
    assert [request.headers["x-stainless-read-timeout"] for request in async_requests] == ["13.0", "8.0"]


async def test_direct_async_injection() -> None:
    async def handler(request: httpx2.Request) -> httpx2.Response:
        return model_list(request)

    direct = httpx2.AsyncClient(transport=httpx2.MockTransport(handler), trust_env=False)
    async with AsyncSEG(
        api_key="test", base_url="https://example.test/v1", http_client=direct, max_retries=0
    ) as client:
        assert client.timeout == DEFAULT_TIMEOUT
        assert (await client.models.list()).object == "list"


@pytest.mark.parametrize("failure", ["timeout", "connection", "status"])
def test_sync_retries_and_failure_families(failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if len(requests) > 1:
            return model_list(request)
        if failure == "timeout":
            raise httpx2.ReadTimeout("timeout", request=request)
        if failure == "connection":
            raise httpx2.ConnectError("connection", request=request)
        return httpx2.Response(500, json={"error": {"message": "bad", "type": "test"}}, request=request)

    client = SEG(
        api_key="test",
        base_url="https://example.test/v1",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler), trust_env=False),
        max_retries=1,
    )

    def no_sleep(**_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(client, "_sleep_for_retry", no_sleep)
    try:
        assert client.models.list().object == "list"
    finally:
        client.close()

    assert len(requests) == 2
    assert all(type(request).__module__ == "httpx2" for request in requests)

    def always_fail(request: httpx2.Request) -> httpx2.Response:
        if failure == "timeout":
            raise httpx2.ReadTimeout("timeout", request=request)
        if failure == "connection":
            raise httpx2.ConnectError("connection", request=request)
        return httpx2.Response(500, json={"error": {"message": "bad", "type": "test"}}, request=request)

    expected: type[Exception]
    if failure == "timeout":
        expected = APITimeoutError
    elif failure == "connection":
        expected = APIConnectionError
    else:
        expected = APIStatusError

    with SEG(
        api_key="test",
        base_url="https://example.test/v1",
        http_client=httpx2.Client(transport=httpx2.MockTransport(always_fail), trust_env=False),
        max_retries=0,
    ) as failing_client:
        with pytest.raises(expected) as exc_info:
            failing_client.models.list()

    error = exc_info.value
    transport_value = getattr(error, "response", None) or getattr(error, "request", None)
    assert type(transport_value).__module__ == "httpx2"


@pytest.mark.parametrize("failure", ["timeout", "connection", "status"])
async def test_async_retries_and_failure_families(failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx2.Request] = []

    async def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        if len(requests) > 1:
            return model_list(request)
        if failure == "timeout":
            raise httpx2.ReadTimeout("timeout", request=request)
        if failure == "connection":
            raise httpx2.ConnectError("connection", request=request)
        return httpx2.Response(500, json={"error": {"message": "bad", "type": "test"}}, request=request)

    client = AsyncSEG(
        api_key="test",
        base_url="https://example.test/v1",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler), trust_env=False),
        max_retries=1,
    )

    async def no_sleep(**_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(client, "_sleep_for_retry", no_sleep)
    try:
        assert (await client.models.list()).object == "list"
    finally:
        await client.close()

    assert len(requests) == 2
    assert all(type(request).__module__ == "httpx2" for request in requests)

    async def always_fail(request: httpx2.Request) -> httpx2.Response:
        if failure == "timeout":
            raise httpx2.ReadTimeout("timeout", request=request)
        if failure == "connection":
            raise httpx2.ConnectError("connection", request=request)
        return httpx2.Response(500, json={"error": {"message": "bad", "type": "test"}}, request=request)

    expected: type[Exception]
    if failure == "timeout":
        expected = APITimeoutError
    elif failure == "connection":
        expected = APIConnectionError
    else:
        expected = APIStatusError

    async with AsyncSEG(
        api_key="test",
        base_url="https://example.test/v1",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(always_fail), trust_env=False),
        max_retries=0,
    ) as failing_client:
        with pytest.raises(expected) as exc_info:
            await failing_client.models.list()

    error = exc_info.value
    transport_value = getattr(error, "response", None) or getattr(error, "request", None)
    assert type(transport_value).__module__ == "httpx2"
