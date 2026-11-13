
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

    conversations = relationship(
        "Conversation",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

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


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
