
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Ticket, User
from ..auth_utils import get_current_user


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Start with tickets belonging to the logged-in user.
    user_tickets = db.query(Ticket).filter(
        Ticket.user_id == current_user.id
    )

    total_tickets = user_tickets.count()

    open_tickets = user_tickets.filter(
        Ticket.status == "Open"
    ).count()

    high_priority = user_tickets.filter(
        Ticket.priority == "High"
    ).count()

    resolved_tickets = user_tickets.filter(
        Ticket.status == "Resolved"
    ).count()

    category_data = (
        db.query(
            func.lower(Ticket.category),
            func.count(Ticket.id)
        )
        .filter(Ticket.user_id == current_user.id)
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
            category.title() if category else "Uncategorized"
        )

        tickets_by_category[display_name] = count

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "high_priority": high_priority,
        "resolved_tickets": resolved_tickets,
        "tickets_by_category": tickets_by_category
    }
