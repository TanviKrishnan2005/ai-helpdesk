from fastapi import APIRouter

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/")
def chat(message: str):

    return {
        "response": f"I received your query: {message}"
    }