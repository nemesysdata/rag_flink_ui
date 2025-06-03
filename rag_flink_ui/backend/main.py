"""
Main FastAPI application for the RAG Flink UI backend.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import streamlit as st
import streamlit.web.bootstrap
import streamlit.web.server.server
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

# Log critical environment variables (without exposing sensitive data)
logger.info(f"KAFKA_BOOTSTRAP_SERVERS: {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
logger.info(f"SCHEMA_REGISTRY_URL: {os.getenv('SCHEMA_REGISTRY_URL')}")
logger.info(f"KAFKA_USERNAME: {'set' if os.getenv('KAFKA_USERNAME') else 'not set'}")
logger.info(f"SCHEMA_REGISTRY_USER: {'set' if os.getenv('SCHEMA_REGISTRY_USER') else 'not set'}")

app = FastAPI(title="RAG Flink UI Backend")

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

# Initialize Streamlit
def init_streamlit():
    """Initialize Streamlit in the background."""
    sys.argv = ["streamlit", "run", str(Path(__file__).parent.parent / "frontend" / "app.py")]
    streamlit.web.bootstrap.run(
        str(Path(__file__).parent.parent / "frontend" / "app.py"),
        "",
        [],
        flag_options={},
    )

@app.on_event("startup")
async def startup_event():
    """Start Streamlit in the background on startup."""
    logger.info("FastAPI startup event: inicializando Streamlit em background...")
    asyncio.create_task(asyncio.to_thread(init_streamlit))
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

# Mount Streamlit's static files
# app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "frontend" / "static")), name="static") 