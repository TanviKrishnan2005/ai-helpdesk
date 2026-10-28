
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket, User
from ..auth_utils import get_current_user


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


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

    return ticket


@router.get("/")
def get_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id,
            Ticket.user_id == current_user.id
        )
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket


@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_statuses = ["Open", "In Progress", "Resolved"]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(allowed_statuses)}"
        )

    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id,
            Ticket.user_id == current_user.id
        )
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    ticket.status = status
    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket status updated successfully",
        "ticket": ticket
    }
