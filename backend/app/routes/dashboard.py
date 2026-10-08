from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Ticket


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db)
):
    total_tickets = db.query(Ticket).count()

    open_tickets = db.query(Ticket).filter(
        Ticket.status == "Open"
    ).count()

    high_priority = db.query(Ticket).filter(
        Ticket.priority == "High"
    ).count()

    resolved_tickets = db.query(Ticket).filter(
        Ticket.status == "Resolved"
    ).count()

    category_data = (
        db.query(
            func.lower(Ticket.category),
            func.count(Ticket.id)
        )
        .group_by(func.lower(Ticket.category))
        .all()
    )

    category_names = {
        "network": "Network",
        "account": "Account",
        "software": "Software",
        "payment": "Payment",
        "general": "General",
    }

    tickets_by_category = {}

    for category, count in category_data:
        display_name = category_names.get(
            category,
            category.title()
        )

        tickets_by_category[display_name] = count

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "high_priority": high_priority,
        "resolved_tickets": resolved_tickets,
        "tickets_by_category": tickets_by_category
    }