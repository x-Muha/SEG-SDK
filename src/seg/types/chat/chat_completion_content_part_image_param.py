from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["ChatCompletionContentPartImageParam", "ImageURL", "PromptCacheBreakpoint"]


class ImageURL(TypedDict, total=False):
    url: Required[str]
    """Either a URL of the image or the base64 encoded image data."""

    detail: Literal["auto", "low", "high", "original"]
    """Specifies the detail level of the image.

    Learn more in the
    [Vision guide](https://sovereigneg.com/dashboard/docs).
    """


class PromptCacheBreakpoint(TypedDict, total=False):
    """Marks the exact end of a reusable prompt prefix.

    The breakpoint inherits its TTL from the request's `prompt_cache_options.ttl`; the boundary is not rounded to a token block.
    """

    mode: Required[Literal["explicit"]]
    """The breakpoint mode. Always `explicit`."""


class ChatCompletionContentPartImageParam(TypedDict, total=False):
    """
    Learn about [image inputs](https://sovereigneg.com/dashboard/docs).
    """

    image_url: Required[ImageURL]

    type: Required[Literal["image_url"]]
    """The type of the content part."""

    prompt_cache_breakpoint: PromptCacheBreakpoint
    """Marks the exact end of a reusable prompt prefix.

    The breakpoint inherits its TTL from the request's `prompt_cache_options.ttl`;
    the boundary is not rounded to a token block.
    """
