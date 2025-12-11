"""
Web Interface for Solairus Intelligence Report Generator
Simple, elegant FastAPI application for generating reports
"""

# Load environment variables from .env file BEFORE any other imports
from pathlib import Path

from dotenv import load_dotenv

# Find and load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try current working directory
    load_dotenv()

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from solairus_intelligence.cli import SolairusIntelligenceGenerator
from solairus_intelligence.utils.config import get_output_dir

# Session configuration
SESSION_TTL_MINUTES = 60  # Sessions expire after 1 hour
SESSION_CLEANUP_INTERVAL_SECONDS = 300  # Run cleanup every 5 minutes
MAX_SESSIONS = 100  # Maximum number of sessions to keep

logger = logging.getLogger(__name__)

# Track generation status per session (supports multiple concurrent users)
sessions: Dict[str, dict] = {}

# Global generator instance (initialized lazily)
generator: Optional[SolairusIntelligenceGenerator] = None


def get_generator() -> SolairusIntelligenceGenerator:
    """Get or create the generator instance"""
    global generator
    if generator is None:
        generator = SolairusIntelligenceGenerator()
    return generator


def cleanup_expired_sessions() -> int:
    """Remove expired sessions based on TTL"""
    now = datetime.now()
    expired_keys: List[str] = []

    for session_id, session_data in sessions.items():
        created_at_str = session_data.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_at_str)
            if now - created_at > timedelta(minutes=SESSION_TTL_MINUTES):
                expired_keys.append(session_id)
        except (ValueError, TypeError):
            # Invalid timestamp, mark for cleanup
            expired_keys.append(session_id)

    for key in expired_keys:
        del sessions[key]

    # Also enforce max sessions limit (keep most recent)
    if len(sessions) > MAX_SESSIONS:
        sorted_sessions = sorted(
            sessions.keys(), key=lambda k: sessions[k].get("created_at", ""), reverse=True
        )
        for key in sorted_sessions[MAX_SESSIONS:]:
            del sessions[key]

    return len(expired_keys)


async def periodic_cleanup() -> None:
    """Background task for periodic session cleanup"""
    while True:
        await asyncio.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)
        removed = cleanup_expired_sessions()
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired sessions")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown"""
    # Startup: start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    logger.info("Started session cleanup background task")

    yield

    # Shutdown: cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Stopped session cleanup background task")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Ergo Intelligence Report Generator",
    description="Generate monthly intelligence reports from ErgoMind Flashpoints Forum data",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files directory for logo and assets
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configure Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


class GenerationRequest(BaseModel):
    """Request model for report generation"""

    test_mode: bool = False


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_report(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start report generation - creates a unique session for each request"""
    # Create unique session ID for this generation request
    session_id = str(uuid.uuid4())

    # Initialize session status
    sessions[session_id] = {
        "in_progress": True,
        "last_run": None,
        "last_report": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
    }

    # Start generation in background
    background_tasks.add_task(run_generation, session_id, request.test_mode)

    return {
        "message": "Report generation started",
        "status": "processing",
        "session_id": session_id,
    }


async def run_generation(session_id: str, test_mode: bool):
    """Run the report generation process for a specific session"""
    try:
        gen = get_generator()
        filepath, status = await gen.generate_monthly_report(test_mode=test_mode)

        if status["success"]:
            sessions[session_id]["last_report"] = filepath
            sessions[session_id]["last_run"] = datetime.now().isoformat()
        else:
            sessions[session_id]["error"] = "Generation failed: " + ", ".join(status["errors"])

    except Exception as e:
        sessions[session_id]["error"] = str(e)
    finally:
        sessions[session_id]["in_progress"] = False


@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """Get generation status for a specific session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.get("/status")
async def get_global_status():
    """Get overall status (for backwards compatibility)"""
    # Return the most recent session status
    if not sessions:
        return {"in_progress": False, "last_run": None, "last_report": None, "error": None}

    # Get the most recent session
    recent_session = max(sessions.values(), key=lambda s: s.get("created_at", ""))
    return recent_session


@app.get("/download/{filename}")
async def download_report(filename: str):
    """Download a generated report"""
    output_dir = get_output_dir()
    filepath = output_dir / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def main():
    """Entry point for solairus-web CLI command"""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
