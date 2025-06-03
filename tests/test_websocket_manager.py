"""
Tests for the WebSocket session manager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from rag_flink_ui.backend.services.websocket_manager import WebSocketSessionManager, SessionState

@pytest.fixture
def websocket_manager():
    """Create a WebSocket manager instance."""
    return WebSocketSessionManager()

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket instance."""
    websocket = AsyncMock(spec=WebSocket)
    return websocket

@pytest.mark.asyncio
async def test_register_session(websocket_manager, mock_websocket):
    """Test session registration."""
    session_id = "test-session"
    
    websocket_manager.register_session(session_id, mock_websocket)
    
    session = websocket_manager.get_session(session_id)
    assert session is not None
    assert session.websocket == mock_websocket
    assert not session.is_waiting_response
    assert session.current_question is None

@pytest.mark.asyncio
async def test_remove_session(websocket_manager, mock_websocket):
    """Test session removal."""
    session_id = "test-session"
    
    websocket_manager.register_session(session_id, mock_websocket)
    websocket_manager.remove_session(session_id)
    
    session = websocket_manager.get_session(session_id)
    assert session is None

@pytest.mark.asyncio
async def test_can_accept_question(websocket_manager, mock_websocket):
    """Test question acceptance check."""
    session_id = "test-session"
    
    # Test before registration
    assert not websocket_manager.can_accept_question(session_id)
    
    # Test after registration
    websocket_manager.register_session(session_id, mock_websocket)
    assert websocket_manager.can_accept_question(session_id)
    
    # Test while waiting for response
    websocket_manager.set_waiting_response(session_id, "test question")
    assert not websocket_manager.can_accept_question(session_id)

@pytest.mark.asyncio
async def test_set_waiting_response(websocket_manager, mock_websocket):
    """Test setting waiting response state."""
    session_id = "test-session"
    question = "test question"
    
    websocket_manager.register_session(session_id, mock_websocket)
    websocket_manager.set_waiting_response(session_id, question)
    
    session = websocket_manager.get_session(session_id)
    assert session.is_waiting_response
    assert session.current_question == question

@pytest.mark.asyncio
async def test_clear_waiting_response(websocket_manager, mock_websocket):
    """Test clearing waiting response state."""
    session_id = "test-session"
    question = "test question"
    
    websocket_manager.register_session(session_id, mock_websocket)
    websocket_manager.set_waiting_response(session_id, question)
    websocket_manager.clear_waiting_response(session_id)
    
    session = websocket_manager.get_session(session_id)
    assert not session.is_waiting_response
    assert session.current_question is None

@pytest.mark.asyncio
async def test_send_response(websocket_manager, mock_websocket):
    """Test sending response."""
    session_id = "test-session"
    question = "test question"
    response = "test response"
    
    # Test without session
    assert not await websocket_manager.send_response(session_id, response)
    
    # Test with session not waiting
    websocket_manager.register_session(session_id, mock_websocket)
    assert not await websocket_manager.send_response(session_id, response)
    
    # Test with session waiting
    websocket_manager.set_waiting_response(session_id, question)
    assert await websocket_manager.send_response(session_id, response)
    
    # Verify WebSocket send
    mock_websocket.send_json.assert_called_once_with({
        'type': 'response',
        'data': response
    })
    
    # Verify state cleared
    session = websocket_manager.get_session(session_id)
    assert not session.is_waiting_response
    assert session.current_question is None

@pytest.mark.asyncio
async def test_send_response_error(websocket_manager, mock_websocket):
    """Test sending response with error."""
    session_id = "test-session"
    question = "test question"
    response = "test response"
    
    # Setup error
    mock_websocket.send_json.side_effect = Exception("Send error")
    
    websocket_manager.register_session(session_id, mock_websocket)
    websocket_manager.set_waiting_response(session_id, question)
    
    # Test error handling
    assert not await websocket_manager.send_response(session_id, response)
    
    # Verify state cleared on error
    session = websocket_manager.get_session(session_id)
    assert not session.is_waiting_response
    assert session.current_question is None 