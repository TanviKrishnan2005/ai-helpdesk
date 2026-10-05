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
        best_score = results[0]["score"]

        if best_score < 0.35:
            return {
                "response": (
                    "I couldn't find enough information in the "
                    "knowledge base to confidently answer this question."
                ),
                "resolved": False,
                "confidence": best_score
            }

        context = "\n\n".join(
            result["content"]
            for result in results
        )

    else:
        return {
            "response": (
                "I couldn't find relevant information "
                "in the knowledge base."
            ),
            "resolved": False,
            "confidence": 0
        }

    prompt = f"""
You are a helpful customer support assistant.

Answer the user's question using only the knowledge base provided below.

Knowledge base:
{context}

User question:
{message}

Give a clear and practical answer.
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
        "response": response["message"]["content"],
        "resolved": True,
        "confidence": results[0]["score"]
    }