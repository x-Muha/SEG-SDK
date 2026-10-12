from typing import Any, List
from typing_extensions import Literal

import pydantic

from .._compat import PYDANTIC_V1
from .._models import BaseModel
from .._utils._embeddings import decode_base64_embedding

__all__ = ["Embedding"]


def _decode_if_base64(value: object) -> object:
    # The SDK asks the gateway for `encoding_format="base64"` by default because it is
    # smaller and faster to parse. Decoding here, before validation, keeps `embedding`
    # a list of floats even when the client validates responses strictly.
    if isinstance(value, str):
        return decode_base64_embedding(value)
    return value


class Embedding(BaseModel):
    """Represents an embedding vector returned by embedding endpoint."""

    embedding: List[float]
    """The embedding vector, which is a list of floats.

    The length of the vector depends on the model; see the model's catalog entry.
    """

    index: int
    """The index of the embedding in the list of embeddings."""

    object: Literal["embedding"]
    """The object type, which is always "embedding"."""

    if PYDANTIC_V1:

        @pydantic.validator("embedding", pre=True)  # pyright: ignore[reportDeprecated, reportUnknownMemberType, reportUntypedFunctionDecorator]
        def _decode_embedding_v1(cls, value: Any) -> Any:  # pyright: ignore[reportSelfClsParameterName]
            return _decode_if_base64(value)

    else:

        @pydantic.field_validator("embedding", mode="before")
        @classmethod
        def _decode_embedding(cls, value: Any) -> Any:
            return _decode_if_base64(value)
