
import logging
from typing import Literal

import ollama
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
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

MIN_RETRIEVAL_SCORE = 0.25
MIN_SOURCE_SCORE = 0.40
MAX_HISTORY_MESSAGES = 10
MAX_HISTORY_CHARS = 4000


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    history: list[HistoryMessage] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_MESSAGES,
    )


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


def prepare_history(history):
    """Limit the conversation context sent to the model."""
    prepared = []
    total_chars = 0

    for item in reversed(history[-MAX_HISTORY_MESSAGES:]):
        content = item.content.strip()

        if not content:
            continue

        remaining = MAX_HISTORY_CHARS - total_chars

        if remaining <= 0:
            break

        content = content[:remaining]

        prepared.append({
            "role": item.role,
            "content": content,
        })

        total_chars += len(content)

    prepared.reverse()
    return prepared


def rewrite_follow_up(message, history):
    """Rewrite contextual follow-ups as standalone search queries."""
    if not history:
        return message

    try:
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Rewrite the latest user message as a standalone "
                        "customer-support search query. Use conversation "
                        "history only to resolve references such as 'it' "
                        "or 'that'. Preserve the user's intent. Return "
                        "only the rewritten query. Do not answer it."
                    ),
                },
                *history,
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )

        rewritten = response["message"]["content"].strip()

        if rewritten:
            return rewritten[:500]

    except Exception:
        logging.exception("Follow-up query rewriting failed")

    return message


def is_password_email_followup(message):
    """Identify questions about a missing password-reset email."""
    text = message.lower()

    refers_to_email = "email" in text or "it" in text

    refers_to_missing_message = any(
        phrase in text
        for phrase in [
            "don't receive",
            "do not receive",
            "not receive",
            "didn't receive",
            "did not receive",
            "never received",
            "haven't received",
            "have not received",
        ]
    )

    refers_to_password_reset = any(
        word in text
        for word in ["password", "reset", "it"]
    )

    return (
        refers_to_email
        and refers_to_missing_message
        and refers_to_password_reset
    )


def sanitize_answer(answer, message):
    """Apply a targeted safeguard for unsupported email advice."""
    answer_lower = answer.lower()

    unsupported_password_advice = [
        "spam folder",
        "spam or junk",
        "junk mail",
        "check your spam",
        "check your junk",
        "verify that you have entered your registered email",
        "ensure that you have entered your registered email",
    ]

    if (
        is_password_email_followup(message)
        and any(
            phrase in answer_lower
            for phrase in unsupported_password_advice
        )
    ):
        return (
            "If you don't receive the password-reset email, contact "
            "the support team. The available instructions do not "
            "specify additional troubleshooting steps."
        )

    return answer


@router.post("/")
def chat(
    message: str,
    payload: ChatRequest | None = None,
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
    history = prepare_history(payload.history if payload else [])

    # Step 1: Interpret the current question using recent context.
    retrieval_query = rewrite_follow_up(message, history)

    # Step 2: Retrieve knowledge-base passages.
    try:
        results = search_knowledge_base(retrieval_query, top_k=3)
    except Exception:
        logging.exception("Knowledge-base retrieval failed")
        results = []

    if not results:
        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=0,
        )

    best_score = float(results[0]["score"])

    if best_score < MIN_RETRIEVAL_SCORE:
        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=best_score,
        )

    # Step 3: Keep only sufficiently relevant passages.
    relevant_results = [
        result
        for result in results
        if float(result["score"]) >= MIN_SOURCE_SCORE
    ]

    if not relevant_results:
        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=best_score,
        )

    context = "\n\n---\n\n".join(
        (
            f"Source file: {result['name']}\n"
            f"Passage:\n{result['content']}"
        )
        for result in relevant_results
    )

    # Step 4: Generate an answer grounded in the retrieved passages.
    system_prompt = """
You are a careful customer-support assistant.

Rules:
1. Answer only with information supported by the supplied passages.
2. Conversation history can clarify the question but is not
   verified evidence.
3. Never invent procedures, policies, URLs, or technical facts.
4. If only part of the answer is supported, explain what is known
   and what remains unspecified.
5. Do not fill gaps with general knowledge or assumptions.
6. If the password-reset email does not arrive, the supplied
   password-reset instructions say to contact the support team.
   Do not invent additional troubleshooting steps.
7. Answer the current question directly without repeating the
   entire previous answer unless requested.
8. Do not mention source filenames in your answer.
9. Never claim an action was completed unless a tool performed it.
10. Be concise, accurate, and helpful.
"""

    model_messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": (
                f"Conversation context:\n"
                f"{format_history(history)}\n\n"
                f"Current user question:\n{message}\n\n"
                f"Retrieved knowledge-base passages:\n{context}\n\n"
                "Answer the current question using only the passages. "
                "If a requested detail is not covered, say so and "
                "provide any supported next step."
            ),
        },
    ]

    try:
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=model_messages,
        )

        answer = response["message"]["content"].strip()

        if not answer:
            raise ValueError("The AI returned an empty answer.")

    except Exception:
        logging.exception("Ollama response generation failed")

        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=best_score,
        )

    # Step 5: Apply the targeted safeguard.
    answer = sanitize_answer(answer, message)

    # Escalate when the model explicitly indicates it cannot answer.
    uncertain_phrases = [
        "the available information is insufficient",
        "the passages do not contain enough information",
        "i cannot determine from the provided information",
        "i don't have enough information",
        "i do not have enough information",
        "the provided passages do not",
        "i cannot answer this confidently",
        "i'm unable to answer this",
    ]

    if any(phrase in answer.lower() for phrase in uncertain_phrases):
        return escalate_to_ticket(
            db=db,
            message=message,
            user_id=current_user.id,
            confidence=best_score,
        )

    # Step 6: Return source metadata from actual retrieved passages.
    sources = [
        {
            "file": result["name"],
            "chunk_id": result["chunk_id"],
            "relevance_score": round(float(result["score"]), 4),
            "passage": result["content"],
        }
        for result in relevant_results
    ]

    return {
        "response": answer,
        "resolved": True,
        "confidence": round(best_score, 4),
        "sources": sources,
        "ticket_id": None,
    }


def format_history(history):
    """Format history to help the model interpret follow-ups."""
    if not history:
        return "No previous conversation."

    return "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history
    )
