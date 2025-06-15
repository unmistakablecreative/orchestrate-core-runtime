FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy all files from your installer folder into /app
COPY . /app

# Install required system packages, Node.js, and ngrok
RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git gnupg ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g netlify-cli \
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
        watchdog  # 👈 File watcher support

# Make sure entrypoint.sh is executable
RUN chmod +x /app/entrypoint.sh

# Expose API port
EXPOSE 8000

# Launch entrypoint script
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
