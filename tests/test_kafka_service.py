"""
Tests for the Kafka service.
"""

import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()

# Mock environment variables for testing
os.environ['KAFKA_BOOTSTRAP_SERVERS'] = 'test-broker:9092'
os.environ['KAFKA_API_KEY'] = 'test-user'
os.environ['KAFKA_API_SECRET'] = 'test-password'
os.environ['KAFKA_SECURITY_PROTOCOL'] = 'SASL_SSL'
os.environ['KAFKA_SASL_MECHANISM'] = 'PLAIN'
os.environ['SCHEMA_REGISTRY_URL'] = 'http://test-registry:8081'
os.environ['SCHEMA_REGISTRY_API_KEY'] = 'test-user'
os.environ['SCHEMA_REGISTRY_API_SECRET'] = 'test-password'

@pytest.fixture(autouse=True)
def mock_kafka_dependencies(monkeypatch):
    from unittest.mock import Mock
    # Patch Producer and SchemaRegistryClient before import
    mock_producer = Mock()
    mock_schema_registry = Mock()
    mock_schema_registry.get_latest_version.return_value.schema.schema_str = (
        '{"doc": "Perguntas feita no chat",'
        '"fields": ['
        '  {"doc": "Identificador da sessão de chat", "name": "session_id", "type": "string"},'
        '  {"doc": "O texto da pergunta feita no chat", "name": "pergunta", "type": "string"}'
        '],'
        '"name": "perguntas",'
        '"namespace": "co.techrom.poc_rag",'
        '"type": "record"}'
    )
    # Patch AvroSerializer to return a fake serialized value
    mock_avro_serializer = Mock()
    mock_avro_serializer.side_effect = lambda value, ctx: b"serialized-value"
    monkeypatch.setattr("confluent_kafka.Producer", lambda conf: mock_producer)
    monkeypatch.setattr("confluent_kafka.schema_registry.SchemaRegistryClient", lambda conf: mock_schema_registry)
    monkeypatch.setattr("confluent_kafka.schema_registry.avro.AvroSerializer", lambda *a, **kw: mock_avro_serializer)
    return {"producer": mock_producer, "schema_registry": mock_schema_registry, "avro_serializer": mock_avro_serializer}

def test_kafka_service_initialization(mock_kafka_dependencies):
    from rag_flink_ui.backend.services.kafka_service import KafkaService, get_kafka_service
    KafkaService._instance = None
    service = get_kafka_service()
    assert service.schema_registry_client is not None
    assert service.producer is not None

def test_produce_question(mock_kafka_dependencies):
    from rag_flink_ui.backend.services.kafka_service import KafkaService, get_kafka_service
    KafkaService._instance = None
    service = get_kafka_service()
    session_id = "test-session"
    pergunta = "Test question"
    service.produce_question(session_id, pergunta)
    service.producer.produce.assert_called_once()
    service.producer.flush.assert_called_once()

def test_produce_question_error(mock_kafka_dependencies):
    from rag_flink_ui.backend.services.kafka_service import KafkaService, get_kafka_service
    KafkaService._instance = None
    service = get_kafka_service()
    # Set the side effect directly on the instance's producer
    service.producer.produce.side_effect = Exception("Test error")
    import pytest
    with pytest.raises(Exception) as exc_info:
        service.produce_question("test-session", "Test question")
    assert str(exc_info.value) == "Test error" 