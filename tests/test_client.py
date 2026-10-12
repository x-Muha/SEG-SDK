from __future__ import annotations

import gc
import io
import os
import sys
import json
import inspect
import dataclasses
import tracemalloc
from typing import Any, Union, TypeVar, Callable, Iterable, Iterator, Optional, Coroutine, AsyncIterable, cast
from unittest import mock
from typing_extensions import Literal, AsyncIterator, override

import httpx2
import pytest
from pydantic import ValidationError

from seg import SEG, AsyncSEG, APIResponseValidationError
from seg._types import Omit
from seg._utils import asyncify
from seg._models import BaseModel, FinalRequestOptions
from tests.respx2 import MockRouter
from seg._streaming import Stream, AsyncStream
from seg._exceptions import APIStatusError, APITimeoutError, APIConnectionError, APIResponseValidationError
from seg._base_client import (
    DEFAULT_TIMEOUT,
    OtherPlatform,
    DefaultHttpxClient,
    DefaultAsyncHttpxClient,
    get_platform,
    make_request_options,
)

T = TypeVar("T")
base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")
api_key = "My API Key"


def _low_retry_timeout(*_args: Any, **_kwargs: Any) -> float:
    return 0.1


def mirror_request_content(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(200, content=request.content)


# note: we can't use the httpx.MockTransport class as it consumes the request
#       body itself, which means we can't test that the body is read lazily
class MockTransport(httpx2.BaseTransport, httpx2.AsyncBaseTransport):
    def __init__(
        self,
        handler: Callable[[httpx2.Request], httpx2.Response]
        | Callable[[httpx2.Request], Coroutine[Any, Any, httpx2.Response]],
    ) -> None:
        self.handler = handler

    @override
    def handle_request(
        self,
        request: httpx2.Request,
    ) -> httpx2.Response:
        assert not inspect.iscoroutinefunction(self.handler), "handler must not be a coroutine function"
        assert inspect.isfunction(self.handler), "handler must be a function"
        return self.handler(request)

    @override
    async def handle_async_request(
        self,
        request: httpx2.Request,
    ) -> httpx2.Response:
        assert inspect.iscoroutinefunction(self.handler), "handler must be a coroutine function"
        return await self.handler(request)


@dataclasses.dataclass
class Counter:
    value: int = 0


def _make_sync_iterator(iterable: Iterable[T], counter: Optional[Counter] = None) -> Iterator[T]:
    for item in iterable:
        if counter:
            counter.value += 1
        yield item


async def _make_async_iterator(iterable: Iterable[T], counter: Optional[Counter] = None) -> AsyncIterator[T]:
    for item in iterable:
        if counter:
            counter.value += 1
        yield item


class _OneShotIterable(Iterable[T]):
    def __init__(self, iterable: Iterable[T]) -> None:
        self._iterator = iter(iterable)

    @override
    def __iter__(self) -> Iterator[T]:
        return self._iterator


class _OneShotAsyncIterable(AsyncIterable[T]):
    def __init__(self, iterable: Iterable[T]) -> None:
        self._iterator = _make_async_iterator(iterable)

    @override
    def __aiter__(self) -> AsyncIterator[T]:
        return self._iterator


class _NonSeekableBytesIO(io.BytesIO):
    @override
    def seekable(self) -> bool:
        return False

    @override
    def seek(self, offset: int, whence: int = 0) -> int:
        raise io.UnsupportedOperation("seek")

    @override
    def tell(self) -> int:
        raise io.UnsupportedOperation("tell")


def _get_open_connections(client: SEG | AsyncSEG) -> int:
    transport = client._client._transport
    if isinstance(transport, httpx2.HTTPTransport) or isinstance(transport, httpx2.AsyncHTTPTransport):
        return len(transport._pool._requests)

    assert type(transport).__module__ == "httpx2"
    return len(cast(Any, transport)._pool._requests)


@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize(
    "extra_headers,expected",
    [
        ({}, ["Bearer fake-default"]),
        ({"AUTHORIZATION": "Bearer fake-request"}, ["Bearer fake-request"]),
        ({"AUTHORIZATION": Omit()}, []),
    ],
    ids=["default", "override", "omit"],
)
async def test_case_insensitive_auth_headers(
    is_async: bool, extra_headers: dict[str, str | Omit], expected: list[str]
) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.headers.get_list("authorization") == expected
        return httpx2.Response(200, json={"object": "list", "data": []})

    transport = httpx2.MockTransport(handler)
    if is_async:
        async with AsyncSEG(
            api_key="fake-original",
            default_headers={"authorization": "Bearer fake-default"},
            http_client=httpx2.AsyncClient(transport=transport),
        ) as async_client:
            await async_client.models.list(extra_headers=extra_headers)
    else:
        with SEG(
            api_key="fake-original",
            default_headers={"authorization": "Bearer fake-default"},
            http_client=httpx2.Client(transport=transport),
        ) as client:
            client.models.list(extra_headers=extra_headers)


class TestSEG:
    @pytest.mark.parametrize(
        "code_fields,expected_code",
        [
            ({"code": 404}, "404"),
            ({"code": 0}, "0"),
            ({"code": "invalid_request"}, "invalid_request"),
            ({"code": ""}, ""),
            ({"code": None}, None),
            ({}, None),
        ],
    )
    @pytest.mark.respx2(base_url=base_url)
    def test_api_error_code_is_string(
        self,
        code_fields: dict[str, object],
        expected_code: str | None,
        respx2_mock: MockRouter,
        client: SEG,
    ) -> None:
        body = {"message": "Example error", "type": "invalid_request_error", "param": "model", **code_fields}
        response = httpx2.Response(400, json={"error": body})
        respx2_mock.get("/foo").mock(return_value=response)

        with pytest.raises(APIStatusError) as exc_info:
            client.get("/foo", cast_to=httpx2.Response)

        error = exc_info.value
        assert error.code == expected_code
        assert error.body == body
        assert error.response.json() == {"error": body}
        assert error.status_code == 400
        assert error.type == "invalid_request_error"
        assert error.param == "model"

    @pytest.mark.respx2(base_url=base_url)
    def test_raw_response(self, respx2_mock: MockRouter, client: SEG) -> None:
        respx2_mock.post("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        response = client.post("/foo", cast_to=httpx2.Response)
        assert response.status_code == 200
        assert type(response).__module__ == os.environ.get("SEG_TEST_HTTP_CLIENT", "httpx2")
        assert response.json() == {"foo": "bar"}

    @pytest.mark.respx2(base_url=base_url)
    def test_raw_response_for_binary(self, respx2_mock: MockRouter, client: SEG) -> None:
        respx2_mock.post("/foo").mock(
            return_value=httpx2.Response(200, headers={"Content-Type": "application/binary"}, content='{"foo": "bar"}')
        )

        response = client.post("/foo", cast_to=httpx2.Response)
        assert response.status_code == 200
        assert type(response).__module__ == os.environ.get("SEG_TEST_HTTP_CLIENT", "httpx2")
        assert response.json() == {"foo": "bar"}

    def test_copy_default_options(self, client: SEG) -> None:
        # options that have a default are overridden correctly
        copied = client.copy(max_retries=7)
        assert copied.max_retries == 7
        assert client.max_retries == 2

        copied2 = copied.copy(max_retries=6)
        assert copied2.max_retries == 6
        assert copied.max_retries == 7

        # timeout
        assert isinstance(client.timeout, httpx2.Timeout)
        copied = client.copy(timeout=None)
        assert copied.timeout is None
        assert isinstance(client.timeout, httpx2.Timeout)

    def test_copy_signature(self, client: SEG) -> None:
        # ensure the same parameters that can be passed to the client are defined in the `.copy()` method
        init_signature = inspect.signature(
            # mypy doesn't like that we access the `__init__` property.
            client.__init__,  # type: ignore[misc]
        )
        copy_signature = inspect.signature(client.copy)
        exclude_params = {"transport", "proxies", "_strict_response_validation"}

        for name in init_signature.parameters.keys():
            if name in exclude_params:
                continue

            copy_param = copy_signature.parameters.get(name)
            assert copy_param is not None, f"copy() signature is missing the {name} param"

    @pytest.mark.skipif(sys.version_info >= (3, 10), reason="fails because of a memory leak that started from 3.12")
    def test_copy_build_request(self, client: SEG) -> None:
        options = FinalRequestOptions(method="get", url="/foo")

        def build_request(options: FinalRequestOptions) -> None:
            client_copy = client.copy()
            client_copy._build_request(options)

        # ensure that the machinery is warmed up before tracing starts.
        build_request(options)
        gc.collect()

        tracemalloc.start(1000)

        snapshot_before = tracemalloc.take_snapshot()

        ITERATIONS = 10
        for _ in range(ITERATIONS):
            build_request(options)

        gc.collect()
        snapshot_after = tracemalloc.take_snapshot()

        tracemalloc.stop()

        def add_leak(leaks: list[tracemalloc.StatisticDiff], diff: tracemalloc.StatisticDiff) -> None:
            if diff.count == 0:
                # Avoid false positives by considering only leaks (i.e. allocations that persist).
                return

            if diff.count % ITERATIONS != 0:
                # Avoid false positives by considering only leaks that appear per iteration.
                return

            for frame in diff.traceback:
                if any(
                    frame.filename.endswith(fragment)
                    for fragment in [
                        # to_raw_response_wrapper leaks through the @functools.wraps() decorator.
                        #
                        # removing the decorator fixes the leak for reasons we don't understand.
                        "seg/_legacy_response.py",
                        "seg/_response.py",
                        # pydantic.BaseModel.model_dump || pydantic.BaseModel.dict leak memory for some reason.
                        "seg/_compat.py",
                        # Standard library leaks we don't care about.
                        "/logging/__init__.py",
                    ]
                ):
                    return

            leaks.append(diff)

        leaks: list[tracemalloc.StatisticDiff] = []
        for diff in snapshot_after.compare_to(snapshot_before, "traceback"):
            add_leak(leaks, diff)
        if leaks:
            for leak in leaks:
                print("MEMORY LEAK:", leak)
                for frame in leak.traceback:
                    print(frame)
            raise AssertionError()

    def test_request_timeout(self, client: SEG) -> None:
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        timeout = httpx2.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == DEFAULT_TIMEOUT

        request = client._build_request(FinalRequestOptions(method="get", url="/foo", timeout=httpx2.Timeout(100.0)))
        timeout = httpx2.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == httpx2.Timeout(100.0)

    def test_hardcoded_query_params_in_url(self, client: SEG) -> None:
        request = client._build_request(FinalRequestOptions(method="get", url="/foo?beta=true"))
        url = httpx2.URL(str(request.url))
        assert dict(url.params) == {"beta": "true"}

        request = client._build_request(
            FinalRequestOptions(
                method="get",
                url="/foo?beta=true",
                params={"limit": "10", "page": "abc"},
            )
        )
        url = httpx2.URL(str(request.url))
        assert dict(url.params) == {"beta": "true", "limit": "10", "page": "abc"}

        request = client._build_request(
            FinalRequestOptions(
                method="get",
                url="/files/a%2Fb?beta=true",
                params={"limit": "10"},
            )
        )
        assert request.url.raw_path == b"/files/a%2Fb?beta=true&limit=10"

    def test_request_extra_json(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": False}

        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"baz": False}

        # `extra_json` takes priority over `json_data` when keys clash
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar", "baz": True},
                extra_json={"baz": None},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": None}

    def test_request_extra_headers(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(extra_headers={"X-Foo": "Foo"}),
            ),
        )
        assert request.headers.get("X-Foo") == "Foo"

        # `extra_headers` takes priority over `default_headers` when keys clash
        request = client.with_options(default_headers={"X-Bar": "true"})._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_headers={"X-Bar": "false"},
                ),
            ),
        )
        assert request.headers.get("X-Bar") == "false"

    def test_request_extra_query(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_query={"my_query_param": "Foo"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"my_query_param": "Foo"}

        # if both `query` and `extra_query` are given, they are merged
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"bar": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"bar": "1", "foo": "2"}

        # `extra_query` takes priority over `query` when keys clash
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"foo": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"foo": "2"}

    def test_multipart_repeating_array(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions.construct(
                method="post",
                url="/foo",
                headers={"Content-Type": "multipart/form-data; boundary=6b7ba517decee4a450543ea6ae821c82"},
                json_data={"array": ["foo", "bar"]},
                files=[("foo.txt", b"hello world")],
            )
        )

        assert request.read().split(b"\r\n") == [
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"foo",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"bar",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="foo.txt"; filename="upload"',
            b"Content-Type: application/octet-stream",
            b"",
            b"hello world",
            b"--6b7ba517decee4a450543ea6ae821c82--",
            b"",
        ]

    @pytest.mark.respx2(base_url=base_url)
    def test_binary_content_upload(self, respx2_mock: MockRouter, client: SEG) -> None:
        respx2_mock.post("/upload").mock(side_effect=mirror_request_content)

        file_content = b"Hello, this is a test file."

        response = client.post(
            "/upload",
            content=file_content,
            cast_to=httpx2.Response,
            options={"headers": {"Content-Type": "application/octet-stream"}},
        )

        assert response.status_code == 200
        assert response.request.headers["Content-Type"] == "application/octet-stream"
        assert response.content == file_content

    @pytest.mark.parametrize("content_factory", [_make_sync_iterator, _OneShotIterable])
    @pytest.mark.parametrize("failure_mode", ["status", "timeout", "connection"])
    def test_binary_content_retry_does_not_reuse_one_shot_iterable(
        self,
        content_factory: Callable[[Iterable[bytes]], Iterable[bytes]],
        failure_mode: Literal["status", "timeout", "connection"],
    ) -> None:
        file_content = b"Hello, this is a test file."
        request_bodies: list[bytes] = []

        def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(request.read())
            if len(request_bodies) > 1:
                return httpx2.Response(200)
            if failure_mode == "timeout":
                raise httpx2.ReadTimeout("timed out", request=request)
            if failure_mode == "connection":
                raise httpx2.ConnectError("connection failed", request=request)
            return httpx2.Response(500, json={"error": {}})

        expected_error = {
            "status": APIStatusError,
            "timeout": APITimeoutError,
            "connection": APIConnectionError,
        }[failure_mode]

        with SEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.Client(transport=MockTransport(handler=mock_handler)),
        ) as client:
            with pytest.raises(expected_error):
                client.post(
                    "/upload",
                    content=content_factory([file_content]),
                    cast_to=httpx2.Response,
                )

        assert request_bodies == [file_content]

    @pytest.mark.parametrize("content_type", [list, tuple])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    def test_binary_content_retry_reuses_known_repeatable_iterable(
        self, content_type: type[list[bytes]] | type[tuple[bytes, ...]]
    ) -> None:
        file_content = b"Hello, this is a test file."
        request_bodies: list[bytes] = []

        def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(request.read())
            return httpx2.Response(500 if len(request_bodies) == 1 else 200, json={"error": {}})

        with SEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.Client(transport=MockTransport(handler=mock_handler)),
        ) as client:
            response = client.post(
                "/upload",
                content=content_type([file_content]),
                cast_to=httpx2.Response,
            )

        assert response.status_code == 200
        assert request_bodies == [file_content, file_content]

    def test_binary_content_retry_checks_prepared_options(self) -> None:
        file_content = b"Hello, this prepared body must not be replayed."
        prepared_content = _OneShotIterable([file_content])
        request_bodies: list[bytes] = []

        def prepare_options(options: FinalRequestOptions) -> FinalRequestOptions:
            options.content = prepared_content
            return options

        def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(request.read())
            return httpx2.Response(500 if len(request_bodies) == 1 else 200, json={"error": {}})

        with SEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.Client(transport=MockTransport(handler=mock_handler)),
        ) as client:
            with mock.patch.object(client, "_prepare_options", side_effect=prepare_options):
                with pytest.raises(APIStatusError):
                    client.post("/upload", content=file_content, cast_to=httpx2.Response)

        assert request_bodies == [file_content]

    def test_multipart_retry_does_not_reuse_non_seekable_file(self) -> None:
        file_content = b"Hello, this multipart file must not be replayed."
        earlier_file = io.BytesIO(b"first file")
        request_bodies: list[bytes] = []

        def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(request.read())
            return httpx2.Response(500, json={"error": {}})

        with SEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.Client(transport=MockTransport(handler=mock_handler)),
        ) as client:
            with pytest.raises(APIStatusError):
                client.post(
                    "/upload",
                    files={
                        "first": ("first.txt", earlier_file),
                        "file": ("upload.txt", _NonSeekableBytesIO(file_content), "text/plain"),
                    },
                    cast_to=httpx2.Response,
                )

        assert len(request_bodies) == 1
        assert file_content in request_bodies[0]
        # The first send consumes this file; refusing a retry must not rewind it.
        assert earlier_file.tell() == len(b"first file")

    @pytest.mark.parametrize("rewind_fails", [False, True], ids=["rewind", "closed-file"])
    def test_multipart_retry_rewinds_seekable_file(self, rewind_fails: bool) -> None:
        file_content = b"Hello, this multipart file can be replayed."
        file = io.BytesIO(file_content)
        original_response = httpx2.Response(500)
        request_bodies: list[bytes] = []

        def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(request.read())
            if rewind_fails:
                file.close()
            return original_response if len(request_bodies) == 1 else httpx2.Response(200)

        with SEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.Client(transport=MockTransport(handler=mock_handler)),
        ) as client:
            try:
                response = client.post(
                    "/upload",
                    files={"file": ("upload.txt", file, "text/plain")},
                    cast_to=httpx2.Response,
                )
            except APIStatusError as exc:
                assert rewind_fails
                assert exc.response is original_response
            else:
                assert not rewind_fails
                assert response.status_code == 200

        assert len(request_bodies) == (1 if rewind_fails else 2)
        assert all(file_content in body for body in request_bodies)

    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    def test_binary_content_retry_rewinds_seekable_stream(self) -> None:
        file_content = b"Hello, this is a test file."
        request_bodies: list[bytes] = []

        def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(request.read())
            return httpx2.Response(500 if len(request_bodies) == 1 else 200, json={"error": {}})

        with SEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.Client(transport=MockTransport(handler=mock_handler)),
        ) as client:
            content = io.BytesIO(b"prefix" + file_content)
            content.seek(len(b"prefix"))
            response = client.post(
                "/upload",
                content=content,
                cast_to=httpx2.Response,
            )

        assert response.status_code == 200
        assert request_bodies == [file_content, file_content]

    @pytest.mark.respx2(base_url=base_url)
    def test_binary_content_upload_with_body_is_deprecated(self, respx2_mock: MockRouter, client: SEG) -> None:
        respx2_mock.post("/upload").mock(side_effect=mirror_request_content)

        file_content = b"Hello, this is a test file."

        with pytest.deprecated_call(
            match="Passing raw bytes as `body` is deprecated and will be removed in a future version. Please pass raw bytes via the `content` parameter instead."
        ):
            response = client.post(
                "/upload",
                body=file_content,
                cast_to=httpx2.Response,
                options={"headers": {"Content-Type": "application/octet-stream"}},
            )

        assert response.status_code == 200
        assert response.request.headers["Content-Type"] == "application/octet-stream"
        assert response.content == file_content

    @pytest.mark.respx2(base_url=base_url)
    @pytest.mark.parametrize("client", [False], indirect=True)
    def test_bare_container_response(self, respx2_mock: MockRouter, client: SEG) -> None:
        class Model(BaseModel):
            metadata: dict  # type: ignore[type-arg]
            items: list  # type: ignore[type-arg]

        data = {"metadata": {"key": "value"}, "items": [1, "two"]}
        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json=data))

        assert client.get("/foo", cast_to=dict) == data
        response = client.get("/foo", cast_to=Model)
        assert response.model_dump() == data

        respx2_mock.get("/items").mock(return_value=httpx2.Response(200, json=[1, "two"]))
        assert client.get("/items", cast_to=list) == [1, "two"]

    @pytest.mark.respx2(base_url=base_url)
    def test_basic_union_response(self, respx2_mock: MockRouter, client: SEG) -> None:
        class Model1(BaseModel):
            name: str

        class Model2(BaseModel):
            foo: str

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        response = client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

    @pytest.mark.respx2(base_url=base_url)
    def test_union_response_different_types(self, respx2_mock: MockRouter, client: SEG) -> None:
        """Union of objects with the same field name using a different type"""

        class Model1(BaseModel):
            foo: int

        class Model2(BaseModel):
            foo: str

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        response = client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": 1}))

        response = client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model1)
        assert response.foo == 1

    @pytest.mark.respx2(base_url=base_url)
    def test_non_application_json_content_type_for_json_data(self, respx2_mock: MockRouter, client: SEG) -> None:
        """
        Response that sets Content-Type to something other than application/json but returns json data
        """

        class Model(BaseModel):
            foo: int

        respx2_mock.get("/foo").mock(
            return_value=httpx2.Response(
                200,
                content=json.dumps({"foo": 2}),
                headers={"Content-Type": "application/text"},
            )
        )

        response = client.get("/foo", cast_to=Model)
        assert isinstance(response, Model)
        assert response.foo == 2

    @pytest.mark.parametrize(
        "client",
        [
            SEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
            ),
            SEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx2.Client(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_base_url_trailing_slash(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"
        client.close()

    @pytest.mark.parametrize(
        "client",
        [
            SEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
            ),
            SEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx2.Client(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_base_url_no_trailing_slash(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"
        client.close()

    @pytest.mark.parametrize(
        "client",
        [
            SEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
            ),
            SEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx2.Client(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_absolute_request_url(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="https://myapi.com/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "https://myapi.com/foo"
        client.close()

    @pytest.mark.respx2(base_url=base_url)
    def test_client_response_validation_error(self, respx2_mock: MockRouter, client: SEG) -> None:
        class Model(BaseModel):
            foo: str

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": {"invalid": True}}))

        with pytest.raises(APIResponseValidationError) as exc:
            client.get("/foo", cast_to=Model)

        assert isinstance(exc.value.__cause__, ValidationError)

    @pytest.mark.respx2(base_url=base_url)
    def test_default_stream_cls(self, respx2_mock: MockRouter, client: SEG) -> None:
        class Model(BaseModel):
            name: str

        respx2_mock.post("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        stream = client.post("/foo", cast_to=Model, stream=True, stream_cls=Stream[Model])
        assert isinstance(stream, Stream)
        stream.response.close()

    @pytest.mark.parametrize(
        "remaining_retries,retry_after,timeout",
        [
            [3, "20", 20],
            [3, "0", 0.5],
            [3, "-10", 0.5],
            [3, "60", 60],
            [3, "61", 61],
            [3, "120", 120],
            [3, "121", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:57 GMT", 20],
            [3, "Fri, 29 Sep 2023 16:26:37 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:27:37 GMT", 60],
            [3, "Fri, 29 Sep 2023 16:27:38 GMT", 61],
            [3, "Fri, 29 Sep 2023 16:28:37 GMT", 120],
            [3, "Fri, 29 Sep 2023 16:28:38 GMT", 0.5],
            [3, "99999999999999999999999999999999999", 0.5],
            [3, "inf", 0.5],
            [3, "nan", 0.5],
            [3, "Zun, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "Fri, 29 Sep 100000 16:26:57 GMT", 0.5],
            [3, "", 0.5],
            [2, "", 0.5 * 2.0],
            [1, "", 0.5 * 4.0],
            [-1100, "", 8],  # test large number potentially overflowing
        ],
    )
    @mock.patch("time.time", mock.MagicMock(return_value=1696004797))
    def test_parse_retry_after_header(
        self, remaining_retries: int, retry_after: str, timeout: float, client: SEG
    ) -> None:
        headers = httpx2.Headers({"retry-after": retry_after})
        options = FinalRequestOptions(method="get", url="/foo", max_retries=3)
        calculated = client._calculate_retry_timeout(remaining_retries, options, headers)
        assert calculated == pytest.approx(timeout, 0.5 * 0.875)  # pyright: ignore[reportUnknownMemberType]

    @pytest.mark.parametrize(
        "headers,should_retry",
        [
            [{"retry-after": "120"}, True],
            [{"retry-after": "121"}, False],
            [{"retry-after-ms": "120000"}, True],
            [{"retry-after-ms": "120001"}, False],
            [{"retry-after": "Fri, 29 Sep 2023 16:28:37 GMT"}, True],
            [{"retry-after": "Fri, 29 Sep 2023 16:28:38 GMT"}, False],
        ],
    )
    @mock.patch("time.time", mock.MagicMock(return_value=1696004797))
    def test_retry_after_max_delay(self, headers: dict[str, str], should_retry: bool, client: SEG) -> None:
        response = httpx2.Response(429, headers=headers)
        assert client._should_retry(response) is should_retry

    @pytest.mark.respx2(base_url=base_url)
    def test_does_not_retry_retry_after_above_max(self, respx2_mock: MockRouter, client: SEG) -> None:
        route = respx2_mock.get("/foo").mock(
            return_value=httpx2.Response(429, headers={"retry-after": "121"}, json={"error": {}})
        )

        with pytest.raises(APIStatusError):
            client.get("/foo", cast_to=httpx2.Response)

        assert route.call_count == 1

    @pytest.mark.respx2(base_url=base_url)
    def test_invalid_retry_after_date_does_not_mask_status_error(self, respx2_mock: MockRouter, client: SEG) -> None:
        route = respx2_mock.get("/foo").mock(
            return_value=httpx2.Response(
                400,
                headers={"retry-after": "Fri, 29 Sep 100000 16:26:57 GMT"},
                json={"error": {}},
            )
        )

        with pytest.raises(APIStatusError):
            client.get("/foo", cast_to=httpx2.Response)

        assert route.call_count == 1

    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    def test_retrying_timeout_errors_doesnt_leak(self, respx2_mock: MockRouter, client: SEG) -> None:
        respx2_mock.post("/chat/completions").mock(side_effect=httpx2.TimeoutException("Test timeout error"))

        with pytest.raises(APITimeoutError):
            client.chat.completions.with_streaming_response.create(
                messages=[
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                model="gpt-5.4",
            ).__enter__()

        assert _get_open_connections(client) == 0

    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    def test_retrying_status_errors_doesnt_leak(self, respx2_mock: MockRouter, client: SEG) -> None:
        respx2_mock.post("/chat/completions").mock(return_value=httpx2.Response(500))

        with pytest.raises(APIStatusError):
            client.chat.completions.with_streaming_response.create(
                messages=[
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                model="gpt-5.4",
            ).__enter__()
        assert _get_open_connections(client) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    @pytest.mark.parametrize("failure_mode", ["status", "exception"])
    @pytest.mark.parametrize("max_retries", [4, 10**100])
    def test_retries_taken(
        self,
        client: SEG,
        failures_before_success: int,
        max_retries: int,
        failure_mode: Literal["status", "exception"],
        respx2_mock: MockRouter,
    ) -> None:
        client = client.with_options(max_retries=max_retries)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                if failure_mode == "exception":
                    raise httpx2.ConnectError("oops")
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        response = client.chat.completions.with_raw_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
        )

        assert response.retries_taken == failures_before_success
        assert int(response.http_request.headers["x-stainless-retry-count"]) == failures_before_success

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    def test_omit_retry_count_header(self, client: SEG, failures_before_success: int, respx2_mock: MockRouter) -> None:
        client = client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        response = client.chat.completions.with_raw_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
            extra_headers={"x-stainless-retry-count": Omit()},
        )

        assert len(response.http_request.headers.get_list("x-stainless-retry-count")) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    def test_overwrite_retry_count_header(
        self, client: SEG, failures_before_success: int, respx2_mock: MockRouter
    ) -> None:
        client = client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        response = client.chat.completions.with_raw_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
            extra_headers={"x-stainless-retry-count": "42"},
        )

        assert response.http_request.headers.get("x-stainless-retry-count") == "42"

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    def test_retries_taken_new_response_class(
        self, client: SEG, failures_before_success: int, respx2_mock: MockRouter
    ) -> None:
        client = client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        with client.chat.completions.with_streaming_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
        ) as response:
            assert response.retries_taken == failures_before_success
            assert int(response.http_request.headers["x-stainless-retry-count"]) == failures_before_success

    @pytest.mark.skipif(
        sys.platform == "win32", reason="httpx2 does not derive proxy mounts from HTTPS_PROXY on Windows"
    )
    def test_proxy_environment_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Test that the proxy environment variables are set correctly
        monkeypatch.setenv("HTTPS_PROXY", "https://example.org")
        # Delete in case our environment has any proxy env vars set
        monkeypatch.delenv("HTTP_PROXY", raising=False)
        monkeypatch.delenv("ALL_PROXY", raising=False)
        monkeypatch.delenv("NO_PROXY", raising=False)
        monkeypatch.delenv("http_proxy", raising=False)
        monkeypatch.delenv("https_proxy", raising=False)
        monkeypatch.delenv("all_proxy", raising=False)
        monkeypatch.delenv("no_proxy", raising=False)

        client = DefaultHttpxClient()

        mounts = tuple(client._mounts.items())
        assert len(mounts) == 1
        assert mounts[0][0].pattern == "https://"

    @pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
    def test_default_client_creation(self) -> None:
        # Ensure that the client can be initialized without any exceptions
        DefaultHttpxClient(
            verify=True,
            cert=None,
            trust_env=True,
            http1=True,
            http2=False,
            limits=httpx2.Limits(max_connections=100, max_keepalive_connections=20),
        )

    @pytest.mark.respx2(base_url=base_url)
    def test_follow_redirects(self, respx2_mock: MockRouter, client: SEG) -> None:
        # Test that the default follow_redirects=True allows following redirects
        respx2_mock.post("/redirect").mock(
            return_value=httpx2.Response(302, headers={"Location": f"{base_url}/redirected"})
        )
        respx2_mock.get("/redirected").mock(return_value=httpx2.Response(200, json={"status": "ok"}))

        response = client.post("/redirect", body={"key": "value"}, cast_to=httpx2.Response)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.respx2(base_url=base_url)
    def test_follow_redirects_disabled(self, respx2_mock: MockRouter, client: SEG) -> None:
        # Test that follow_redirects=False prevents following redirects
        respx2_mock.post("/redirect").mock(
            return_value=httpx2.Response(302, headers={"Location": f"{base_url}/redirected"})
        )

        with pytest.raises(APIStatusError) as exc_info:
            client.post(
                "/redirect", body={"key": "value"}, options={"follow_redirects": False}, cast_to=httpx2.Response
            )

        assert exc_info.value.response.status_code == 302
        assert exc_info.value.response.headers["Location"] == f"{base_url}/redirected"

    def test_api_key_before_after_refresh_str(self) -> None:
        client = SEG(base_url=base_url, api_key="test_api_key")

        assert client.auth_headers.get("Authorization") == "Bearer test_api_key"
        client._refresh_api_key()

        assert client.auth_headers.get("Authorization") == "Bearer test_api_key"

    def test_copy_auth(self) -> None:
        client = SEG(base_url=base_url, api_key=lambda: "test_bearer_token_1").copy(
            api_key=lambda: "test_bearer_token_2"
        )
        client._refresh_api_key()
        assert client.auth_headers == {"Authorization": "Bearer test_bearer_token_2"}


class TestAsyncSEG:
    @pytest.mark.parametrize(
        "code_fields,expected_code",
        [
            ({"code": 404}, "404"),
            ({"code": 0}, "0"),
            ({"code": "invalid_request"}, "invalid_request"),
            ({"code": ""}, ""),
            ({"code": None}, None),
            ({}, None),
        ],
    )
    @pytest.mark.respx2(base_url=base_url)
    async def test_api_error_code_is_string(
        self,
        code_fields: dict[str, object],
        expected_code: str | None,
        respx2_mock: MockRouter,
        async_client: AsyncSEG,
    ) -> None:
        body = {"message": "Example error", "type": "invalid_request_error", "param": "model", **code_fields}
        response = httpx2.Response(400, json={"error": body})
        respx2_mock.get("/foo").mock(return_value=response)

        with pytest.raises(APIStatusError) as exc_info:
            await async_client.get("/foo", cast_to=httpx2.Response)

        error = exc_info.value
        assert error.code == expected_code
        assert error.body == body
        assert error.response.json() == {"error": body}
        assert error.status_code == 400
        assert error.type == "invalid_request_error"
        assert error.param == "model"

    @pytest.mark.respx2(base_url=base_url)
    async def test_raw_response(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        respx2_mock.post("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        response = await async_client.post("/foo", cast_to=httpx2.Response)
        assert response.status_code == 200
        assert type(response).__module__ == os.environ.get("SEG_TEST_HTTP_CLIENT", "httpx2")
        assert response.json() == {"foo": "bar"}

    @pytest.mark.respx2(base_url=base_url)
    async def test_raw_response_for_binary(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        respx2_mock.post("/foo").mock(
            return_value=httpx2.Response(200, headers={"Content-Type": "application/binary"}, content='{"foo": "bar"}')
        )

        response = await async_client.post("/foo", cast_to=httpx2.Response)
        assert response.status_code == 200
        assert type(response).__module__ == os.environ.get("SEG_TEST_HTTP_CLIENT", "httpx2")
        assert response.json() == {"foo": "bar"}

    def test_copy_default_options(self, async_client: AsyncSEG) -> None:
        # options that have a default are overridden correctly
        copied = async_client.copy(max_retries=7)
        assert copied.max_retries == 7
        assert async_client.max_retries == 2

        copied2 = copied.copy(max_retries=6)
        assert copied2.max_retries == 6
        assert copied.max_retries == 7

        # timeout
        assert isinstance(async_client.timeout, httpx2.Timeout)
        copied = async_client.copy(timeout=None)
        assert copied.timeout is None
        assert isinstance(async_client.timeout, httpx2.Timeout)

    def test_copy_signature(self, async_client: AsyncSEG) -> None:
        # ensure the same parameters that can be passed to the client are defined in the `.copy()` method
        init_signature = inspect.signature(
            # mypy doesn't like that we access the `__init__` property.
            async_client.__init__,  # type: ignore[misc]
        )
        copy_signature = inspect.signature(async_client.copy)
        exclude_params = {"transport", "proxies", "_strict_response_validation"}

        for name in init_signature.parameters.keys():
            if name in exclude_params:
                continue

            copy_param = copy_signature.parameters.get(name)
            assert copy_param is not None, f"copy() signature is missing the {name} param"

    @pytest.mark.skipif(sys.version_info >= (3, 10), reason="fails because of a memory leak that started from 3.12")
    def test_copy_build_request(self, async_client: AsyncSEG) -> None:
        options = FinalRequestOptions(method="get", url="/foo")

        def build_request(options: FinalRequestOptions) -> None:
            client_copy = async_client.copy()
            client_copy._build_request(options)

        # ensure that the machinery is warmed up before tracing starts.
        build_request(options)
        gc.collect()

        tracemalloc.start(1000)

        snapshot_before = tracemalloc.take_snapshot()

        ITERATIONS = 10
        for _ in range(ITERATIONS):
            build_request(options)

        gc.collect()
        snapshot_after = tracemalloc.take_snapshot()

        tracemalloc.stop()

        def add_leak(leaks: list[tracemalloc.StatisticDiff], diff: tracemalloc.StatisticDiff) -> None:
            if diff.count == 0:
                # Avoid false positives by considering only leaks (i.e. allocations that persist).
                return

            if diff.count % ITERATIONS != 0:
                # Avoid false positives by considering only leaks that appear per iteration.
                return

            for frame in diff.traceback:
                if any(
                    frame.filename.endswith(fragment)
                    for fragment in [
                        # to_raw_response_wrapper leaks through the @functools.wraps() decorator.
                        #
                        # removing the decorator fixes the leak for reasons we don't understand.
                        "seg/_legacy_response.py",
                        "seg/_response.py",
                        # pydantic.BaseModel.model_dump || pydantic.BaseModel.dict leak memory for some reason.
                        "seg/_compat.py",
                        # Standard library leaks we don't care about.
                        "/logging/__init__.py",
                    ]
                ):
                    return

            leaks.append(diff)

        leaks: list[tracemalloc.StatisticDiff] = []
        for diff in snapshot_after.compare_to(snapshot_before, "traceback"):
            add_leak(leaks, diff)
        if leaks:
            for leak in leaks:
                print("MEMORY LEAK:", leak)
                for frame in leak.traceback:
                    print(frame)
            raise AssertionError()

    async def test_request_timeout(self, async_client: AsyncSEG) -> None:
        request = async_client._build_request(FinalRequestOptions(method="get", url="/foo"))
        timeout = httpx2.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == DEFAULT_TIMEOUT

        request = async_client._build_request(
            FinalRequestOptions(method="get", url="/foo", timeout=httpx2.Timeout(100.0))
        )
        timeout = httpx2.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == httpx2.Timeout(100.0)

    async def test_hardcoded_query_params_in_url(self, async_client: AsyncSEG) -> None:
        request = async_client._build_request(FinalRequestOptions(method="get", url="/foo?beta=true"))
        url = httpx2.URL(str(request.url))
        assert dict(url.params) == {"beta": "true"}

        request = async_client._build_request(
            FinalRequestOptions(
                method="get",
                url="/foo?beta=true",
                params={"limit": "10", "page": "abc"},
            )
        )
        url = httpx2.URL(str(request.url))
        assert dict(url.params) == {"beta": "true", "limit": "10", "page": "abc"}

        request = async_client._build_request(
            FinalRequestOptions(
                method="get",
                url="/files/a%2Fb?beta=true",
                params={"limit": "10"},
            )
        )
        assert request.url.raw_path == b"/files/a%2Fb?beta=true&limit=10"

    def test_request_extra_json(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": False}

        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"baz": False}

        # `extra_json` takes priority over `json_data` when keys clash
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar", "baz": True},
                extra_json={"baz": None},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": None}

    def test_request_extra_headers(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(extra_headers={"X-Foo": "Foo"}),
            ),
        )
        assert request.headers.get("X-Foo") == "Foo"

        # `extra_headers` takes priority over `default_headers` when keys clash
        request = client.with_options(default_headers={"X-Bar": "true"})._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_headers={"X-Bar": "false"},
                ),
            ),
        )
        assert request.headers.get("X-Bar") == "false"

    def test_request_extra_query(self, client: SEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_query={"my_query_param": "Foo"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"my_query_param": "Foo"}

        # if both `query` and `extra_query` are given, they are merged
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"bar": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"bar": "1", "foo": "2"}

        # `extra_query` takes priority over `query` when keys clash
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"foo": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"foo": "2"}

    def test_multipart_repeating_array(self, async_client: AsyncSEG) -> None:
        request = async_client._build_request(
            FinalRequestOptions.construct(
                method="post",
                url="/foo",
                headers={"Content-Type": "multipart/form-data; boundary=6b7ba517decee4a450543ea6ae821c82"},
                json_data={"array": ["foo", "bar"]},
                files=[("foo.txt", b"hello world")],
            )
        )

        assert request.read().split(b"\r\n") == [
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"foo",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"bar",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="foo.txt"; filename="upload"',
            b"Content-Type: application/octet-stream",
            b"",
            b"hello world",
            b"--6b7ba517decee4a450543ea6ae821c82--",
            b"",
        ]

    @pytest.mark.respx2(base_url=base_url)
    async def test_binary_content_upload(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        respx2_mock.post("/upload").mock(side_effect=mirror_request_content)

        file_content = b"Hello, this is a test file."

        response = await async_client.post(
            "/upload",
            content=file_content,
            cast_to=httpx2.Response,
            options={"headers": {"Content-Type": "application/octet-stream"}},
        )

        assert response.status_code == 200
        assert response.request.headers["Content-Type"] == "application/octet-stream"
        assert response.content == file_content

    @pytest.mark.parametrize("content_factory", [_make_async_iterator, _OneShotAsyncIterable])
    @pytest.mark.parametrize("failure_mode", ["status", "timeout", "connection"])
    async def test_binary_content_retry_does_not_reuse_one_shot_asynciterable(
        self,
        content_factory: Callable[[Iterable[bytes]], AsyncIterable[bytes]],
        failure_mode: Literal["status", "timeout", "connection"],
    ) -> None:
        file_content = b"Hello, this is a test file."
        request_bodies: list[bytes] = []

        async def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(await request.aread())
            if len(request_bodies) > 1:
                return httpx2.Response(200)
            if failure_mode == "timeout":
                raise httpx2.ReadTimeout("timed out", request=request)
            if failure_mode == "connection":
                raise httpx2.ConnectError("connection failed", request=request)
            return httpx2.Response(500, json={"error": {}})

        expected_error = {
            "status": APIStatusError,
            "timeout": APITimeoutError,
            "connection": APIConnectionError,
        }[failure_mode]

        async with AsyncSEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.AsyncClient(transport=MockTransport(handler=mock_handler)),
        ) as client:
            with pytest.raises(expected_error):
                await client.post(
                    "/upload",
                    content=content_factory([file_content]),
                    cast_to=httpx2.Response,
                )

        assert request_bodies == [file_content]

    async def test_binary_content_retry_checks_prepared_options(self) -> None:
        file_content = b"Hello, this prepared body must not be replayed."
        prepared_content = _OneShotAsyncIterable([file_content])
        request_bodies: list[bytes] = []

        async def prepare_options(options: FinalRequestOptions) -> FinalRequestOptions:
            options.content = prepared_content
            return options

        async def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(await request.aread())
            return httpx2.Response(500 if len(request_bodies) == 1 else 200, json={"error": {}})

        async with AsyncSEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.AsyncClient(transport=MockTransport(handler=mock_handler)),
        ) as client:
            with mock.patch.object(client, "_prepare_options", side_effect=prepare_options):
                with pytest.raises(APIStatusError):
                    await client.post("/upload", content=file_content, cast_to=httpx2.Response)

        assert request_bodies == [file_content]

    async def test_multipart_retry_does_not_reuse_non_seekable_file(self) -> None:
        file_content = b"Hello, this multipart file must not be replayed."
        earlier_file = io.BytesIO(b"first file")
        request_bodies: list[bytes] = []

        async def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(await request.aread())
            return httpx2.Response(500, json={"error": {}})

        async with AsyncSEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.AsyncClient(transport=MockTransport(handler=mock_handler)),
        ) as client:
            with pytest.raises(APIStatusError):
                await client.post(
                    "/upload",
                    files={
                        "first": ("first.txt", earlier_file),
                        "file": ("upload.txt", _NonSeekableBytesIO(file_content), "text/plain"),
                    },
                    cast_to=httpx2.Response,
                )

        assert len(request_bodies) == 1
        assert file_content in request_bodies[0]
        # The first send consumes this file; refusing a retry must not rewind it.
        assert earlier_file.tell() == len(b"first file")

    @pytest.mark.parametrize("rewind_fails", [False, True], ids=["rewind", "closed-file"])
    async def test_multipart_retry_rewinds_seekable_file(self, rewind_fails: bool) -> None:
        file_content = b"Hello, this multipart file can be replayed."
        file = io.BytesIO(file_content)
        original_response = httpx2.Response(500)
        request_bodies: list[bytes] = []

        async def mock_handler(request: httpx2.Request) -> httpx2.Response:
            request_bodies.append(await request.aread())
            if rewind_fails:
                file.close()
            return original_response if len(request_bodies) == 1 else httpx2.Response(200)

        async with AsyncSEG(
            base_url=base_url,
            api_key=api_key,
            max_retries=1,
            http_client=httpx2.AsyncClient(transport=MockTransport(handler=mock_handler)),
        ) as client:
            try:
                response = await client.post(
                    "/upload",
                    files={"file": ("upload.txt", file, "text/plain")},
                    cast_to=httpx2.Response,
                )
            except APIStatusError as exc:
                assert rewind_fails
                assert exc.response is original_response
            else:
                assert not rewind_fails
                assert response.status_code == 200

        assert len(request_bodies) == (1 if rewind_fails else 2)
        assert all(file_content in body for body in request_bodies)

    @pytest.mark.respx2(base_url=base_url)
    async def test_binary_content_upload_with_body_is_deprecated(
        self, respx2_mock: MockRouter, async_client: AsyncSEG
    ) -> None:
        respx2_mock.post("/upload").mock(side_effect=mirror_request_content)

        file_content = b"Hello, this is a test file."

        with pytest.deprecated_call(
            match="Passing raw bytes as `body` is deprecated and will be removed in a future version. Please pass raw bytes via the `content` parameter instead."
        ):
            response = await async_client.post(
                "/upload",
                body=file_content,
                cast_to=httpx2.Response,
                options={"headers": {"Content-Type": "application/octet-stream"}},
            )

        assert response.status_code == 200
        assert response.request.headers["Content-Type"] == "application/octet-stream"
        assert response.content == file_content

    @pytest.mark.respx2(base_url=base_url)
    @pytest.mark.parametrize("async_client", [False], indirect=True)
    async def test_bare_container_response(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        class Model(BaseModel):
            metadata: dict  # type: ignore[type-arg]
            items: list  # type: ignore[type-arg]

        data = {"metadata": {"key": "value"}, "items": [1, "two"]}
        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json=data))

        assert await async_client.get("/foo", cast_to=dict) == data
        response = await async_client.get("/foo", cast_to=Model)
        assert response.model_dump() == data

        respx2_mock.get("/items").mock(return_value=httpx2.Response(200, json=[1, "two"]))
        assert await async_client.get("/items", cast_to=list) == [1, "two"]

    @pytest.mark.respx2(base_url=base_url)
    async def test_basic_union_response(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        class Model1(BaseModel):
            name: str

        class Model2(BaseModel):
            foo: str

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        response = await async_client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

    @pytest.mark.respx2(base_url=base_url)
    async def test_union_response_different_types(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        """Union of objects with the same field name using a different type"""

        class Model1(BaseModel):
            foo: int

        class Model2(BaseModel):
            foo: str

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        response = await async_client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": 1}))

        response = await async_client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model1)
        assert response.foo == 1

    @pytest.mark.respx2(base_url=base_url)
    async def test_non_application_json_content_type_for_json_data(
        self, respx2_mock: MockRouter, async_client: AsyncSEG
    ) -> None:
        """
        Response that sets Content-Type to something other than application/json but returns json data
        """

        class Model(BaseModel):
            foo: int

        respx2_mock.get("/foo").mock(
            return_value=httpx2.Response(
                200,
                content=json.dumps({"foo": 2}),
                headers={"Content-Type": "application/text"},
            )
        )

        response = await async_client.get("/foo", cast_to=Model)
        assert isinstance(response, Model)
        assert response.foo == 2

    @pytest.mark.parametrize(
        "client",
        [
            AsyncSEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
            ),
            AsyncSEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx2.AsyncClient(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    async def test_base_url_trailing_slash(self, client: AsyncSEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"
        await client.close()

    @pytest.mark.parametrize(
        "client",
        [
            AsyncSEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
            ),
            AsyncSEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx2.AsyncClient(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    async def test_base_url_no_trailing_slash(self, client: AsyncSEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"
        await client.close()

    @pytest.mark.parametrize(
        "client",
        [
            AsyncSEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
            ),
            AsyncSEG(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx2.AsyncClient(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    async def test_absolute_request_url(self, client: AsyncSEG) -> None:
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="https://myapi.com/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "https://myapi.com/foo"
        await client.close()

    @pytest.mark.respx2(base_url=base_url)
    async def test_client_response_validation_error(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        class Model(BaseModel):
            foo: str

        respx2_mock.get("/foo").mock(return_value=httpx2.Response(200, json={"foo": {"invalid": True}}))

        with pytest.raises(APIResponseValidationError) as exc:
            await async_client.get("/foo", cast_to=Model)

        assert isinstance(exc.value.__cause__, ValidationError)

    @pytest.mark.respx2(base_url=base_url)
    async def test_default_stream_cls(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        class Model(BaseModel):
            name: str

        respx2_mock.post("/foo").mock(return_value=httpx2.Response(200, json={"foo": "bar"}))

        stream = await async_client.post("/foo", cast_to=Model, stream=True, stream_cls=AsyncStream[Model])
        assert isinstance(stream, AsyncStream)
        await stream.response.aclose()

    @pytest.mark.parametrize(
        "remaining_retries,retry_after,timeout",
        [
            [3, "20", 20],
            [3, "0", 0.5],
            [3, "-10", 0.5],
            [3, "60", 60],
            [3, "61", 61],
            [3, "120", 120],
            [3, "121", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:57 GMT", 20],
            [3, "Fri, 29 Sep 2023 16:26:37 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:27:37 GMT", 60],
            [3, "Fri, 29 Sep 2023 16:27:38 GMT", 61],
            [3, "Fri, 29 Sep 2023 16:28:37 GMT", 120],
            [3, "Fri, 29 Sep 2023 16:28:38 GMT", 0.5],
            [3, "99999999999999999999999999999999999", 0.5],
            [3, "inf", 0.5],
            [3, "nan", 0.5],
            [3, "Zun, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "Fri, 29 Sep 100000 16:26:57 GMT", 0.5],
            [3, "", 0.5],
            [2, "", 0.5 * 2.0],
            [1, "", 0.5 * 4.0],
            [-1100, "", 8],  # test large number potentially overflowing
        ],
    )
    @mock.patch("time.time", mock.MagicMock(return_value=1696004797))
    async def test_parse_retry_after_header(
        self, remaining_retries: int, retry_after: str, timeout: float, async_client: AsyncSEG
    ) -> None:
        headers = httpx2.Headers({"retry-after": retry_after})
        options = FinalRequestOptions(method="get", url="/foo", max_retries=3)
        calculated = async_client._calculate_retry_timeout(remaining_retries, options, headers)
        assert calculated == pytest.approx(timeout, 0.5 * 0.875)  # pyright: ignore[reportUnknownMemberType]

    @pytest.mark.respx2(base_url=base_url)
    async def test_does_not_retry_retry_after_above_max(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        route = respx2_mock.get("/foo").mock(
            return_value=httpx2.Response(429, headers={"retry-after": "121"}, json={"error": {}})
        )

        with pytest.raises(APIStatusError):
            await async_client.get("/foo", cast_to=httpx2.Response)

        assert route.call_count == 1

    @pytest.mark.respx2(base_url=base_url)
    async def test_invalid_retry_after_date_does_not_mask_status_error(
        self, respx2_mock: MockRouter, async_client: AsyncSEG
    ) -> None:
        route = respx2_mock.get("/foo").mock(
            return_value=httpx2.Response(
                400,
                headers={"retry-after": "Fri, 29 Sep 100000 16:26:57 GMT"},
                json={"error": {}},
            )
        )

        with pytest.raises(APIStatusError):
            await async_client.get("/foo", cast_to=httpx2.Response)

        assert route.call_count == 1

    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    async def test_retrying_timeout_errors_doesnt_leak(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        respx2_mock.post("/chat/completions").mock(side_effect=httpx2.TimeoutException("Test timeout error"))

        with pytest.raises(APITimeoutError):
            await async_client.chat.completions.with_streaming_response.create(
                messages=[
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                model="gpt-5.4",
            ).__aenter__()

        assert _get_open_connections(async_client) == 0

    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    async def test_retrying_status_errors_doesnt_leak(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        respx2_mock.post("/chat/completions").mock(return_value=httpx2.Response(500))

        with pytest.raises(APIStatusError):
            await async_client.chat.completions.with_streaming_response.create(
                messages=[
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                model="gpt-5.4",
            ).__aenter__()
        assert _get_open_connections(async_client) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    @pytest.mark.parametrize("failure_mode", ["status", "exception"])
    @pytest.mark.parametrize("max_retries", [4, 10**100])
    async def test_retries_taken(
        self,
        async_client: AsyncSEG,
        failures_before_success: int,
        max_retries: int,
        failure_mode: Literal["status", "exception"],
        respx2_mock: MockRouter,
    ) -> None:
        client = async_client.with_options(max_retries=max_retries)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                if failure_mode == "exception":
                    raise httpx2.ConnectError("oops")
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        response = await client.chat.completions.with_raw_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
        )

        assert response.retries_taken == failures_before_success
        assert int(response.http_request.headers["x-stainless-retry-count"]) == failures_before_success

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    async def test_omit_retry_count_header(
        self, async_client: AsyncSEG, failures_before_success: int, respx2_mock: MockRouter
    ) -> None:
        client = async_client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        response = await client.chat.completions.with_raw_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
            extra_headers={"x-stainless-retry-count": Omit()},
        )

        assert len(response.http_request.headers.get_list("x-stainless-retry-count")) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    async def test_overwrite_retry_count_header(
        self, async_client: AsyncSEG, failures_before_success: int, respx2_mock: MockRouter
    ) -> None:
        client = async_client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        response = await client.chat.completions.with_raw_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
            extra_headers={"x-stainless-retry-count": "42"},
        )

        assert response.http_request.headers.get("x-stainless-retry-count") == "42"

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("seg._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx2(base_url=base_url)
    async def test_retries_taken_new_response_class(
        self, async_client: AsyncSEG, failures_before_success: int, respx2_mock: MockRouter
    ) -> None:
        client = async_client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx2.Request) -> httpx2.Response:
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx2.Response(500)
            return httpx2.Response(200)

        respx2_mock.post("/chat/completions").mock(side_effect=retry_handler)

        async with client.chat.completions.with_streaming_response.create(
            messages=[
                {
                    "content": "string",
                    "role": "developer",
                }
            ],
            model="gpt-5.4",
        ) as response:
            assert response.retries_taken == failures_before_success
            assert int(response.http_request.headers["x-stainless-retry-count"]) == failures_before_success

    async def test_get_platform(self) -> None:
        platform = await asyncify(get_platform)()
        assert isinstance(platform, (str, OtherPlatform))

    @pytest.mark.skipif(
        sys.platform == "win32", reason="httpx2 does not derive proxy mounts from HTTPS_PROXY on Windows"
    )
    async def test_proxy_environment_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Test that the proxy environment variables are set correctly
        monkeypatch.setenv("HTTPS_PROXY", "https://example.org")
        # Delete in case our environment has any proxy env vars set
        monkeypatch.delenv("HTTP_PROXY", raising=False)
        monkeypatch.delenv("ALL_PROXY", raising=False)
        monkeypatch.delenv("NO_PROXY", raising=False)
        monkeypatch.delenv("http_proxy", raising=False)
        monkeypatch.delenv("https_proxy", raising=False)
        monkeypatch.delenv("all_proxy", raising=False)
        monkeypatch.delenv("no_proxy", raising=False)

        client = DefaultAsyncHttpxClient()

        mounts = tuple(client._mounts.items())
        assert len(mounts) == 1
        assert mounts[0][0].pattern == "https://"

    @pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
    async def test_default_client_creation(self) -> None:
        # Ensure that the client can be initialized without any exceptions
        DefaultAsyncHttpxClient(
            verify=True,
            cert=None,
            trust_env=True,
            http1=True,
            http2=False,
            limits=httpx2.Limits(max_connections=100, max_keepalive_connections=20),
        )

    @pytest.mark.respx2(base_url=base_url)
    async def test_follow_redirects(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        # Test that the default follow_redirects=True allows following redirects
        respx2_mock.post("/redirect").mock(
            return_value=httpx2.Response(302, headers={"Location": f"{base_url}/redirected"})
        )
        respx2_mock.get("/redirected").mock(return_value=httpx2.Response(200, json={"status": "ok"}))

        response = await async_client.post("/redirect", body={"key": "value"}, cast_to=httpx2.Response)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.respx2(base_url=base_url)
    async def test_follow_redirects_disabled(self, respx2_mock: MockRouter, async_client: AsyncSEG) -> None:
        # Test that follow_redirects=False prevents following redirects
        respx2_mock.post("/redirect").mock(
            return_value=httpx2.Response(302, headers={"Location": f"{base_url}/redirected"})
        )

        with pytest.raises(APIStatusError) as exc_info:
            await async_client.post(
                "/redirect", body={"key": "value"}, options={"follow_redirects": False}, cast_to=httpx2.Response
            )

        assert exc_info.value.response.status_code == 302
        assert exc_info.value.response.headers["Location"] == f"{base_url}/redirected"

    async def test_api_key_before_after_refresh_str(self) -> None:
        client = AsyncSEG(base_url=base_url, api_key="test_api_key")

        assert client.auth_headers.get("Authorization") == "Bearer test_api_key"
        await client._refresh_api_key()

        assert client.auth_headers.get("Authorization") == "Bearer test_api_key"
