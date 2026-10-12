#!/usr/bin/env -S uv run python

import asyncio

from seg import AsyncSEG

# gets API Key from environment variable SEG_API_KEY
client = AsyncSEG()


async def main() -> None:
    stream = await client.chat.completions.create(
        model="Qwen/Qwen3-0.6B",
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            },
        ],
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue

        print(chunk.choices[0].delta.content or "", end="")
    print()


asyncio.run(main())
