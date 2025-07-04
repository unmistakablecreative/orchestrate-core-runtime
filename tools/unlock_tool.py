import json
import sys
import requests
import os

# Constants
BIN_ID = "68292fcf8561e97a50162139"
API_KEY = "$2a$10$MoavwaWsCucy2FkU/5ycV.lBTPWoUq4uKHhCi9Y47DOHWyHFL3o2C"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

# Paths
IDENTITY_PATH = "/container_state/system_identity.json"
NDJSON_PATH = "/opt/orchestrate-core-runtime/system_settings.ndjson"
REFERRAL_STATUS_PATH = "/container_state/referrals.json"

def load_system_identity():
    with open(IDENTITY_PATH, "r") as f:
        return json.load(f)["user_id"]

def get_ledger():
    res = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
    res.raise_for_status()
    return res.json()["record"]

def put_ledger(ledger):
    payload = {
        "filename": "install_ledger.json",
        "installs": ledger["installs"]
    }
    res = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=payload)
    res.raise_for_status()

def load_ndjson(path):
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def save_ndjson(path, data):
    with open(path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")

def save_referral_status(user):
    data = {
        "referral_count": user.get("referral_count", 0),
        "referral_credits": user.get("referral_credits", 0),
        "tools_unlocked": user.get("tools_unlocked", [])
    }
    with open(REFERRAL_STATUS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def unlock_tool(tool_name):
    user_id = load_system_identity()
    ledger = get_ledger()

    if user_id not in ledger["installs"]:
        save_referral_status({})
        return {
            "status": "error",
            "message": "❌ User not found in install_ledger"
        }

    user = ledger["installs"][user_id]
    available_credits = user.get("referral_credits", 0)
    settings = load_ndjson(NDJSON_PATH)

    credential_warning = {
        "outline_editor": "⚠️ This tool requires your Outline API key. Use system_settings.set_credential() to set it.",
        "ideogram_tool": "⚠️ This tool requires your Ideogram API key.",
        "buffer_engine": "⚠️ This tool requires your Twitter API credentials.",
        "readwise_tool": "⚠️ This tool requires your Readwise API key."
    }

    for entry in settings:
        if entry["tool"] == tool_name:
            if not entry.get("locked", False):
                save_referral_status(user)
                return {
                    "status": "noop",
                    "message": f"⚠️ Tool '{tool_name}' is already unlocked."
                }

            cost = entry.get("referral_unlock_cost", 1)
            if available_credits < cost:
                save_referral_status(user)
                return {
                    "status": "locked",
                    "message": f"🚫 You need {cost} credits to unlock '{tool_name}'. Refer someone to earn credits and you'll be able to unlock more tools."
                }

            entry["locked"] = False
            user["referral_credits"] = available_credits - cost
            user["tools_unlocked"] = list(set(user.get("tools_unlocked", []) + [tool_name]))

            save_ndjson(NDJSON_PATH, settings)
            put_ledger(ledger)
            save_referral_status(user)

            message = f"✅ '{tool_name}' unlocked. Remaining credits: {user['referral_credits']}"
            if tool_name in credential_warning:
                message += f"\n{credential_warning[tool_name]}"

            return {
                "status": "success",
                "message": message
            }

    save_referral_status(user)
    return {
        "status": "error",
        "message": f"❌ Tool '{tool_name}' not found."
    }



def run(params):
    try:
        tool_name = params.get("tool_name")
        return unlock_tool(tool_name)
    except Exception as e:
        return {"status": "error", "message": "Execution failed", "details": str(e)}

if __name__ == "__main__":
    parser = sys.argv
    if len(parser) < 3 or parser[1] != "unlock_tool":
        print(json.dumps({"status": "error", "message": "Usage: python unlock_tool.py unlock_tool --params '{\"tool_name\": \"calendar_tool\"}'"}, indent=2))
        sys.exit(1)
    raw_params = json.loads(parser[3]) if parser[2] == "--params" else {}
    result = run(raw_params)
    print(json.dumps(result, indent=2))
