#!/bin/bash

# Start FastAPI Webhook Server in background
uvicorn app.main_api:app --host 0.0.0.0 --port 8000 &

# Start Streamlit Operations Dashboard in foreground
streamlit run ui/dashboard.py --server.port 8501 --server.address 0.0.0.0