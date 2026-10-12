from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["DecisionInputTextParam"]


class DecisionInputTextParam(TypedDict, total=False):
    text: Required[str]

    type: Required[Literal["input_text"]]
