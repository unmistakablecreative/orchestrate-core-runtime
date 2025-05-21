#!/bin/bash

cd "$(dirname "$0")"

# Prompt for ngrok credentials
if [ -z "$NGROK_TOKEN" ]; then
  read -p "🔐 Enter your ngrok authtoken: " NGROK_TOKEN
fi

if [ -z "$NGROK_DOMAIN" ]; then
  read -p "🌐 Enter your ngrok domain (e.g. custom-subdomain.ngrok.app): " NGROK_DOMAIN
fi

export NGROK_TOKEN
export NGROK_DOMAIN
export DOMAIN="$NGROK_DOMAIN"
export SAFE_DOMAIN=$(echo "$NGROK_DOMAIN" | sed 's|https://||g' | sed 's|[-.]|_|g')

UUID=$(cat /proc/sys/kernel/random/uuid)
USER_ID="orch-${UUID}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "{\"user_id\": \"$USER_ID\", \"installed_at\": \"$TIMESTAMP\"}" > ../system_identity.json
echo '{ "referral_count": 0, "referral_credits": 0, "tools_unlocked": ["json_manager"] }' > ../referrals.json

# Clone core logic if missing (failsafe)
if [ ! -d "orchestrate-core-runtime" ]; then
  git clone https://github.com/unmistakablecreative/orchestrate-core-runtime.git
fi

cd orchestrate-core-runtime

# Build config files from templates
envsubst < openapi_template.yaml > ../openapi.yaml
envsubst < instructions_template.json > ../custom_instructions.json

cd ..

# Launch ngrok and server
ngrok config add-authtoken "$NGROK_TOKEN"
ngrok http --domain="$NGROK_DOMAIN" 8000 > /dev/null &

sleep 3
cd orchestrate-core-runtime
exec uvicorn jarvis:app --host 0.0.0.0 --port 8000
