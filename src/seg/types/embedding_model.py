from typing_extensions import Literal, TypeAlias

__all__ = ["EmbeddingModel"]

EmbeddingModel: TypeAlias = Literal["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
