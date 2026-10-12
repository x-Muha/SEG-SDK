from __future__ import annotations

from typing import cast

from ..._types import Omit, NotGiven
from ..._utils import is_given
from ..._extras import has_numpy
from ..._utils._embeddings import decode_base64_embedding
from ...types.create_embedding_response import CreateEmbeddingResponse


def parse_embedding_response(
    obj: CreateEmbeddingResponse, *, encoding_format: str | Omit | NotGiven
) -> CreateEmbeddingResponse:
    """Decode base64 vectors the SDK asked for on the user's behalf.

    Under strict response validation the `Embedding` model already decodes them during
    validation, so this is a no-op there; in the default (constructed) mode this is where
    the decoding happens.
    """
    if is_given(encoding_format):
        # don't modify the response object if a user explicitly asked for a format
        return obj

    if not obj.data:
        raise ValueError("No embedding data received")

    if not any(isinstance(embedding.embedding, str) for embedding in obj.data):
        return obj

    use_numpy = has_numpy()
    for embedding in obj.data:
        data = cast(object, embedding.embedding)
        if isinstance(data, str):
            embedding.embedding = decode_base64_embedding(data, use_numpy=use_numpy)

    return obj
