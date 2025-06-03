"""
Script to run the application.
"""

import subprocess
import sys
import os
from pathlib import Path
from loguru import logger

def get_port() -> int:
    """Get the port from environment variable or use default."""
    return int(os.getenv("PORT", "8080"))

def run_service():
    """Run the application service."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Get port from environment
    port = get_port()

    logger.info(f"Iniciando backend na porta {port}...")

    # Caminho absoluto para o uvicorn dentro do virtualenv
    uvicorn_path = str(project_root / ".venv" / "bin" / "uvicorn")

    # Start the backend
    backend_cmd = [
        uvicorn_path,
        "rag_flink_ui.backend.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--reload" if os.getenv("ENVIRONMENT") == "development" else None
    ]
    # Remove None values
    backend_cmd = [cmd for cmd in backend_cmd if cmd is not None]

    try:
        # Start backend process
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        logger.info(f"Service started successfully! Application running at: http://localhost:{port}")

        # Wait for process
        backend_process.wait()

    except Exception as e:
        logger.exception(f"Erro ao iniciar o backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_service() 