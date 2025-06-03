"""
Kafka consumer service for processing responses from the RAG system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.avro import AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka.serialization import SerializationContext, MessageField
from .websocket_manager import WebSocketSessionManager
import os
from concurrent.futures import ThreadPoolExecutor
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer

logger = logging.getLogger(__name__)

class KafkaConfig:
    """Kafka configuration manager."""
    
    def __init__(self, bootstrap_servers: str, schema_registry_url: str, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.schema_registry_url = schema_registry_url
        self.group_id = group_id
        
        # Schema Registry configuration
        self._schema_registry_config = {
            'url': schema_registry_url,
            'basic.auth.credentials.source': 'USER_INFO',
            'basic.auth.user.info': f"{os.getenv('SCHEMA_REGISTRY_API_KEY')}:{os.getenv('SCHEMA_REGISTRY_API_SECRET')}"
        }
        
        # Kafka consumer configuration
        self._consumer_config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': os.getenv('KAFKA_AUTO_OFFSET_RESET', 'latest'),
            'security.protocol': os.getenv('KAFKA_SECURITY_PROTOCOL'),
            'sasl.mechanisms': os.getenv('KAFKA_SASL_MECHANISM'),
            'sasl.username': os.getenv('KAFKA_API_KEY'),
            'sasl.password': os.getenv('KAFKA_API_SECRET'),
            'client.id': 'rag-flink-ui-consumer'
        }
        
        logger.info(f"Schema Registry config: {self._schema_registry_config}")
        logger.info(f"Kafka consumer config: {self._consumer_config}")
    
    def create_schema_registry(self) -> CachedSchemaRegistryClient:
        """Create and return a Schema Registry client."""
        try:
            logger.info("Creating Schema Registry client...")
            client = CachedSchemaRegistryClient(self._schema_registry_config)
            logger.info("Schema Registry client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create Schema Registry client: {str(e)}")
            raise
    
    def create_consumer(self) -> Consumer:
        """Create and return a Kafka consumer."""
        try:
            logger.info("Creating Kafka consumer...")
            consumer = Consumer(self._consumer_config)
            logger.info("Kafka consumer created successfully")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise
    
    def create_avro_deserializer(self, schema_registry: CachedSchemaRegistryClient, topic: str):
        """Create and return an Avro deserializer."""
        try:
            logger.info(f"Creating Avro deserializer for topic {topic}...")
            deserializer = MessageSerializer(schema_registry)
            logger.info("Avro deserializer created successfully")
            return deserializer
        except Exception as e:
            logger.error(f"Failed to create Avro deserializer: {str(e)}")
            raise

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
        self.kafka_config = KafkaConfig(bootstrap_servers, schema_registry_url, group_id)
        self._consumer = None
        self._schema_registry = None
        self._message_serializer = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    @property
    def schema_registry(self):
        """Lazy initialization of Schema Registry client."""
        if self._schema_registry is None:
            self._schema_registry = self.kafka_config.create_schema_registry()
        return self._schema_registry
    
    @property
    def message_serializer(self):
        """Lazy initialization of Message Serializer."""
        if self._message_serializer is None:
            self._message_serializer = self.kafka_config.create_avro_deserializer(
                self.schema_registry, 'respostas'
            )
        return self._message_serializer
    
    @property
    def consumer(self):
        """Lazy initialization of Kafka Consumer."""
        if self._consumer is None:
            self._consumer = self.kafka_config.create_consumer()
            self._consumer.subscribe(['respostas'])
            logger.info("Kafka consumer initialized and subscribed to 'respostas' topic")
        return self._consumer
    
    async def start(self) -> None:
        """Start consuming messages from Kafka."""
        try:
            # Test Schema Registry connection
            try:
                logger.info("Testing Schema Registry connection...")
                # Try to get a schema by ID 1 to test connection
                schema = self.schema_registry.get_by_id(1)
                logger.info(f"Successfully connected to Schema Registry. Retrieved schema: {schema}")
            except Exception as e:
                logger.error(f"Failed to connect to Schema Registry: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            self.running = True
            logger.info("Starting Kafka message consumption loop")
            await self._consume_messages()
            
        except Exception as e:
            logger.error(f"Error starting Kafka consumer: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def stop(self) -> None:
        """Stop consuming messages from Kafka."""
        self.running = False
        if self._consumer:
            self._consumer.close()
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Kafka consumer stopped")
    
    async def _consume_messages(self) -> None:
        """Consume and process messages from Kafka."""
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
                    error = message.error()
                    if error.code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka error: {error}")
                        logger.error(f"Error details: code={error.code()}, name={error.name()}, description={error.str()}")
                        continue
                
                try:
                    # Deserialize message using Schema Registry
                    value = self.message_serializer.decode_message(message.value())
                    session_id = value.get('session_id')
                    logger.info(f"[KAFKA] Recebida resposta para session_id={session_id} no tópico {message.topic()}, partição {message.partition()}, offset {message.offset()}")
                    logger.info(f"[KAFKA] Conteúdo da mensagem: {value}")
                    
                    # Process message
                    await self._process_message(value)
                    
                    # Commit offset after successful processing
                    self.consumer.commit(message)
                    logger.info(f"[KAFKA] Offset {message.offset()} commitado com sucesso para session_id={session_id}")
                    
                except SerializerError as e:
                    logger.error(f"Message deserialization failed: {e}")
                    if hasattr(e, 'message'):
                        logger.error(f"Deserialization error details: {e.message}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await asyncio.sleep(1)  # Backoff on error
                
            except Exception as e:
                logger.error(f"Error in message consumption loop: {e}")
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
            
            logger.info(f"[WEBSOCKET] Tentando enviar resposta para session_id={session_id}")
            
            # Send response to WebSocket
            success = await self.websocket_manager.send_response(session_id, resposta)
            
            if not success:
                logger.warning(f"[WEBSOCKET] Falha ao enviar resposta para session_id={session_id}")
            else:
                logger.info(f"[WEBSOCKET] Resposta enviada com sucesso para session_id={session_id}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}") 