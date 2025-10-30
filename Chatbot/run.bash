# # Run QDRANT Cluster on Cloud
# curl \
#     -X GET 'https://8bbf5100-21d0-4beb-85e8-e100c56dbadc.eu-west-1-0.aws.cloud.qdrant.io:6333' \
#     --header 'api-key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.caaq-EykmYTiwew-uRA0KUCgLFX9jlzVEAnxUBoH0Ws'

#
# TO RUN DOCKER CONTAINERS LOCALLY AND CONNECT STREAMLIT TO QDRANT
#
# Pull QDRANT Docker Image
docker pull qdrant/qdrant

# Run QDRANT Docker Container
# Remove old container (if it exists)
docker rm -f qdrant-db

# Run new QDRANT Docker Container with correct name placement
docker run --rm -p 6333:6333 -p 6334:6334 \
    --name qdrant-db \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant

docker run -d \
  --name streamlit-app \
  --network chatbot-network \
  -p 8501:8501 \
  -e QDRANT_HOST=qdrant \
  -e QDRANT_PORT=6333 \
  --restart always \
  streamlit-app:latest

docker stop streamlit-app qdrant
docker rm streamlit-app qdrant
docker network rm chatbot-network

# Dockerfile for QDRANT and Streamlit App
# Build
docker build -t streamlit-app-all-in-one .

# Run with ONE command
docker run -d \
  --name my-app \
  -p 8501:8501 \
  -p 6333:6333 \
  -v $(pwd)/qdrant_data:/qdrant/storage \
  streamlit-app-all-in-one