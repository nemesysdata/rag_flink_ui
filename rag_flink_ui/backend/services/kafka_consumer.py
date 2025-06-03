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
        group_id: str = "rag-flink-ui-group"
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
        
        # Kafka consumer configuration
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'latest',
            'schema.registry.url': schema_registry_url
        }
    
    async def start(self) -> None:
        """Start consuming messages from Kafka."""
        try:
            self.consumer = AvroConsumer(self.config)
            self.consumer.subscribe(['respostas'])
            self.running = True
            
            logger.info("Kafka consumer started")
            await self._consume_messages()
            
        except Exception as e:
            logger.error(f"Error starting Kafka consumer: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop consuming messages from Kafka."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer stopped")
    
    async def _consume_messages(self) -> None:
        """Consume and process messages from Kafka."""
        while self.running:
            try:
                # Poll for messages
                message = self.consumer.poll(1.0)
                
                if message is None:
                    continue
                
                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka error: {message.error()}")
                        continue
                
                # Process message
                await self._process_message(message.value())
                
            except SerializerError as e:
                logger.error(f"Message deserialization failed: {e}")
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
            
            # Send response to WebSocket
            success = await self.websocket_manager.send_response(session_id, resposta)
            
            if not success:
                logger.warning(f"Failed to send response to session {session_id}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}") 