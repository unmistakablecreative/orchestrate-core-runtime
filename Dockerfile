FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y \
    curl jq unzip gettext \
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
    oauthlib

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["uvicorn", "jarvis:app", "--host", "0.0.0.0", "--port", "8000"]
