import typing as _t

if _t.TYPE_CHECKING:
    from .chat import (
        Chat as Chat,
        AsyncChat as AsyncChat,
        ChatWithRawResponse as ChatWithRawResponse,
        AsyncChatWithRawResponse as AsyncChatWithRawResponse,
        ChatWithStreamingResponse as ChatWithStreamingResponse,
        AsyncChatWithStreamingResponse as AsyncChatWithStreamingResponse,
    )
    from .images import (
        Images as Images,
        AsyncImages as AsyncImages,
        ImagesWithRawResponse as ImagesWithRawResponse,
        AsyncImagesWithRawResponse as AsyncImagesWithRawResponse,
        ImagesWithStreamingResponse as ImagesWithStreamingResponse,
        AsyncImagesWithStreamingResponse as AsyncImagesWithStreamingResponse,
    )
    from .models import (
        Models as Models,
        AsyncModels as AsyncModels,
        ModelsWithRawResponse as ModelsWithRawResponse,
        AsyncModelsWithRawResponse as AsyncModelsWithRawResponse,
        ModelsWithStreamingResponse as ModelsWithStreamingResponse,
        AsyncModelsWithStreamingResponse as AsyncModelsWithStreamingResponse,
    )
    from .decisions import (
        Decisions as Decisions,
        AsyncDecisions as AsyncDecisions,
        DecisionsWithRawResponse as DecisionsWithRawResponse,
        AsyncDecisionsWithRawResponse as AsyncDecisionsWithRawResponse,
        DecisionsWithStreamingResponse as DecisionsWithStreamingResponse,
        AsyncDecisionsWithStreamingResponse as AsyncDecisionsWithStreamingResponse,
    )
    from .embeddings import (
        Embeddings as Embeddings,
        AsyncEmbeddings as AsyncEmbeddings,
        EmbeddingsWithRawResponse as EmbeddingsWithRawResponse,
        AsyncEmbeddingsWithRawResponse as AsyncEmbeddingsWithRawResponse,
        EmbeddingsWithStreamingResponse as EmbeddingsWithStreamingResponse,
        AsyncEmbeddingsWithStreamingResponse as AsyncEmbeddingsWithStreamingResponse,
    )
    from .moderations import (
        Moderations as Moderations,
        AsyncModerations as AsyncModerations,
        ModerationsWithRawResponse as ModerationsWithRawResponse,
        AsyncModerationsWithRawResponse as AsyncModerationsWithRawResponse,
        ModerationsWithStreamingResponse as ModerationsWithStreamingResponse,
        AsyncModerationsWithStreamingResponse as AsyncModerationsWithStreamingResponse,
    )

