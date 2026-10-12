from __future__ import annotations

from typing import Union, Iterable
from functools import partial
from typing_extensions import Literal

import httpx2

from .. import _legacy_response
from ..types import embedding_create_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import is_given, maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_streamed_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options
from ..types.embedding_model import EmbeddingModel
from ..lib._parsing._embeddings import parse_embedding_response as _parse_embedding_response
from ..types.create_embedding_response import CreateEmbeddingResponse

__all__ = ["Embeddings", "AsyncEmbeddings"]


class Embeddings(SyncAPIResource):
    """
    Get a vector representation of a given input that can be easily consumed by machine learning models and algorithms.
    """

    @cached_property
    def with_raw_response(self) -> EmbeddingsWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return EmbeddingsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EmbeddingsWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return EmbeddingsWithStreamingResponse(self)

    def create(
        self,
        *,
        input: Union[str, SequenceNotStr[str], Iterable[int], Iterable[Iterable[int]]],
        model: Union[str, EmbeddingModel],
        dimensions: int | Omit = omit,
        encoding_format: Literal["float", "base64"] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> CreateEmbeddingResponse:
        """
        Creates an embedding vector representing the input text.

        Args:
          input: Input text to embed, as a string or an array of strings. Token arrays are
              accepted for providers that support them. The input cannot be an empty string
              and must fit the model's `context_window` (see `client.models.retrieve`).

          model: ID of an embedding model from the SovereignEG catalog, e.g.
              `embeddinggemma-300m`. List the catalog with `client.models.list()` and pick an
              entry whose `modality` is `"embed"`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

          dimensions: The number of dimensions the resulting output embeddings should have. Only
              honoured by models that support truncated embeddings.

          encoding_format: The format to return the embeddings in. Can be either `float` or
              `base64`. When omitted, the SDK requests `base64` and decodes it to floats for you.
              Clients created with `_strict_response_validation=True` always decode `base64`
              to floats, even when you ask for it explicitly.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.
              [Learn more](https://sovereigneg.com/dashboard/docs).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        params = {
            "model": model,
            "input": input,
            "user": user,
            "dimensions": dimensions,
            "encoding_format": encoding_format,
        }
        if not is_given(encoding_format):
            # Ask for base64: it is smaller on the wire and faster to parse than JSON floats.
            # `Embedding` decodes it during validation and `parse_embedding_response` decodes
            # it for constructed (non-strict) responses, so callers always get floats.
            params["encoding_format"] = "base64"

        return self._post(
            "/embeddings",
            body=maybe_transform(params, embedding_create_params.EmbeddingCreateParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                post_parser=partial(_parse_embedding_response, encoding_format=encoding_format),
                security={"bearer_auth": True},
            ),
            cast_to=CreateEmbeddingResponse,
        )


class AsyncEmbeddings(AsyncAPIResource):
    """
    Get a vector representation of a given input that can be easily consumed by machine learning models and algorithms.
    """

    @cached_property
    def with_raw_response(self) -> AsyncEmbeddingsWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return AsyncEmbeddingsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEmbeddingsWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return AsyncEmbeddingsWithStreamingResponse(self)

    async def create(
        self,
        *,
        input: Union[str, SequenceNotStr[str], Iterable[int], Iterable[Iterable[int]]],
        model: Union[str, EmbeddingModel],
        dimensions: int | Omit = omit,
        encoding_format: Literal["float", "base64"] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> CreateEmbeddingResponse:
        """
        Creates an embedding vector representing the input text.

        Args:
          input: Input text to embed, as a string or an array of strings. Token arrays are
              accepted for providers that support them. The input cannot be an empty string
              and must fit the model's `context_window` (see `client.models.retrieve`).

          model: ID of an embedding model from the SovereignEG catalog, e.g.
              `embeddinggemma-300m`. List the catalog with `client.models.list()` and pick an
              entry whose `modality` is `"embed"`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

          dimensions: The number of dimensions the resulting output embeddings should have. Only
              honoured by models that support truncated embeddings.

          encoding_format: The format to return the embeddings in. Can be either `float` or
              `base64`. When omitted, the SDK requests `base64` and decodes it to floats for you.
              Clients created with `_strict_response_validation=True` always decode `base64`
              to floats, even when you ask for it explicitly.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.
              [Learn more](https://sovereigneg.com/dashboard/docs).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        params = {
            "model": model,
            "input": input,
            "user": user,
            "dimensions": dimensions,
            "encoding_format": encoding_format,
        }
        if not is_given(encoding_format):
            # Ask for base64: it is smaller on the wire and faster to parse than JSON floats.
            # `Embedding` decodes it during validation and `parse_embedding_response` decodes
            # it for constructed (non-strict) responses, so callers always get floats.
            params["encoding_format"] = "base64"

        return await self._post(
            "/embeddings",
            body=maybe_transform(params, embedding_create_params.EmbeddingCreateParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                post_parser=partial(_parse_embedding_response, encoding_format=encoding_format),
                security={"bearer_auth": True},
            ),
            cast_to=CreateEmbeddingResponse,
        )


class EmbeddingsWithRawResponse:
    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings

        self.create = _legacy_response.to_raw_response_wrapper(
            embeddings.create,
        )


class AsyncEmbeddingsWithRawResponse:
    def __init__(self, embeddings: AsyncEmbeddings) -> None:
        self._embeddings = embeddings

        self.create = _legacy_response.async_to_raw_response_wrapper(
            embeddings.create,
        )


class EmbeddingsWithStreamingResponse:
    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings

        self.create = to_streamed_response_wrapper(
            embeddings.create,
        )


class AsyncEmbeddingsWithStreamingResponse:
    def __init__(self, embeddings: AsyncEmbeddings) -> None:
        self._embeddings = embeddings

        self.create = async_to_streamed_response_wrapper(
            embeddings.create,
        )
