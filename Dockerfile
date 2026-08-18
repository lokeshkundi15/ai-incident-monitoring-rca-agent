FROM python:3.12-slim

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and scripts
COPY . .

# Set execution permission for entrypoint script
RUN chmod +x /app/entrypoint.sh

# Expose Streamlit (8501) and FastAPI (8000)
EXPOSE 8501 8000

# Wire entrypoint script as main container startup command
ENTRYPOINT ["/app/entrypoint.sh"]