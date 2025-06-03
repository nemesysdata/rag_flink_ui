"""
Kafka service for producing messages to Kafka topics.
"""

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer
import os
from typing import Dict, Any
from loguru import logger

class KafkaService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KafkaService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize Kafka producer and Schema Registry client."""
        if self._initialized:
            return

        # Schema Registry configuration
        schema_registry_conf = {
            'url': os.getenv('SCHEMA_REGISTRY_URL'),
            'basic.auth.user.info': f"{os.getenv('SCHEMA_REGISTRY_API_KEY')}:{os.getenv('SCHEMA_REGISTRY_API_SECRET')}"
        }
        
        # Kafka producer configuration
        producer_conf = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'security.protocol': os.getenv('KAFKA_SECURITY_PROTOCOL'),
            'sasl.mechanisms': os.getenv('KAFKA_SASL_MECHANISM'),
            'sasl.username': os.getenv('KAFKA_API_KEY'),
            'sasl.password': os.getenv('KAFKA_API_SECRET'),
            'client.id': 'rag-flink-ui-producer'
        }

        logger.info(f"Initializing Kafka service with config: {producer_conf}")
        logger.info(f"Schema Registry config: {schema_registry_conf}")

        try:
            # Initialize Schema Registry client
            self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
            logger.info("Schema Registry client initialized successfully")
            
            # Get the latest schema version
            schema_str = self.schema_registry_client.get_latest_version('perguntas-value').schema.schema_str
            logger.info(f"Retrieved schema: {schema_str}")
            
            # Initialize Avro serializer
            self.avro_serializer = AvroSerializer(
                self.schema_registry_client,
                schema_str,
                lambda obj, ctx: obj
            )
            logger.info("Avro serializer initialized successfully")
            
            # Initialize string serializer for keys
            self.string_serializer = StringSerializer('utf_8')
            
            # Initialize producer
            self.producer = Producer(producer_conf)
            logger.info("Kafka producer initialized successfully")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            raise

    def produce_question(self, session_id: str, pergunta: str) -> None:
        """
        Produce a question message to Kafka.
        
        Args:
            session_id: The session ID from the frontend
            pergunta: The question text
        """
        try:
            # Prepare message value
            message_value = {
                'session_id': session_id,
                'pergunta': pergunta
            }
            logger.info(f"Preparing to produce message: {message_value}")
            
            # Serialize message
            serialized_value = self.avro_serializer(message_value, None)
            serialized_key = self.string_serializer(session_id, None)
            logger.info("Message serialized successfully")
            
            # Produce message
            self.producer.produce(
                topic='perguntas',
                key=serialized_key,
                value=serialized_value,
                on_delivery=self._delivery_report
            )
            logger.info("Message produced to Kafka")
            
            # Flush to ensure message is sent
            self.producer.flush()
            logger.info("Producer flushed successfully")
            
            logger.info(f"Message produced successfully for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to produce message: {str(e)}")
            raise

    def _delivery_report(self, err, msg):
        """
        Callback for message delivery reports.
        
        Args:
            err: Error object if any
            msg: Message object
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def get_kafka_service():
    """Get or create the Kafka service instance."""
    return KafkaService() 