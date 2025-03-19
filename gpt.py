import os
from openai import AzureOpenAI
from dotenv import load_dotenv

endpoint = os.getenv('GPT_ENDPOINT')
model_name = "gpt-35-turbo"
deployment = "gpt-35-turbo"

subscription_key = os.getenv('GPT_KEY')
api_version = "2025-01-01-preview"
# gpt_key = 
# print(f'GPT_KEY: {gpt_key}')
# gpt_endpoint = os.getenv('GPT_ENDPOINT')
# print(f'GPT_ENDPOINT: {gpt_endpoint}')
# gpt_region = os.getenv('GPT_REGION')
# print(f'GPT_REGION: {gpt_region}')

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
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