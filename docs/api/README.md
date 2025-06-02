# API Documentation

## WebSocket Endpoints

### Connection
- **URL**: `ws://<host>:<port>/ws/{session_id}`
- **Method**: WebSocket
- **Parameters**:
  - `session_id`: UUID v4 string

### Message Format

#### Client to Server
```json
{
    "type": "message",
    "content": "User message content",
    "user_name": "User's name or nickname"
}
```

#### Server to Client
```json
{
    "type": "response",
    "content": "API response content",
    "timestamp": "ISO 8601 timestamp"
}
```

## Error Handling

### Connection Errors
- Invalid session ID format
- Connection timeout
- Server unavailable

### Message Errors
- Invalid message format
- Missing required fields
- Server processing error

## Session Management
- Sessions are created when a user first connects
- Each session has a unique UUID v4 identifier
- Sessions are maintained until WebSocket connection is closed
- No persistent storage of session data 