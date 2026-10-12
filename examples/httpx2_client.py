from seg import SEG, DefaultHttpx2Client

# The SDK uses HTTPX2 by default; pass an explicit client to tune limits, timeouts or proxies.
client = SEG(http_client=DefaultHttpx2Client())

completion = client.chat.completions.create(
    model="llama-3.1-8b-instruct",
    messages=[{"role": "user", "content": "Say this is a test"}],
    max_tokens=200,
)

print(completion.choices[0].message.content)
