# 🤖 AI-Based Helpdesk System

An intelligent technical support platform powered by **Generative AI, Retrieval-Augmented Generation (RAG), and automated ticket management**.

The AI-Based Helpdesk System helps users resolve common technical issues through a conversational AI assistant. It retrieves relevant information from a dedicated knowledge base, provides contextual troubleshooting guidance, and allows unresolved issues to be escalated into structured support tickets.

🌐 **Live Application:** https://ai-helpdesk-pi-nine.vercel.app/

📡 **Backend API:** https://ai-helpdesk-0lnj.onrender.com/

📖 **API Documentation:** https://ai-helpdesk-0lnj.onrender.com/docs

---

## ✨ Key Features

### 1. AI-Powered Chatbot
- Natural-language interaction for technical support.
- AI-generated responses using Google's Gemini API.
- Knowledge-base-grounded responses through RAG.
- Greeting and small-talk handling.

### 2. Retrieval-Augmented Generation (RAG)
- Retrieves relevant information from a custom knowledge base.
- Generates semantic embeddings using Sentence Transformers.
- Uses cosine similarity to identify relevant content.
- Provides retrieved context to the language model before response generation.

### 3. Context-Aware Conversations
- Maintains conversation history.
- Understands contextual follow-up questions.
- Handles short responses such as Yes and No.
- Supports guided troubleshooting workflows.

### 4. Guided Troubleshooting
- Step-by-step Wi-Fi troubleshooting.
- Software issue troubleshooting.
- Context-aware progression through troubleshooting steps.
- Issue escalation when troubleshooting is unsuccessful.

### 5. Ticket Management
- Create and track support tickets.
- User-specific ticket numbering.
- Update ticket status.
- Modify ticket priority:
  - Low
  - Medium
  - High
- Modify ticket category:
  - Network
  - Account
  - Software
  - Payment
  - General

### 6. User Authentication
- User registration and login.
- JWT-based authentication.
- Protected API endpoints.
- User-specific ticket and conversation access.

### 7. Dashboard and Conversation History
- Dashboard statistics.
- Persistent conversation history.
- New conversation creation.
- Conversations ordered by recent activity.

### 8. Error Handling
- Backend connection error handling.
- AI service error handling.
- User-friendly service-unavailable messages.
- Retry functionality.
- AI response loading indicators.

---

## 🏗️ System Architecture

The application follows a frontend-backend architecture with separate AI, retrieval and database services.

```text
                   USER
                    |
                    v
             REACT FRONTEND
                (Vite)
                    |
                    | HTTP / REST API
                    v
              FASTAPI BACKEND
                    |
          +---------+----------+
          |         |          |
          v         v          v
      AUTHENTI-   CHAT       TICKET
      CATION      SERVICE    SERVICE
          |         |
          |         v
          |     RAG RETRIEVER
          |         |
          |         v
          |    KNOWLEDGE BASE
          |         |
          |         v
          |    EMBEDDINGS
          |         |
          |         v
          |  COSINE SIMILARITY
          |         |
          |         v
          |     GEMINI API
          |
          v
      POSTGRESQL
      (SUPABASE)
```

### Request Processing Workflow

1. The user submits a question through the React frontend.
2. The frontend sends the request to the FastAPI backend.
3. The backend processes the request and retrieves relevant conversation context.
4. The RAG retriever searches the knowledge base using semantic similarity.
5. Relevant information is added to the prompt.
6. Gemini generates a response using the provided context.
7. The backend returns the response to the frontend.
8. If the issue remains unresolved, the user can escalate it into a support ticket.
9. Conversations, messages and tickets are persisted in PostgreSQL.

---

## 🧠 RAG Implementation

The system uses Retrieval-Augmented Generation to improve the relevance of AI responses.

### Retrieval Pipeline

**Step 1: Knowledge Base Preparation**

Text documents are maintained inside the `knowledge_base/` directory.

**Step 2: Embedding Generation**

Sentence Transformers converts text into numerical vector representations.

Model used:

`all-MiniLM-L6-v2`

**Step 3: Query Embedding**

The user's question is converted into an embedding using the same model.

**Step 4: Similarity Search**

Cosine similarity is used to compare the query embedding with knowledge-base embeddings.

**Step 5: Context Retrieval**

Relevant content is selected and added to the LLM prompt.

**Step 6: Response Generation**

Gemini generates a natural-language response using the user's query and retrieved context.

### Why RAG?

