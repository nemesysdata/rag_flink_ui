"""
Kafka service for producing messages to Kafka topics.
"""

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
import os
from typing import Dict, Any
from loguru import logger
import avro.schema
import json

class KafkaService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.debug("Creating new KafkaService instance")
            cls._instance = super(KafkaService, cls).__new__(cls)
            cls._instance._initialized = False
        else:
            logger.debug("Returning existing KafkaService instance")
        return cls._instance

    def __init__(self):
        """Initialize Kafka producer and Schema Registry client."""
        if self._initialized:
            logger.debug("KafkaService already initialized, skipping initialization")
            return

        logger.debug("Starting KafkaService initialization")
        
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

        logger.debug(f"Schema Registry URL: {os.getenv('SCHEMA_REGISTRY_URL')}")
        logger.debug(f"Kafka Bootstrap Servers: {os.getenv('KAFKA_BOOTSTRAP_SERVERS')}")
        logger.debug(f"Kafka Security Protocol: {os.getenv('KAFKA_SECURITY_PROTOCOL')}")
        logger.debug(f"Kafka SASL Mechanism: {os.getenv('KAFKA_SASL_MECHANISM')}")
        logger.info(f"Initializing Kafka service with config: {producer_conf}")
        logger.info(f"Schema Registry config: {schema_registry_conf}")

        try:
            # Initialize Schema Registry client
            logger.debug("Initializing Schema Registry client...")
            self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
            logger.info("Schema Registry client initialized successfully")
            
            # Get the latest schema version
            logger.debug("Retrieving latest schema version for 'perguntas-value'...")
            try:
                schema_version = self.schema_registry_client.get_latest_version('perguntas-value')
                logger.debug(f"Schema version retrieved: {schema_version}")
                schema_str = schema_version.schema.schema_str
                logger.debug(f"Retrieved schema version: {schema_str}")
            except Exception as e:
                logger.error(f"Failed to get schema version: {str(e)}", exc_info=True)
                raise
            
            # Initialize Avro serializer
            logger.debug("Initializing Avro serializer...")
            try:
                # Create the serializer
                self.avro_serializer = AvroSerializer(
                    self.schema_registry_client,
                    schema_str
                )
                logger.info("Avro serializer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Avro serializer: {str(e)}", exc_info=True)
                raise
            
            # Initialize string serializer for keys
            logger.debug("Initializing string serializer...")
            self.string_serializer = StringSerializer('utf_8')
            
            # Initialize producer
            logger.debug("Initializing Kafka producer...")
            self.producer = Producer(producer_conf)
            logger.info("Kafka producer initialized successfully")
            self._initialized = True
            logger.debug("KafkaService initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}", exc_info=True)
            raise

    def produce_question(self, session_id: str, pergunta: str) -> None:
        """
        Produce a question message to Kafka.
        
        Args:
            session_id: The session ID from the frontend
            pergunta: The question text
        """
        logger.debug(f"Starting to produce question for session {session_id}")
        try:
            # Check if producer is initialized
            if not hasattr(self, 'producer') or self.producer is None:
                logger.error("Kafka producer is not initialized")
                raise RuntimeError("Kafka producer is not initialized")

            # Prepare message value
            message_value = {
                'session_id': session_id,
                'pergunta': pergunta
            }
            logger.debug(f"Prepared message value: {message_value}")
            
            # Check if serializers are initialized
            if not hasattr(self, 'avro_serializer') or self.avro_serializer is None:
                logger.error("Avro serializer is not initialized")
                raise RuntimeError("Avro serializer is not initialized")
            if not hasattr(self, 'string_serializer') or self.string_serializer is None:
                logger.error("String serializer is not initialized")
                raise RuntimeError("String serializer is not initialized")
            
            # Serialize message
            logger.debug("Serializing message value...")
            try:
                logger.debug(f"Serializing message value: {message_value}")
                serialized_value = self.avro_serializer(
                    message_value,
                    SerializationContext("perguntas", MessageField.VALUE)
                )
                logger.debug("Message value serialized successfully")
            except Exception as e:
                logger.error(f"Failed to serialize message value: {str(e)}", exc_info=True)
                raise

            logger.debug("Serializing message key...")
            try:
                serialized_key = self.string_serializer(session_id, None)
                logger.debug("Message key serialized successfully")
            except Exception as e:
                logger.error(f"Failed to serialize message key: {str(e)}", exc_info=True)
                raise

            logger.debug("Message serialization completed")
            
            # Produce message
            logger.debug(f"Producing message to topic 'perguntas'...")
            try:
                self.producer.produce(
                    topic='perguntas',
                    key=serialized_key,
                    value=serialized_value,
                    on_delivery=self._delivery_report
                )
                logger.debug("Message production initiated")
            except Exception as e:
                logger.error(f"Failed to produce message: {str(e)}", exc_info=True)
                raise
            
            # Flush to ensure message is sent
            logger.debug("Flushing producer to ensure message delivery...")
            try:
                self.producer.flush()
                logger.debug("Producer flush completed")
            except Exception as e:
                logger.error(f"Failed to flush producer: {str(e)}", exc_info=True)
                raise
            
            logger.info(f"Message produced successfully for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to produce message: {str(e)}", exc_info=True)
            raise

    def _delivery_report(self, err, msg):
        """
        Callback for message delivery reports.
        
        Args:
            err: Error object if any
            msg: Message object
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}", exc_info=True)
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
            logger.info(f"Message delivery confirmed to {msg.topic()} [{msg.partition()}]")

def get_kafka_service():
    """Get or create the Kafka service instance."""
    logger.debug("Getting Kafka service instance")
    return KafkaService() 