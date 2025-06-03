#!/bin/bash

# Ativar o ambiente virtual do Poetry
source /app/.venv/bin/activate

if [ "$SERVICO" = "front" ]; then
    echo "Iniciando frontend (Streamlit)..."
    streamlit run rag_flink_ui/frontend/app.py
elif [ "$SERVICO" = "back" ]; then
    echo "Iniciando backend (FastAPI)..."
    uvicorn rag_flink_ui.backend.main:app --host 0.0.0.0 --port 8080
else
    echo "Erro: Variável de ambiente SERVICO deve ser 'front' ou 'back'."
    exit 1
fi 