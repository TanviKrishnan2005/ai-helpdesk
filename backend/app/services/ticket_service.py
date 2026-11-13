
import logging
import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from ..models import Ticket

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

GEMINI_MODEL = "gemini-3.5-flash"


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
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                "Create a short support ticket subject from "
                "the user's problem. Return only the subject, "
                "with no quotes. Keep it under 8 words.\n\n"
                f"User problem: {message}"
            ),
        )

        subject = (response.text or "").strip()

        if subject:
            return subject[:100]

    except Exception:
        logging.exception("Gemini ticket subject generation failed")

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
