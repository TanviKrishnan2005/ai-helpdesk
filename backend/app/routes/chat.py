import logging
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User ,Ticket
from ..auth_utils import get_current_user
from ..services.retriever import search_knowledge_base
from ..services.llm_service import generate_ai_response
from ..services.ticket_service import (
    create_support_ticket,
    classify_ticket,
    generate_ticket_subject,
)

router = APIRouter(prefix="/chat", tags=["Chat"])

MIN_RETRIEVAL_SCORE = 0.25
MIN_SOURCE_SCORE = 0.35
MAX_HISTORY_MESSAGES = 30
MAX_HISTORY_CHARS = 8000


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    history: list[HistoryMessage] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_MESSAGES,
    )


# --------------------------------------------------
# TICKET ESCALATION
# --------------------------------------------------

def escalate_to_ticket(db, message, user_id, confidence):
    """Create a support ticket with a user-specific ticket number."""

    category, priority = classify_ticket(message)
    subject = generate_ticket_subject(message)

    ticket = create_support_ticket(
        db=db,
        subject=subject,
        description=message,
        user_id=user_id,
        category=category,
        priority=priority,
    )

    # Calculate this user's ticket number.
    display_number = db.query(Ticket).filter(
        Ticket.user_id == user_id,
        or_(
            Ticket.created_at < ticket.created_at,
            and_(
                Ticket.created_at == ticket.created_at,
                Ticket.id <= ticket.id,
            ),
        ),
    ).count()

    return {
        "response": (
            "I couldn't confidently resolve your issue using the "
            "available knowledge base. "
            f"I've created support ticket #{display_number} for you."
        ),
        "resolved": False,
        "confidence": round(float(confidence), 4),
        "ticket_id": ticket.id,
        "display_ticket_number": display_number,
    }

def ask_for_clarification(message):
    """Ask for more details instead of prematurely creating a ticket."""

    return {
        "response": (
            "I understand you're still experiencing an issue. "
            "Could you share a little more detail about what happened "
            "or what you tried so far? I'll help you with the next step."
        ),
        "resolved": True,
        "confidence": 0,
        "sources": [],
        "ticket_id": None,
    }


# --------------------------------------------------
# CONVERSATION HISTORY
# --------------------------------------------------

def prepare_history(history):
    """Keep enough recent context to preserve multi-step troubleshooting state."""

    prepared = []
    total_chars = 0

    for item in reversed(history[-MAX_HISTORY_MESSAGES:]):
        content = item.content.strip()

        if not content:
            continue

        remaining = MAX_HISTORY_CHARS - total_chars

        if remaining <= 0:
            break

        content = content[:remaining]

        prepared.append({
            "role": item.role,
            "content": content,
        })

        total_chars += len(content)

    prepared.reverse()

    return prepared


def format_history(history):
    if not history:
        return "No previous conversation."

    return "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history
    )


# --------------------------------------------------
# GREETING AND SMALL-TALK HANDLER
# --------------------------------------------------

