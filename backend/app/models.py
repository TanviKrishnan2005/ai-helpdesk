
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")

    tickets = relationship("Ticket", back_populates="owner")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), default="General")
    priority = Column(String(50), default="Medium")
    status = Column(String(50), default="Open")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Link each ticket to the user who created it
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="tickets")
