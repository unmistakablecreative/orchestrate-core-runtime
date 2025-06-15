FROM python:3.10-slim

# Create runtime directory
RUN mkdir -p /opt/orchestrate-core-runtime

# Set working directory
WORKDIR /opt/orchestrate-core-runtime

# Copy all files into the container
COPY . /opt/orchestrate-core-runtime

# Install system packages, node, npm, ngrok
RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git nodejs npm \
 && curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
 && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list \
 && apt-get update && apt-get install -y ngrok

# Install Netlify CLI globally
RUN npm install -g netlify-cli

# Install all Python dependencies explicitly
RUN pip install --no-cache-dir watchdog && \
    pip install --no-cache-dir \
        fastapi \
        uvicorn \
        pydantic \
        requests \
        beautifulsoup4 \
        python-dotenv \
        pyyaml \
        python-multipart \
        astor \
        oauthlib \
        requests-oauthlib

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose app port
EXPOSE 8000

# Start entrypoint
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
