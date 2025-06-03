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

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "websocket" not in st.session_state:
    st.session_state.websocket = None
if "is_connected" not in st.session_state:
    st.session_state.is_connected = False

logger.info("Iniciando Streamlit frontend do RAG Flink UI...")

def get_backend_url() -> str:
    """Get the backend URL from environment or use default."""
    host = os.getenv("BACKEND_HOST", "localhost")
    port = os.getenv("BACKEND_PORT", "8080")
    url = f"ws://{host}:{port}"
    logger.info(f"Backend URL configurado para: {url}")
    return url

async def connect_websocket():
    """Connect to the WebSocket server."""
    try:
        uri = f"{get_backend_url()}/ws/{st.session_state.session_id}"
        logger.info(f"Tentando conectar ao WebSocket: {uri}")
        st.session_state.websocket = await websockets.connect(uri)
        st.session_state.is_connected = True
        logger.info("Conexão WebSocket estabelecida com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Falha ao conectar ao WebSocket: {str(e)}")
        st.error(f"Failed to connect to WebSocket server: {str(e)}")
        return False

async def send_message(message: str):
    """Send a message through the WebSocket connection."""
    if not st.session_state.is_connected:
        if not await connect_websocket():
            return None
    
    try:
        message_data = {
            "type": "message",
            "content": message,
            "user_name": st.session_state.user_name
        }
        logger.info(f"Enviando mensagem pelo WebSocket: {message_data}")
        await st.session_state.websocket.send(json.dumps(message_data))
        response = await st.session_state.websocket.recv()
        logger.info(f"Resposta recebida do WebSocket: {response}")
        return json.loads(response)
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem pelo WebSocket: {str(e)}")
        st.error(f"Error sending message: {str(e)}")
        st.session_state.is_connected = False
        return None

def initialize_chat() -> None:
    """Initialize the chat interface."""
    st.title("RAG Flink Chat")
    
    # User name input
    if not st.session_state.user_name:
        user_name = st.text_input("Enter your name or nickname:")
        if user_name:
            st.session_state.user_name = user_name
            st.rerun()
    else:
        st.write(f"Welcome, {st.session_state.user_name}!")
        st.write(f"Session ID: {st.session_state.session_id}")
        
        # Connection status
        if st.session_state.is_connected:
            st.success("Connected to server")
        else:
            st.warning("Not connected to server")

def display_messages() -> None:
    """Display chat messages."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "confidence" in message:
                st.caption(f"Confidence: {message['confidence']:.2%}")
            if "processing_time" in message:
                st.caption(f"Processing time: {message['processing_time']:.2f}s")

def main() -> None:
    """Main application entry point."""
    initialize_chat()
    
    if st.session_state.user_name:
        display_messages()
        
        # Chat input
        if prompt := st.chat_input("What would you like to know?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Send message and get response
            with st.spinner("Thinking..."):
                response = asyncio.run(send_message(prompt))
            
            if response:
                # Display assistant message
                with st.chat_message("assistant"):
                    st.write(response["content"])
                    if "confidence" in response:
                        st.caption(f"Confidence: {response['confidence']:.2%}")
                    if "processing_time" in response:
                        st.caption(f"Processing time: {response['processing_time']:.2f}s")
                
                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["content"],
                    "confidence": response.get("confidence"),
                    "processing_time": response.get("processing_time")
                })

if __name__ == "__main__":
    main() 