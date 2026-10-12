from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping, Callable
from typing_extensions import Self, override

import httpx2

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, is_mapping, get_async_library
from ._compat import cached_property
from ._httpx2 import normalize_httpx_url
from ._models import SecurityOptions, FinalRequestOptions
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import SEGError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import (
        chat,
        images,
        models,
        decisions,
        embeddings,
        moderations,
    )
    from .resources.images import Images, AsyncImages
    from .resources.models import Models, AsyncModels
    from .resources.chat.chat import Chat, AsyncChat
    from .resources.decisions import Decisions, AsyncDecisions
    from .resources.embeddings import Embeddings, AsyncEmbeddings
    from .resources.moderations import Moderations, AsyncModerations

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "SEG",
    "AsyncSEG",
    "Client",
    "AsyncClient",
    "DEFAULT_BASE_URL",
]

DEFAULT_BASE_URL = "https://sovereigneg.com/v1"
"""The SovereignEG API. Override with `base_url=` or the `SEG_BASE_URL` environment variable."""


def _has_header(headers: Headers, header: str) -> bool:
    header = header.lower()
    return any(key.lower() == header for key in headers)


def _has_omitted_header(headers: Headers, header: str) -> bool:
    header = header.lower()
    return any(key.lower() == header and isinstance(value, Omit) for key, value in headers.items())


def _resolve_base_url(base_url: str | httpx2.URL | None | NotGiven) -> str | httpx2.URL:
    if is_given(base_url) and base_url is not None:
        return base_url
    return os.environ.get("SEG_BASE_URL") or DEFAULT_BASE_URL


class SEG(SyncAPIClient):
    # client options
    api_key: str
    _api_key_provider: Callable[[], str] | None

    @property
    @override
    def base_url(self) -> httpx2.URL:
        return self._base_url

    @base_url.setter
    def base_url(self, url: httpx2.URL | str) -> None:
        self._base_url = self._enforce_trailing_slash(normalize_httpx_url(url))

    def __init__(
        self,
        *,
        api_key: str | Callable[[], str] | None = None,
        base_url: str | httpx2.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx2 client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx2 documentation](https://httpx2.pydantic.dev/api/#client) for more details.
        http_client: httpx2.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
        _enforce_credentials: bool = True,
    ) -> None:
        """Construct a new synchronous SEG client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `SEG_API_KEY`
        - `base_url` from `SEG_BASE_URL` (defaults to `https://sovereigneg.com/v1`)

        `api_key` may also be a callable returning the key, which is invoked before each request.
        """
        if api_key is None:
            api_key = os.environ.get("SEG_API_KEY")
        if callable(api_key):
            self.api_key = ""
            self._api_key_provider = api_key
        else:
            self.api_key = api_key or ""
            self._api_key_provider = None

        if _enforce_credentials and not self.api_key and self._api_key_provider is None:
            raise SEGError(
                "Missing credentials. Please pass an `api_key` or set the `SEG_API_KEY` environment variable."
            )

        super().__init__(
            version=__version__,
            base_url=_resolve_base_url(base_url),
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self._default_stream_cls = Stream

    @cached_property
    def chat(self) -> Chat:
        from .resources.chat import Chat

        return Chat(self)

    @cached_property
    def embeddings(self) -> Embeddings:
        from .resources.embeddings import Embeddings

        return Embeddings(self)

    @cached_property
    def images(self) -> Images:
        from .resources.images import Images

        return Images(self)

    @cached_property
    def moderations(self) -> Moderations:
        from .resources.moderations import Moderations

        return Moderations(self)

    @cached_property
    def models(self) -> Models:
        from .resources.models import Models

        return Models(self)

    @cached_property
    def decisions(self) -> Decisions:
        from .resources.decisions import Decisions

        return Decisions(self)

    @cached_property
    def with_raw_response(self) -> SEGWithRawResponse:
        return SEGWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SEGWithStreamedResponse:
        return SEGWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="brackets")

    @override
    def _auth_headers(self, security: SecurityOptions) -> dict[str, str]:
        if security.get("bearer_auth", False):
            return self.auth_headers
        return {}

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if not api_key:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if _has_header(headers, "Authorization") or _has_omitted_header(custom_headers, "Authorization"):
            return

        raise TypeError(
            "Could not resolve authentication method. Expected the api_key to be set. Or for the `Authorization` header to be explicitly omitted."
        )

    @override
    def _prepare_options(self, options: FinalRequestOptions) -> FinalRequestOptions:
        if self._api_key_provider is not None and options.security.get("bearer_auth", False):
            self._refresh_api_key()

        return super()._prepare_options(options)

    def _refresh_api_key(self) -> str:
        if self._api_key_provider is not None:
            self.api_key = self._api_key_provider()

        return self.api_key

    def copy(
        self,
        *,
        api_key: str | Callable[[], str] | None = None,
        base_url: str | httpx2.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx2.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _enforce_credentials: bool | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self._api_key_provider or self.api_key,
            base_url=base_url if is_given(base_url) and base_url is not None else self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            _enforce_credentials=True if _enforce_credentials is None else _enforce_credentials,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx2.Response,
    ) -> APIStatusError:
        data = body.get("error", body) if is_mapping(body) else body
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=data)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=data)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=data)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=data)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=data)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=data)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=data)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=data)
        return APIStatusError(err_msg, response=response, body=data)


