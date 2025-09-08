#!/bin/bash
export PYTHONPATH="$PYTHONPATH:/opt/orchestrate-core-runtime"
USER_DIR="/orchestrate_user"
STATE_DIR="/container_state"
OUTPUT_DIR="/app"
RUNTIME_DIR="/tmp/runtime"
mkdir -p "$USER_DIR/dropzone"
mkdir -p "$USER_DIR/vault/watch_books"
mkdir -p "$USER_DIR/vault/watch_transcripts"
mkdir -p "$USER_DIR/orchestrate_exports/markdown"
mkdir -p "$STATE_DIR"
# Prompt if not passed in
if [ -z "$NGROK_TOKEN" ]; then
  read -p "🔐 Enter your ngrok authtoken: " NGROK_TOKEN
fi
if [ -z "$NGROK_DOMAIN" ]; then
  read -p "🌐 Enter your ngrok domain (e.g. clever-bear.ngrok-free.app): " NGROK_DOMAIN
fi
export NGROK_TOKEN
export NGROK_DOMAIN
export DOMAIN="$NGROK_DOMAIN"
export SAFE_DOMAIN=$(echo "$NGROK_DOMAIN" | sed 's|https://||g' | sed 's|[-.]|_|g')
IDENTITY_FILE="$STATE_DIR/system_identity.json"
if [ ! -f "$IDENTITY_FILE" ]; then
  UUID=$(cat /proc/sys/kernel/random/uuid)
  USER_ID="orch-${UUID}"
  TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "{\"user_id\": \"$USER_ID\", \"installed_at\": \"$TIMESTAMP\"}" > "$IDENTITY_FILE"
  # Ledger sync
  BIN_ID="68292fcf8561e97a50162139"
  API_KEY='$2a$10$MoavwaWsCucy2FkU/5ycV.lBTPWoUq4uKHhCi9Y47DOHWyHFL3o2C'
  
  # DEBUG: Check what's in the app directory
  echo "DEBUG: Contents of /app:"
  ls -la /app/
  echo "DEBUG: Looking for: $OUTPUT_DIR/referrer.txt"
  
  if [ -f "$OUTPUT_DIR/referrer.txt" ]; then
    REFERRER_ID=$(cat "$OUTPUT_DIR/referrer.txt" | tr -d '\n\r' | xargs)
    echo "DEBUG: Found referrer ID: '$REFERRER_ID'"
  else
    REFERRER_ID=""
    echo "DEBUG: No referrer file found"
  fi
  
  LEDGER=$(curl -s -X GET "https://api.jsonbin.io/v3/b/$BIN_ID/latest" -H "X-Master-Key: $API_KEY")
  INSTALLS=$(echo "$LEDGER" | jq '.record.installs')
  INSTALLS=$(echo "$INSTALLS" | jq --arg uid "$USER_ID" --arg ts "$TIMESTAMP" \
    '.[$uid] = { referral_count: 0, referral_credits: 3, tools_unlocked: ["json_manager"], timestamp: $ts }')
  
  if [ "$REFERRER_ID" != "" ]; then
    echo "DEBUG: About to credit referrer: $REFERRER_ID"
    INSTALLS=$(echo "$INSTALLS" | jq --arg rid "$REFERRER_ID" \
      'if .[$rid] != null then .[$rid].referral_count += 1 | .[$rid].referral_credits += 3 else . end')
    echo "DEBUG: Referrer crediting completed"
  else
    echo "DEBUG: No referrer to credit"
  fi
  
  FINAL=$(jq -n --argjson installs "$INSTALLS" '{filename: "install_ledger.json", installs: $installs}')
  echo "$FINAL" | curl -s -X PUT "https://api.jsonbin.io/v3/b/$BIN_ID" \
    -H "Content-Type: application/json" -H "X-Master-Key: $API_KEY" --data @-
  echo '{ "referral_count": 0, "referral_credits": 3, "tools_unlocked": ["json_manager"] }' > "$STATE_DIR/referrals.json"
fi
RUNTIME_DIR="/opt/orchestrate-core-runtime"
if [ ! -d "$RUNTIME_DIR/.git" ]; then
  git clone https://github.com/unmistakablecreative/orchestrate-core-runtime.git "$RUNTIME_DIR"
fi
mkdir -p "$RUNTIME_DIR/data"
echo '{ "token": "'$NGROK_TOKEN'", "domain": "'$NGROK_DOMAIN'" }' > "$RUNTIME_DIR/data/ngrok.json"
cd "$RUNTIME_DIR"
# Writable GPT output path inside Docker (host-mapped)
GPT_FILE="/orchestrate_user/_paste_into_gpt.txt"
rm -f "$GPT_FILE"
if [ -f "openapi_template.yaml" ] && [ -f "instructions_template.json" ]; then
  envsubst < openapi_template.yaml > /orchestrate_user/openapi.yaml
  envsubst < instructions_template.json > /orchestrate_user/custom_instructions.json
  echo "📎 === CUSTOM INSTRUCTIONS ===" > "$GPT_FILE"
  cat /orchestrate_user/custom_instructions.json >> "$GPT_FILE"
  echo -e "\n\n📎 === OPENAPI.YAML ===" >> "$GPT_FILE"
  cat /orchestrate_user/openapi.yaml >> "$GPT_FILE"
else
  echo "⚠️ Template files missing. You can still run Orchestrate." > "$GPT_FILE"
fi
echo ""
echo "📄 Instruction file content:"
cat "$GPT_FILE"
# Launch tunnel + FastAPI
ngrok config add-authtoken "$NGROK_TOKEN"
ngrok http --domain="$NGROK_DOMAIN" 8000 > /dev/null &
sleep 3
exec uvicorn jarvis:app --host 0.0.0.0 --port 8000
