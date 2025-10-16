from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(
    model="mistral",
    messages=[
        {
            "role": "user",
            "content": "This is a test",
        },
    ],
)
print(response["message"]["content"])
# or access fields directly from the response object
print("------")

print(response.message.content)