class AsyncSEG(AsyncAPIClient):
    # client options
    api_key: str
    _api_key_provider: Callable[[], str] | None

    @property
    @override
    def base_url(self) -> httpx2.URL:
        return self._base_url

    @base_url.setter
    def base_url(self, url: httpx2.URL | str) -> None:
        self._base_url = self._enforce_trailing_slash(normalize_httpx_url(url))

    def __init__(
        self,
        *,
        api_key: str | Callable[[], str] | None = None,
        base_url: str | httpx2.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx2 client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx2 documentation](https://httpx2.pydantic.dev/api/#asyncclient) for more details.
        http_client: httpx2.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
        _enforce_credentials: bool = True,
    ) -> None:
        """Construct a new async AsyncSEG client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `SEG_API_KEY`
        - `base_url` from `SEG_BASE_URL` (defaults to `https://sovereigneg.com/v1`)

        `api_key` may also be a callable returning the key, which is invoked before each request.
        """
        if api_key is None:
            api_key = os.environ.get("SEG_API_KEY")
        if callable(api_key):
            self.api_key = ""
            self._api_key_provider = api_key
        else:
            self.api_key = api_key or ""
            self._api_key_provider = None

        if _enforce_credentials and not self.api_key and self._api_key_provider is None:
            raise SEGError(
                "Missing credentials. Please pass an `api_key` or set the `SEG_API_KEY` environment variable."
            )

        super().__init__(
            version=__version__,
            base_url=_resolve_base_url(base_url),
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self._default_stream_cls = AsyncStream

    @cached_property
    def chat(self) -> AsyncChat:
        from .resources.chat import AsyncChat

        return AsyncChat(self)

    @cached_property
    def embeddings(self) -> AsyncEmbeddings:
        from .resources.embeddings import AsyncEmbeddings

        return AsyncEmbeddings(self)

    @cached_property
    def images(self) -> AsyncImages:
        from .resources.images import AsyncImages

        return AsyncImages(self)

    @cached_property
    def moderations(self) -> AsyncModerations:
        from .resources.moderations import AsyncModerations

        return AsyncModerations(self)

    @cached_property
    def models(self) -> AsyncModels:
        from .resources.models import AsyncModels

        return AsyncModels(self)

    @cached_property
    def decisions(self) -> AsyncDecisions:
        from .resources.decisions import AsyncDecisions

        return AsyncDecisions(self)

    @cached_property
    def with_raw_response(self) -> AsyncSEGWithRawResponse:
        return AsyncSEGWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSEGWithStreamedResponse:
        return AsyncSEGWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="brackets")

    @override
    def _auth_headers(self, security: SecurityOptions) -> dict[str, str]:
        if security.get("bearer_auth", False):
            return self.auth_headers
        return {}

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if not api_key:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if _has_header(headers, "Authorization") or _has_omitted_header(custom_headers, "Authorization"):
            return

        raise TypeError(
            "Could not resolve authentication method. Expected the api_key to be set. Or for the `Authorization` header to be explicitly omitted."
        )

    @override
    async def _prepare_options(self, options: FinalRequestOptions) -> FinalRequestOptions:
        if self._api_key_provider is not None and options.security.get("bearer_auth", False):
            await self._refresh_api_key()

        return await super()._prepare_options(options)

    async def _refresh_api_key(self) -> str:
        if self._api_key_provider is not None:
            self.api_key = self._api_key_provider()

        return self.api_key

    def copy(
        self,
        *,
        api_key: str | Callable[[], str] | None = None,
        base_url: str | httpx2.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx2.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _enforce_credentials: bool | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self._api_key_provider or self.api_key,
            base_url=base_url if is_given(base_url) and base_url is not None else self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            _enforce_credentials=True if _enforce_credentials is None else _enforce_credentials,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx2.Response,
    ) -> APIStatusError:
        data = body.get("error", body) if is_mapping(body) else body
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=data)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=data)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=data)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=data)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=data)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=data)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=data)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=data)
        return APIStatusError(err_msg, response=response, body=data)


