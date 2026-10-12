import seg

# will default to `os.environ['SEG_API_KEY']` if not explicitly set
seg.api_key = "..."

# all client options can be configured just like the `SEG` instantiation counterpart
seg.base_url = "https://..."
seg.default_headers = {"x-foo": "true"}

# all API calls work in the exact same fashion as well
stream = seg.chat.completions.create(
    model="Qwen/Qwen3-0.6B",
    messages=[
        {
            "role": "user",
            "content": "How do I output all files in a directory using Python?",
        },
    ],
    stream=True,
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)

print()
