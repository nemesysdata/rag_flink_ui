"""
Kafka consumer service for processing responses from the RAG system.
"""

import asyncio
import logging
from typing import Optional
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.avro import AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from .websocket_manager import WebSocketSessionManager
import os
from concurrent.futures import ThreadPoolExecutor
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient

logger = logging.getLogger(__name__)

class KafkaResponseConsumer:
    """
    Kafka consumer for processing responses from the RAG system.
    
    This class is responsible for:
    - Consuming messages from the 'respostas' topic
    - Processing Avro messages
    - Routing responses to appropriate WebSocket sessions
    """
    
    def __init__(
        self,
        websocket_manager: WebSocketSessionManager,
        bootstrap_servers: str,
        schema_registry_url: str,
        group_id: str = os.getenv('KAFKA_CONSUMER_GROUP', 'pdf-processor-group')
    ):
        """
        Initialize the Kafka consumer.
        
        Args:
            websocket_manager: WebSocket session manager instance
            bootstrap_servers: Kafka bootstrap servers
            schema_registry_url: Schema Registry URL
            group_id: Consumer group ID
        """
        self.websocket_manager = websocket_manager
        self.consumer = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Schema Registry configuration
        schema_registry_config = {
            'url': schema_registry_url,
            'basic.auth.credentials.source': 'USER_INFO',
            'basic.auth.user.info': f"{os.getenv('SCHEMA_REGISTRY_API_KEY')}:{os.getenv('SCHEMA_REGISTRY_API_SECRET')}"
        }
        
        # Initialize Schema Registry client
        self.schema_registry_client = CachedSchemaRegistryClient(schema_registry_config)
        logger.info(f"Initialized Schema Registry client with URL: {schema_registry_url}")
        
        # Kafka consumer configuration
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': os.getenv('KAFKA_AUTO_OFFSET_RESET', 'latest'),
            'schema.registry.url': schema_registry_url,
            'security.protocol': os.getenv('KAFKA_SECURITY_PROTOCOL'),
            'sasl.mechanisms': os.getenv('KAFKA_SASL_MECHANISM'),
            'sasl.username': os.getenv('KAFKA_API_KEY'),
            'sasl.password': os.getenv('KAFKA_API_SECRET'),
            'client.id': 'rag-flink-ui-consumer',
            'schema.registry.basic.auth.credentials.source': 'USER_INFO',
            'schema.registry.basic.auth.user.info': f"{os.getenv('SCHEMA_REGISTRY_API_KEY')}:{os.getenv('SCHEMA_REGISTRY_API_SECRET')}"
        }
        
        logger.info(f"Initializing Kafka consumer with config: {self.config}")
    
    async def start(self) -> None:
        """Start consuming messages from Kafka."""
        try:
            # Test Schema Registry connection
            try:
                # Try to get a schema by ID 1 to test connection
                self.schema_registry_client.get_by_id(1)
                logger.info("Successfully connected to Schema Registry")
            except Exception as e:
                logger.error(f"Failed to connect to Schema Registry: {e}")
                raise
            
            self.consumer = AvroConsumer(self.config)
            self.consumer.subscribe(['respostas'])
            self.running = True
            
            logger.info("Kafka consumer started and subscribed to 'respostas' topic")
            await self._consume_messages()
            
        except Exception as e:
            logger.error(f"Error starting Kafka consumer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop consuming messages from Kafka."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Kafka consumer stopped")
    
    async def _consume_messages(self) -> None:
        """Consume and process messages from Kafka."""
        logger.info("Starting Kafka message consumption loop")
        while self.running:
            try:
                # Run poll in a thread to avoid blocking the event loop
                message = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: self.consumer.poll(1.0)
                )
                
                if message is None:
                    continue
                
                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka error: {message.error()}")
                        continue
                
                try:
                    # Try to get schema ID from message
                    schema_id = message.headers().get('schema_id')
                    if schema_id:
                        logger.info(f"Message schema ID: {schema_id}")
                        try:
                            schema = self.schema_registry_client.get_by_id(schema_id)
                            logger.info(f"Successfully retrieved schema for ID {schema_id}")
                        except Exception as e:
                            logger.error(f"Failed to get schema for ID {schema_id}: {e}")
                except Exception as e:
                    logger.error(f"Error getting schema ID from message: {e}")
                
                logger.info(f"Received message from Kafka: {message.value()}")
                # Process message
                await self._process_message(message.value())
                
            except SerializerError as e:
                logger.error(f"Message deserialization failed: {e}")
                # Try to get more details about the error
                try:
                    if hasattr(e, 'message'):
                        logger.error(f"Deserialization error details: {e.message}")
                except Exception as detail_error:
                    logger.error(f"Error getting deserialization details: {detail_error}")
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(1)  # Backoff on error
    
    async def _process_message(self, message: dict) -> None:
        """
        Process a Kafka message.
        
        Args:
            message: The message to process
        """
        try:
            session_id = message.get('session_id')
            resposta = message.get('resposta')
            
            if not session_id or not resposta:
                logger.error("Invalid message format: missing session_id or resposta")
                return
            
            logger.info(f"Processing message for session {session_id}: {resposta}")
            
            # Send response to WebSocket
            success = await self.websocket_manager.send_response(session_id, resposta)
            
            if not success:
                logger.warning(f"Failed to send response to session {session_id}")
            else:
                logger.info(f"Successfully sent response to session {session_id}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}") 