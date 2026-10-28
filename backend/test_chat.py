
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.routes import chat as chat_module


client = TestClient(app)

# Mock an authenticated user so tests don't depend on login.
test_user = SimpleNamespace(
    id=999,
    name="Test User",
    email="test@example.com",
    role="user",
)


def fake_current_user():
    return test_user


def fake_db():
    return Mock()


# Override dependencies for isolated API tests.
from app.auth_utils import get_current_user
from app.database import get_db

app.dependency_overrides[get_current_user] = fake_current_user
app.dependency_overrides[get_db] = fake_db


def test_empty_question_does_not_create_ticket():
    response = client.post("/chat/", params={"message": "   "})

    assert response.status_code == 200
    assert response.json()["resolved"] is False
    assert response.json()["ticket_id"] is None


@patch.object(chat_module, "search_knowledge_base", return_value=[])
@patch.object(chat_module, "escalate_to_ticket")
def test_no_retrieval_results_escalates(mock_escalate, mock_search):
    mock_escalate.return_value = {
        "response": "Ticket created",
        "resolved": False,
        "confidence": 0,
        "ticket_id": 123,
    }

    response = client.post(
        "/chat/",
        params={"message": "An unsupported question"},
    )

    assert response.status_code == 200
    mock_search.assert_called_once()
    mock_escalate.assert_called_once()


@patch.object(chat_module, "search_knowledge_base")
@patch.object(chat_module, "escalate_to_ticket")
def test_retrieval_failure_escalates(mock_escalate, mock_search):
    mock_search.side_effect = RuntimeError("Retrieval failed")

    mock_escalate.return_value = {
        "response": "Ticket created",
        "resolved": False,
        "confidence": 0,
        "ticket_id": 124,
    }

    response = client.post(
        "/chat/",
        params={"message": "Why is my account unavailable?"},
    )

    assert response.status_code == 200
    mock_escalate.assert_called_once()


@patch.object(chat_module, "search_knowledge_base")
@patch.object(chat_module, "escalate_to_ticket")
def test_low_retrieval_score_escalates(mock_escalate, mock_search):
    mock_search.return_value = [
        {
            "name": "software.txt",
            "chunk_id": 1,
            "content": "Unrelated software information.",
            "score": 0.10,
        }
    ]

    mock_escalate.return_value = {
        "response": "Ticket created",
        "resolved": False,
        "confidence": 0.10,
        "ticket_id": 125,
    }

    response = client.post(
        "/chat/",
        params={"message": "How do I repair a 3D printer?"},
    )

    assert response.status_code == 200
    mock_escalate.assert_called_once()


@patch.object(chat_module.ollama, "chat")
@patch.object(chat_module, "search_knowledge_base")
@patch.object(chat_module, "escalate_to_ticket")
def test_ollama_failure_escalates(
    mock_escalate,
    mock_search,
    mock_ollama,
):
    mock_search.return_value = [
        {
            "name": "software.txt",
            "chunk_id": 1,
            "content": (
                "The IT support desk operates from "
                "10 AM to 5 PM on weekdays."
            ),
            "score": 0.80,
        }
    ]

    mock_ollama.side_effect = RuntimeError("Ollama unavailable")

    mock_escalate.return_value = {
        "response": "Ticket created",
        "resolved": False,
        "confidence": 0.80,
        "ticket_id": 126,
    }

    response = client.post(
        "/chat/",
        params={"message": "What are the IT support hours?"},
    )

    assert response.status_code == 200
    mock_ollama.assert_called_once()
    mock_escalate.assert_called_once()


@patch.object(chat_module, "create_support_ticket")
def test_ticket_creation_failure_is_not_hidden(mock_create_ticket):
    mock_create_ticket.side_effect = RuntimeError(
        "Database unavailable"
    )

    try:
        chat_module.escalate_to_ticket(
            db=Mock(),
            message="Unsupported issue",
            user_id=test_user.id,
            confidence=0,
        )
    except RuntimeError as exc:
        assert str(exc) == "Database unavailable"
    else:
        raise AssertionError(
            "Ticket-creation errors should propagate to the caller."
        )


def teardown_module():
    app.dependency_overrides.clear()

@patch.object(chat_module.ollama, "chat")
@patch.object(chat_module, "search_knowledge_base")
def test_follow_up_uses_conversation_history(
    mock_search,
    mock_ollama,
):
    mock_search.return_value = [
        {
            "name": "password.txt",
            "chunk_id": 1,
            "content": (
                "If you do not receive the reset email or cannot "
                "complete the reset process, contact the support team."
            ),
            "score": 0.80,
        }
    ]

    # First Ollama call rewrites the follow-up query.
    # Second Ollama call generates the final answer.
    mock_ollama.side_effect = [
        {
            "message": {
                "content": (
                    "What should I do if I do not receive "
                    "the password reset email?"
                )
            }
        },
        {
            "message": {
                "content": (
                    "If you don't receive the reset email, "
                    "contact the support team."
                )
            }
        },
    ]

    response = client.post(
        "/chat/",
        params={"message": "What if I don't receive it?"},
        json={
            "history": [
                {
                    "role": "user",
                    "content": "How do I reset my password?",
                },
                {
                    "role": "assistant",
                    "content": "Follow the password-reset instructions.",
                },
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["resolved"] is True
    assert "contact the support team" in (
        response.json()["response"].lower()
    )
    mock_search.assert_called_once()
    assert mock_ollama.call_count == 2


@patch.object(chat_module.ollama, "chat")
@patch.object(chat_module, "search_knowledge_base")
def test_unsupported_password_email_advice_is_sanitized(
    mock_search,
    mock_ollama,
):
    mock_search.return_value = [
        {
            "name": "password.txt",
            "chunk_id": 1,
            "content": (
                "If you do not receive the reset email, "
                "contact the support team."
            ),
            "score": 0.80,
        }
    ]

    mock_ollama.side_effect = [
        {
            "message": {
                "content": (
                    "What should I do if I do not receive "
                    "the password reset email?"
                )
            }
        },
        {
            "message": {
                "content": (
                    "Check your spam or junk mail folders. "
                    "If that fails, contact support."
                )
            }
        },
    ]

    response = client.post(
        "/chat/",
        params={"message": "What if I don't receive it?"},
        json={
            "history": [
                {
                    "role": "user",
                    "content": "How do I reset my password?",
                }
            ]
        },
    )

    assert response.status_code == 200

    answer = response.json()["response"].lower()

    assert "contact the support team" in answer
    assert "spam" not in answer


@patch.object(chat_module, "search_knowledge_base", return_value=[])
@patch.object(chat_module, "escalate_to_ticket")
def test_follow_up_without_relevant_knowledge_escalates(
    mock_escalate,
    mock_search,
):
    mock_escalate.return_value = {
        "response": "Ticket created",
        "resolved": False,
        "confidence": 0,
        "ticket_id": 456,
    }

    response = client.post(
        "/chat/",
        params={"message": "What if I don't receive it?"},
        json={
            "history": [
                {
                    "role": "user",
                    "content": "How do I reset my password?",
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["resolved"] is False
    mock_escalate.assert_called_once()
