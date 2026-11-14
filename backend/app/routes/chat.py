import logging
import os
import re
from typing import Literal

from dotenv import load_dotenv
from google import genai
from fastapi import APIRouter, Depends, HTTPException
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

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)
GEMINI_MODEL = "gemini-3.5-flash"

router = APIRouter(prefix="/chat", tags=["Chat"])

MIN_RETRIEVAL_SCORE = 0.25
MIN_SOURCE_SCORE = 0.35
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


# --------------------------------------------------
# GREETING AND SMALL-TALK HANDLER
# --------------------------------------------------

def handle_small_talk(message):
    """
    Handle standalone greetings and casual messages
    without triggering knowledge-base retrieval
    or automatic ticket escalation.
    """

    text = message.lower().strip()

    # Normalize punctuation and extra spaces.
    text = re.sub(r"[^\w\s']", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    responses = {
        "hi": "Hi! How can I help you today?",
        "hello": "Hello! How can I assist you?",
        "hey": "Hey! What can I help you with?",

        "good morning": "Good morning! How can I help you today?",
        "good afternoon": "Good afternoon! How can I assist you?",
        "good evening": "Good evening! What can I help you with?",

        "how are you": (
            "I'm doing well, thank you! "
            "How can I help you today?"
        ),

        "how are you doing": (
            "I'm here and ready to help! "
            "What can I do for you?"
        ),

        "thanks": (
            "You're welcome! Let me know if you need anything else."
        ),

        "thank you": (
            "You're welcome! Happy to help."
        ),

        "ok": (
            "Alright! Let me know if you need any assistance."
        ),

        "okay": (
            "Alright! Let me know if you need any assistance."
        ),

        "bye": (
            "Goodbye! Feel free to come back whenever you need help."
        ),

        "goodbye": (
            "Goodbye! Have a great day."
        ),

        "see you": (
            "See you! Have a great day."
        ),
    }

    response = responses.get(text)

    if response:
        return {
            "response": response,
            "resolved": True,
            "confidence": 1.0,
            "sources": [],
            "ticket_id": None,
        }

    return None


# --------------------------------------------------
# FOLLOW-UP MESSAGE REWRITING
# --------------------------------------------------

def rewrite_follow_up(message, history):
    """Only rewrite contextual follow-ups when history exists."""

    if not history:
        return message

    simple_messages = {
        "hi",
        "hello",
        "hey",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "bye",
        "good morning",
        "good evening",
    }

    if message.lower().strip() in simple_messages:
        return message

    try:
        conversation = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                "Rewrite the latest user message as a standalone "
                "customer-support search query. Preserve intent. "
                "Return only the rewritten query.\n\n"
                f"Conversation history:\n{conversation}\n\n"
                f"Latest user message: {message}"
            ),
        )

        rewritten = (response.text or "").strip()

        if rewritten:
            return rewritten[:500]

    except Exception:
        logging.warning(
            "Follow-up rewriting failed. Using original message.",
            exc_info=True,
        )

    return message


# --------------------------------------------------
# PASSWORD RESET FOLLOW-UP HANDLING
# --------------------------------------------------

def is_password_email_followup(message):
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


# --------------------------------------------------
# MAIN CHAT ENDPOINT
# --------------------------------------------------

@router.post("/")
def chat(
    message: str,
    payload: ChatRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Validate message.
    if not message or not message.strip():
        return {
            "response": "Please enter a question so I can help.",
            "resolved": False,
            "confidence": 0,
            "ticket_id": None,
        }

    message = message.strip()

    history = prepare_history(
        payload.history if payload else []
    )

    # Step 1: Handle standalone greetings and small talk.
    # This happens BEFORE RAG retrieval and ticket escalation.

    small_talk_response = handle_small_talk(message)

    if small_talk_response:
        return small_talk_response

    # Step 2: Interpret the current question.
    retrieval_query = rewrite_follow_up(message, history)

    # Step 3: Retrieve knowledge-base passages.
    try:
        results = search_knowledge_base(
            retrieval_query,
            top_k=3,
        )

    except Exception:
        logging.exception("Knowledge-base retrieval failed")
        results = []

    if not results:
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            0,
        )

    best_score = float(results[0]["score"])

    if best_score < MIN_RETRIEVAL_SCORE:
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    relevant_results = [
        result
        for result in results
        if float(result["score"]) >= MIN_SOURCE_SCORE
    ]

    if not relevant_results:
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    context = "\n\n---\n\n".join(
        f"Source file: {result['name']}\n"
        f"Passage:\n{result['content']}"
        for result in relevant_results
    )

    # Step 4: Generate a grounded answer.

    system_prompt = """
You are a precise and helpful customer-support assistant.

RULES:

1. Answer the user's latest question using the conversation history for context.

2. Use only the supplied knowledge-base passages.

3. Carefully read the conversation history to identify troubleshooting
   steps the user has already attempted.

4. Never recommend repeating a step the user has explicitly tried.

5. Suggest the next relevant, untried troubleshooting step.

6. If the user reports that a previous step did not work,
   acknowledge it briefly and continue with the next step.

7. Include only steps directly relevant to the user's issue.

8. Do not invent troubleshooting steps, policies, or procedures.

9. If the knowledge base does not contain another useful step,
   recommend contacting the support team.

10. Keep answers concise, clear, and conversational.

11. Never mention source filenames.

12. Never claim an action was completed unless a tool performed it.

13. Never assume the user has tried a step unless they said so.

14. If the user explicitly says their account is locked,
    tell them to contact support.

15. Never assume an account is locked because a password reset failed.
"""

    prompt = (
        f"{system_prompt}\n\n"
        f"Conversation context:\n"
        f"{format_history(history)}\n\n"
        f"Current user question:\n"
        f"{message}\n\n"
        f"Retrieved knowledge-base passages:\n"
        f"{context}\n\n"
        "Answer using only the supplied passages."
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        answer = (response.text or "").strip()

        if not answer:
            raise ValueError(
                "The AI returned an empty answer."
            )

    except Exception:
        logging.exception(
            "Gemini response generation failed"
        )

        # Do not create a ticket just because Gemini is temporarily down.
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI assistant is temporarily unavailable. "
                "Please try again in a moment."
            ),
        )

    # Step 5: Sanitize the generated answer.
    answer = sanitize_answer(answer, message)

    # Step 6: Check whether escalation is required.
    escalation_phrases = [
        "contact the support team",
        "contact support",
        "reach out to the support team",
        "contact your support team",
    ]

    if any(
        phrase in answer.lower()
        for phrase in escalation_phrases
    ):
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

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

    if any(
        phrase in answer.lower()
        for phrase in uncertain_phrases
    ):
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    # Step 7: Prepare source information.
    sources = [
        {
            "file": result["name"],
            "chunk_id": result["chunk_id"],
            "relevance_score": round(
                float(result["score"]),
                4,
            ),
            "passage": result["content"],
        }
        for result in relevant_results
    ]

    # Step 8: Return the final response.
    return {
        "response": answer,
        "resolved": True,
        "confidence": round(best_score, 4),
        "sources": sources,
        "ticket_id": None,
    }


# --------------------------------------------------
# CONVERSATION HISTORY FORMATTING
# --------------------------------------------------

def format_history(history):
    if not history:
        return "No previous conversation."

    return "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history
    )