from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Literal, Required, TypedDict

from .image_model import ImageModel

__all__ = ["ImageGenerateParamsBase", "ImageGenerateParamsNonStreaming", "ImageGenerateParamsStreaming"]


class ImageGenerateParamsBase(TypedDict, total=False):
    prompt: Required[str]
    """A text description of the desired image(s)."""

    background: Optional[Literal["transparent", "opaque", "auto"]]
    """Background transparency, when the provider supports it.

    Must be one of `transparent`, `opaque`, or `auto` (default value). When using
    `transparent`, set the output format to `png` or `webp`.
    """

    model: Union[str, ImageModel, None]
    """ID of an image model from the SovereignEG catalog, e.g. `flux-1-schnell`.

    List the catalog with `client.models.list()` and pick an entry whose `modality` is
    `"image"`; its `image_options` describe the accepted `size` format and modes.
    See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).
    """

    moderation: Optional[Literal["low", "auto"]]
    """Provider content-moderation level.

    Must be either `low` for less restrictive filtering or `auto` (default value).
    """

    n: Optional[int]
    """The number of images to generate. Must be between 1 and 10."""

    output_compression: Optional[int]
    """The compression level (0-100%) for the generated images.

    Applies to `webp` or `jpeg` output for providers that support it, and defaults
    to 100.
    """

    output_format: Optional[Literal["png", "jpeg", "webp"]]
    """The format in which the generated images are returned.

    Must be one of `png`, `jpeg`, or `webp`. The gateway echoes the format actually
    used in `ImagesResponse.output_format`.
    """

    partial_images: Optional[int]
    """The number of partial images to generate.

    This parameter is used for streaming responses that return partial images. Value
    must be between 0 and 3. When set to 0, the response will be a single image sent
    in one streaming event.

    Note that the final image may be sent before the full number of partial images
    are generated if the full image is generated more quickly.
    """

    quality: Optional[Literal["low", "medium", "high", "xhigh", "max", "auto", "standard", "hd"]]
    """The quality of the image that will be generated.

    `auto` (default value) lets the provider pick. Accepted values such as `low`,
    `medium`, and `high` depend on the provider; the gateway echoes the value used.
    """

    response_format: Optional[Literal["url", "b64_json"]]
    """`url` or `b64_json`.

    Most providers return base64-encoded images (`b64_json`).
    """

    size: Union[
        str,
        Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"],
        None,
    ]
    """The size of the generated images.

    A `WIDTHxHEIGHT` string such as `1024x1024`, or an aspect ratio such as `1:1` for
    providers that use one. See the model's `image_options` in the catalog.
    """

    style: Optional[Literal["vivid", "natural"]]
    """Legacy style hint.

    Most providers ignore it; describe the desired style in the prompt instead.
    """

    user: str
    """
    A unique identifier representing your end-user, which can help SEG to monitor
    and detect abuse.
    [Learn more](https://sovereigneg.com/dashboard/docs).
    """


class ImageGenerateParamsNonStreaming(ImageGenerateParamsBase, total=False):
    stream: Optional[Literal[False]]
    """Generate the image in streaming mode.

    Defaults to `false`. Only providers that support progressive previews emit partial
    images; the final image is always sent as a completed event.
    """


class ImageGenerateParamsStreaming(ImageGenerateParamsBase):
    stream: Required[Literal[True]]
    """Generate the image in streaming mode.

    Defaults to `false`. Only providers that support progressive previews emit partial
    images; the final image is always sent as a completed event.
    """


ImageGenerateParams = Union[ImageGenerateParamsNonStreaming, ImageGenerateParamsStreaming]
