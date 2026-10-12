from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from pydantic import StrictStr, StrictBool

from .._utils import PropertyInfo
from .._models import BaseModel

__all__ = [
    "Decision",
    "Answer",
    "PredicateAnswer",
    "ChoiceAnswer",
    "ChoiceProbability",
    "ScoreAnswer",
    "ScoreProbability",
    "RefusalAnswer",
    "Usage",
    "UsageInputTokensDetails",
    "UsageOutputTokensDetails",
]


class PredicateAnswer(BaseModel):
    name: Optional[str] = None

    probability: float

    type: Literal["predicate"]
    """The type of the object. Always `predicate`."""


class ChoiceProbability(BaseModel):
    probability: float

    value: Union[StrictStr, StrictBool]
    """
    Choice values may be strings or booleans; their text form must be unique within a question.
    """


class ChoiceAnswer(BaseModel):
    choice: Union[StrictStr, StrictBool]
    """
    Choice values may be strings or booleans; their text form must be unique within a question.
    """

    confidence: float

    name: Optional[str] = None

    probabilities: List[ChoiceProbability]

    type: Literal["choice"]
    """The type of the object. Always `choice`."""


class ScoreProbability(BaseModel):
    label: str

    probability: float

    value: int


class ScoreAnswer(BaseModel):
    confidence: float

    name: Optional[str] = None

    probabilities: List[ScoreProbability]

    score: float

    type: Literal["score"]
    """The type of the object. Always `score`."""


class RefusalAnswer(BaseModel):
    """The model declined to answer this question.

    Other questions in the same request can still receive answers.
    """

    name: Optional[str] = None

    type: Literal["refusal"]
    """The type of the object. Always `refusal`."""


Answer: TypeAlias = Annotated[
    Union[
        PredicateAnswer,
        ChoiceAnswer,
        ScoreAnswer,
        RefusalAnswer,
    ],
    PropertyInfo(discriminator="type"),
]


class UsageInputTokensDetails(BaseModel):
    cache_write_tokens: int

    cached_tokens: int


class UsageOutputTokensDetails(BaseModel):
    reasoning_tokens: int


class Usage(BaseModel):
    input_tokens: int

    input_tokens_details: UsageInputTokensDetails

    output_tokens: int

    output_tokens_details: UsageOutputTokensDetails

    total_tokens: int


class Decision(BaseModel):
    answers: List[Answer]

    model: str

    object: Optional[Literal["decision"]] = None
    """The object type. Always `decision` when returned by the SovereignEG API."""

    usage: Usage
