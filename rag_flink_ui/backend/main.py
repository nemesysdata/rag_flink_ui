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
from .services.websocket_manager import WebSocketSessionManager
from .services.kafka_consumer import KafkaResponseConsumer
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

# Initialize WebSocket session manager
websocket_manager = WebSocketSessionManager()

# Initialize Kafka consumer
kafka_consumer = KafkaResponseConsumer(
    websocket_manager=websocket_manager,
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    schema_registry_url=os.getenv('SCHEMA_REGISTRY_URL')
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Kafka consumer...")
    asyncio.create_task(kafka_consumer.start())
    logger.info("FastAPI está ouvindo e pronto para receber requisições.")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    logger.info("Stopping Kafka consumer...")
    await kafka_consumer.stop()
    logger.info("Kafka consumer stopped.")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for chat communication."""
    try:
        # Register WebSocket session
        websocket_manager.register_session(session_id, websocket)
        await websocket.accept()
        
        while True:
            data = await websocket.receive_json()
            
            # Check if session can accept new question
            if not websocket_manager.can_accept_question(session_id):
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Please wait for the previous response'
                })
                continue
            
            # Mark session as waiting for response
            websocket_manager.set_waiting_response(session_id, data['content'])
            
            # Produce message to Kafka
            try:
                kafka_service = get_kafka_service()
                kafka_service.produce_question(session_id, data['content'])
                logger.info(f"Question produced to Kafka for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to produce message to Kafka: {str(e)}")
                # Clear waiting state on error
                websocket_manager.clear_waiting_response(session_id)
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Failed to send question to processing system'
                })
                
    except WebSocketDisconnect:
        websocket_manager.remove_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.remove_session(session_id)

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