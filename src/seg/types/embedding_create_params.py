from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr
from .embedding_model import EmbeddingModel

__all__ = ["EmbeddingCreateParams"]


class EmbeddingCreateParams(TypedDict, total=False):
    input: Required[Union[str, SequenceNotStr[str], Iterable[int], Iterable[Iterable[int]]]]
    """Input text to embed, as a string or an array of strings.

    Token arrays are accepted for providers that support them. The input cannot be an
    empty string and must fit the model's `context_window` (see
    `client.models.retrieve`).
    """

    model: Required[Union[str, EmbeddingModel]]
    """ID of an embedding model from the SovereignEG catalog, e.g. `embeddinggemma-300m`.

    List the catalog with `client.models.list()` and pick an entry whose `modality` is
    `"embed"`. See the [SovereignEG docs](https://sovereigneg.com/dashboard/docs).
    """

    dimensions: int
    """The number of dimensions the resulting output embeddings should have.

    Only honoured by models that support truncated embeddings.
    """

    encoding_format: Literal["float", "base64"]
    """The format to return the embeddings in.

    Can be either `float` or [`base64`](https://pypi.org/project/pybase64/).
    """

    user: str
    """
    A unique identifier representing your end-user, which can help SEG to monitor
    and detect abuse.
    [Learn more](https://sovereigneg.com/dashboard/docs).
    """
