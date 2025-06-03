# WebSocket Session Manager

## Overview

The WebSocket Session Manager is responsible for managing WebSocket connections and their states. It ensures that each session can only process one question at a time, waiting for the response before accepting a new question.

## Architecture

### Components

1. **SessionState**
   - Tracks WebSocket connection
   - Manages waiting state
   - Stores current question

2. **WebSocketSessionManager**
   - Manages session lifecycle
   - Controls message flow
   - Handles thread safety

### Session Lifecycle

1. **Registration**
   - New WebSocket connection
   - Session ID assignment
   - State initialization

2. **Question Processing**
   - Check if session can accept question
   - Mark session as waiting
   - Store current question

3. **Response Handling**
   - Receive response
   - Send to WebSocket
   - Clear waiting state

4. **Cleanup**
   - Remove session
   - Clear resources
   - Log removal

## Usage

### Session Management

```python
# Initialize manager
websocket_manager = WebSocketSessionManager()

# Register new session
websocket_manager.register_session(session_id, websocket)

# Check if session can accept question
if websocket_manager.can_accept_question(session_id):
    websocket_manager.set_waiting_response(session_id, question)
else:
    # Handle busy session

# Send response
success = await websocket_manager.send_response(session_id, response)

# Remove session
websocket_manager.remove_session(session_id)
```

## Thread Safety

The manager implements thread safety through:

1. **Lock Mechanism**
   - Thread-safe session access
   - Atomic state changes
   - Protected resource access

2. **State Management**
   - Atomic state transitions
   - Protected session updates
   - Safe cleanup

## Error Handling

### Connection Errors

1. **WebSocket Failures**
   - Connection drops
   - Send failures
   - Receive errors

2. **State Management**
   - Invalid states
   - Race conditions
   - Resource leaks

### Recovery

1. **Automatic Cleanup**
   - Failed connections
   - Stale sessions
   - Resource release

2. **Error Logging**
   - Connection issues
   - State errors
   - Processing failures

## Monitoring

### Logging

The manager logs important events:

- Session registration/removal
- State changes
- Error conditions
- Processing status

### Metrics

Key metrics to monitor:

- Active sessions
- Waiting sessions
- Error rate
- Processing time

## Security

1. **Session Validation**
   - ID verification
   - State validation
   - Access control

2. **Resource Protection**
   - Memory management
   - Connection limits
   - Timeout handling

## Best Practices

1. **Session Management**
   - Regular cleanup
   - State verification
   - Resource monitoring

2. **Error Handling**
   - Graceful degradation
   - Proper cleanup
   - Error recovery

3. **Performance**
   - Efficient locking
   - Resource pooling
   - Connection reuse

## Troubleshooting

### Common Issues

1. **Session State**
   - Stuck in waiting
   - Invalid transitions
   - Resource leaks

2. **Connection Problems**
   - Dropouts
   - Timeouts
   - Send failures

3. **Resource Issues**
   - Memory leaks
   - Connection limits
   - Thread contention

### Debugging

Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Integration

### FastAPI Integration

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        await websocket.accept()
        websocket_manager.register_session(session_id, websocket)
        
        while True:
            data = await websocket.receive_json()
            
            if websocket_manager.can_accept_question(session_id):
                websocket_manager.set_waiting_response(session_id, data['question'])
            else:
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Please wait for the previous response'
                })
                
    except WebSocketDisconnect:
        websocket_manager.remove_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.remove_session(session_id)
``` 