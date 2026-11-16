#!/usr/bin/env bash
set -e

# SteadyHome – AI-Powered Loan EMI Voice Helpline
# Unified One-Click Launcher for Local Hosting

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -d "$SCRIPT_DIR/steadyhome" ]; then
    PROJECT_DIR="$SCRIPT_DIR/steadyhome"
else
    PROJECT_DIR="$SCRIPT_DIR"
fi

echo "=================================================================="
echo "  SteadyHome – AI-Powered Loan EMI Voice Helpline"
echo "  Unified Localhost Hosting Launcher"
echo "=================================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Ensure database exists and is seeded
if [ ! -f "$PROJECT_DIR/steadyhome.db" ]; then
    echo "[1/3] Initializing and seeding SQLite core banking database..."
    (cd "$PROJECT_DIR" && python3 database/seed.py)
else
    echo "[1/3] Database ready: steadyhome.db"
fi

# Ensure frontend build exists
if [ ! -d "$PROJECT_DIR/frontend/dist" ]; then
    echo "[2/3] Building unified React frontend..."
    (cd "$PROJECT_DIR/frontend" && npm run build)
else
    echo "[2/3] Frontend build ready: frontend/dist"
fi

echo "[3/3] Starting Unified Server on http://localhost:8000 ..."
echo ""
echo "------------------------------------------------------------------"
echo "  🌐 Access the Complete Application: http://localhost:8000"
echo "  📖 Interactive API Documentation:   http://localhost:8000/docs"
echo "  🏥 Health Check Endpoint:           http://localhost:8000/api/health"
echo "------------------------------------------------------------------"
echo "Press Ctrl+C to stop the server."
echo ""

# Automatically open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    (sleep 1.5 && open "http://localhost:8000") &
elif command -v xdg-open &> /dev/null; then
    (sleep 1.5 && xdg-open "http://localhost:8000") &
fi

# Launch FastAPI / Uvicorn server directly
cd "$PROJECT_DIR/backend"
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

