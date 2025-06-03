"""
WebSocket session manager for handling client connections and message routing.
"""

import asyncio
import logging
from typing import Dict, Optional
from fastapi import WebSocket
import threading

logger = logging.getLogger(__name__)

class SessionState:
    """Represents the state of a WebSocket session."""
    
    def __init__(self):
        self.websocket: WebSocket = None
        self.is_waiting_response: bool = False
        self.current_question: str = None

class WebSocketSessionManager:
    """
    Manages WebSocket sessions and their states.
    
    This class is responsible for:
    - Tracking active WebSocket connections
    - Managing session states
    - Controlling message flow (one question at a time)
    """
    
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()
    
    def register_session(self, session_id: str, websocket: WebSocket) -> None:
        """
        Register a new WebSocket session.
        
        Args:
            session_id: Unique identifier for the session
            websocket: WebSocket connection instance
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionState()
            self._sessions[session_id].websocket = websocket
            logger.info(f"Session {session_id} registered")
    
    def remove_session(self, session_id: str) -> None:
        """
        Remove a WebSocket session.
        
        Args:
            session_id: Session identifier to remove
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Session {session_id} removed")
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Get a session by its ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionState if found, None otherwise
        """
        with self._lock:
            return self._sessions.get(session_id)
    
    def can_accept_question(self, session_id: str) -> bool:
        """
        Check if a session can accept a new question.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session can accept new question, False otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            return session is not None and not session.is_waiting_response
    
    def set_waiting_response(self, session_id: str, question: str) -> None:
        """
        Mark a session as waiting for response.
        
        Args:
            session_id: Session identifier
            question: The question being asked
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_waiting_response = True
                session.current_question = question
                logger.info(f"Session {session_id} waiting for response")
    
    def clear_waiting_response(self, session_id: str) -> None:
        """
        Clear the waiting response state for a session.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_waiting_response = False
                session.current_question = None
                logger.info(f"Session {session_id} cleared waiting state")
    
    async def send_response(self, session_id: str, response: str) -> bool:
        """
        Send a response to a WebSocket session.
        
        Args:
            session_id: Session identifier
            response: Response message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        session = self.get_session(session_id)
        if session and session.is_waiting_response:
            try:
                await session.websocket.send_json({
                    'type': 'response',
                    'data': response
                })
                self.clear_waiting_response(session_id)
                return True
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                self.clear_waiting_response(session_id)
                return False
        return False 