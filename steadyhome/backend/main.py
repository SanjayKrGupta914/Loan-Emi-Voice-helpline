"""
SteadyHome – AI-Powered Loan EMI Voice Helpline
Main FastAPI Application Entrypoint
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from app.core.config import settings
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.core.auth import admin_guard
from database.schema import init_db
from app.services import gemini, supabase_sync

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent AI-powered voice helpline and customer support system for SteadyHome home loans.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local development and web speech client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database tables exist
init_db()

# Mount API router
app.include_router(auth_router, prefix="/api")
app.include_router(api_router, prefix="/api", dependencies=[Depends(admin_guard)])

# Mount frontend static files
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))
if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

@app.get("/api/health")
def health_check():
    return {
        "institution": "SteadyHome Home Loans",
        "system": "AI-Powered Loan EMI Voice Helpline",
        "status": "OPERATIONAL",
        "simulated_clock": settings.CURRENT_SIMULATED_NOW,
        "api_docs": "/docs",
        "demo_mode": True,
        "gemini_enabled": gemini.is_enabled(),
        "supabase_enabled": supabase_sync.is_enabled()
    }

@app.get("/")
def serve_root(request: Request):
    accept = request.headers.get("accept", "")
    index_file = os.path.join(frontend_dist, "index.html")
    # If client explicitly asks for application/json without text/html
    if "application/json" in accept and "text/html" not in accept:
        return health_check()
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return health_check()

# SPA catch-all for direct links or refreshes
@app.get("/{full_path:path}")
def catch_all(request: Request, full_path: str):
    if full_path.startswith("api") or full_path in ["docs", "redoc", "openapi.json", "assets"]:
        raise HTTPException(status_code=404, detail="Not Found")
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
