FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files into container
COPY . /app

# Install required system packages, Node.js, and Netlify CLI
RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git gnupg ca-certificates build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g netlify-cli \
    && ln -s /usr/local/bin/netlify /usr/bin/netlify \
    && netlify --version \
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

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose required ports
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
