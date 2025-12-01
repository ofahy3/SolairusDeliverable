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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from datetime import datetime
import json

from solairus_intelligence.cli import SolairusIntelligenceGenerator
from solairus_intelligence.utils.config import get_output_dir

# Create FastAPI app
app = FastAPI(
    title="Solairus Intelligence Report Generator",
    description="Generate monthly intelligence reports from ErgoMind Flashpoints Forum data",
    version="1.0.0"
)

# Global generator instance
generator = SolairusIntelligenceGenerator()

# Track generation status
generation_status = {
    "in_progress": False,
    "last_run": None,
    "last_report": None,
    "error": None
}

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
    <title>Solairus Intelligence Report Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1B2946 0%, #0271C3 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
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
            border-bottom: 2px solid #f0f0f0;
        }
        
        .logo-icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #0271C3 0%, #94B0C9 100%);
            border-radius: 50%;
            margin-right: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 24px;
        }
        
        h1 {
            color: #1B2946;
            font-size: 24px;
            font-weight: 600;
        }
        
        .subtitle {
            color: #666;
            margin-top: 5px;
            font-size: 14px;
        }
        
        .form-section {
            margin: 30px 0;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #1B2946;
            font-weight: 500;
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
        }
        
        .checkbox-label {
            cursor: pointer;
            user-select: none;
        }
        
        .generate-btn {
            background: linear-gradient(135deg, #0271C3 0%, #1B2946 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .generate-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(2,113,195,0.3);
        }
        
        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        
        .status-section.active {
            display: block;
        }
        
        .status-title {
            font-weight: 600;
            color: #1B2946;
            margin-bottom: 10px;
        }
        
        .status-message {
            color: #666;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0271C3 0%, #94B0C9 100%);
            animation: progress 2s ease-in-out infinite;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        
        .success-message {
            color: #28a745;
            font-weight: 500;
        }
        
        .error-message {
            color: #dc3545;
            font-weight: 500;
        }
        
        .download-link {
            display: inline-block;
            margin-top: 15px;
            padding: 10px 20px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .download-link:hover {
            background: #218838;
            transform: translateY(-1px);
        }
        
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #0271C3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .info-box p {
            color: #1B2946;
            font-size: 14px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <div class="logo-icon">S</div>
            <div>
                <h1>Solairus Intelligence Report</h1>
                <div class="subtitle">Powered by ErgoMind Flashpoints Forum</div>
            </div>
        </div>
        
        <div class="info-box">
            <p>Generate a comprehensive monthly intelligence report analyzing geopolitical and economic developments relevant to Solairus Aviation and its clients.</p>
        </div>
        
        <div class="form-section">
            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" id="testMode" name="testMode">
                    <label for="testMode" class="checkbox-label">Test Mode (Limited queries for faster generation)</label>
                </div>
            </div>
            
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
        
        async function generateReport() {
            const button = document.querySelector('.generate-btn');
            const statusSection = document.getElementById('status');
            const statusMessage = document.getElementById('statusMessage');
            const progressBar = document.getElementById('progressBar');
            const downloadLink = document.getElementById('downloadLink');
            const testMode = document.getElementById('testMode').checked;
            
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
                        test_mode: testMode,
                        focus_areas: []
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Start checking status
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
            try {
                const response = await fetch('/status');
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
                        downloadLink.textContent = `Download Report (${filename})`;
                        downloadLink.style.display = 'inline-block';
                    } else if (data.error) {
                        statusMessage.textContent = '❌ ' + data.error;
                        statusMessage.className = 'status-message error-message';
                    }
                    
                    button.disabled = false;
                    button.textContent = 'Generate Intelligence Report';
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
    """Start report generation"""
    global generation_status
    
    if generation_status["in_progress"]:
        raise HTTPException(status_code=400, detail="Generation already in progress")
    
    generation_status["in_progress"] = True
    generation_status["error"] = None
    
    # Start generation in background
    background_tasks.add_task(run_generation, request.test_mode, request.focus_areas)
    
    return {"message": "Report generation started", "status": "processing"}

async def run_generation(test_mode: bool, focus_areas: Optional[List[str]]):
    """Run the report generation process"""
    global generation_status
    
    try:
        filepath, status = await generator.generate_monthly_report(
            focus_areas=focus_areas,
            test_mode=test_mode
        )
        
        if status['success']:
            generation_status["last_report"] = filepath
            generation_status["last_run"] = datetime.now().isoformat()
        else:
            generation_status["error"] = "Generation failed: " + ", ".join(status['errors'])
            
    except Exception as e:
        generation_status["error"] = str(e)
    finally:
        generation_status["in_progress"] = False

@app.get("/status")
async def get_status():
    """Get current generation status"""
    return generation_status

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
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
