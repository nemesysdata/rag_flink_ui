"""
Tests for WebSocket functionality.
"""

import pytest
from fastapi.testclient import TestClient
from rag_flink_ui.backend.main import app
import json
import uuid

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "RAG Flink UI Backend is running"}

def test_websocket_connection():
    """Test WebSocket connection and message exchange."""
    session_id = str(uuid.uuid4())
    with client.websocket_connect(f"/ws/{session_id}") as websocket:
        # Send a test message
        test_message = {
            "type": "message",
            "content": "Hello, World!",
            "user_name": "test_user"
        }
        websocket.send_text(json.dumps(test_message))
        
        # Receive the response
        response = websocket.receive_text()
        response_data = json.loads(response)
        
        # Verify response format
        assert "type" in response_data
        assert "content" in response_data
        assert "timestamp" in response_data
        assert response_data["type"] == "response"
        assert "Echo: Hello, World!" in response_data["content"] 