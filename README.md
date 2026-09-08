# AURA — AI Voice Intelligence Assistant

> **Research, explained.**

AURA is an AI-powered voice intelligence assistant that combines **Agentic AI, Retrieval-Augmented Generation (RAG), web research, document intelligence, OCR, SQL querying, conversational memory, and speech interfaces** into one application.

AURA can decide how to answer a user's request, retrieve information from the appropriate source, and return a conversational response through text or voice.

---

## 🚀 Live Demo

| Resource | Link |
|---|---|
| 🌐 **Live AURA Frontend** | https://aura-agentic-ai-assistant-1.onrender.com |
| ⚙️ **Live Backend API** | https://aura-agentic-ai-assistant.onrender.com |
| 📚 **Swagger API Documentation** | https://aura-agentic-ai-assistant.onrender.com/docs |
| 💻 **GitHub Repository** | https://github.com/Deekshitha-Gajjala/AURA-Agentic-AI-Assistant |

---

## ✨ What AURA Does

AURA is designed as a **multi-source AI assistant** rather than a simple chatbot.

Instead of sending every question directly to an LLM, AURA uses an agentic routing layer to determine the most appropriate path:

```text
                         ┌──────────────────────┐
                         │       User Query     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Agentic Router     │
                         └──────────┬───────────┘
                                    │
          ┌───────────────┬─────────┼──────────┬───────────────┐
          ▼               ▼         ▼          ▼               ▼
      GENERAL           WEB       PDF/RAG      SQL          OCR/Image
          │               │         │          │               │
          └───────────────┴─────────┼──────────┴───────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │      LLM Reasoning   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Conversational Answer│
                         └──────────┬───────────┘
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                       Text                Voice
```

---

## 🎯 Key Features

### 🤖 Agentic AI
- Intelligent query routing
- Separate processing paths for different information sources
- General conversational reasoning
- Tool-based agent workflow
- Context-aware responses

### 📄 Document Intelligence
- PDF upload
- Multiple PDF support
- PDF text extraction
- Document chunking
- Embedding generation
- FAISS vector search
- Chat with uploaded documents
- PDF summarization
- Quiz generation from PDFs
- Document management and deletion

### 🔎 RAG
AURA uses a Retrieval-Augmented Generation pipeline:

```text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embeddings
 ↓
FAISS Vector Store
 ↓
Semantic Retrieval
 ↓
Relevant Context
 ↓
LLM
 ↓
Grounded Answer
```

The embedding model is loaded lazily so that the backend can start without loading the model into memory immediately.

### 🌐 Web Research
- Current web search
- Research-oriented responses
- Source-aware information retrieval
- Useful for time-sensitive questions

### ▶️ YouTube Intelligence
- YouTube search
- Video identification
- Transcript retrieval
- Transcript-based question answering

### 🗄️ SQL Querying
- Natural-language questions can be routed to the SQL tool
- Structured data can be queried through the SQL workflow

### 🖼️ Image & OCR
- Image upload
- OCR-based text extraction
- Image analysis
- Vision-model powered responses

### 🎙️ Voice
- Speech-to-text using Groq Whisper
- Voice question answering
- Text-to-speech responses
- Audio response playback

### 🧠 Conversational Memory
- User-specific conversations
- Conversation history
- Multiple conversations
- Conversation retrieval
- Conversation deletion
- Context from previous interactions

### 🔐 Authentication
- User registration
- Login
- JWT-based authentication
- Protected API endpoints
- User-specific data access

### 🎨 Frontend
- React + Vite
- Component-based architecture
- Authentication screens
- Chat interface
- PDF/document workflow
- Voice interaction
- Image interaction
- Conversation management

---

## 🧩 Technology Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- Fetch API

### Backend

- Python
- FastAPI
- Uvicorn
- REST APIs
- JWT authentication

### AI / GenAI

