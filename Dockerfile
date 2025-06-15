FROM python:3.10-slim

RUN mkdir -p /opt/orchestrate-core-runtime
WORKDIR /opt/orchestrate-core-runtime
COPY . /opt/orchestrate-core-runtime

RUN apt-get update && apt-get install -y \
  build-essential \
  gcc \
  python3-dev \
  libffi-dev \
  libc-dev \
  curl jq unzip gettext git nodejs npm \
  && curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list \
  && apt-get update && apt-get install -y ngrok \
  && apt-get clean

RUN npm install -g netlify-cli

# Isolate watchdog fix
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir watchdog

# Install all other required packages
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
