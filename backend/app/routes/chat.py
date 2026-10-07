import ollama

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.retriever import search_knowledge_base
from ..services.ticket_service import (
    create_support_ticket,
    classify_ticket
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/")
def chat(
    message: str,
    db: Session = Depends(get_db)
):

    results = search_knowledge_base(message)

    if results:
        best_score = results[0]["score"]

        if best_score < 0.35:

            category, priority = classify_ticket(message)

            ticket = create_support_ticket(
                db=db,
                subject=message[:80],
                description=message,
                category=category,
                priority=priority
            )

            return {
                "response": (
                    "I couldn't find enough information in the "
                    "knowledge base to resolve your issue. "
                    f"I've created support ticket #{ticket.id} "
                    "for you."
                ),
                "resolved": False,
                "confidence": best_score,
                "ticket_id": ticket.id
            }

        context = "\n\n".join(
            result["content"]
            for result in results
        )

    else:

        category, priority = classify_ticket(message)

        ticket = create_support_ticket(
            db=db,
            subject=message[:80],
            description=message,
            category=category,
            priority=priority
        )

        return {
            "response": (
                "I couldn't find relevant information in the "
                "knowledge base. "
                f"I've created support ticket #{ticket.id} "
                "for you."
            ),
            "resolved": False,
            "confidence": 0,
            "ticket_id": ticket.id
        }

    prompt = f"""
You are a helpful customer support assistant.

Answer the user's question using only the knowledge base
provided below.

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