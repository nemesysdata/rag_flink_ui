"""
Main Streamlit application for the RAG Flink UI.
"""

import streamlit as st
import uuid
import json
import websockets
import asyncio
import os
from typing import Dict, List, Optional
import time
from loguru import logger
from dotenv import load_dotenv
from queue import Queue, Empty
import threading

# Load environment variables
load_dotenv()

# Get port from environment variable or use default
PORT = int(os.getenv("PORT", 8501))

logger.info("Iniciando Streamlit frontend do RAG Flink UI...")

class WebSocketState:
    def __init__(self):
        self.message_queue = Queue()
        self.websocket = None
        self.is_connected = False
        self.loop = None
        self.websocket_task = None
        self.session_id = str(uuid.uuid4())
        self.user_name = None
        self.messages = []
        
        # Start WebSocket handler
        self._start_websocket_handler()
    
    def get_backend_url(self) -> str:
        """Get the backend URL from environment or use default."""
        backend_url = os.getenv("BACKEND_URL", "ws://localhost:8080")
        # Convert http/https to ws/wss
        if backend_url.startswith("http://"):
            backend_url = "ws://" + backend_url[7:]
        elif backend_url.startswith("https://"):
            backend_url = "wss://" + backend_url[8:]
        logger.info(f"Backend URL configurado para: {backend_url}")
        return backend_url
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and message processing."""
        while True:
            try:
                if self.websocket is None:
                    websocket_url = f"{self.get_backend_url()}/ws/{self.session_id}"
                    logger.info(f"Tentando conectar ao WebSocket: {websocket_url}")
                    self.websocket = await websockets.connect(websocket_url)
                    self.is_connected = True
                    logger.info("Conexão WebSocket estabelecida com sucesso.")

                # Check for messages in the queue
                try:
                    message = self.message_queue.get_nowait()
                    logger.info(f"[FILA] Mensagem recebida da fila: {message}")
                    
                    # Send message through WebSocket
                    message_data = {
                        "type": "message",
                        "content": message,
                        "user_name": self.user_name
                    }
                    logger.info(f"[WEBSOCKET] Enviando mensagem pelo WebSocket: {message_data}")
                    await self.websocket.send(json.dumps(message_data))
                    logger.info("[WEBSOCKET] Mensagem enviada com sucesso")
                    
                    # Wait for response
                    logger.debug("[WEBSOCKET] Aguardando resposta...")
                    response = await self.websocket.recv()
                    logger.info(f"[WEBSOCKET] Resposta recebida: {response}")
                    
                    # Update UI with response
                    response_data = json.loads(response)
                    self.messages.append({
                        "role": "assistant",
                        "content": response_data["content"],
                        "confidence": response_data.get("confidence"),
                        "processing_time": response_data.get("processing_time")
                    })
                    logger.info("[UI] Interface atualizada com a resposta")
                    st.rerun()
                    
                except Empty:
                    # No messages in queue, continue waiting
                    await asyncio.sleep(0.1)  # Add small delay to prevent CPU spinning
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem: {str(e)}")
                    self.is_connected = False
                    self.websocket = None
                    
            except Exception as e:
                logger.error(f"Erro na conexão WebSocket: {str(e)}")
                self.is_connected = False
                self.websocket = None
                await asyncio.sleep(5)  # Wait before retrying
    
    def _start_websocket_handler(self):
        """Start the WebSocket handler in a separate thread."""
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.websocket_task = self.loop.create_task(self._websocket_handler())
            
            def run_loop():
                self.loop.run_forever()
            
            thread = threading.Thread(target=run_loop, daemon=True)
            thread.start()
    
    def send_message(self, message: str):
        """Send a message through the WebSocket connection."""
        logger.info(f"[FILA] Enfileirando mensagem do usuário: {message}")
        self.message_queue.put(message)
        logger.info("[FILA] Mensagem enfileirada com sucesso")
        self.messages.append({"role": "user", "content": message})
        logger.info("[UI] Mensagem do usuário adicionada ao histórico")

# Initialize session state
if "ws_state" not in st.session_state:
    st.session_state.ws_state = WebSocketState()

def initialize_chat() -> None:
    """Initialize the chat interface."""
    st.title("RAG Flink Chat")
    
    # User name input
    if not st.session_state.ws_state.user_name:
        user_name = st.text_input("Enter your name or nickname:")
        if user_name:
            st.session_state.ws_state.user_name = user_name
            st.rerun()
    else:
        st.write(f"Welcome, {st.session_state.ws_state.user_name}!")
        st.write(f"Session ID: {st.session_state.ws_state.session_id}")
        
        # Connection status
        if st.session_state.ws_state.is_connected:
            st.success("Connected to server")
        else:
            st.warning("Not connected to server")

def display_messages() -> None:
    """Display chat messages."""
    for message in st.session_state.ws_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "confidence" in message:
                st.caption(f"Confidence: {message['confidence']:.2%}")
            if "processing_time" in message:
                st.caption(f"Processing time: {message['processing_time']:.2f}s")

def main() -> None:
    """Main application entry point."""
    initialize_chat()
    
    if st.session_state.ws_state.user_name:
        display_messages()
        
        # Chat input
        if prompt := st.chat_input("What would you like to know?"):
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Send message
            st.session_state.ws_state.send_message(prompt)

if __name__ == "__main__":
    main() 