from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Literal, overload

import httpx2

from .. import _legacy_response
from ..types import image_generate_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import required_args, maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_streamed_response_wrapper, async_to_streamed_response_wrapper
from .._streaming import Stream, AsyncStream
from .._base_client import make_request_options
from ..types.image_model import ImageModel
from ..types.images_response import ImagesResponse
from ..types.image_gen_stream_event import ImageGenStreamEvent

__all__ = ["Images", "AsyncImages"]


class Images(SyncAPIResource):
    """Given a prompt and/or an input image, the model will generate a new image."""

    @cached_property
    def with_raw_response(self) -> ImagesWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return ImagesWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ImagesWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return ImagesWithStreamingResponse(self)

    @overload
    def generate(
        self,
        *,
        prompt: str,
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        stream: Optional[Literal[False]] | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ImagesResponse:
        """
        Creates one or more images from a text prompt using an image model from the
        SovereignEG catalog, e.g. `flux-1-schnell`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          prompt: A text description of the desired image(s).

          model: ID of an image model from the SovereignEG catalog. List the catalog with
              `client.models.list()` and pick an entry whose `modality` is `"image"`; its
              `image_options` describe the accepted `size` format and modes.

          background: Background transparency, when the provider supports it: `transparent`,
              `opaque`, or `auto` (default).

          moderation: Provider content-moderation level: `low` or `auto` (default).

          n: The number of images to generate. Must be between 1 and 10.

          output_compression: Compression level (0-100%) for `webp` or `jpeg` output, when the
              provider supports it.

          output_format: Format of the returned images: `png`, `jpeg`, or `webp`. The gateway
              echoes the format actually used in `ImagesResponse.output_format`.

          partial_images: Number of partial images (0-3) to emit when streaming, for providers
              that support progressive previews.

          quality: Requested quality such as `auto`, `low`, `medium`, or `high`. Accepted values
              depend on the provider; the gateway echoes the value used.

          response_format: `url` or `b64_json`. Most providers return base64 (`b64_json`).

          size: Image dimensions as a `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect
              ratio such as `1:1` for providers that use one. See the model's `image_options`.

          stream: Generate the image in streaming mode and return stream events instead of the
              final response. Defaults to `false`.

          style: Legacy style hint; most providers ignore it, so describe the style in the
              prompt instead.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def generate(
        self,
        *,
        prompt: str,
        stream: Literal[True],
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> Stream[ImageGenStreamEvent]:
        """
        Creates one or more images from a text prompt using an image model from the
        SovereignEG catalog, e.g. `flux-1-schnell`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          prompt: A text description of the desired image(s).

          model: ID of an image model from the SovereignEG catalog. List the catalog with
              `client.models.list()` and pick an entry whose `modality` is `"image"`; its
              `image_options` describe the accepted `size` format and modes.

          background: Background transparency, when the provider supports it: `transparent`,
              `opaque`, or `auto` (default).

          moderation: Provider content-moderation level: `low` or `auto` (default).

          n: The number of images to generate. Must be between 1 and 10.

          output_compression: Compression level (0-100%) for `webp` or `jpeg` output, when the
              provider supports it.

          output_format: Format of the returned images: `png`, `jpeg`, or `webp`. The gateway
              echoes the format actually used in `ImagesResponse.output_format`.

          partial_images: Number of partial images (0-3) to emit when streaming, for providers
              that support progressive previews.

          quality: Requested quality such as `auto`, `low`, `medium`, or `high`. Accepted values
              depend on the provider; the gateway echoes the value used.

          response_format: `url` or `b64_json`. Most providers return base64 (`b64_json`).

          size: Image dimensions as a `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect
              ratio such as `1:1` for providers that use one. See the model's `image_options`.

          stream: Generate the image in streaming mode and return stream events instead of the
              final response. Defaults to `false`.

          style: Legacy style hint; most providers ignore it, so describe the style in the
              prompt instead.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def generate(
        self,
        *,
        prompt: str,
        stream: bool,
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ImagesResponse | Stream[ImageGenStreamEvent]:
        """
        Creates one or more images from a text prompt using an image model from the
        SovereignEG catalog, e.g. `flux-1-schnell`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          prompt: A text description of the desired image(s).

          model: ID of an image model from the SovereignEG catalog. List the catalog with
              `client.models.list()` and pick an entry whose `modality` is `"image"`; its
              `image_options` describe the accepted `size` format and modes.

          background: Background transparency, when the provider supports it: `transparent`,
              `opaque`, or `auto` (default).

          moderation: Provider content-moderation level: `low` or `auto` (default).

          n: The number of images to generate. Must be between 1 and 10.

          output_compression: Compression level (0-100%) for `webp` or `jpeg` output, when the
              provider supports it.

          output_format: Format of the returned images: `png`, `jpeg`, or `webp`. The gateway
              echoes the format actually used in `ImagesResponse.output_format`.

          partial_images: Number of partial images (0-3) to emit when streaming, for providers
              that support progressive previews.

          quality: Requested quality such as `auto`, `low`, `medium`, or `high`. Accepted values
              depend on the provider; the gateway echoes the value used.

          response_format: `url` or `b64_json`. Most providers return base64 (`b64_json`).

          size: Image dimensions as a `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect
              ratio such as `1:1` for providers that use one. See the model's `image_options`.

          stream: Generate the image in streaming mode and return stream events instead of the
              final response. Defaults to `false`.

          style: Legacy style hint; most providers ignore it, so describe the style in the
              prompt instead.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["prompt"], ["prompt", "stream"])
    def generate(
        self,
        *,
        prompt: str,
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        stream: Optional[Literal[False]] | Literal[True] | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ImagesResponse | Stream[ImageGenStreamEvent]:
        return self._post(
            "/images/generations",
            body=maybe_transform(
                {
                    "model": model,
                    "stream": stream,
                    "prompt": prompt,
                    "background": background,
                    "moderation": moderation,
                    "n": n,
                    "output_compression": output_compression,
                    "output_format": output_format,
                    "partial_images": partial_images,
                    "quality": quality,
                    "response_format": response_format,
                    "size": size,
                    "style": style,
                    "user": user,
                },
                image_generate_params.ImageGenerateParamsStreaming
                if stream
                else image_generate_params.ImageGenerateParamsNonStreaming,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                security={"bearer_auth": True},
            ),
            cast_to=ImagesResponse,
            stream=stream or False,
            stream_cls=Stream[ImageGenStreamEvent],
        )


class AsyncImages(AsyncAPIResource):
    """Given a prompt and/or an input image, the model will generate a new image."""

    @cached_property
    def with_raw_response(self) -> AsyncImagesWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return AsyncImagesWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncImagesWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return AsyncImagesWithStreamingResponse(self)

    @overload
    async def generate(
        self,
        *,
        prompt: str,
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        stream: Optional[Literal[False]] | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ImagesResponse:
        """
        Creates one or more images from a text prompt using an image model from the
        SovereignEG catalog, e.g. `flux-1-schnell`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          prompt: A text description of the desired image(s).

          model: ID of an image model from the SovereignEG catalog. List the catalog with
              `client.models.list()` and pick an entry whose `modality` is `"image"`; its
              `image_options` describe the accepted `size` format and modes.

          background: Background transparency, when the provider supports it: `transparent`,
              `opaque`, or `auto` (default).

          moderation: Provider content-moderation level: `low` or `auto` (default).

          n: The number of images to generate. Must be between 1 and 10.

          output_compression: Compression level (0-100%) for `webp` or `jpeg` output, when the
              provider supports it.

          output_format: Format of the returned images: `png`, `jpeg`, or `webp`. The gateway
              echoes the format actually used in `ImagesResponse.output_format`.

          partial_images: Number of partial images (0-3) to emit when streaming, for providers
              that support progressive previews.

          quality: Requested quality such as `auto`, `low`, `medium`, or `high`. Accepted values
              depend on the provider; the gateway echoes the value used.

          response_format: `url` or `b64_json`. Most providers return base64 (`b64_json`).

          size: Image dimensions as a `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect
              ratio such as `1:1` for providers that use one. See the model's `image_options`.

          stream: Generate the image in streaming mode and return stream events instead of the
              final response. Defaults to `false`.

          style: Legacy style hint; most providers ignore it, so describe the style in the
              prompt instead.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def generate(
        self,
        *,
        prompt: str,
        stream: Literal[True],
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> AsyncStream[ImageGenStreamEvent]:
        """
        Creates one or more images from a text prompt using an image model from the
        SovereignEG catalog, e.g. `flux-1-schnell`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          prompt: A text description of the desired image(s).

          model: ID of an image model from the SovereignEG catalog. List the catalog with
              `client.models.list()` and pick an entry whose `modality` is `"image"`; its
              `image_options` describe the accepted `size` format and modes.

          background: Background transparency, when the provider supports it: `transparent`,
              `opaque`, or `auto` (default).

          moderation: Provider content-moderation level: `low` or `auto` (default).

          n: The number of images to generate. Must be between 1 and 10.

          output_compression: Compression level (0-100%) for `webp` or `jpeg` output, when the
              provider supports it.

          output_format: Format of the returned images: `png`, `jpeg`, or `webp`. The gateway
              echoes the format actually used in `ImagesResponse.output_format`.

          partial_images: Number of partial images (0-3) to emit when streaming, for providers
              that support progressive previews.

          quality: Requested quality such as `auto`, `low`, `medium`, or `high`. Accepted values
              depend on the provider; the gateway echoes the value used.

          response_format: `url` or `b64_json`. Most providers return base64 (`b64_json`).

          size: Image dimensions as a `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect
              ratio such as `1:1` for providers that use one. See the model's `image_options`.

          stream: Generate the image in streaming mode and return stream events instead of the
              final response. Defaults to `false`.

          style: Legacy style hint; most providers ignore it, so describe the style in the
              prompt instead.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def generate(
        self,
        *,
        prompt: str,
        stream: bool,
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ImagesResponse | AsyncStream[ImageGenStreamEvent]:
        """
        Creates one or more images from a text prompt using an image model from the
        SovereignEG catalog, e.g. `flux-1-schnell`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          prompt: A text description of the desired image(s).

          model: ID of an image model from the SovereignEG catalog. List the catalog with
              `client.models.list()` and pick an entry whose `modality` is `"image"`; its
              `image_options` describe the accepted `size` format and modes.

          background: Background transparency, when the provider supports it: `transparent`,
              `opaque`, or `auto` (default).

          moderation: Provider content-moderation level: `low` or `auto` (default).

          n: The number of images to generate. Must be between 1 and 10.

          output_compression: Compression level (0-100%) for `webp` or `jpeg` output, when the
              provider supports it.

          output_format: Format of the returned images: `png`, `jpeg`, or `webp`. The gateway
              echoes the format actually used in `ImagesResponse.output_format`.

          partial_images: Number of partial images (0-3) to emit when streaming, for providers
              that support progressive previews.

          quality: Requested quality such as `auto`, `low`, `medium`, or `high`. Accepted values
              depend on the provider; the gateway echoes the value used.

          response_format: `url` or `b64_json`. Most providers return base64 (`b64_json`).

          size: Image dimensions as a `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect
              ratio such as `1:1` for providers that use one. See the model's `image_options`.

          stream: Generate the image in streaming mode and return stream events instead of the
              final response. Defaults to `false`.

          style: Legacy style hint; most providers ignore it, so describe the style in the
              prompt instead.

          user: A unique identifier representing your end-user, which can help SEG to monitor
              and detect abuse.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["prompt"], ["prompt", "stream"])
    async def generate(
        self,
        *,
        prompt: str,
        background: Optional[Literal["transparent", "opaque", "auto"]] | Omit = omit,
        model: Union[str, ImageModel, None] | Omit = omit,
        moderation: Optional[Literal["low", "auto"]] | Omit = omit,
        n: Optional[int] | Omit = omit,
        output_compression: Optional[int] | Omit = omit,
        output_format: Optional[Literal["png", "jpeg", "webp"]] | Omit = omit,
        partial_images: Optional[int] | Omit = omit,
        quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]] | Omit = omit,
        response_format: Optional[Literal["url", "b64_json"]] | Omit = omit,
        size: Union[
            str,
            Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
            None,
        ]
        | Omit = omit,
        stream: Optional[Literal[False]] | Literal[True] | Omit = omit,
        style: Optional[Literal["vivid", "natural"]] | Omit = omit,
        user: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ImagesResponse | AsyncStream[ImageGenStreamEvent]:
        return await self._post(
            "/images/generations",
            body=await async_maybe_transform(
                {
                    "model": model,
                    "stream": stream,
                    "prompt": prompt,
                    "background": background,
                    "moderation": moderation,
                    "n": n,
                    "output_compression": output_compression,
                    "output_format": output_format,
                    "partial_images": partial_images,
                    "quality": quality,
                    "response_format": response_format,
                    "size": size,
                    "style": style,
                    "user": user,
                },
                image_generate_params.ImageGenerateParamsStreaming
                if stream
                else image_generate_params.ImageGenerateParamsNonStreaming,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                security={"bearer_auth": True},
            ),
            cast_to=ImagesResponse,
            stream=stream or False,
            stream_cls=AsyncStream[ImageGenStreamEvent],
        )


class ImagesWithRawResponse:
    def __init__(self, images: Images) -> None:
        self._images = images

        self.generate = _legacy_response.to_raw_response_wrapper(
            images.generate,
        )


class AsyncImagesWithRawResponse:
    def __init__(self, images: AsyncImages) -> None:
        self._images = images

        self.generate = _legacy_response.async_to_raw_response_wrapper(
            images.generate,
        )


class ImagesWithStreamingResponse:
    def __init__(self, images: Images) -> None:
        self._images = images

        self.generate = to_streamed_response_wrapper(
            images.generate,
        )


class AsyncImagesWithStreamingResponse:
    def __init__(self, images: AsyncImages) -> None:
        self._images = images

        self.generate = async_to_streamed_response_wrapper(
            images.generate,
        )
