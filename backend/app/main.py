from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine

from .routes import tickets, chat, dashboard, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Based Helpdesk API",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(tickets.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {
        "message": "AI-Based Helpdesk API is running"
    }