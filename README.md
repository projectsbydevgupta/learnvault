# LEARNVAULT — Personal AI Learning Assistant

[![Live Web App](https://img.shields.io/badge/Live%20App-Vercel-black?style=flat-square&logo=vercel&logoColor=white)](https://learnvault-sandy.vercel.app)
[![Live Backend](https://img.shields.io/badge/Live%20Backend-Render-46E3B7?style=flat-square&logo=render&logoColor=white)](https://learnvault-vcxh.onrender.com)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger%20UI-85EA2D?style=flat-square&logo=swagger&logoColor=black)](https://learnvault-vcxh.onrender.com/docs)
[![Test Suite](https://img.shields.io/badge/Tests-273%20Passed%20(100%25)-brightgreen?style=flat-square&logo=pytest&logoColor=white)](backend/tests)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

An agentic, full-stack learning platform that transforms dense lecture notes, textbooks, and research papers into an interactive, grounded study partner. Students upload course PDFs, receive natural-language explanations with exact page-level citations, and master weak subjects through deterministic diagnostic quizzes.

---

## Live Deployments & Endpoints

| Component | Platform | Status | Live Link |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | Vercel | 🟢 Operational | [https://learnvault-sandy.vercel.app](https://learnvault-sandy.vercel.app) |
| **Backend API & Engine** | Render | 🟢 Operational | [https://learnvault-vcxh.onrender.com](https://learnvault-vcxh.onrender.com) |
| **Interactive API Docs** | FastAPI Swagger | 🟢 Available | [https://learnvault-vcxh.onrender.com/docs](https://learnvault-vcxh.onrender.com/docs) |
| **OpenAPI ReDoc** | FastAPI ReDoc | 🟢 Available | [https://learnvault-vcxh.onrender.com/redoc](https://learnvault-vcxh.onrender.com/redoc) |

> 💡 **Architecture Note:** The live Render service hosts the **FastAPI Backend & Agent Pipeline**. Opening the root URL in a browser displays the live API Status Dashboard; API clients and curl receive structured JSON. The web user interface is built with **Next.js** in `frontend/`.

---

## System Architecture

```text
               ┌────────────────────────────────────────────────────────┐
               │                  Student PDF Document                  │
               └───────────────────────────┬────────────────────────────┘
                                           │
                    [PyMuPDF Extraction & Scanned Page Detection]
                                           │
                    [Text Cleaning & Hierarchical Chunking]
                    ├─ Parent Chunks: 2,800 chars (broad contextual window)
                    └─ Child Chunks:    800 chars (dense semantic retrieval)
                                           │
                    [FastEmbed ONNX Embeddings (all-MiniLM-L6-v2, 384-dim)]
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
              [Qdrant Vector Database]           [Supabase Object Storage]
              (Filtered by user_id & doc_id)     (Private persistent PDF cache)
                         │
┌────────────────────────┴──────────────────────────────────────────────────────┐
│                    FOUR BOUNDED AGENTS & CORE RAG ENGINE                      │
│                                                                               │
│  1. Query Router & Rewriter Agent (Groq / Llama 3.3)                         │
│     ├─ Fast-path regex detects greetings (skips LLM overhead)                │
│     └─ Rewrites follow-up queries using chat history into standalone search   │
│                                                                               │
│  2. Corrective RAG (CRAG) Agent (Groq / Llama 3.3)                            │
│     ├─ Evaluates cross-encoder retrieval relevance (threshold: 0.35)          │
│     └─ Performs max 1 query reformulation retry; refuses gracefully on failure│
│                                                                               │
│  3. Hallucination & Citation Grader (Groq / Llama 3.3)                        │
│     ├─ Cross-verifies draft answer claims against retrieved parent evidence   │
│     ├─ Max 1 regeneration retry; returns safe refusal on double failure       │
│     └─ Streams only verified tokens via Server-Sent Events (SSE)              │
│                                                                               │
│  4. Adaptive Diagnostic Quiz Agent (Groq + Deterministic Engine)              │
│     ├─ Generates grounded 4-option MCQs directly from uploaded student notes  │
│     ├─ Deterministic grading: 100% backend equality check (no LLM bias)       │
│     └─ Weak topic diagnostic: flags <60% accuracy with targeted practice CTAs│
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities

- **Resilient Document Pipeline**:
  - Drag-and-drop PDF ingestion (up to 20 MB) with automatic scanned-page detection.
  - Hybrid storage: Render container handles processing; Supabase Storage provides persistent private object storage across container reboots.
  - Hierarchical parent-child chunking preserves high-resolution context for generation while enabling dense child matching.
  - Cascading deletion across all storage tiers (Supabase, Qdrant, PostgreSQL/SQLite).

- **Grounded Conversational RAG**:
  - Authenticated Qdrant vector retrieval strictly isolated by `user_id` and `document_id`.
  - Local FlashRank cross-encoder reranking (`ms-marco-TinyBERT-L-2-v2`).
  - Strict grounding: answers only from uploaded context with clickable `[Source N | Page X]` citations.
  - Real-time Server-Sent Events (SSE) token streaming.

- **Adaptive Diagnostic Quizzes**:
  - On-demand 4-option MCQ generation tailored to student materials or weak topics.
  - 100% deterministic auto-grading executed by backend code.
  - Clear score bands: Strong (80–100%), Good (60–79%), Weak (<60%).
  - Post-quiz review filter: "Show Incorrect Answers Only" for rapid revision.

- **Enterprise Security & Clean UX**:
  - Google Identity Services (GIS) OAuth + stateless guest sessions.
  - Cross-user data isolation across database queries and vector filters.
  - 3 persistable themes: **Light ☀️**, **Dark 🌙**, and **Green 🌿** with zero theme flash.
  - 100% accessible UI with consistent edit/rename iconography and keyboard navigation.

---

## Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 | Responsive UI, SSE token streaming, client state |
| **Backend** | FastAPI, Python 3.10+, Pydantic v2, SQLAlchemy | Async REST APIs, SSE streaming, authentication |
| **Vector Engine** | Qdrant (Cloud / Local) | 384-dimensional dense semantic vector retrieval |
| **Relational DB** | PostgreSQL (Neon) / SQLite fallback | User profiles, document metadata, chat history, quizzes |
| **Object Storage** | Supabase Storage (Private) | Persistent PDF storage across ephemeral container restarts |
| **Embeddings** | FastEmbed (ONNX Runtime, `all-MiniLM-L6-v2`) | High-speed local CPU embeddings (no PyTorch overhead) |
| **Reranker** | FlashRank (`ms-marco-TinyBERT-L-2-v2`) | Local cross-encoder reranker (no external API calls) |
| **LLM Inference** | Groq API (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`) | Fast, low-latency reasoning for bounded agents |
| **PDF Extraction** | PyMuPDF (`fitz`) | High-precision text and layout extraction |

---

## Quickstart (Local Development)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- *(Optional)* Docker Desktop for local PostgreSQL & Qdrant containers

> **Zero-Config Fallback:** If Docker or PostgreSQL is not running locally, LearnVault automatically boots with an embedded SQLite database (`data/ai_learning_local.db`) and local Qdrant storage (`data/qdrant_local/`).

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/projectsbydevgupta/learnvault.git
cd learnvault

# Create your local environment configuration
cp .env.example .env     # macOS / Linux
Copy-Item .env.example .env  # Windows PowerShell
```
Configure your Groq API key in `.env`:
```env
RAG_API_KEY=gsk_your_groq_api_key_here
```

### 3. Start Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
.\.venv\Scripts\Activate.ps1    # Windows

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API runs at `http://127.0.0.1:8000` (Docs at `http://127.0.0.1:8000/docs`).

### 4. Start Frontend
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Production Deployment

### Backend Deployment (Render)
1. Create a **Web Service** on [Render](https://render.com) connected to your repository.
2. Select **Docker** environment (uses `backend/Dockerfile`) with Root Directory set to `backend`.
3. Set environment variables in the Render Dashboard (from `.env.example`):
   - `DATABASE_URL` (Neon PostgreSQL)
   - `QDRANT_URL` & `QDRANT_API_KEY` (Qdrant Cloud)
   - `RAG_API_KEY`, `ROUTER_API_KEY`, `CRAG_API_KEY`, `GRADER_API_KEY`, `QUIZ_API_KEY`
   - `SUPABASE_URL` & `SUPABASE_SECRET_KEY` (Private Bucket `learnvault-documents`)
   - `FRONTEND_URL` (Your Vercel deployment URL)

### Frontend Deployment (Vercel)
1. Import repository on [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `https://learnvault-vcxh.onrender.com`
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = `your_google_client_id.apps.googleusercontent.com`
4. Click **Deploy**.

---

## Verification & Quality Assurance

- **Backend Automated Tests**: 273 tests executed via `pytest` (259 passed, 14 skipped for optional local Docker containers, **0 failures**).
- **Frontend Type Safety**: `npx tsc --noEmit` passed with 0 errors.
- **Production Build**: 10/10 Next.js routes statically prerendered with Turbopack.
- **Data Isolation**: All database operations and Qdrant queries enforce strict `user_id == current_user` validation.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
