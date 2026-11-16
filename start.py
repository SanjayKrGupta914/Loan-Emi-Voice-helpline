#!/usr/bin/env python3
"""
SteadyHome – AI-Powered Loan EMI Voice Helpline
Unified One-Click Python Launcher
Combines Frontend, Backend, Database, and Voice Engine on http://localhost:8000
"""

import os
import sys
import time
import subprocess
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(BASE_DIR, "steadyhome")):
    STEADYHOME_DIR = os.path.join(BASE_DIR, "steadyhome")
else:
    STEADYHOME_DIR = BASE_DIR

BACKEND_DIR = os.path.join(STEADYHOME_DIR, "backend")
DB_FILE = os.path.join(STEADYHOME_DIR, "steadyhome.db")
DIST_DIR = os.path.join(STEADYHOME_DIR, "frontend", "dist")

def main():
    print("=" * 66)
    print("  SteadyHome – AI-Powered Loan EMI Voice Helpline")
    print("  Unified Localhost Hosting Launcher")
    print("=" * 66)

    # 1. Ensure database exists
    if not os.path.exists(DB_FILE):
        print("[1/3] Seeding SQLite database with 25+ fictional loan scenarios...")
        subprocess.run([sys.executable, "database/seed.py"], cwd=STEADYHOME_DIR, check=True)
    else:
        print("[1/3] Database ready: steadyhome.db")

    # 2. Ensure frontend dist exists
    if not os.path.exists(DIST_DIR):
        print("[2/3] Building frontend bundle...")
        subprocess.run(["npm", "run", "build"], cwd=os.path.join(STEADYHOME_DIR, "frontend"), check=True)
    else:
        print("[2/3] Frontend bundle ready in frontend/dist")

    # 3. Print URLs
    print("[3/3] Starting Unified Server on http://localhost:8000 ...")
    print("-" * 66)
    print("  🌐 Unified Application Link:  http://localhost:8000")
    print("  📖 Interactive Swagger Docs:  http://localhost:8000/docs")
    print("  🏥 API Health Endpoint:       http://localhost:8000/api/health")
    print("-" * 66)
    print("Opening browser automatically... (Press Ctrl+C to stop)\n")

    # Open browser in a separate thread/timer
    def open_browser():
        time.sleep(1.2)
        webbrowser.open("http://localhost:8000")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch uvicorn server
    sys.path.insert(0, BACKEND_DIR)
    import uvicorn
    uvicorn.run("main:app", app_dir=BACKEND_DIR, host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()

