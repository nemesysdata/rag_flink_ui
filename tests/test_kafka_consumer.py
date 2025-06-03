"""
Tests for the Kafka consumer service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from confluent_kafka import KafkaError
from rag_flink_ui.backend.services.kafka_consumer import KafkaResponseConsumer
from rag_flink_ui.backend.services.websocket_manager import WebSocketSessionManager

@pytest.fixture
def websocket_manager():
    """Create a WebSocket manager instance."""
    return WebSocketSessionManager()

@pytest.fixture
def kafka_consumer(websocket_manager):
    """Create a Kafka consumer instance."""
    return KafkaResponseConsumer(
        websocket_manager=websocket_manager,
        bootstrap_servers="localhost:9092",
        schema_registry_url="http://localhost:8081"
    )

@pytest.mark.asyncio
async def test_start_consumer(kafka_consumer):
    """Test starting the consumer."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_consumer.return_value = MagicMock()
        
        # Start consumer
        await kafka_consumer.start()
        
        # Verify consumer setup
        assert kafka_consumer.consumer is not None
        assert kafka_consumer.running
        mock_consumer.return_value.subscribe.assert_called_once_with(['respostas'])

@pytest.mark.asyncio
async def test_stop_consumer(kafka_consumer):
    """Test stopping the consumer."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_consumer.return_value = MagicMock()
        
        # Start and stop consumer
        await kafka_consumer.start()
        await kafka_consumer.stop()
        
        # Verify consumer cleanup
        assert not kafka_consumer.running
        mock_consumer.return_value.close.assert_called_once()

@pytest.mark.asyncio
async def test_process_message(kafka_consumer, websocket_manager):
    """Test processing a message."""
    session_id = "test-session"
    response = "test response"
    
    # Setup WebSocket
    mock_websocket = AsyncMock()
    websocket_manager.register_session(session_id, mock_websocket)
    websocket_manager.set_waiting_response(session_id, "test question")
    
    # Process message
    message = {
        'session_id': session_id,
        'resposta': response
    }
    
    await kafka_consumer._process_message(message)
    
    # Verify response sent
    mock_websocket.send_json.assert_called_once_with({
        'type': 'response',
        'data': response
    })

@pytest.mark.asyncio
async def test_process_message_invalid_format(kafka_consumer):
    """Test processing an invalid message."""
    # Process invalid message
    message = {
        'invalid_field': 'value'
    }
    
    await kafka_consumer._process_message(message)
    
    # No errors should be raised, just logged

@pytest.mark.asyncio
async def test_process_message_no_session(kafka_consumer):
    """Test processing a message for non-existent session."""
    # Process message for non-existent session
    message = {
        'session_id': 'non-existent',
        'resposta': 'test response'
    }
    
    await kafka_consumer._process_message(message)
    
    # No errors should be raised, just logged

@pytest.mark.asyncio
async def test_consume_messages(kafka_consumer):
    """Test consuming messages."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = {
            'session_id': 'test-session',
            'resposta': 'test response'
        }
        
        mock_consumer.return_value = MagicMock()
        mock_consumer.return_value.poll.side_effect = [
            mock_message,
            None,  # No more messages
            Exception("Stop consuming")  # Force stop
        ]
        
        # Start consumer
        with pytest.raises(Exception):
            await kafka_consumer.start()
        
        # Verify message processing
        assert mock_consumer.return_value.poll.call_count > 1

@pytest.mark.asyncio
async def test_consume_messages_error(kafka_consumer):
    """Test handling consumer errors."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_consumer.return_value = MagicMock()
        mock_consumer.return_value.poll.side_effect = Exception("Consumer error")
        
        # Start consumer
        with pytest.raises(Exception):
            await kafka_consumer.start()
        
        # Verify error handling
        assert mock_consumer.return_value.poll.call_count == 1

@pytest.mark.asyncio
async def test_consume_messages_kafka_error(kafka_consumer):
    """Test handling Kafka errors."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_message = MagicMock()
        mock_message.error.return_value = KafkaError()
        
        mock_consumer.return_value = MagicMock()
        mock_consumer.return_value.poll.side_effect = [
            mock_message,
            None,  # No more messages
            Exception("Stop consuming")  # Force stop
        ]
        
        # Start consumer
        with pytest.raises(Exception):
            await kafka_consumer.start()
        
        # Verify error handling
        assert mock_consumer.return_value.poll.call_count > 1 