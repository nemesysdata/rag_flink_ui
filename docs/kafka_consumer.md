# Kafka Consumer Service

## Overview

The Kafka Consumer Service is responsible for processing responses from the RAG system and routing them to the appropriate WebSocket sessions. It runs in a separate thread from the main application thread to ensure non-blocking operation.

## Architecture

### Components

1. **KafkaResponseConsumer**
   - Consumes messages from the 'respostas' topic
   - Processes Avro messages
   - Routes responses to WebSocket sessions

2. **WebSocketSessionManager**
   - Manages WebSocket connections
   - Tracks session states
   - Controls message flow (one question at a time)

### Message Flow

1. User sends a question via WebSocket
2. System marks session as waiting for response
3. Kafka consumer receives response message
4. Response is routed to appropriate WebSocket session
5. Session is cleared for next question

## Configuration

### Kafka Consumer Configuration

```python
config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'rag-flink-ui-group',
    'auto.offset.reset': 'latest',
    'schema.registry.url': 'http://schema-registry:8081'
}
```

### Environment Variables

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers
- `KAFKA_SCHEMA_REGISTRY_URL`: Schema Registry URL
- `KAFKA_CONSUMER_GROUP_ID`: Consumer group ID (optional)

## Usage

### Starting the Consumer

```python
# Initialize components
websocket_manager = WebSocketSessionManager()
kafka_consumer = KafkaResponseConsumer(
    websocket_manager=websocket_manager,
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    schema_registry_url=os.getenv('KAFKA_SCHEMA_REGISTRY_URL')
)

# Start consumer in background
asyncio.create_task(kafka_consumer.start())
```

### Stopping the Consumer

```python
await kafka_consumer.stop()
```

## Error Handling

The service implements several error handling mechanisms:

1. **Message Deserialization**
   - Invalid Avro messages are logged and skipped
   - Schema Registry errors are handled gracefully

2. **WebSocket Communication**
   - Failed message deliveries are logged
   - Sessions are cleared on communication errors

3. **Kafka Connection**
   - Connection errors trigger reconnection attempts
   - Backoff strategy for repeated failures

## Monitoring

### Logging

The service logs important events:

- Consumer start/stop
- Message processing errors
- WebSocket communication failures
- Session state changes

### Metrics

Key metrics to monitor:

- Message processing rate
- Error rate
- WebSocket delivery success rate
- Session count

## Security

1. **Authentication**
   - Kafka authentication via SASL/SSL
   - Schema Registry authentication

2. **Authorization**
   - Topic-level access control
   - WebSocket session validation

## Deployment

### Requirements

- Python 3.8+
- confluent-kafka
- avro-python3
- fastapi

### Dependencies

```toml
[tool.poetry.dependencies]
confluent-kafka = "^2.3.0"
avro-python3 = "^1.10.2"
```

## Troubleshooting

### Common Issues

1. **Message Processing Failures**
   - Check Schema Registry connection
   - Verify message format
   - Review error logs

2. **WebSocket Delivery Failures**
   - Check session state
   - Verify WebSocket connection
   - Review error logs

3. **Kafka Connection Issues**
   - Verify bootstrap servers
   - Check network connectivity
   - Review error logs

### Debugging

Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
``` 