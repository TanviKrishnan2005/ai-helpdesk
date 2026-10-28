
import ollama

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..auth_utils import get_current_user
from ..services.retriever import search_knowledge_base
from ..services.ticket_service import (
    create_support_ticket,
    classify_ticket,
    generate_ticket_subject,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

# Starting point only; validate this threshold against your own questions.
MIN_RETRIEVAL_SCORE = 0.25


def escalate_to_ticket(db, message, user_id, confidence):
    """Create a ticket when the assistant cannot safely answer."""
    category, priority = classify_ticket(message)
    subject = generate_ticket_subject(message)

    ticket = create_support_ticket(
        db=db,
        subject=subject,
        description=message,
        user_id=user_id,
        category=category,
        priority=priority,
    )

    return {
        "response": (
            "I couldn't confidently resolve your issue using the "
            "available knowledge base. "
            f"I've created support ticket #{ticket.id} for you."
        ),
        "resolved": False,
        "confidence": round(float(confidence), 4),
        "ticket_id": ticket.id,
    }


@router.post("/")
def chat(
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not message or not message.strip():
        return {
            "response": "Please enter a question so I can help.",
            "resolved": False,
            "confidence": 0,
            "ticket_id": None,
        }

    message = message.strip()

    try:
        results = search_knowledge_base(message, top_k=3)
    except Exception:
        # Log the error in the backend terminal for debugging.
        import logging
        logging.exception("Knowledge-base retrieval failed")
        results = []

    if not results:
        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=0,
        )

    best_score = results[0]["score"]

    if best_score < MIN_RETRIEVAL_SCORE:
        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=best_score,
        )

    context_parts = []

    for result in results:
        context_parts.append(
            f"Source: {result['name']}\n"
            f"Relevant passage:\n{result['content']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """
You are a careful customer-support assistant.

Rules:
1. Answer using only the supplied knowledge-base passages.
2. Do not invent policies, steps, URLs, or technical facts.
3. If the passages do not contain enough information to answer,
   say that the available information is insufficient.
4. If the question is only partially answered by the passages,
   clearly explain what is known and what is missing.
5. Give practical, clear, numbered steps when appropriate.
6. Never claim that an action was completed unless a tool actually
   performed that action.
7. Do not treat similarity scores as proof that a passage is correct.
"""

    user_prompt = f"""
Knowledge-base passages:

{context}

User question:
{message}

Provide the best answer supported by these passages.
"""

    try:
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        answer = response["message"]["content"].strip()

        if not answer:
            raise ValueError("The AI returned an empty answer.")

        # Avoid presenting an explicit uncertainty response as resolved.
        uncertain_phrases = [
            "the available information is insufficient",
            "the passages do not contain enough information",
            "i cannot determine from the provided information",
        ]

        if any(
            phrase in answer.lower()
            for phrase in uncertain_phrases
        ):
            return escalate_to_ticket(
                db=db,
                message=message,
                user_id=current_user.id,
                confidence=best_score,
            )

        return {
            "response": answer,
            "resolved": True,
            "confidence": round(float(best_score), 4),
            "sources": list(dict.fromkeys(
                result["name"] for result in results
            )),
        }

    except Exception:
        import logging
        logging.exception("Ollama response generation failed")

        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=best_score,
        )
