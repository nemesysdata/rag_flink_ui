import pytest
import asyncio
from unittest.mock import Mock, patch
from confluent_kafka import KafkaError
from ..services.kafka_consumer import KafkaResponseConsumer
from ..services.websocket_manager import WebSocketSessionManager

@pytest.fixture
def mock_websocket_manager():
    return Mock(spec=WebSocketSessionManager)

@pytest.fixture
def kafka_consumer(mock_websocket_manager):
    return KafkaResponseConsumer(
        websocket_manager=mock_websocket_manager,
        bootstrap_servers='localhost:9092',
        schema_registry_url='http://localhost:8081',
        group_id='test-group'
    )

@pytest.mark.asyncio
async def test_consumer_initialization(kafka_consumer):
    """Test consumer initialization with correct configuration."""
    assert kafka_consumer.websocket_manager is not None
    assert kafka_consumer.running is False
    assert kafka_consumer.consumer is None
    assert kafka_consumer.config['group.id'] == 'test-group'
    assert kafka_consumer.config['bootstrap.servers'] == 'localhost:9092'
    assert kafka_consumer.config['schema.registry.url'] == 'http://localhost:8081'

@pytest.mark.asyncio
async def test_consumer_start_stop(kafka_consumer):
    """Test consumer start and stop functionality."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_consumer_instance = Mock()
        mock_consumer.return_value = mock_consumer_instance
        
        # Start consumer
        await kafka_consumer.start()
        assert kafka_consumer.running is True
        assert kafka_consumer.consumer is not None
        mock_consumer_instance.subscribe.assert_called_once_with(['respostas'])
        
        # Stop consumer
        await kafka_consumer.stop()
        assert kafka_consumer.running is False
        mock_consumer_instance.close.assert_called_once()

@pytest.mark.asyncio
async def test_process_valid_message(kafka_consumer):
    """Test processing of a valid message."""
    test_message = {
        'session_id': 'test-session',
        'resposta': 'Test response'
    }
    
    kafka_consumer.websocket_manager.send_response.return_value = True
    
    await kafka_consumer._process_message(test_message)
    
    kafka_consumer.websocket_manager.send_response.assert_called_once_with(
        'test-session',
        'Test response'
    )

@pytest.mark.asyncio
async def test_process_invalid_message(kafka_consumer):
    """Test processing of an invalid message."""
    test_message = {
        'session_id': 'test-session'
        # Missing resposta field
    }
    
    await kafka_consumer._process_message(test_message)
    
    kafka_consumer.websocket_manager.send_response.assert_not_called()

@pytest.mark.asyncio
async def test_consume_messages_with_error(kafka_consumer):
    """Test message consumption with error handling."""
    with patch('confluent_kafka.avro.AvroConsumer') as mock_consumer:
        mock_consumer_instance = Mock()
        mock_consumer.return_value = mock_consumer_instance
        
        # Simulate Kafka error
        mock_consumer_instance.poll.side_effect = KafkaError(KafkaError._PARTITION_EOF)
        
        await kafka_consumer.start()
        await asyncio.sleep(0.1)  # Allow time for error handling
        await kafka_consumer.stop()
        
        assert kafka_consumer.running is False

@pytest.mark.asyncio
async def test_websocket_send_failure(kafka_consumer):
    """Test handling of WebSocket send failures."""
    test_message = {
        'session_id': 'test-session',
        'resposta': 'Test response'
    }
    
    kafka_consumer.websocket_manager.send_response.return_value = False
    
    await kafka_consumer._process_message(test_message)
    
    kafka_consumer.websocket_manager.send_response.assert_called_once_with(
        'test-session',
        'Test response'
    ) 