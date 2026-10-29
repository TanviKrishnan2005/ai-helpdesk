# AI-Based Helpdesk System

An AI-powered customer support application that answers user questions using a local knowledge base, manages support tickets, and escalates unresolved issues to the support team.

## Features

- **AI Support Assistant:** Uses Ollama with the `qwen2.5:3b` model to generate responses grounded in knowledge-base documents.
- **Knowledge-Base Retrieval:** Uses Sentence Transformers (`all-MiniLM-L6-v2`) and cosine similarity to retrieve relevant support documents.
- **Automatic Ticket Escalation:** Creates support tickets when relevant information is unavailable or the AI cannot confidently resolve an issue.
- **Ticket Management:** Supports ticket creation, status updates, category classification, and priority assignment.
- **Authentication:** Uses JWT-based authentication to protect API endpoints.
- **Role-Based Access:** Supports regular users and administrators, with ticket access controlled by role and ownership.
- **Dashboard:** Displays ticket totals, statuses, priorities, and category statistics.
- **Persistent Storage:** Uses SQLite to store users and support tickets.
- **Frontend Interface:** Provides pages for the overview dashboard, AI assistant, and ticket management.

## Technology Stack

### Frontend
- React
- Vite
- CSS

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- PyJWT-compatible JWT handling through `python-jose`

### AI and Retrieval
- Ollama
- Qwen 2.5 3B
- Sentence Transformers
- `all-MiniLM-L6-v2`
- scikit-learn cosine similarity

### Testing
- pytest
- FastAPI TestClient

## Project Structure

```text
ai-helpdesk/
├── frontend/
│   └── src/
│       ├── components/
│       ├── App.jsx
│       └── App.css
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth_utils.py
│   │   ├── routes/
│   │   └── services/
│   ├── test_chat.py
│   └── requirements.txt
├── knowledge_base/
│   ├── wifi.txt
│   ├── account.txt
│   ├── software.txt
│   └── password.txt
└── README.md
```

## Prerequisites

- Python 3.11 or a compatible Python version
- Node.js and npm
- Ollama
- Git

## Local Setup

### 1. Start Ollama

Install Ollama and download the model:

```bash
ollama pull qwen2.5:3b
```

Ensure Ollama is running before testing AI responses.

### 2. Set up the backend

Open a terminal in the `backend` directory:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the API:

```powershell
python -m uvicorn app.main:app --reload
```

The backend runs at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

The local SQLite database is configured as `helpdesk.db`.

### 3. Set up the frontend

Open a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in the terminal.

If your frontend requires an API base URL, configure it to point to `http://127.0.0.1:8000` for local development.

## Knowledge Base

The knowledge base contains text documents with support instructions. The retrieval service:

1. Loads available `.txt` documents.
2. Generates embeddings using `all-MiniLM-L6-v2`.
3. Encodes the user's question.
4. Ranks documents using cosine similarity.
5. Passes sufficiently relevant passages to the language model.

The chat route uses retrieval-score thresholds to decide whether to provide context to the AI or escalate the issue. These thresholds should be calibrated against representative questions rather than treated as universal confidence values.

## Authentication and Authorization

- Users authenticate through the authentication API.
- JWT tokens protect authenticated endpoints.
- Expired or invalid tokens are rejected.
- Regular users can access their own tickets.
- Administrators can access tickets across users.
- Ticket status updates are checked against ownership and role permissions.

Configure `JWT_SECRET_KEY` through the environment for deployment. The development fallback secret must not be used in production.

## API Endpoints

The exact request fields can be inspected in the interactive API documentation.

| Endpoint | Purpose |
|---|---|
| `POST /auth/register` | Register a user |
| `POST /auth/login` | Authenticate a user |
| `GET /auth/me` | Get the authenticated user's details |
| `GET /tickets/` | List accessible tickets |
| `POST /tickets/` | Create a ticket |
| `GET /tickets/{ticket_id}` | Retrieve an accessible ticket |
| `PATCH /tickets/{ticket_id}/status` | Update ticket status |
| `POST /chat/` | Submit a support question |
| `GET /dashboard/stats` | Retrieve dashboard statistics |

## Testing

Run the backend tests from the `backend` directory:

```powershell
python -m pytest -v
```

### Verified test results

The test suite was run locally and reported **9 passed, 0 failed**.

The tests cover:

- Empty-question handling
- Escalation when retrieval returns no results
- Retrieval failure handling
- Low retrieval-score escalation
- Ollama failure escalation
- Ticket-creation failure handling
- Conversation-history follow-ups
- Sanitization of unsupported password-reset advice
- Escalation when a follow-up has no relevant knowledge

Additional manual checks confirmed ticket ownership, administrator permissions, JWT expiration, dashboard authentication, knowledge-base responses, automatic escalation, dashboard statistics against SQLite, and ticket persistence after a backend restart.

A Starlette/AnyIO deprecation warning appeared during testing; the test suite still passed.

## Current Limitations

- The knowledge base only covers the support topics documented in its text files.
- Retrieval similarity is not a calibrated probability of factual correctness.
- AI responses depend on Ollama and the availability of the configured model.
- The current database configuration uses local SQLite storage.
- Production deployment has not yet been completed.

## Future Improvements

- Expand the knowledge base and evaluate retrieval thresholds systematically.
- Improve automated integration and authorization tests.
- Configure production environment variables and restrictive CORS settings.
- Use persistent database storage suitable for the deployment platform.
- Plan reliable hosting for the Ollama model.
- Deploy the frontend and backend and verify communication between them.

## Security Notes

- Never commit real secrets, passwords, API keys, or production environment files.
- Use a strong, unique `JWT_SECRET_KEY` in production.
- Configure `APP_ENV=production` and the correct `FRONTEND_ORIGIN` when deploying.
- Review database persistence, CORS, and access control before public deployment.