else:
    _EXPORTS = {
        "Chat": (".chat", "Chat"),
        "AsyncChat": (".chat", "AsyncChat"),
        "ChatWithRawResponse": (".chat", "ChatWithRawResponse"),
        "AsyncChatWithRawResponse": (".chat", "AsyncChatWithRawResponse"),
        "ChatWithStreamingResponse": (".chat", "ChatWithStreamingResponse"),
        "AsyncChatWithStreamingResponse": (".chat", "AsyncChatWithStreamingResponse"),
        "Decisions": (".decisions", "Decisions"),
        "AsyncDecisions": (".decisions", "AsyncDecisions"),
        "DecisionsWithRawResponse": (".decisions", "DecisionsWithRawResponse"),
        "AsyncDecisionsWithRawResponse": (".decisions", "AsyncDecisionsWithRawResponse"),
        "DecisionsWithStreamingResponse": (".decisions", "DecisionsWithStreamingResponse"),
        "AsyncDecisionsWithStreamingResponse": (".decisions", "AsyncDecisionsWithStreamingResponse"),
        "Embeddings": (".embeddings", "Embeddings"),
        "AsyncEmbeddings": (".embeddings", "AsyncEmbeddings"),
        "EmbeddingsWithRawResponse": (".embeddings", "EmbeddingsWithRawResponse"),
        "AsyncEmbeddingsWithRawResponse": (".embeddings", "AsyncEmbeddingsWithRawResponse"),
        "EmbeddingsWithStreamingResponse": (".embeddings", "EmbeddingsWithStreamingResponse"),
        "AsyncEmbeddingsWithStreamingResponse": (".embeddings", "AsyncEmbeddingsWithStreamingResponse"),
        "Images": (".images", "Images"),
        "AsyncImages": (".images", "AsyncImages"),
        "ImagesWithRawResponse": (".images", "ImagesWithRawResponse"),
        "AsyncImagesWithRawResponse": (".images", "AsyncImagesWithRawResponse"),
        "ImagesWithStreamingResponse": (".images", "ImagesWithStreamingResponse"),
        "AsyncImagesWithStreamingResponse": (".images", "AsyncImagesWithStreamingResponse"),
        "Models": (".models", "Models"),
        "AsyncModels": (".models", "AsyncModels"),
        "ModelsWithRawResponse": (".models", "ModelsWithRawResponse"),
        "AsyncModelsWithRawResponse": (".models", "AsyncModelsWithRawResponse"),
        "ModelsWithStreamingResponse": (".models", "ModelsWithStreamingResponse"),
        "AsyncModelsWithStreamingResponse": (".models", "AsyncModelsWithStreamingResponse"),
        "Moderations": (".moderations", "Moderations"),
        "AsyncModerations": (".moderations", "AsyncModerations"),
        "ModerationsWithRawResponse": (".moderations", "ModerationsWithRawResponse"),
        "AsyncModerationsWithRawResponse": (".moderations", "AsyncModerationsWithRawResponse"),
        "ModerationsWithStreamingResponse": (".moderations", "ModerationsWithStreamingResponse"),
        "AsyncModerationsWithStreamingResponse": (".moderations", "AsyncModerationsWithStreamingResponse"),
    }
    _SUBMODULES = {
        "chat",
        "decisions",
        "embeddings",
        "images",
        "models",
        "moderations",
    }

    def __getattr__(name: str) -> _t.Any:
        import importlib

        if name in _EXPORTS:
            module_name, symbol_name = _EXPORTS[name]
            value = getattr(importlib.import_module(module_name, __name__), symbol_name)
        elif name in _SUBMODULES:
            value = importlib.import_module(f".{name}", __name__)
        else:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        globals()[name] = value
        return value

    def __dir__() -> list[str]:
        return sorted(set(globals()) | set(_EXPORTS) | _SUBMODULES)


__all__ = [
    "Chat",
    "AsyncChat",
    "ChatWithRawResponse",
    "AsyncChatWithRawResponse",
    "ChatWithStreamingResponse",
    "AsyncChatWithStreamingResponse",
    "Decisions",
    "AsyncDecisions",
    "DecisionsWithRawResponse",
    "AsyncDecisionsWithRawResponse",
    "DecisionsWithStreamingResponse",
    "AsyncDecisionsWithStreamingResponse",
    "Embeddings",
    "AsyncEmbeddings",
    "EmbeddingsWithRawResponse",
    "AsyncEmbeddingsWithRawResponse",
    "EmbeddingsWithStreamingResponse",
    "AsyncEmbeddingsWithStreamingResponse",
    "Images",
    "AsyncImages",
    "ImagesWithRawResponse",
    "AsyncImagesWithRawResponse",
    "ImagesWithStreamingResponse",
    "AsyncImagesWithStreamingResponse",
    "Models",
    "AsyncModels",
    "ModelsWithRawResponse",
    "AsyncModelsWithRawResponse",
    "ModelsWithStreamingResponse",
    "AsyncModelsWithStreamingResponse",
    "Moderations",
    "AsyncModerations",
    "ModerationsWithRawResponse",
    "AsyncModerationsWithRawResponse",
    "ModerationsWithStreamingResponse",
    "AsyncModerationsWithStreamingResponse",
]