- Groq API
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`
- `qwen/qwen3.6-27b`
- Groq Whisper
- Groq Orpheus TTS

### RAG / Document Processing

- Sentence Transformers
- `all-MiniLM-L6-v2`
- FAISS
- PyPDF
- PDF chunking
- Semantic search

### Vision / OCR

- Pillow
- Tesseract OCR
- Vision LLM

### Data / Storage

- SQLite
- FAISS indexes
- Local document storage

### External APIs

- Groq
- YouTube Data API
- YouTube Transcript API
- Web search through the AI/search workflow

### Deployment

- Render Static Site — frontend
- Render Web Service — backend
- GitHub — source control

---

## 🏗️ Project Architecture

```text
AURA-Agentic-AI-Assistant/
│
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── router.py
│   ├── llm.py
│   │
│   ├── auth.py
│   │
│   ├── tools/
│   │   ├── pdf_tool.py
│   │   ├── web_search.py
│   │   ├── youtube_tool.py
│   │   ├── stt_tool.py
│   │   ├── tts_tool.py
│   │   └── ...
│   │
│   ├── database/
│   │   ├── auth_db.py
│   │   └── memory_db.py
│   │
│   ├── uploads/
│   ├── vectorstore/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🔄 Agent Routing

AURA's router determines which capability should process a query.

```text
User Query
    │
    ▼
Router
    │
    ├── GENERAL ──→ General LLM response
    │
    ├── WEB ──────→ Web search → LLM
    │
    ├── YOUTUBE ──→ YouTube search/transcript → LLM
    │
    ├── PDF ──────→ FAISS retrieval → LLM
    │
    ├── SQL ──────→ SQL database → LLM
    │
    └── OCR ──────→ Image/OCR processing → Vision LLM
```

This avoids treating every request as the same type of problem.

---

## 📚 RAG Pipeline

When a user uploads a PDF:

### 1. Upload

The PDF is received by the FastAPI backend.

### 2. Text extraction

Text is extracted page-by-page.

### 3. Chunking

The extracted content is divided into smaller chunks suitable for semantic retrieval.

### 4. Embedding

Each chunk is converted into a vector using:

```text
all-MiniLM-L6-v2
```

### 5. Vector storage

Embeddings are stored in a FAISS index.

### 6. Retrieval

When the user asks a question about the PDF, the question is embedded and semantically matched against the document chunks.

### 7. Generation

The most relevant context is supplied to the LLM.

### 8. Response

AURA generates an answer based on the retrieved document context.

---

## 🎙️ Voice Pipeline

```text
Microphone
    ↓
Audio File
    ↓
Groq Whisper
    ↓
Speech → Text
    ↓
AURA Agent
    ↓
LLM Response
    ↓
Groq Orpheus TTS
    ↓
Audio Response
    ↓
User
```

---

## 🔐 Authentication Flow

```text
Register
   ↓
User stored securely
   ↓
Login
   ↓
JWT access token
   ↓
Token stored by frontend
   ↓
Authorization header
   ↓
Protected FastAPI endpoint
```

Protected requests use:

```http
Authorization: Bearer <token>
```

Passwords are not stored as plain text.

---

## 🔌 Important API Endpoints

The complete interactive API documentation is available here:

**Swagger UI:**  
https://aura-agentic-ai-assistant.onrender.com/docs

### Core

```text
GET  /
GET  /health
POST /ask
```

### Authentication

```text
POST /register
POST /login
```

### Documents

```text
POST   /upload-pdf
GET    /documents
DELETE /documents/{document_id}
```

### Conversations

```text
POST   /conversations
GET    /conversations
GET    /conversations/{conversation_id}
DELETE /conversations/{conversation_id}
DELETE /conversations
```

### Chat History

```text
GET    /history
DELETE /history/{chat_id}
DELETE /history
```

### Image / OCR

```text
POST /ask-image
```

### Voice

```text
POST /transcribe
POST /voice-ask
POST /speak
```

### PDF utilities

```text
POST /summarize-pdf
POST /generate-quiz
```

---

## 💻 Run Locally

### Prerequisites

- Python 3.12+
- Node.js
- npm
- Git
- Tesseract OCR
- API keys for the external services used by the application

