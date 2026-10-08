import ollama

from sqlalchemy.orm import Session

from ..models import Ticket


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
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a short support ticket subject from "
                        "the user's problem. "
                        "Return only the subject, with no quotes. "
                        "Keep it under 8 words."
                    )
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        subject = response["message"]["content"].strip()

        if subject:
            return subject[:100]

    except Exception:
        pass

    return message[:80]


def create_support_ticket(
    db: Session,
    subject: str,
    description: str,
    category: str = "General",
    priority: str = "Medium"
):
    ticket = Ticket(
        subject=subject,
        description=description,
        category=category,
        priority=priority
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket