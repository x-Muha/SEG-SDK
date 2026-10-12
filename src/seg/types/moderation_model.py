# Written by scripts/update_model_types.py from its MODERATION_MODELS constant; the moderation
# scorer is not part of GET /v1/models, so update that constant when the gateway adds one.
from typing_extensions import Literal, TypeAlias

__all__ = ["ModerationModel"]

ModerationModel: TypeAlias = Literal["sovereigneg-basic-keyword-check"]
"""Model ids served by the SovereignEG moderation endpoint.

This list only drives editor autocomplete; the ``model`` parameter also accepts any
``str``, so ids added to the catalog after this release still work. Regenerate it with
``scripts/update_model_types.py``.
"""