---

### 1. Clone the repository

```bash
git clone https://github.com/Deekshitha-Gajjala/AURA-Agentic-AI-Assistant.git
cd AURA-Agentic-AI-Assistant
```

---

### 2. Backend setup

```bash
cd backend
python -m venv .venv
```

Activate the environment.

#### Windows

```bash
.venv\Scripts\activate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 3. Backend environment variables

Create:

```text
backend/.env
```

Example:

```env
GROQ_API_KEY=your_groq_api_key
YOUTUBE_API_KEY=your_youtube_api_key
AURA_SECRET_KEY=your_long_random_secret
```

**Never commit `.env` or real API keys to GitHub.**

---

### 4. Start the backend

From the `backend` directory:

```bash
uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

### 5. Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
```

Create:

```text
frontend/.env
```

For local development:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start Vite:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## ☁️ Deployment

AURA is deployed as two services on Render.

### Frontend

```text
Platform: Render Static Site
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

Production environment variable:

```env
VITE_API_BASE_URL=https://aura-agentic-ai-assistant.onrender.com
```

Live frontend:

https://aura-agentic-ai-assistant-1.onrender.com

### Backend

```text
Platform: Render Web Service
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Live backend:

https://aura-agentic-ai-assistant.onrender.com

Swagger:

https://aura-agentic-ai-assistant.onrender.com/docs

---

## 🛡️ Security

The project follows several basic security practices:

- JWT authentication
- Password hashing
- Environment variables for secrets
- Protected API endpoints
- User-scoped conversations
- User-scoped document access
- No API keys in frontend source code
- `.env` excluded from version control

For production environments, additional controls such as managed databases, object storage, rate limiting, secret management, and stronger observability should be considered.

---

## ⚠️ Deployment Notes

The current deployment uses Render and local application storage for some data.

For a production-scale deployment, consider:

- PostgreSQL instead of SQLite
- Object storage for uploaded PDFs/images
- Persistent vector storage
- Redis for caching/background tasks
- Dedicated worker services for expensive document processing
- Centralized logging
- Rate limiting
- Monitoring and alerting

Render free services can sleep when inactive and local filesystem data should not be treated as durable production storage.

---

## 🧪 Testing

The backend was tested through FastAPI Swagger UI, including:

- Health check
- User registration
- User login
- JWT authorization
- General `/ask`
- PDF upload
- PDF-based RAG queries
- Voice/TTS endpoints
- Deployed backend availability

The deployed frontend was also built successfully as a Vite production application.

---

## 📈 Future Improvements

Potential next improvements include:

- Streaming LLM responses
- Better citation presentation
- Persistent cloud vector database
- PostgreSQL migration
- Cloud object storage
- Background document processing
- More advanced agent planning
- Multi-agent collaboration
- Improved voice conversation latency
- More robust observability
- Automated tests and CI/CD
- Custom AURA favicon/branding
- Custom domain

---

## 👩‍💻 Author

**Deekshitha Gajjala**

Computer Science & Engineering — Data Science

### Links

- GitHub: https://github.com/Deekshitha-Gajjala
- AURA Repository: https://github.com/Deekshitha-Gajjala/AURA-Agentic-AI-Assistant
- Live AURA: https://aura-agentic-ai-assistant-1.onrender.com
- Backend API: https://aura-agentic-ai-assistant.onrender.com
- Swagger Docs: https://aura-agentic-ai-assistant.onrender.com/docs

---

## 📄 License

This project is intended as a personal portfolio and learning project.

Add an explicit open-source license to the repository if you want others to legally reuse, modify, and distribute the code.

---

## ⭐ Acknowledgements

Built using the ecosystem around:

- FastAPI
- React
- Vite
- Groq
- Sentence Transformers
- FAISS
- PyPDF
- Tesseract OCR
- YouTube APIs
- Render

---

<p align="center">
  <strong>AURA — AI Unified Research Assistant</strong><br>
  <em>Research, explained.</em>
</p>
