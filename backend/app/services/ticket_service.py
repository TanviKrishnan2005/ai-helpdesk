from sqlalchemy.orm import Session

from ..models import Ticket


def classify_ticket(message):
    text = message.lower()

    if any(word in text for word in ["wifi", "wi-fi", "internet", "network"]):
        category = "Network"

    elif any(word in text for word in ["password", "login", "account", "access"]):
        category = "Account"

    elif any(word in text for word in ["software", "application", "app", "program"]):
        category = "Software"

    elif any(word in text for word in ["payment", "refund", "billing"]):
        category = "Payment"

    else:
        category = "General"

    if any(word in text for word in ["urgent", "cannot", "can't", "down", "blocked"]):
        priority = "High"
    else:
        priority = "Medium"

    return category, priority


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