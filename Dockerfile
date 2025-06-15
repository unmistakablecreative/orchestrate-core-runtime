FROM python:3.10-slim

# Create runtime directory
RUN mkdir -p /opt/orchestrate-core-runtime

# Set working directory to runtime path
WORKDIR /opt/orchestrate-core-runtime

# Copy all files into the runtime path
COPY . /opt/orchestrate-core-runtime

# Install system packages, Node.js (for Netlify), and ngrok
RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git nodejs npm \
 && curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
 && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list \
 && apt-get update && apt-get install -y ngrok \
 && pip install --no-cache-dir \
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
    requests-oauthlib \
    watchdog

# Install Netlify CLI globally
RUN npm install -g netlify-cli

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Open port
EXPOSE 8000

# Start the app
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
