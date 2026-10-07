from sqlalchemy.orm import Session

from ..models import Ticket


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