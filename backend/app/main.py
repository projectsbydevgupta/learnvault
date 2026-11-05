"""
main.py

FastAPI application entry point.

On startup, creates all database tables that don't already exist.
Tables are never dropped on startup to protect existing data.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings
from app.db.base import Base
from app.db.database import engine
from app.api.auth import router as auth_router  # Day 7
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.quiz import router as quiz_router  # Day 6
# Import all models so Base.metadata.create_all() creates every table
from app.models import Document, Session, Message, Quiz, QuizAttempt, User  # noqa: F401


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — creating database tables if needed")
    Base.metadata.create_all(bind=engine)
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        if "sessions" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("sessions")]
            if "title" not in columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE sessions ADD COLUMN title VARCHAR(255);"))
                    conn.commit()
    except Exception as exc:
        logger.warning("Could not run title column migration: %s", exc)
    logger.info("Database tables ready")

    # Day 3: Ensure Qdrant collection and payload indexes exist
    try:
        from app.services.qdrant_service import ensure_collection, is_qdrant_available
        if is_qdrant_available():
            ensure_collection()
            logger.info("Qdrant collection and payload indexes ready")
        else:
            logger.warning(
                "Qdrant is not currently reachable; collection will be initialized when reachable"
            )
    except Exception as exc:
        logger.warning("Could not initialize Qdrant on startup: %s", exc)

    yield
    logger.info("Shutting down")



app = FastAPI(
    title="LearnVault API",
    description="Backend API for LearnVault — Personal AI Learning Assistant.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_allowed_origins() -> list[str]:
    """
    Construct the list of allowed CORS origins from settings.
    Ensures local development hosts are always permitted, while production
    origins (such as Vercel) can be supplied via CORS_ORIGINS or FRONTEND_URL.
    """
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if settings.CORS_ORIGINS:
        for item in settings.CORS_ORIGINS.split(","):
            cleaned = item.strip()
            if cleaned and cleaned not in origins:
                origins.append(cleaned)
    if settings.FRONTEND_URL:
        cleaned_frontend = settings.FRONTEND_URL.strip()
        if cleaned_frontend and cleaned_frontend not in origins:
            origins.append(cleaned_frontend)
    return origins


# Enable safe CORS for Next.js frontend (never wildcard with credentials in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)       # Day 7: /auth/login, /auth/me, /auth/status
app.include_router(documents_router)
app.include_router(chat_router)       # includes /chat, /chat/stream, /sessions, /sessions/{id}/messages
app.include_router(quiz_router)       # Day 6: /quiz/generate, /quiz/{id}, /quiz/{id}/submit, /quiz/history



@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {"status": "ok"}



API_LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LearnVault API — System Operational</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%236366f1'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg>">
    <style>
        :root {
            --bg: #090d16;
            --surface: #111827;
            --surface-hover: #1f2937;
            --border: #1f2937;
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.2);
            --emerald: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.15);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .container {
            max-width: 680px;
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 36px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: var(--emerald-glow);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 500;
            color: var(--emerald);
            margin-bottom: 20px;
        }
        .indicator {
            width: 8px;
            height: 8px;
            background: var(--emerald);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--emerald);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        h1 {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
        }
        p.subtitle {
            color: var(--text-secondary);
            font-size: 15px;
            line-height: 1.5;
            margin-bottom: 24px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
            margin-bottom: 28px;
        }
        .card {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding: 16px 20px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s ease;
        }
        .card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px var(--accent-glow);
        }
        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .card-desc {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .info-box {
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 10px;
            padding: 14px 18px;
            font-size: 13px;
            color: #c7d2fe;
            line-height: 1.5;
        }
        .info-box strong { color: #fff; }
        .footer {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="badge">
            <span class="indicator"></span>
            System Status: Operational
        </div>
        <h1>LearnVault Backend API</h1>
        <p class="subtitle">
            Agentic full-stack learning assistant powering lecture PDF extraction, hierarchical vector search, 4 bounded LLM agents, and adaptive diagnostic quizzes.
        </p>

        <div class="grid">
            <a href="https://learnvault-sandy.vercel.app" target="_blank" rel="noopener noreferrer" class="card" style="border-color: rgba(99, 102, 241, 0.4); background: rgba(99, 102, 241, 0.08);">
                <div class="card-title">
                    <span style="color: #a5b4fc;">Launch Web Application</span>
                    <span>&#8599;</span>
                </div>
                <div class="card-desc">Interactive student UI with PDF notes upload, RAG chat, and quizzes.</div>
            </a>
            <a href="/docs" class="card">
                <div class="card-title">
                    <span>Interactive API Docs</span>
                    <span>&rarr;</span>
                </div>
                <div class="card-desc">Explore and execute Swagger UI endpoints live in your browser.</div>
            </a>
            <a href="/health" class="card">
                <div class="card-title">
                    <span>Health Check Endpoint</span>
                    <span>&rarr;</span>
                </div>
                <div class="card-desc">Real-time health ping and system availability status.</div>
            </a>
            <a href="/redoc" class="card">
                <div class="card-title">
                    <span>ReDoc Specification</span>
                    <span>&rarr;</span>
                </div>
                <div class="card-desc">Clean, comprehensive OpenAPI schema reference.</div>
            </a>
            <a href="https://github.com/projectsbydevgupta/learnvault" target="_blank" rel="noopener noreferrer" class="card">
                <div class="card-title">
                    <span>GitHub Repository</span>
                    <span>&#8599;</span>
                </div>
                <div class="card-desc">Source code, bounded agent architecture, and documentation.</div>
            </a>
        </div>

        <div class="info-box">
            &#128161; <strong>Live Web App:</strong> Visit the official student web interface at <a href="https://learnvault-sandy.vercel.app" target="_blank" rel="noopener noreferrer" style="color: #fff; font-weight: 600; text-decoration: underline;">learnvault-sandy.vercel.app</a>.
        </div>

        <div class="footer">
            <span>Version: 1.0.0 (Production Ready)</span>
            <span>FastAPI &bull; Qdrant &bull; Neon PostgreSQL &bull; Groq</span>
        </div>
    </div>
</body>
</html>"""

@app.get("/", tags=["Health"])
def root(request: Request):
    """Root endpoint — serves interactive HTML portal to browsers and JSON to API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(content=API_LANDING_HTML)
    return {
        "message": "Personal AI Learning Assistant API",
        "name": "LearnVault API",
        "status": "operational",
        "version": "1.0.0",
        "frontend": "https://learnvault-sandy.vercel.app",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "repository": "https://github.com/projectsbydevgupta/learnvault",
    }
