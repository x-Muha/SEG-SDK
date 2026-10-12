from typing import List

import rich
from pydantic import BaseModel

from seg import SEG


class Step(BaseModel):
    explanation: str
    output: str


class MathResponse(BaseModel):
    steps: List[Step]
    final_answer: str


client = SEG()

completion = client.chat.completions.parse(
    model="Qwen/Qwen3-0.6B",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
    response_format=MathResponse,
)

message = completion.choices[0].message
if message.parsed:
    rich.print(message.parsed.steps)

    print("answer: ", message.parsed.final_answer)
else:
    print(message.refusal)
