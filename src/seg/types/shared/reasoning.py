from typing import Union, Optional
from typing_extensions import Literal

from ..._models import BaseModel
from .reasoning_effort import ReasoningEffort

__all__ = ["Reasoning"]


class Reasoning(BaseModel):
    """
    Configuration options for
    [reasoning models](https://sovereigneg.com/dashboard/docs).
    """

    context: Optional[Literal["auto", "current_turn", "all_turns"]] = None
    """
    Controls which reasoning items are rendered back to the model on later turns. If
    omitted or set to `auto`, the model determines the context mode. Defaults depend
    on the provider and model.

    When returned on a response, this is the effective reasoning context mode used
    for the response.
    """

    effort: Optional[ReasoningEffort] = None
    """Constrains effort on reasoning for reasoning models.

    Currently supported values are `none`, `minimal`, `low`, `medium`, `high`,
    `xhigh`, and `max`. Reducing reasoning effort can result in faster responses and
    fewer tokens used on reasoning in a response. Not all reasoning models support
    every value. See the
    [reasoning guide](https://sovereigneg.com/dashboard/docs) for
    model-specific support.
    """

    generate_summary: Optional[Literal["auto", "concise", "detailed"]] = None
    """**Deprecated:** use `summary` instead.

    A summary of the reasoning performed by the model. This can be useful for
    debugging and understanding the model's reasoning process. One of `auto`,
    `concise`, or `detailed`.
    """

    mode: Union[str, Literal["standard", "pro"], None] = None
    """Controls the reasoning execution mode for the request.

    When returned on a response, this is the effective execution mode.
    """

    summary: Optional[Literal["auto", "concise", "detailed"]] = None
    """A summary of the reasoning performed by the model.

    This can be useful for debugging and understanding the model's reasoning
    process. One of `auto`, `concise`, or `detailed`.

    Support for `concise` depends on the provider and model.
    """
