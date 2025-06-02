# Architecture Overview

## System Components

### Frontend (Streamlit)
- Chat interface similar to ChatGPT
- Session management using UUID v4
- Real-time communication via WebSocket
- Simple user identification by name/nickname
- In-memory chat history during active sessions

### Backend (FastAPI)
- WebSocket server for real-time communication
- Session-based message routing
- Q&A API integration
- Simple ws:// protocol implementation

## Technical Stack
- Python 3.12
- Poetry for dependency management
- Streamlit for frontend
- FastAPI for backend
- WebSocket for real-time communication

## Data Flow
1. User enters name/nickname
2. System generates UUID v4 session ID
3. WebSocket connection established
4. Messages are routed based on session ID
5. Chat history maintained in memory during active session
6. Session data discarded on connection close

## Security Considerations
- Basic session management
- No authentication required
- Simple WebSocket protocol (ws://)
- No persistent data storage 