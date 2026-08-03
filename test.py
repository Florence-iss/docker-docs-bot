import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=200,
    messages=[
        { "role" : "user",
                "content" :"Say Hello and confirm my API key is working."}
    ],

)

print(message.content[0].text)

                                          