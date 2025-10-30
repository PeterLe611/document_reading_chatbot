# # Multi-stage build: Use Qdrant base and add Python
# FROM qdrant/qdrant:latest as qdrant-base

# # Start from Python and copy Qdrant binary
# FROM python:3.12-slim
# # FROM python:3.12-bookworm

# # Install required system dependencies
# RUN apt-get update && apt-get install -y \
#     wget \
#     curl \
#     supervisor \
#     && rm -rf /var/lib/apt/lists/*

# # Install Qdrant
# RUN wget https://github.com/qdrant/qdrant/releases/download/v1.15.5/qdrant-x86_64-unknown-linux-gnu.tar.gz && \
#     tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz && \
#     mv qdrant /usr/local/bin/ && \
#     rm qdrant-x86_64-unknown-linux-gnu.tar.gz

# # Set working directory
# WORKDIR /app

# # Copy Python requirements and install
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# # Copy application code
# COPY . .

# # Create directories for Qdrant
# RUN mkdir -p /qdrant/storage /qdrant/config

# # Create Qdrant config
# RUN echo 'log_level: INFO' > /qdrant/config/production.yaml

# # Create supervisor config to run both services
# RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo '[program:qdrant]' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'command=/usr/local/bin/qdrant --config-path /qdrant/config/production.yaml' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'directory=/qdrant' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo '[program:streamlit]' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'command=streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
#     echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf

# # Update your Python code to use localhost instead of "qdrant"
# ENV QDRANT_HOST=localhost
# ENV QDRANT_PORT=6333

# # Expose both ports
# EXPOSE 8501 6333 6334

# # Start supervisor to manage both processes
# CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# Builder stage - Install dependencies
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python packages
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage - Minimal final image
FROM python:3.12-slim

# Install only runtime dependencies
# In your runtime stage
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    supervisor \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Qdrant
RUN wget https://github.com/qdrant/qdrant/releases/download/v1.15.5/qdrant-x86_64-unknown-linux-gnu.tar.gz && \
    tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz && \
    mv qdrant /usr/local/bin/ && \
    rm qdrant-x86_64-unknown-linux-gnu.tar.gz

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create Qdrant directories
RUN mkdir -p /qdrant/storage /qdrant/config && \
    echo 'log_level: INFO' > /qdrant/config/production.yaml

# Create supervisor config
RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:qdrant]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/usr/local/bin/qdrant --config-path /qdrant/config/production.yaml' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:streamlit]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf

ENV QDRANT_HOST=localhost
ENV QDRANT_PORT=6333

EXPOSE 8501 6333 6334

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]