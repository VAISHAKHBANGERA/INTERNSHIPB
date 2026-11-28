import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": "Reply in one concise sentence."},
        {"role": "user", "content": "Explain what an API token is."},
    ],
    temperature=0.3,
)

print("Reply:", response.choices[0].message.content)
print(
    f"Tokens -> input: {response.usage.prompt_tokens}, "
    f"output: {response.usage.completion_tokens}"
)