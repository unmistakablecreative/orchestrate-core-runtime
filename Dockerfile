FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy all files from your installer folder into /app
COPY . /app

# Install required system packages and ngrok
RUN apt-get update && apt-get install -y \
    curl jq unzip gettext git \
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
    requests-oauthlib

# Make sure entrypoint.sh is executable
RUN chmod +x /app/entrypoint.sh

# Open port 8000 for the API
EXPOSE 8000

# When container starts, run the entrypoint script
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
