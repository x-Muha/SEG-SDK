from typing import Any, Dict, List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["Model"]


class Model(BaseModel):
    """A model from the SovereignEG catalog.

    `GET /v1/models` and `GET /v1/models/{id}` return the OpenAI-compatible core
    fields plus catalog metadata; the two routes do not return exactly the same
    set, so everything beyond `id` and `object` is optional.
    """

    id: str
    """The model identifier, which can be referenced in the API endpoints."""

    object: Literal["model"]
    """The object type, which is always "model"."""

    created: Optional[int] = None
    """The Unix timestamp (in seconds) when the model was created, when known."""

    owned_by: Optional[str] = None
    """The organization that owns the model."""

    display_name: Optional[str] = None
    """Human-readable model name, e.g. "Meta: Llama 3.1 8B Instruct"."""

    description: Optional[str] = None

    provider: Optional[str] = None
    """The upstream provider serving the model."""

    provider_handle: Optional[str] = None

    modality: Optional[str] = None
    """What the model does: "chat", "embedding", "image", or "decision"."""

    input_modalities: Optional[List[str]] = None

    output_modalities: Optional[List[str]] = None

    context_window: Optional[int] = None
    """Maximum prompt + completion tokens the model accepts."""

    max_output_tokens: Optional[int] = None

    pricing: Optional[Dict[str, Any]] = None
    """Per-token prices in EGP, as published in the catalog."""

    capabilities: Optional[Dict[str, Any]] = None

    supported_parameters: Optional[List[str]] = None

    image_options: Optional[Dict[str, Any]] = None
    """Image-model options such as the accepted `size` format and supported modes."""

    weights_type: Optional[str] = None
    """"open_weights" or "proprietary", when known."""

    benchmarks: Optional[Dict[str, Any]] = None
    """Published benchmark scores, when the catalog has them."""

    card_url: Optional[str] = None
    """Link to the model card, when the catalog has one."""

    status: Optional[str] = None
    """Lifecycle status, e.g. "live" or "deprecated"."""

    visibility: Optional[str] = None

    published_at: Optional[str] = None

    deprecated_at: Optional[str] = None

    sunset_at: Optional[str] = None

    deprecation_notice: Optional[str] = None