- Provides access to project-specific information.
- Improves relevance compared with relying only on general model knowledge.
- Allows knowledge-base updates without retraining the LLM.
- Helps reduce unsupported responses by supplying relevant context.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| API Communication | REST APIs, Axios |
| Database | PostgreSQL |
| Database Hosting | Supabase |
| ORM | SQLAlchemy |
| Authentication | JWT |
| AI Model | Google Gemini |
| Local LLM | Ollama, Qwen 2.5 3B |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Similarity Algorithm | Cosine Similarity |
| Backend Server | Uvicorn |
| Frontend Deployment | Vercel |
| Backend Deployment | Render |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
ai-helpdesk/
│
├── backend/
│   │
│   ├── app/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── conversations.py
│   │   │   └── tickets.py
│   │   │
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── retriever.py
│   │   │   └── ticket_service.py
│   │   │
│   │   └── main.py
│   │
│   ├── knowledge_base/
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── Auth.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Overview.jsx
│   │   │   ├── Assistant.jsx
│   │   │   └── Tickets.jsx
│   │   │
│   │   ├── App.jsx
│   │   └── App.css
│   │
│   ├── .env
│   └── package.json
│
└── README.md
```

---

## ⚙️ Installation and Setup

Follow these steps to run the project locally.

### Prerequisites

Make sure you have installed:

- Python 3.11+
- Node.js and npm
- Git
- PostgreSQL database or a Supabase project
- Gemini API key (for Gemini-based response generation)

### 1. Clone the Repository

```bash
git clone https://github.com/TanviKrishnan2005/ai-helpdesk.git

cd ai-helpdesk
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Backend Environment Variables

Create a `.env` file inside the `backend/` directory.

Configure the following variables:

```env
DATABASE_URL=your_postgresql_connection_string

JWT_SECRET_KEY=your_secure_random_secret

GEMINI_API_KEY=your_gemini_api_key

APP_ENV=development

AI_PROVIDER=gemini

FRONTEND_ORIGIN=http://localhost:5173
```

For local Ollama development, set:

```env
AI_PROVIDER=ollama
```

Make sure Ollama is running and the configured model is available locally.

**Important:** Never commit `.env` files, API keys, database credentials or JWT secrets to GitHub.

### 4. Start the Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The backend should be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create a `.env` file:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

The frontend will generally be available at:

```text
http://localhost:5173
```

---

## 🔐 Authentication Workflow

The application uses JSON Web Tokens (JWT) for authentication.

1. A user registers with their credentials.
2. The backend validates the registration request.
3. The user's password is securely hashed before storage.
4. During login, the backend verifies the credentials.
5. A JWT is generated after successful authentication.
6. The frontend uses the token for subsequent protected API requests.
7. The backend validates the token and identifies the authenticated user.

Ticket ownership checks ensure that users can only access permitted ticket records.

---

## 🎫 Ticket Management Workflow

The ticket module connects AI-assisted troubleshooting with structured issue tracking.

A typical workflow:

```text
User reports an issue
        |
        v
AI-assisted troubleshooting
        |
        v
Issue resolved?
     /       \
   Yes        No
   |           |
   v           v
 End       Create Ticket
               |
               v
         Assign Priority
               |
               v
         Select Category
               |
               v
         Track Ticket
```

Supported priority values:

- Low
- Medium
- High

Supported categories:

- Network
- Account
- Software
- Payment
- General

---

## 🌐 Deployment

The application is deployed using separate frontend and backend hosting services.

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | Supabase |
| AI Response Generation | Google Gemini API |

### Production URLs

**Frontend:**  
https://ai-helpdesk-pi-nine.vercel.app/

**Backend:**  
https://ai-helpdesk-0lnj.onrender.com/

**API Documentation:**  
https://ai-helpdesk-0lnj.onrender.com/docs

### Frontend Production Configuration

Set the following environment variable in Vercel:

```env
VITE_API_URL=https://ai-helpdesk-0lnj.onrender.com
```

The frontend uses this variable to communicate with the deployed backend.

### Backend Production Configuration

Configure the required database credentials, JWT secret, Gemini API key and frontend origin in Render's environment settings.

Production should use Gemini rather than the locally hosted Ollama service.

---

## 🧪 Testing

The following functional areas are included in the project's testing plan:

| Module | Test Cases |
|---|---|
| Authentication | Registration, login and session handling |
| Chatbot | Greetings, general queries and AI responses |
| RAG | Knowledge-base retrieval and relevant responses |
| Context Handling | Follow-up questions and conversation history |
| Troubleshooting | Wi-Fi and software troubleshooting |
| Ticket Management | Creation, status, priority and category updates |
| Dashboard | Statistics and ticket information |
| Persistence | Conversation and ticket data retention |
| Error Handling | Backend and AI service failures |

---

## 🚀 Future Enhancements

Potential improvements include:

- Admin dashboard for managing users and tickets.
- Knowledge-base document upload and automatic indexing.
- Support-agent assignment and management.
- Ticket SLA monitoring and escalation.
- Advanced analytics and reporting.
- User feedback and AI response evaluation.
- More comprehensive automated testing.
- Integration with external support platforms.

---

## 👥 Contributors

**Tanvi Lekshmi RM**  
B.Tech Computer Science and Engineering  
Bennett University

**Anmol Malhotra**  
B.Tech Computer Science and Engineering  
Bennett University

---

## 📌 Conclusion

The AI-Based Helpdesk System demonstrates how Generative AI and Retrieval-Augmented Generation can be integrated with a conventional helpdesk workflow.

By combining conversational AI, semantic knowledge retrieval, contextual troubleshooting and structured ticket management, the project aims to make technical support more accessible, efficient and organised.

---

**Built with React, FastAPI, PostgreSQL and Generative AI.**
