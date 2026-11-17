from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Conversation, Message, User
from ..auth_utils import get_current_user


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


class MessageCreate(BaseModel):
    role: str
    content: str


class ConversationCreate(BaseModel):
    title: str = "New Chat"


@router.post("/")
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = Conversation(
        title=payload.title,
        user_id=current_user.id
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("/")
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(
            Conversation.updated_at.desc(),
            Conversation.id.desc()
        )
        .all()
    )


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at
            }
            for message in conversation.messages
        ]
    }


@router.post("/{conversation_id}/messages")
def add_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    if payload.role not in ["user", "assistant"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid message role"
        )

    message = Message(
        role=payload.role,
        content=payload.content,
        conversation_id=conversation.id
    )

    db.add(message)

    # Update the conversation timestamp whenever a message is added.
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    # Use the first user message as the conversation title.
    if payload.role == "user" and conversation.title == "New Chat":
        conversation.title = payload.content[:50]
        db.commit()

    return message


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted"}