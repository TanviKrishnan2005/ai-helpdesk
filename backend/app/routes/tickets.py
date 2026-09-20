from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket

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
    db: Session = Depends(get_db)
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


@router.get("/")
def get_tickets(
    db: Session = Depends(get_db)
):
    return db.query(Ticket).all()