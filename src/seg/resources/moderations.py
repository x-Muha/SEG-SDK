from __future__ import annotations

from typing import Union, Iterable

import httpx2

from .. import _legacy_response
from ..types import moderation_create_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import to_streamed_response_wrapper, async_to_streamed_response_wrapper
from .._base_client import make_request_options
from ..types.moderation_model import ModerationModel
from ..types.moderation_create_response import ModerationCreateResponse
from ..types.moderation_multi_modal_input_param import ModerationMultiModalInputParam

__all__ = ["Moderations", "AsyncModerations"]


class Moderations(SyncAPIResource):
    """
    Given text and/or image inputs, classifies if those inputs are potentially harmful.
    """

    @cached_property
    def with_raw_response(self) -> ModerationsWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return ModerationsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModerationsWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return ModerationsWithStreamingResponse(self)

    def create(
        self,
        *,
        input: Union[str, SequenceNotStr[str], Iterable[ModerationMultiModalInputParam]],
        model: Union[str, ModerationModel] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ModerationCreateResponse:
        """Scores text inputs against the SovereignEG moderation categories.

        The gateway currently runs a basic keyword scorer (reported as
        `sovereigneg-basic-keyword-check` in the response `model`). It returns a `flagged`
        boolean and a per-category score for each input. Treat the result as a coarse
        pre-filter, not a full safety classifier. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          input: Input (or inputs) to classify. Can be a single string, an array of strings, or
              an array of multi-modal input objects; only the text parts are scored today.

          model: Optional moderation model id. The gateway currently serves a single scorer, so
              this can be omitted.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/moderations",
            body=maybe_transform(
                {
                    "model": model,
                    "input": input,
                },
                moderation_create_params.ModerationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                security={"bearer_auth": True},
            ),
            cast_to=ModerationCreateResponse,
        )


class AsyncModerations(AsyncAPIResource):
    """
    Given text and/or image inputs, classifies if those inputs are potentially harmful.
    """

    @cached_property
    def with_raw_response(self) -> AsyncModerationsWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return AsyncModerationsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModerationsWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://github.com/x-Muha/SEG-SDK#raw-responses-and-headers
        """
        return AsyncModerationsWithStreamingResponse(self)

    async def create(
        self,
        *,
        input: Union[str, SequenceNotStr[str], Iterable[ModerationMultiModalInputParam]],
        model: Union[str, ModerationModel] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx2.Timeout | None | NotGiven = not_given,
    ) -> ModerationCreateResponse:
        """Scores text inputs against the SovereignEG moderation categories.

        The gateway currently runs a basic keyword scorer (reported as
        `sovereigneg-basic-keyword-check` in the response `model`). It returns a `flagged`
        boolean and a per-category score for each input. Treat the result as a coarse
        pre-filter, not a full safety classifier. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).

        Args:
          input: Input (or inputs) to classify. Can be a single string, an array of strings, or
              an array of multi-modal input objects; only the text parts are scored today.

          model: Optional moderation model id. The gateway currently serves a single scorer, so
              this can be omitted.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/moderations",
            body=await async_maybe_transform(
                {
                    "model": model,
                    "input": input,
                },
                moderation_create_params.ModerationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                security={"bearer_auth": True},
            ),
            cast_to=ModerationCreateResponse,
        )


class ModerationsWithRawResponse:
    def __init__(self, moderations: Moderations) -> None:
        self._moderations = moderations

        self.create = _legacy_response.to_raw_response_wrapper(
            moderations.create,
        )


class AsyncModerationsWithRawResponse:
    def __init__(self, moderations: AsyncModerations) -> None:
        self._moderations = moderations

        self.create = _legacy_response.async_to_raw_response_wrapper(
            moderations.create,
        )


class ModerationsWithStreamingResponse:
    def __init__(self, moderations: Moderations) -> None:
        self._moderations = moderations

        self.create = to_streamed_response_wrapper(
            moderations.create,
        )


class AsyncModerationsWithStreamingResponse:
    def __init__(self, moderations: AsyncModerations) -> None:
        self._moderations = moderations

        self.create = async_to_streamed_response_wrapper(
            moderations.create,
        )
