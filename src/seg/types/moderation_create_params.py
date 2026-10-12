from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr
from .moderation_model import ModerationModel
from .moderation_multi_modal_input_param import ModerationMultiModalInputParam

__all__ = ["ModerationCreateParams"]


class ModerationCreateParams(TypedDict, total=False):
    input: Required[Union[str, SequenceNotStr[str], Iterable[ModerationMultiModalInputParam]]]
    """Input (or inputs) to classify.

    Can be a single string, an array of strings, or an array of multi-modal input
    objects similar to other models.
    """

    model: Union[str, ModerationModel]
    """Optional moderation model id.

    The gateway currently serves a single scorer (`sovereigneg-basic-keyword-check`),
    so this can be omitted.
    """
