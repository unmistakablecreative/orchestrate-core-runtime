FROM python:3.10-slim

WORKDIR /opt/orchestrate-core-runtime

COPY . /opt/orchestrate-core-runtime

RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git gnupg ca-certificates build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g netlify-cli --prefix=/usr/local \
    && ln -s /usr/local/bin/netlify /usr/bin/netlify \
    && /usr/local/bin/netlify --version || (echo '❌ Netlify CLI not installed' && exit 1) \
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

RUN chmod +x /opt/orchestrate-core-runtime/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/bash", "/opt/orchestrate-core-runtime/entrypoint.sh"]
