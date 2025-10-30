#!/bin/bash

# Start Qdrant in the background
echo "Starting Qdrant..."
/usr/local/bin/qdrant --config-path /qdrant/config/production.yaml &

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to start..."
sleep 5

# Start Streamlit
echo "Starting Streamlit..."
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501