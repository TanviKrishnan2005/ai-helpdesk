from app.database import SessionLocal
from app.models import Ticket, User
from sqlalchemy import func

db = SessionLocal()

try:
    # Find the user account whose dashboard you checked.
    email = input("Enter that user's registered email: ").strip()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        print("User not found.")
    else:
        tickets = db.query(Ticket).filter(
            Ticket.user_id == user.id
        )

        print(f"\nUser: {user.email}")
        print("Total tickets:", tickets.count())
        print(
            "Open tickets:",
            tickets.filter(Ticket.status == "Open").count()
        )
        print(
            "In-progress tickets:",
            tickets.filter(Ticket.status == "In Progress").count()
        )
        print(
            "Resolved tickets:",
            tickets.filter(Ticket.status == "Resolved").count()
        )
        print(
            "High-priority tickets:",
            tickets.filter(
                func.lower(Ticket.priority) == "high"
            ).count()
        )

        print("\nTickets by category:")
        categories = (
            db.query(
                func.lower(Ticket.category),
                func.count(Ticket.id)
            )
            .filter(Ticket.user_id == user.id)
            .group_by(func.lower(Ticket.category))
            .all()
        )

        for category, count in categories:
            print(f"{category or 'uncategorized'}: {count}")

finally:
    db.close()