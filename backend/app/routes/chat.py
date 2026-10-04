import ollama

from fastapi import APIRouter

from ..services.retriever import search_knowledge_base


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/")
def chat(message: str):

    results = search_knowledge_base(message)

    if results:
        context = "\n\n".join(
            result["content"]
            for result in results
        )
    else:
        context = "No relevant information was found in the knowledge base."

    prompt = f"""
You are a helpful customer support assistant.

Answer the user's question using the knowledge base provided below.

Knowledge base:
{context}

User question:
{message}

Give a clear and practical answer.
If the knowledge base does not contain enough information to answer the question,
say that you do not have enough information and recommend contacting support.
"""

    response = ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "response": response["message"]["content"]
    }