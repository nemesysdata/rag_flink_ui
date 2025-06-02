"""
Main FastAPI application for the RAG Flink UI backend.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from datetime import datetime
from .mock_api import mock_service

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

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for chat communication."""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Get response from mock service
            response = mock_service.get_response(message["content"])
            
            await manager.send_message(json.dumps(response), session_id)
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "RAG Flink UI Backend is running"} 