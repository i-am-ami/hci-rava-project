import os
from openai import AzureOpenAI
from dotenv import load_dotenv

model_name = "gpt-35-turbo"
deployment = "gpt-35-turbo"

api_version = "2025-01-01-preview"

load_dotenv()

client = AzureOpenAI(
    api_version=api_version,
)


# this is just test code. Doesn't have the ability of context/remembering past messages.
response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "Give me 2 concrete, specific options though",
        }
    ],
    max_tokens=600,
    temperature=1.0,
    top_p=1.0,
    model=deployment
)

print(response.choices[0].message.content)