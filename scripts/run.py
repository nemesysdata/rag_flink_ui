"""
Script to run both the frontend and backend services.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_services():
    """Run both frontend and backend services."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Start the backend
    backend_cmd = [
        "uvicorn",
        "rag_flink_ui.backend.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
    ]

    # Start the frontend
    frontend_cmd = [
        "streamlit",
        "run",
        str(project_root / "rag_flink_ui" / "frontend" / "app.py"),
        "--server.port",
        "8501"
    ]

    try:
        # Start backend in a separate process
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Start frontend in a separate process
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print("Services started successfully!")
        print("Backend running at: http://localhost:8000")
        print("Frontend running at: http://localhost:8501")

        # Wait for both processes
        backend_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        print("\nShutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    run_services() 