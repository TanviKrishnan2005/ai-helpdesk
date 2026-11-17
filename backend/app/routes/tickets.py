from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket, User
from ..auth_utils import get_current_user


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


def serialize_ticket(ticket, display_number):
    """Return ticket information with a user-specific display number."""

    return {
        "id": ticket.id,
        "display_ticket_number": display_number,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "user_id": ticket.user_id,
    }


def get_display_number(db, ticket):
    """Calculate a ticket's position among its owner's tickets."""

    if ticket.user_id is None:
        return None

    return db.query(Ticket).filter(
        Ticket.user_id == ticket.user_id,
        (
            (Ticket.created_at < ticket.created_at)
            |
            (
                (Ticket.created_at == ticket.created_at)
                & (Ticket.id <= ticket.id)
            )
        )
    ).count()


@router.post("/")
def create_ticket(
    subject: str,
    description: str,
    category: str = "General",
    priority: str = "Medium",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = Ticket(
        subject=subject,
        description=description,
        category=category,
        priority=priority,
        user_id=current_user.id
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    display_number = get_display_number(db, ticket)

    return serialize_ticket(ticket, display_number)


@router.get("/")
def get_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket)

    # Admins can see all tickets.
    # Regular users can see only their own tickets.
    if (current_user.role or "").lower() != "admin":
        query = query.filter(
            Ticket.user_id == current_user.id
        )

    tickets = query.order_by(
        Ticket.created_at.asc(),
        Ticket.id.asc()
    ).all()

    # Maintain a separate counter for every user.
    counters = {}

    numbered_tickets = []

    for ticket in tickets:

        if ticket.user_id is None:
            display_number = None

        else:
            counters[ticket.user_id] = (
                counters.get(ticket.user_id, 0) + 1
            )

            display_number = counters[ticket.user_id]

        numbered_tickets.append(
            serialize_ticket(ticket, display_number)
        )

    # Return newest tickets first.
    numbered_tickets.reverse()

    return numbered_tickets


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket).filter(
        Ticket.id == ticket_id
    )

    if (current_user.role or "").lower() != "admin":
        query = query.filter(
            Ticket.user_id == current_user.id
        )

    ticket = query.first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    display_number = get_display_number(db, ticket)

    return serialize_ticket(ticket, display_number)


@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_statuses = [
        "Open",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Status must be one of: "
                f"{', '.join(allowed_statuses)}"
            )
        )

    query = db.query(Ticket).filter(
        Ticket.id == ticket_id
    )

    # Only admins can update tickets belonging to other users.
    if (current_user.role or "").lower() != "admin":
        query = query.filter(
            Ticket.user_id == current_user.id
        )

    ticket = query.first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    ticket.status = status

    db.commit()
    db.refresh(ticket)

    display_number = get_display_number(db, ticket)

    return {
        "message": "Ticket status updated successfully",
        "ticket": serialize_ticket(
            ticket,
            display_number
        )
    }

@router.patch("/{ticket_id}/priority")
def update_ticket_priority(
    ticket_id: int,
    priority: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_priorities = [
        "Low",
        "Medium",
        "High"
    ]

    if priority not in allowed_priorities:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Priority must be one of: "
                f"{', '.join(allowed_priorities)}"
            )
        )

    query = db.query(Ticket).filter(
        Ticket.id == ticket_id
    )

    # Only admins can update tickets belonging to other users.
    if (current_user.role or "").lower() != "admin":
        query = query.filter(
            Ticket.user_id == current_user.id
        )

    ticket = query.first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    ticket.priority = priority

    db.commit()
    db.refresh(ticket)

    display_number = get_display_number(db, ticket)

    return {
        "message": "Ticket priority updated successfully",
        "ticket": serialize_ticket(
            ticket,
            display_number
        )
    }

@router.patch("/{ticket_id}/category")
def update_ticket_category(
    ticket_id: int,
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_categories = [
        "Network",
        "Account",
        "Software",
        "Payment",
        "General"
    ]

    if category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=(
                "Category must be one of: "
                + ", ".join(allowed_categories)
            )
        )

    query = db.query(Ticket).filter(
        Ticket.id == ticket_id
    )

    # Users can edit their own tickets.
    # Admins can edit any ticket.
    if (current_user.role or "").lower() != "admin":
        query = query.filter(
            Ticket.user_id == current_user.id
        )

    ticket = query.first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    ticket.category = category

    db.commit()
    db.refresh(ticket)

    display_number = get_display_number(db, ticket)

    return {
        "message": "Ticket category updated successfully",
        "ticket": serialize_ticket(ticket, display_number)
    }