class SEGWithRawResponse:
    _client: SEG

    def __init__(self, client: SEG) -> None:
        self._client = client

    @cached_property
    def chat(self) -> chat.ChatWithRawResponse:
        from .resources.chat import ChatWithRawResponse

        return ChatWithRawResponse(self._client.chat)

    @cached_property
    def embeddings(self) -> embeddings.EmbeddingsWithRawResponse:
        from .resources.embeddings import EmbeddingsWithRawResponse

        return EmbeddingsWithRawResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.ImagesWithRawResponse:
        from .resources.images import ImagesWithRawResponse

        return ImagesWithRawResponse(self._client.images)

    @cached_property
    def moderations(self) -> moderations.ModerationsWithRawResponse:
        from .resources.moderations import ModerationsWithRawResponse

        return ModerationsWithRawResponse(self._client.moderations)

    @cached_property
    def models(self) -> models.ModelsWithRawResponse:
        from .resources.models import ModelsWithRawResponse

        return ModelsWithRawResponse(self._client.models)

    @cached_property
    def decisions(self) -> decisions.DecisionsWithRawResponse:
        from .resources.decisions import DecisionsWithRawResponse

        return DecisionsWithRawResponse(self._client.decisions)


class AsyncSEGWithRawResponse:
    _client: AsyncSEG

    def __init__(self, client: AsyncSEG) -> None:
        self._client = client

    @cached_property
    def chat(self) -> chat.AsyncChatWithRawResponse:
        from .resources.chat import AsyncChatWithRawResponse

        return AsyncChatWithRawResponse(self._client.chat)

    @cached_property
    def embeddings(self) -> embeddings.AsyncEmbeddingsWithRawResponse:
        from .resources.embeddings import AsyncEmbeddingsWithRawResponse

        return AsyncEmbeddingsWithRawResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.AsyncImagesWithRawResponse:
        from .resources.images import AsyncImagesWithRawResponse

        return AsyncImagesWithRawResponse(self._client.images)

    @cached_property
    def moderations(self) -> moderations.AsyncModerationsWithRawResponse:
        from .resources.moderations import AsyncModerationsWithRawResponse

        return AsyncModerationsWithRawResponse(self._client.moderations)

    @cached_property
    def models(self) -> models.AsyncModelsWithRawResponse:
        from .resources.models import AsyncModelsWithRawResponse

        return AsyncModelsWithRawResponse(self._client.models)

    @cached_property
    def decisions(self) -> decisions.AsyncDecisionsWithRawResponse:
        from .resources.decisions import AsyncDecisionsWithRawResponse

        return AsyncDecisionsWithRawResponse(self._client.decisions)


class SEGWithStreamedResponse:
    _client: SEG

    def __init__(self, client: SEG) -> None:
        self._client = client

    @cached_property
    def chat(self) -> chat.ChatWithStreamingResponse:
        from .resources.chat import ChatWithStreamingResponse

        return ChatWithStreamingResponse(self._client.chat)

    @cached_property
    def embeddings(self) -> embeddings.EmbeddingsWithStreamingResponse:
        from .resources.embeddings import EmbeddingsWithStreamingResponse

        return EmbeddingsWithStreamingResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.ImagesWithStreamingResponse:
        from .resources.images import ImagesWithStreamingResponse

        return ImagesWithStreamingResponse(self._client.images)

    @cached_property
    def moderations(self) -> moderations.ModerationsWithStreamingResponse:
        from .resources.moderations import ModerationsWithStreamingResponse

        return ModerationsWithStreamingResponse(self._client.moderations)

    @cached_property
    def models(self) -> models.ModelsWithStreamingResponse:
        from .resources.models import ModelsWithStreamingResponse

        return ModelsWithStreamingResponse(self._client.models)

    @cached_property
    def decisions(self) -> decisions.DecisionsWithStreamingResponse:
        from .resources.decisions import DecisionsWithStreamingResponse

        return DecisionsWithStreamingResponse(self._client.decisions)


class AsyncSEGWithStreamedResponse:
    _client: AsyncSEG

    def __init__(self, client: AsyncSEG) -> None:
        self._client = client

    @cached_property
    def chat(self) -> chat.AsyncChatWithStreamingResponse:
        from .resources.chat import AsyncChatWithStreamingResponse

        return AsyncChatWithStreamingResponse(self._client.chat)

    @cached_property
    def embeddings(self) -> embeddings.AsyncEmbeddingsWithStreamingResponse:
        from .resources.embeddings import AsyncEmbeddingsWithStreamingResponse

        return AsyncEmbeddingsWithStreamingResponse(self._client.embeddings)

    @cached_property
    def images(self) -> images.AsyncImagesWithStreamingResponse:
        from .resources.images import AsyncImagesWithStreamingResponse

        return AsyncImagesWithStreamingResponse(self._client.images)

    @cached_property
    def moderations(self) -> moderations.AsyncModerationsWithStreamingResponse:
        from .resources.moderations import AsyncModerationsWithStreamingResponse

        return AsyncModerationsWithStreamingResponse(self._client.moderations)

    @cached_property
    def models(self) -> models.AsyncModelsWithStreamingResponse:
        from .resources.models import AsyncModelsWithStreamingResponse

        return AsyncModelsWithStreamingResponse(self._client.models)

    @cached_property
    def decisions(self) -> decisions.AsyncDecisionsWithStreamingResponse:
        from .resources.decisions import AsyncDecisionsWithStreamingResponse

        return AsyncDecisionsWithStreamingResponse(self._client.decisions)


Client = SEG

AsyncClient = AsyncSEG
