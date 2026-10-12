from __future__ import annotations

import rich
from pydantic import BaseModel

import seg
from seg import SEG


class GetWeather(BaseModel):
    city: str
    country: str


client = SEG()


with client.chat.completions.stream(
    model="llama-3.1-8b-instruct",
    messages=[
        {
            "role": "user",
            "content": "What's the weather like in SF and New York?",
        },
    ],
    tools=[
        # because the tool is built with `pydantic_function_tool(...)`, the returned tool calls
        # will be automatically deserialized into this `GetWeather` type
        seg.pydantic_function_tool(GetWeather, name="get_weather"),
    ],
    parallel_tool_calls=True,
) as stream:
    for event in stream:
        if event.type == "tool_calls.function.arguments.delta" or event.type == "tool_calls.function.arguments.done":
            rich.get_console().print(event, width=80)

print("----\n")
rich.print(stream.get_final_completion())
