FROM python:3.10-slim

RUN mkdir -p /opt/orchestrate-core-runtime
WORKDIR /opt/orchestrate-core-runtime
COPY . /opt/orchestrate-core-runtime

RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git nodejs npm \
 && curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
 && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list \
 && apt-get update && apt-get install -y ngrok

RUN npm install -g netlify-cli

RUN pip install --no-cache-dir --only-binary=:all: watchdog

RUN pip install --no-cache-dir \
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

RUN chmod +x entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
