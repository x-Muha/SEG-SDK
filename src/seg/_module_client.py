from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import override

if TYPE_CHECKING:
    from .resources.images import Images
    from .resources.models import Models
    from .resources.chat.chat import Chat
    from .resources.decisions import Decisions
    from .resources.embeddings import Embeddings
    from .resources.moderations import Moderations

from . import _load_client
from ._utils import LazyProxy


class ChatProxy(LazyProxy["Chat"]):
    @override
    def __load__(self) -> Chat:
        return _load_client().chat


class ImagesProxy(LazyProxy["Images"]):
    @override
    def __load__(self) -> Images:
        return _load_client().images


class ModelsProxy(LazyProxy["Models"]):
    @override
    def __load__(self) -> Models:
        return _load_client().models


class DecisionsProxy(LazyProxy["Decisions"]):
    @override
    def __load__(self) -> Decisions:
        return _load_client().decisions


class EmbeddingsProxy(LazyProxy["Embeddings"]):
    @override
    def __load__(self) -> Embeddings:
        return _load_client().embeddings


class ModerationsProxy(LazyProxy["Moderations"]):
    @override
    def __load__(self) -> Moderations:
        return _load_client().moderations


chat: Chat = ChatProxy().__as_proxied__()
images: Images = ImagesProxy().__as_proxied__()
models: Models = ModelsProxy().__as_proxied__()
decisions: Decisions = DecisionsProxy().__as_proxied__()
embeddings: Embeddings = EmbeddingsProxy().__as_proxied__()
moderations: Moderations = ModerationsProxy().__as_proxied__()
