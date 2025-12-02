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

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from solairus_intelligence.cli import SolairusIntelligenceGenerator
from solairus_intelligence.utils.config import get_output_dir

# Create FastAPI app
app = FastAPI(
    title="Ergo Intelligence Report Generator",
    description="Generate monthly intelligence reports from ErgoMind Flashpoints Forum data",
    version="1.0.0",
)

# Mount static files directory for logo and assets
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global generator instance
generator = SolairusIntelligenceGenerator()

# Track generation status per session (supports multiple concurrent users)
sessions: Dict[str, dict] = {}


class GenerationRequest(BaseModel):
    """Request model for report generation"""

    test_mode: bool = False
    focus_areas: Optional[List[str]] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ergo Intelligence Report Generator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --colorBlack: #000000;
            --colorWhite: #FFFFFF;
            --colorP1: #1B2946;
            --colorP2: #0271C3;
            --colorP3: #94B0C9;
            --colorP4: var(--colorWhite);
            --colorS1: #E87449;
            --colorS2: #00DDCC;
            --colorS3: #131F33;
            --colorT1: #C4613C;
            --colorT2: #E5EAEF;
            --colorT3: #01B9AB;
            --colorT4: #015DA2;
            --colorE1: #F2F6F9;
            --colorE2: #F3F6F8;
            --headingFontFamily: 'Plus Jakarta Sans', sans-serif;
            --bodyFontFamily: 'Plus Jakarta Sans', sans-serif;
            --light: 300;
            --regular: 400;
            --medium: 500;
            --semibold: 600;
            --bold: 700;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--bodyFontFamily);
            font-weight: var(--regular);
            background: linear-gradient(135deg, var(--colorP1) 0%, var(--colorP2) 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: var(--colorWhite);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }

        .logo {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--colorE2);
        }

        .logo-img {
            height: 50px;
            width: auto;
            margin-right: 15px;
        }

        h1 {
            font-family: var(--headingFontFamily);
            color: var(--colorP1);
            font-size: 24px;
            font-weight: var(--semibold);
        }

        .subtitle {
            color: var(--colorP3);
            margin-top: 5px;
            font-size: 14px;
            font-weight: var(--regular);
        }

        .form-section {
            margin: 30px 0;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            color: var(--colorP1);
            font-weight: var(--medium);
            margin-bottom: 8px;
            font-size: 14px;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
        }

        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin-right: 10px;
            cursor: pointer;
            accent-color: var(--colorP2);
        }

        .checkbox-label {
            cursor: pointer;
            user-select: none;
        }

        .generate-btn {
            background: linear-gradient(135deg, var(--colorS1) 0%, var(--colorT1) 100%);
            color: var(--colorWhite);
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-family: var(--bodyFontFamily);
            font-size: 16px;
            font-weight: var(--semibold);
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }

        .generate-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(232,116,73,0.3);
        }

        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .status-section {
            margin-top: 30px;
            padding: 20px;
            background: var(--colorE1);
            border-radius: 10px;
            display: none;
        }

        .status-section.active {
            display: block;
        }

        .status-title {
            font-family: var(--headingFontFamily);
            font-weight: var(--semibold);
            color: var(--colorP1);
            margin-bottom: 10px;
        }

        .status-message {
            color: var(--colorS3);
            font-size: 14px;
            line-height: 1.5;
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: var(--colorT2);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--colorS2) 0%, var(--colorT3) 100%);
            animation: progress 2s ease-in-out infinite;
        }

        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }

        .success-message {
            color: var(--colorT3);
            font-weight: var(--medium);
        }

        .error-message {
            color: var(--colorT1);
            font-weight: var(--medium);
        }

        .download-link {
            display: inline-block;
            margin-top: 15px;
            padding: 10px 20px;
            background: var(--colorS2);
            color: var(--colorS3);
            text-decoration: none;
            border-radius: 6px;
            font-weight: var(--semibold);
            transition: all 0.3s ease;
            max-width: 100%;
            box-sizing: border-box;
            word-wrap: break-word;
            overflow-wrap: break-word;
            text-align: center;
        }

        .download-link:hover {
            background: var(--colorT3);
            transform: translateY(-1px);
        }

        .info-box {
            background: var(--colorE1);
            border-left: 4px solid var(--colorP2);
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }

        .info-box p {
            color: var(--colorP1);
            font-size: 14px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="/static/images/ergo_logo.png" alt="Ergo Logo" class="logo-img">
            <div>
                <h1>Ergo Intelligence Report</h1>
                <div class="subtitle">Powered by ErgoMind</div>
            </div>
        </div>
        
        <div class="info-box">
            <p>Generate a comprehensive monthly intelligence report analyzing geopolitical and economic developments relevant to Solairus Aviation and its clients.</p>
        </div>
        
        <div class="form-section">
            <button class="generate-btn" onclick="generateReport()">
                Generate Intelligence Report
            </button>
        </div>
        
        <div id="status" class="status-section">
            <div class="status-title">Status</div>
            <div class="status-message" id="statusMessage">Initializing...</div>
            <div class="progress-bar" id="progressBar" style="display: none;">
                <div class="progress-fill"></div>
            </div>
            <a href="#" id="downloadLink" class="download-link" style="display: none;">Download Report</a>
        </div>
    </div>
    
    <script>
        let statusCheckInterval;
        let currentSessionId = null;

        async function generateReport() {
            const button = document.querySelector('.generate-btn');
            const statusSection = document.getElementById('status');
            const statusMessage = document.getElementById('statusMessage');
            const progressBar = document.getElementById('progressBar');
            const downloadLink = document.getElementById('downloadLink');

            // Disable button and show status
            button.disabled = true;
            button.textContent = 'Generating...';
            statusSection.classList.add('active');
            statusMessage.textContent = 'Starting intelligence gathering from ErgoMind...';
            statusMessage.className = 'status-message';
            progressBar.style.display = 'block';
            downloadLink.style.display = 'none';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        test_mode: false,
                        focus_areas: []
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Store session ID for status tracking
                    currentSessionId = data.session_id;
                    // Start checking status for this session
                    statusCheckInterval = setInterval(checkStatus, 2000);
                } else {
                    throw new Error(data.detail || 'Generation failed');
                }
            } catch (error) {
                statusMessage.textContent = 'Error: ' + error.message;
                statusMessage.className = 'status-message error-message';
                progressBar.style.display = 'none';
                button.disabled = false;
                button.textContent = 'Generate Intelligence Report';
            }
        }

        async function checkStatus() {
            if (!currentSessionId) return;

            try {
                const response = await fetch(`/status/${currentSessionId}`);
                const data = await response.json();

                const statusMessage = document.getElementById('statusMessage');
                const progressBar = document.getElementById('progressBar');
                const downloadLink = document.getElementById('downloadLink');
                const button = document.querySelector('.generate-btn');

                if (!data.in_progress) {
                    clearInterval(statusCheckInterval);
                    progressBar.style.display = 'none';

                    if (data.last_report) {
                        statusMessage.textContent = '✅ Report generated successfully!';
                        statusMessage.className = 'status-message success-message';

                        // Show download link
                        const filename = data.last_report.split('/').pop();
                        downloadLink.href = `/download/${filename}`;
                        downloadLink.textContent = 'Download Report';
                        downloadLink.style.display = 'inline-block';
                    } else if (data.error) {
                        statusMessage.textContent = '❌ ' + data.error;
                        statusMessage.className = 'status-message error-message';
                    }

                    button.disabled = false;
                    button.textContent = 'Generate Intelligence Report';
                    currentSessionId = null;
                } else {
                    statusMessage.textContent = 'Processing intelligence data...';
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


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
    background_tasks.add_task(run_generation, session_id, request.test_mode, request.focus_areas)

    return {
        "message": "Report generation started",
        "status": "processing",
        "session_id": session_id,
    }


async def run_generation(session_id: str, test_mode: bool, focus_areas: Optional[List[str]]):
    """Run the report generation process for a specific session"""
    try:
        filepath, status = await generator.generate_monthly_report(
            focus_areas=focus_areas, test_mode=test_mode
        )

        if status["success"]:
            sessions[session_id]["last_report"] = filepath
            sessions[session_id]["last_run"] = datetime.now().isoformat()
        else:
            sessions[session_id]["error"] = "Generation failed: " + ", ".join(status["errors"])

    except Exception as e:
        sessions[session_id]["error"] = str(e)
    finally:
        sessions[session_id]["in_progress"] = False

        # Clean up old sessions (keep last 50)
        if len(sessions) > 50:
            oldest_keys = sorted(sessions.keys(), key=lambda k: sessions[k].get("created_at", ""))[
                : len(sessions) - 50
            ]
            for key in oldest_keys:
                del sessions[key]


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
