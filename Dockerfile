FROM python:3.10-slim

# Install system packages
RUN apt-get update && apt-get install -y \
  build-essential \
  gcc \
  python3-dev \
  libffi-dev \
  libc-dev \
  curl jq unzip gettext git nodejs npm \
  poppler-utils \
  && curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list \
  && apt-get update && apt-get install -y ngrok \
  && apt-get clean

# Install Netlify CLI
RUN npm install -g netlify-cli

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Python packages (original + new)
RUN pip install --no-cache-dir \
  watchdog \
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
  pdfplumber \
  python-docx \
  pandas \
  lxml

# Prepare runtime
RUN mkdir -p /opt/orchestrate-core-runtime
WORKDIR /opt/orchestrate-core-runtime
COPY . /opt/orchestrate-core-runtime

# Set executable permissions
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Keep the original entrypoint path
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
