
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import tickets, chat, dashboard, auth, conversations
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Based Helpdesk API",
    version="1.0",
)

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "https://ai-helpdesk-pi-nine.vercel.app",
).rstrip("/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_origin,
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(conversations.router)


@app.get("/")
def root():
    return {
        "message": "AI-Based Helpdesk API is running"
    }
