FROM python:3.10-slim

RUN mkdir -p /opt/orchestrate-core-runtime
WORKDIR /opt/orchestrate-core-runtime
COPY . /opt/orchestrate-core-runtime

RUN apt-get update && apt-get install -y \
  build-essential \
  gcc \
  python3-dev \
  libffi-dev \
  libc6-dev \
  curl jq unzip gettext git nodejs npm \
  && apt-get clean

RUN pip install --no-cache-dir watchdog

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

RUN npm install -g netlify-cli

RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
