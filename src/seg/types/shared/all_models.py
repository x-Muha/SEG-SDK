from typing import Union
from typing_extensions import TypeAlias

from .chat_model import ChatModel

__all__ = ["AllModels"]

AllModels: TypeAlias = Union[str, ChatModel]
"""Any model id accepted by the chat endpoint; kept as an alias of `ChatModel` for compatibility."""