def handle_small_talk(message):
    """
    Handle standalone greetings and casual messages
    without triggering knowledge-base retrieval
    or automatic ticket escalation.
    """

    text = message.lower().strip()

    text = re.sub(r"[^\w\s']", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    responses = {
        "hi": "Hi! How can I help you today?",
        "hello": "Hello! How can I assist you?",
        "helo": "Hello! How can I assist you?",
        "heelo": "Hello! How can I assist you?",
        "heello": "Hello! How can I assist you?",
        "hey": "Hey! What can I help you with?",

        "good morning": "Good morning! How can I help you today?",
        "good afternoon": "Good afternoon! How can I assist you?",
        "good evening": "Good evening! What can I help you with?",

        "how are you": (
            "I'm doing well, thank you! "
            "How can I help you today?"
        ),

        "how are you doing": (
            "I'm here and ready to help! "
            "What can I do for you?"
        ),

        "thanks": (
            "You're welcome! Let me know if you need anything else."
        ),

        "thank you": "You're welcome! Happy to help.",
        "thankyou": "You're welcome! Happy to help.",

        "ok": "Alright! Let me know if you need any assistance.",
        "okay": "Alright! Let me know if you need any assistance.",

        "bye": (
            "Goodbye! Feel free to come back whenever you need help."
        ),

        "goodbye": "Goodbye! Have a great day.",
        "see you": "See you! Have a great day.",
    }

    response = responses.get(text)

    if response:
        return {
            "response": response,
            "resolved": True,
            "confidence": 1.0,
            "sources": [],
            "ticket_id": None,
        }

    return None


# --------------------------------------------------
# FOLLOW-UP RETRIEVAL CONTEXT
# --------------------------------------------------

def build_retrieval_query(message, history):
    """
    Build a search query from the latest issue and its follow-up.

    This avoids making a separate LLM request just to rewrite
    every follow-up message.
    """

    previous_user_message = next(
        (
            item["content"]
            for item in reversed(history)
            if item["role"] == "user" and item["content"].strip()
        ),
        None,
    )

    if not previous_user_message:
        return message

    return (
        f"Previous customer issue: {previous_user_message}\n"
        f"Latest follow-up: {message}"
    )


# --------------------------------------------------
# PASSWORD RESET FOLLOW-UP HANDLING
# --------------------------------------------------

def is_password_email_followup(message):
    text = message.lower()

    refers_to_email = "email" in text or "it" in text

    refers_to_missing_message = any(
        phrase in text
        for phrase in [
            "don't receive",
            "do not receive",
            "not receive",
            "didn't receive",
            "did not receive",
            "never received",
            "haven't received",
            "have not received",
        ]
    )

    refers_to_password_reset = any(
        word in text
        for word in ["password", "reset", "it"]
    )

    return (
        refers_to_email
        and refers_to_missing_message
        and refers_to_password_reset
    )


def sanitize_answer(answer, message):
    answer_lower = answer.lower()

    unsupported_password_advice = [
        "spam folder",
        "spam or junk",
        "junk mail",
        "check your spam",
        "check your junk",
        "verify that you have entered your registered email",
        "ensure that you have entered your registered email",
    ]

    if (
        is_password_email_followup(message)
        and any(
            phrase in answer_lower
            for phrase in unsupported_password_advice
        )
    ):
        return (
            "If you don't receive the password-reset email, contact "
            "the support team. The available instructions do not "
            "specify additional troubleshooting steps."
        )

    return answer

def build_support_hours_answer(message, relevant_results):
    """Return a concise answer for support-hours questions when the KB supports it."""

    text = message.lower()
    asks_about_hours = any(
        phrase in text
        for phrase in (
            "working hours",
            "support hours",
            "desk hours",
            "operating hours",
            "opening hours",
            "what time",
            "when is the support",
            "when does the support",
            "when are you open",
            "when is the helpdesk",
            "when is the help desk",
        )
    )

    if not asks_about_hours:
        return None

    hours_source_found = any(
        "support_hours" in result["name"].lower()
        or (
            "support desk" in result["content"].lower()
            and "10 am" in result["content"].lower()
            and "weekdays" in result["content"].lower()
        )
        for result in relevant_results
    )

    if not hours_source_found:
        return None

    return (
        "Our IT Support Desk is available Monday through Friday, "
        "from 10 AM to 5 PM."
    )


def build_password_reset_answer(message, relevant_results):
    """Return complete password-reset instructions from the retrieved KB."""

    password_source_found = any(
        "password" in result["name"].lower()
        or "password reset" in result["content"].lower()
        for result in relevant_results
    )

    if not password_source_found:
        return None

    if is_password_email_followup(message):
        return (
            "If you do not receive the reset email or cannot complete "
            "the reset process, contact the support team."
        )

    text = message.lower()
    is_reset_request = (
        "password" in text
        and any(
            phrase in text
            for phrase in (
                "forgot", "reset", "forgotten",
                "can't remember", "cannot remember",
            )
        )
    )

    if not is_reset_request:
        return None

    return (
        "To reset your forgotten password, follow these steps:\n\n"
        "1. Open the account login page.\n"
        "2. Select the password reset or forgot password option.\n"
        "3. Enter your registered email address.\n"
        "4. Follow the password reset instructions sent to your email.\n"
        "5. Create a new strong password.\n\n"
        "If you do not receive the reset email or cannot complete the "
        "reset process, contact the support team."
    )



# --------------------------------------------------
# DETERMINISTIC WI-FI TROUBLESHOOTING
# --------------------------------------------------

WIFI_STEPS = [
    (
        "First, check that Wi-Fi is enabled on your device. "
        "Tell me once you've checked."
    ),
    (
        "Next, make sure you're connected to the correct Wi-Fi network. "
        "Tell me once you've checked."
    ),
    (
        "Now turn Wi-Fi off, wait a few seconds, and turn it back on. "
        "Let me know whether that helps."
    ),
    (
        "Next, restart your device and check whether Wi-Fi works afterward."
    ),
    (
        "If it still doesn't work, forget the Wi-Fi network and reconnect "
        "using the correct password."
    ),
    (
        "Finally, check whether another device can connect to the same "
        "Wi-Fi network."
    ),
]


def handle_wifi_troubleshooting(
    message,
    history,
    db,
    user_id,
    confidence=1.0,
):
    """
    Follow Wi-Fi troubleshooting instructions in order.

    The backend tracks completed steps instead of relying on
    the language model to choose the next step.
    """

    current_text = message.lower()

    user_messages = [
        item["content"].lower()
        for item in history
        if item["role"] == "user"
    ]

    conversation_text = " ".join(
        user_messages + [current_text]
    )

    wifi_terms = (
    "wi-fi",
    "wifi",
    "wireless network",
    )
    # Check whether the current message explicitly mentions Wi-Fi
    current_message_is_wifi = any(
    term in current_text for term in wifi_terms
    )
    # Detect a clearly new, unrelated support topic. 
    new_topic_terms = (
    "password",
    "reset",
    "login",
    "account",
    "software",
    "application",
    "billing",
    "payment",
)
    if not current_message_is_wifi and any(
        term in current_text for term in new_topic_terms
):
        return None
    # Continue Wi-Fi troubleshooting only if the conversation
    # # is about Wi-Fi or the current message is a Wi-Fi follow-up.
    if not any(term in conversation_text for term in wifi_terms):
        return None

    # Find the most recent step suggested by the assistant.
    last_assistant = next(
        (
            item["content"]
            for item in reversed(history)
            if item["role"] == "assistant"
        ),
        "",
    )

    step_match = re.search(
        r"Step\s+([1-6])\s*:",
        last_assistant,
        re.IGNORECASE,
    )

    asked_step = (
        int(step_match.group(1))
        if step_match
        else None
    )

    completed = set()

    # Identify steps explicitly completed by the user.
    for text in user_messages + [current_text]:

        # Step 1: Wi-Fi enabled.
        if (
            re.search(
                r"wi[- ]?fi.{0,25}(enabled|already on|turned on)",
                text,
            )
            or re.search(
                r"(enabled|turned on).{0,25}wi[- ]?fi",
                text,
            )
            or "wi-fi is on" in text
            or "wifi is on" in text
        ):
            completed.add(1)

        # Step 2: The user checked/selected the correct network or
        # explicitly attempted to connect to the selected network.
        if (
            (
                "correct network" in text
                or "right network" in text
            )
            and not any(
                word in text
                for word in ("not ", "wrong", "isn't", "isnt")
            )
        ) or re.search(
            r"\b(tried|attempted)\s+(to\s+)?connect(ing)?\b",
            text,
        ):
            completed.add(2)

        # Step 3: Toggle Wi-Fi.
        if any(
            phrase in text
            for phrase in (
                "off and on",
                "turned wi-fi off",
                "turned wifi off",
                "toggle wi-fi",
                "toggle wifi",
                "toggled wi-fi",
                "toggled wifi",
                "turned it off and on",
            )
        ):
            completed.add(3)

        # Step 4: Restart device.
        if any(
            phrase in text
            for phrase in (
                "restarted my device",
                "restarted the device",
                "restart my device",
                "rebooted my device",
                "rebooted the device",
                "restarted my laptop",
                "restarted the laptop",
                "restart my laptop",
                "rebooted my laptop",
                "rebooted the laptop",
                "restarted my computer",
                "restarted the computer",
                "restart my computer",
                "rebooted my computer",
                "rebooted the computer",
            )
        ):
            completed.add(4)

        # Step 5: Forget and reconnect.
        if (
            ("forget" in text or "forgot" in text)
            and (
                "network" in text
                or "wi-fi" in text
                or "wifi" in text
            )
        ):
            completed.add(5)

        # Step 6: Test another device.
        if any(
            phrase in text
            for phrase in (
                "other devices",
                "another device",
                "different device",
                "other phone",
                "other laptop",
            )
        ):
            completed.add(6)

    # Replay earlier turns so short replies such as "yes" are
    # associated with the step the assistant asked about at that time.
    previous_assistant_step = None
    short_affirmatives = {
        "yes", "yep", "yeah", "done", "i did", "already did",
        "checked", "that's done", "that is done",
    }
    for item in history:
        if item["role"] == "assistant":
            previous_match = re.search(
                r"Step\s+([1-6])\s*:",
                item["content"],
                re.IGNORECASE,
            )
            previous_assistant_step = (
                int(previous_match.group(1))
                if previous_match
                else None
            )
        elif item["role"] == "user":
            previous_reply = item["content"].strip().lower()
            if previous_assistant_step and previous_reply in short_affirmatives:
                completed.add(previous_assistant_step)

    # A clear statement that the user tried connecting to the selected
    # network completes Step 2, even if the connection still fails.
    if re.search(
        r"(tried|attempted)\s+(to\s+)?connect(ing)?",
        current_text,
    ) or re.search(
        r"connect(ed|ion)?\s+to\s+(the\s+)?(wi[- ]?fi|network)",
        current_text,
    ):
        completed.add(2)

    # Short affirmative responses confirm the step
    # suggested in the previous assistant message.
    affirmative = current_text.strip() in {
        "yes",
        "yep",
        "yeah",
        "done",
        "i did",
        "already did",
        "checked",
        "that's done",
        "that is done",
    }

    negative = current_text.strip() in {
        "no",
        "nope",
        "not yet",
        "haven't",
        "have not",
        "i haven't",
        "i have not",
    }

    if asked_step and affirmative:
        completed.add(asked_step)

    # If the user has not completed the requested step, give
    # a more actionable explanation instead of repeating the
    # same generic instruction.
    if asked_step and negative and asked_step not in completed:
        negative_guidance = {
            1: (
                "No problem. Turn on Wi-Fi using the Wi-Fi icon in your "
                "taskbar or your laptop's network settings. Once Wi-Fi is "
                "enabled, tell me."
            ),
            2: (
                "No problem. Open your laptop's Wi-Fi settings, select the "
                "network you want to use, and choose Connect. If prompted, "
                "enter that network's password. Tell me once you've tried "
                "connecting."
            ),
            3: (
                "No problem. Open your Wi-Fi settings, turn Wi-Fi off, "
                "wait a few seconds, and turn it back on. Tell me whether "
                "you've tried this."
            ),
            4: (
                "No problem. Save your work, restart your laptop, and then "
                "check whether it can connect to Wi-Fi. Let me know when "
                "you've tried this."
            ),
            5: (
                "No problem. In your Wi-Fi settings, select the network, "
                "choose Forget, then select it again and reconnect using "
                "the correct password. Tell me once you've tried."
            ),
            6: (
                "No problem. If possible, try connecting another phone or "
                "computer to the same Wi-Fi network. This helps us check "
                "whether the issue is limited to your laptop. Let me know "
                "what happens."
            ),
        }

        return {
            "response": (
                f"Step {asked_step}: "
                f"{negative_guidance[asked_step]}"
            ),
            "resolved": True,
            "confidence": 1.0,
            "sources": [],
            "ticket_id": None,
        }

    # Select the next uncompleted step.
    next_step = next(
        (
            number
            for number in range(1, 7)
            if number not in completed
        ),
        None,
    )

    if next_step is not None:
        return {
            "response": (
                f"Step {next_step}: "
                f"{WIFI_STEPS[next_step - 1]}"
            ),
            "resolved": True,
            "confidence": 1.0,
            "sources": [],
            "ticket_id": None,
        }

    # All documented Wi-Fi checks have been attempted.
    return escalate_to_ticket(
        db,
        message,
        user_id,
        confidence,
    )


# --------------------------------------------------
# DETERMINISTIC SOFTWARE TROUBLESHOOTING
# --------------------------------------------------

SOFTWARE_STEPS = [
    "Close the application completely and reopen it.",
    "Restart your device, then open the application again.",
    "Check whether the application has any pending updates and install them if available.",
    "Check that your device has enough available storage.",
    "If the issue continues, reinstall the application if you are permitted to do so.",
]

def handle_software_resolution(message, history):
    """Recognise when the user confirms that software is working."""

    current_text = message.lower().strip()

    resolution_phrases = (
        "it's working now",
        "it is working now",
        "its working now",
        "it's working",
        "it is working",
        "works now",
        "working now",
        "working fine",
        "works fine",
        "that fixed it",
        "this fixed it",
        "problem solved",
        "issue resolved",
        "it's fixed",
        "it is fixed",
        "all fixed",
    )

    is_resolved = any(
        phrase in current_text
        for phrase in resolution_phrases
    )

    if not is_resolved:
        return None

    # Confirm that the conversation is about software troubleshooting.
    software_context = any(
        item["role"] == "assistant"
        and re.search(
            r"Step\s+[1-5]\s*:",
            item["content"],
            re.IGNORECASE,
        )
        for item in history
    )

    if not software_context:
        return None

    return {
        "response": (
            "Glad to hear it's working now! "
            "Your issue appears to be resolved. "
            "If you need anything else, feel free to ask."
        ),
        "resolved": True,
        "confidence": 1.0,
        "sources": [],
        "ticket_id": None,
    }

def handle_software_troubleshooting(
    message,
    history,
    relevant_results,
    db,
    user_id,
    confidence,
):
    """Guide the user through the documented software steps one at a time."""

    source_found = any(
        "software" in result["name"].lower()
        or "software support" in result["content"].lower()
        for result in relevant_results
    )
    if not source_found:
        return None

    current_text = message.lower().strip()
    software_terms = ("application", "software", "app", "program")
    issue_terms = (
        "not working", "isn't working", "isnt working",
        "doesn't work", "doesnt work", "won't work",
        "wont work", "not opening", "keeps crashing",
        "not responding", "problem", "issue",
    )

    user_messages = [
        item["content"].lower()
        for item in history
        if item["role"] == "user"
    ]
    conversation_text = " ".join(user_messages + [current_text])
    has_software_context = any(term in conversation_text for term in software_terms)
    has_software_issue = any(term in current_text for term in software_terms) and any(
        term in current_text for term in issue_terms
    )

    last_assistant = next(
        (item["content"] for item in reversed(history) if item["role"] == "assistant"),
        "",
    )
    step_match = re.search(r"Step\s+([1-5])\s*:", last_assistant, re.IGNORECASE)

    # Only start this flow for a software problem, or continue an existing one.
    if not has_software_issue and not (has_software_context and step_match):
        return None

    # Detect whether the user confirms the issue is resolved.
    resolution_phrases = (
    "it's working now",
    "it is working now",
    "its working now",
    "yes, it's working",
    "yes, it is working",
    "working fine",
    "works now",
    "that fixed it",
    "this fixed it",
    "problem solved",
    "issue resolved",
    "it's fixed",
    "it is fixed",
    "all fixed",
    )
    if any(phrase in current_text for phrase in resolution_phrases):
        return {
        "response": (
            "Glad to hear it's working now! "
            "Your issue appears to be resolved. "
            "If you need anything else, feel free to ask."
        ),
        "resolved": True,
        "confidence": round(float(confidence), 4),
        "sources": [],
        "ticket_id": None,
    }

    
    asked_step = int(step_match.group(1)) if step_match else None
    completed = set()

    # Recognize explicit reports that a documented step was attempted.
    for text in user_messages + [current_text]:
        if any(phrase in text for phrase in (
            "closed and reopened", "close and reopen",
            "reopened the application", "reopened the app",
        )):
            completed.add(1)

        if any(phrase in text for phrase in (
            "restarted my device", "restarted the device",
            "rebooted my device", "rebooted the device",
            "restarted my computer", "restarted the computer",
        )):
            completed.add(2)

        if any(phrase in text for phrase in (
            "checked for updates", "check for updates",
            "installed the update", "updated the application",
            "updated the app", "no pending updates",
        )):
            completed.add(3)

        if any(phrase in text for phrase in (
            "checked storage", "checked my storage",
            "enough storage", "storage space",
            "freed up storage", "freed storage",
        )):
            completed.add(4)

        if any(phrase in text for phrase in (
            "reinstalled the application", "reinstalled the app",
            "reinstalling the application", "reinstalling the app",
        )):
            completed.add(5)

    affirmative = current_text in {
        "yes", "yep", "yeah", "done", "i did", "already did",
        "checked", "that's done", "that is done",
    }
    negative = current_text in {
        "no", "nope", "not yet", "haven't", "have not",
        "i haven't", "i have not",
    }

    if asked_step and affirmative:
        completed.add(asked_step)

    if asked_step and negative and asked_step not in completed:
        response = (
            f"Step {asked_step}: {SOFTWARE_STEPS[asked_step - 1]} "
            "Let me know once you've tried it."
        )
    else:
        next_step = next(
            (number for number in range(1, 6) if number not in completed),
            None,
        )
        if next_step is None:
            return escalate_to_ticket(
                db,
                message,
                user_id,
                confidence,
            )

        response = (
            f"Step {next_step}: {SOFTWARE_STEPS[next_step - 1]} "
            "Let me know whether that resolves the issue. If not, we'll "
            "move on to the next step."
        )

    return {
        "response": response,
        "resolved": True,
        "confidence": round(float(confidence), 4),
        "sources": [
            {
                "file": result["name"],
                "chunk_id": result["chunk_id"],
                "relevance_score": round(float(result["score"]), 4),
                "passage": result["content"],
            }
            for result in relevant_results
        ],
        "ticket_id": None,
    }


# --------------------------------------------------
# MAIN CHAT ENDPOINT
# --------------------------------------------------
@router.post("/")
def chat(
    message: str,
    payload: ChatRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not message or not message.strip():
        return {
            "response": "Please enter a question so I can help.",
            "resolved": False,
            "confidence": 0,
            "ticket_id": None,
        }

    message = message.strip()

    history = prepare_history(
        payload.history if payload else []
    )

    # Step 1: Handle greetings and small talk.
    small_talk_response = handle_small_talk(message)

    if small_talk_response:
        return small_talk_response

    # Step 2: Detect explicitly locked accounts.
    # This must run BEFORE Wi-Fi follow-up handling.
    message_lower = message.lower()

    locked_account_phrases = [
        "account is locked",
        "account has been locked",
        "permanently locked",
        "locked out of my account",
        "account locked",
        "my account is locked",
        "my account has been locked",
        "company account is locked",
        "company account has been locked",
    ]

    if any(
        phrase in message_lower
        for phrase in locked_account_phrases
    ):
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            1.0,
        )

    # Step 3: Handle Wi-Fi troubleshooting deterministically.
    wifi_response = handle_wifi_troubleshooting(
        message,
        history,
        db,
        current_user.id,
    )

    if wifi_response:
        return wifi_response

    # Step 4: Build the retrieval query.
    retrieval_query = build_retrieval_query(
        message,
        history,
    )

    # Step 5: Retrieve knowledge-base passages.
    try:
        results = search_knowledge_base(
            retrieval_query,
            top_k=3,
        )

    except Exception:
        logging.exception("Knowledge-base retrieval failed")
        results = []

    if not results:

        if history:
            return ask_for_clarification(message)

        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            0,
        )

    best_score = float(results[0]["score"])

    if best_score < MIN_RETRIEVAL_SCORE:

        if history:
            return ask_for_clarification(message)

        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    relevant_results = [
        result
        for result in results
        if float(result["score"]) >= MIN_SOURCE_SCORE
    ]

    if not relevant_results:

        if history:
            return ask_for_clarification(message)

        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    context = "\n\n---\n\n".join(
        f"Source file: {result['name']}\n"
        f"Passage:\n{result['content']}"
        for result in relevant_results
    )

    sources = [
        {
            "file": result["name"],
            "chunk_id": result["chunk_id"],
            "relevance_score": round(float(result["score"]), 4),
            "passage": result["content"],
        }
        for result in relevant_results
    ]

    # Return concise, deterministic answers for supported common questions.
    support_hours_answer = build_support_hours_answer(
        message,
        relevant_results,
    )

    if support_hours_answer:
        return {
            "response": support_hours_answer,
            "resolved": True,
            "confidence": round(best_score, 4),
            "sources": sources,
            "ticket_id": None,
        }

    # Use the complete documented procedure for password-reset requests.
    password_reset_answer = build_password_reset_answer(
        message,
        relevant_results,
    )

    if password_reset_answer:
        return {
            "response": password_reset_answer,
            "resolved": True,
            "confidence": round(best_score, 4),
            "sources": sources,
            "ticket_id": None,
        }

    # Guide software issues through the documented steps one at a time.
    software_response = handle_software_troubleshooting(
        message,
        history,
        relevant_results,
        db,
        current_user.id,
        best_score,
    )

    if software_response:
        return software_response

    # Step 6: Generate a grounded AI response.
    system_prompt = """
You are a precise and helpful customer-support assistant.

RULES:

1. Answer the user's latest question using the conversation history for context.

2. Use only the supplied knowledge-base passages.

3. Carefully read the conversation history to identify troubleshooting
   steps the user has already attempted.

4. Never recommend repeating a step the user has explicitly tried.

5. Suggest the next relevant, untried troubleshooting step.

6. If the user reports that a previous step did not work,
   acknowledge it briefly and continue with the next step.

7. Include only steps directly relevant to the user's issue.

8. Do not invent troubleshooting steps, policies, or procedures.

9. Work through the numbered troubleshooting steps in order,
   one step at a time.

10. If relevant troubleshooting steps remain that the user has
    not tried, suggest the next untried step.

11. Do not recommend contacting support while useful steps remain.

12. If support escalation is genuinely required, begin your response
    with exactly "ESCALATE:".

13. Otherwise begin your response with exactly "STEP:".

14. Keep answers concise, clear, and conversational.

15. When the knowledge base contains numbered instructions, include ALL relevant steps in the correct order.

16. Do not skip the final steps, even if the main process appears complete.

17. Preserve important final instructions, warnings, and support-contact information from the knowledge base.

18. Do not unnecessarily shorten procedural answers. Prioritize completeness and accuracy over brevity.
"""

    prompt = (
        f"{system_prompt}\n\n"
        f"Conversation context:\n"
        f"{format_history(history)}\n\n"
        f"Current user question:\n"
        f"{message}\n\n"
        f"Retrieved knowledge-base passages:\n"
        f"{context}\n\n"
        "Answer using only the supplied passages."
    )

    try:
        answer = generate_ai_response(prompt)

        if not answer:
            raise ValueError(
                "The AI returned an empty answer."
            )

    except Exception:
        logging.exception("AI response generation failed")

        raise HTTPException(
            status_code=503,
            detail=(
                "The AI assistant is temporarily unavailable. "
                "Please try again in a moment."
            ),
        )

    # Step 7: Sanitize the generated answer.
    answer = sanitize_answer(answer, message)

    # Step 8: Escalate only when explicitly requested.
    should_escalate = (
        answer.lstrip().upper().startswith("ESCALATE:")
    )

    if should_escalate:
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    # Remove the STEP marker before displaying the answer.
    answer = re.sub(
    r"\bSTEP:\s*",
    "",
    answer,
    flags=re.IGNORECASE,
    ).strip()

    uncertain_phrases = [
        "the available information is insufficient",
        "the passages do not contain enough information",
        "i cannot determine from the provided information",
        "i don't have enough information",
        "i do not have enough information",
        "the provided passages do not",
        "i cannot answer this confidently",
        "i'm unable to answer this",
    ]

    if any(
        phrase in answer.lower()
        for phrase in uncertain_phrases
    ):
        return escalate_to_ticket(
            db,
            message,
            current_user.id,
            best_score,
        )

    # Step 10: Return the final response.
    return {
        "response": answer,
        "resolved": True,
        "confidence": round(best_score, 4),
        "sources": sources,
        "ticket_id": None,
    }
