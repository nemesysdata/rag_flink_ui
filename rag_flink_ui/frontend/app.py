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
from streamlit.runtime import get_instance
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx

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
        ctx = get_script_run_ctx()
        assert ctx, "Context must be set with `add_script_run_ctx`."
        runtime = get_instance()
        
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
                        "content": response_data["data"],
                        "confidence": response_data.get("confidence"),
                        "processing_time": response_data.get("processing_time")
                    })
                    logger.info("[UI] Interface atualizada com a resposta")
                    st.session_state.waiting_for_response = False

                    
                    # Request UI update
                    if runtime.is_active_session(ctx.session_id):
                        session_info = runtime._session_mgr.get_active_session_info(ctx.session_id)
                        if session_info:
                            session_info.session.request_rerun(None)
                    
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
            add_script_run_ctx(thread)  # Add Streamlit context to the thread
            thread.start()
    
    def send_message(self, message: str):
        """Send a message through the WebSocket connection."""
        logger.info(f"[FILA] Enfileirando mensagem do usuário: {message}")
        self.message_queue.put(message)
        logger.info("[FILA] Mensagem enfileirada com sucesso")
        self.messages.append({"role": "user", "content": message})
        logger.info("[UI] Mensagem do usuário adicionada ao histórico")
        # Store the time when we sent the message
        st.session_state.last_message_time = time.time()

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
            st.error("Not connected to server. Please refresh the page.")

def display_messages() -> None:
    """Display chat messages."""
    for message in st.session_state.ws_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:  # assistant
            with st.chat_message("assistant"):
                # Check if this is the first time displaying this message
                if not message.get("displayed", False):
                    # Create a generator function for the message content
                    def message_generator():
                        for char in message["content"]:
                            yield char
                            time.sleep(0.02)  # Ajustar velocidade conforme necessário
                    
                    st.write_stream(message_generator)
                    message["displayed"] = True  # Mark message as displayed
                else:
                    # For subsequent displays, just show the content directly
                    st.write(message["content"])
                
                if message.get("confidence") is not None:
                    st.caption(f"Confidence: {message['confidence']:.2%}")
                if message.get("processing_time") is not None:
                    st.caption(f"Processing time: {message['processing_time']:.2f}s")

def main() -> None:
    """Main application entry point."""
    initialize_chat()
    
    if st.session_state.ws_state.user_name:
        display_messages()
        
        # Initialize waiting state if not exists
        if "waiting_for_response" not in st.session_state:
            st.session_state.waiting_for_response = False
        
        # Chat input
        if not st.session_state.waiting_for_response and (prompt := st.chat_input("What would you like to know?")):
            # Check if we're connected
            if not st.session_state.ws_state.is_connected:
                st.error("Not connected to server. Please refresh the page.")
                return
                
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Send message and show spinner immediately
            st.session_state.ws_state.send_message(prompt)
            st.session_state.waiting_for_response = True
            
        if st.session_state.waiting_for_response:
            with st.chat_message("assistant"):
                st.write("Thinking...")
            
        # Check for timeout
        if st.session_state.waiting_for_response:
            if time.time() - st.session_state.get("last_message_time", time.time()) > 30:
                st.error("The server is taking too long to respond. Please check if the backend is running and try again.")
                st.session_state.waiting_for_response = False
                st.session_state.ws_state.is_connected = False

if __name__ == "__main__":
    main() 