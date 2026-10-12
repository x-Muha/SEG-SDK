from typing_extensions import Literal, TypeAlias

__all__ = ["ChatCompletionRole"]

ChatCompletionRole: TypeAlias = Literal["developer", "system", "user", "assistant", "tool", "function"]
