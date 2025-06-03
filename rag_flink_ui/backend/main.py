"""
Main FastAPI application for the RAG Flink UI backend.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Dict, List
import json
from datetime import datetime
from .mock_api import mock_service
from .services.kafka_service import get_kafka_service
import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get port from environment variable or use default
PORT = int(os.getenv("PORT", 8080))

# Log critical environment variables (without exposing sensitive data)
logger.info(f"KAFKA_BOOTSTRAP_SERVERS: {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
logger.info(f"SCHEMA_REGISTRY_URL: {os.getenv('SCHEMA_REGISTRY_URL')}")
logger.info(f"KAFKA_API_KEY: {'set' if os.getenv('KAFKA_API_KEY') else 'not set'}")
logger.info(f"SCHEMA_REGISTRY_API_KEY: {'set' if os.getenv('SCHEMA_REGISTRY_API_KEY') else 'not set'}")
logger.info(f"Using port: {PORT}")

app = FastAPI(title="RAG Flink UI Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("FastAPI está ouvindo e pronto para receber requisições.")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for chat communication."""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Produce message to Kafka
            try:
                kafka_service = get_kafka_service()
                kafka_service.produce_question(session_id, message["content"])
                logger.info(f"Question produced to Kafka for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to produce message to Kafka: {str(e)}")
                # Continue processing even if Kafka fails
                # The mock service will still provide a response
            
            # Get response from mock service
            response = mock_service.get_response(message["content"])
            
            await manager.send_message(json.dumps(response), session_id)
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "RAG Flink UI Backend is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Service healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

# Mount Streamlit's static files
# app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "frontend" / "static")), name="static") 