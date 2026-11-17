import logging

from sqlalchemy.orm import Session

from ..models import Ticket
from .llm_service import generate_ai_response


def classify_ticket(message):
    text = message.lower()

    if any(
        word in text
        for word in ["wifi", "wi-fi", "internet", "network", "router"]
    ):
        category = "Network"

    elif any(
        word in text
        for word in ["password", "login", "account", "access"]
    ):
        category = "Account"

    elif any(
        word in text
        for word in ["software", "application", "app", "program"]
    ):
        category = "Software"

    elif any(
        word in text
        for word in ["payment", "refund", "billing"]
    ):
        category = "Payment"

    else:
        category = "General"

    if any(
        word in text
        for word in ["urgent", "cannot", "can't", "down", "blocked"]
    ):
        priority = "High"
    else:
        priority = "Medium"

    return category, priority


def generate_ticket_subject(message):
    try:
        prompt = (
            "Create a short support ticket subject from "
            "the user's problem. Return only the subject, "
            "with no quotes. Keep it under 8 words.\n\n"
            f"User problem: {message}"
        )

        subject = generate_ai_response(prompt)

        if subject:
            return subject[:100]

    except Exception:
        logging.exception("AI ticket subject generation failed")

    return message[:80]


def create_support_ticket(
    db: Session,
    subject: str,
    description: str,
    user_id: int,
    category: str = "General",
    priority: str = "Medium",
):
    ticket = Ticket(
        subject=subject,
        description=description,
        category=category,
        priority=priority,
        user_id=user_id,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket
