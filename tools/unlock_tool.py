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
UNLOCK_STATUS_PATH = "/opt/orchestrate-core-runtime/data/unlock_status.json"

# === Utilities ===
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

def save_unlock_status(user):
    data = {
        "unlock_credits": user.get("unlock_credits", 0),
        "tools_unlocked": user.get("tools_unlocked", [])
    }
    os.makedirs(os.path.dirname(UNLOCK_STATUS_PATH), exist_ok=True)
    with open(UNLOCK_STATUS_PATH, "w") as f:
        json.dump(data, f, indent=2)

# === Main Unlock Logic ===
def unlock_tool(tool_name):
    user_id = load_system_identity()
    ledger = get_ledger()

    if user_id not in ledger["installs"]:
        save_unlock_status({})
        return {
            "status": "error",
            "message": "❌ User not found in install_ledger"
        }

    user = ledger["installs"][user_id]
    available_credits = user.get("referral_credits", 0)  # Still named this in JSONBin
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
                save_unlock_status({
                    "unlock_credits": available_credits,
                    "tools_unlocked": user.get("tools_unlocked", [])
                })
                return {
                    "status": "noop",
                    "message": f"⚠️ Tool '{tool_name}' is already unlocked."
                }

            cost = entry.get("referral_unlock_cost", 1)
            if available_credits < cost:
                save_unlock_status({
                    "unlock_credits": available_credits,
                    "tools_unlocked": user.get("tools_unlocked", [])
                })
                return {
                    "status": "locked",
                    "message": f"🚫 You need {cost} credits to unlock '{tool_name}'. Refer someone to earn credits and you'll be able to unlock more tools."
                }

            # ✅ Perform unlock
            entry["locked"] = False
            user["referral_credits"] = available_credits - cost
            user["tools_unlocked"] = list(set(user.get("tools_unlocked", []) + [tool_name]))

            save_ndjson(NDJSON_PATH, settings)
            put_ledger(ledger)

            save_unlock_status({
                "unlock_credits": user["referral_credits"],
                "tools_unlocked": user["tools_unlocked"]
            })

            message = f"✅ '{tool_name}' unlocked. Remaining credits: {user['referral_credits']}"
            if tool_name in credential_warning:
                message += f"\n{credential_warning[tool_name]}"

            return {
                "status": "success",
                "message": message
            }

    save_unlock_status({
        "unlock_credits": available_credits,
        "tools_unlocked": user.get("tools_unlocked", [])
    })

    return {
        "status": "error",
        "message": f"❌ Tool '{tool_name}' not found."
    }



def unlock_marketplace_tool(tool_name):
    import subprocess
    import importlib.util
    import re

    def install_dependencies(dependencies):
        installed = []
        for dep in dependencies:
            if importlib.util.find_spec(dep) is None:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    installed.append(dep)
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"❌ Failed to install dependency: {dep}",
                        "details": str(e)
                    }
        return {"status": "success", "message": f"✅ Installed: {', '.join(installed)}"}

    def register_tool_and_actions(script_path, module_name):
        abs_path = os.path.join("/opt/orchestrate-core-runtime", script_path)
        if not os.path.exists(abs_path):
            return {"status": "error", "message": f"Script path not found: {abs_path}"}

        with open(abs_path, "r") as f:
            code = f.read()

        pattern = r"def (\w+)\(params\):"
        matches = re.findall(pattern, code)

        settings = load_ndjson(NDJSON_PATH)

        tool_entry = {
            "tool": module_name,
            "action": "__tool__",
            "script_path": script_path
        }

        actions = []
        for name in matches:
            if name.startswith("_"):
                continue
            actions.append({
                "tool": module_name,
                "action": name,
                "script_path": script_path,
                "params": [],
                "example": {
                    "tool_name": module_name,
                    "action": name,
                    "params": {}
                }
            })

        settings.append(tool_entry)
        settings.extend(actions)
        save_ndjson(NDJSON_PATH, settings)

        return {
            "status": "success",
            "message": f"✅ Registered tool '{module_name}' with {len(actions)} actions."
        }

    # === Step 1: Load user + store
    user_id = load_system_identity()
    ledger = get_ledger()

    if user_id not in ledger["installs"]:
        save_unlock_status({})
        return {"status": "error", "message": "❌ User not found in install_ledger"}

    user = ledger["installs"][user_id]
    available_credits = user.get("referral_credits", 0)

    app_store_path = "/opt/orchestrate-core-runtime/data/orchestrate_app_store.json"
    if not os.path.exists(app_store_path):
        return {"status": "error", "message": "❌ App store metadata not found in container."}

    with open(app_store_path, "r") as f:
        store_data = json.load(f)

    store_entry = store_data.get("entries", {}).get(tool_name)
    if not store_entry:
        return {"status": "error", "message": f"❌ Tool '{tool_name}' not found in app store."}

    cost = store_entry.get("referral_unlock_cost", 1)
    if available_credits < cost:
        return {"status": "locked", "message": f"🚫 You need {cost} credits to unlock '{tool_name}'."}

    # === Step 2: Pull tool script from GitHub
    github_url = f"https://raw.githubusercontent.com/unmistakablecreative/orchestrate-core-runtime/main/tools/{tool_name}.py"
    dest_path = f"/opt/orchestrate-core-runtime/tools/{tool_name}.py"
    rel_path = f"tools/{tool_name}.py"

    try:
        response = requests.get(github_url)
        response.raise_for_status()
        with open(dest_path, "w") as f:
            f.write(response.text)
    except Exception as e:
        return {"status": "error", "message": f"❌ Failed to fetch script: {str(e)}"}

    # === Step 3: Install any needed dependencies
    known_dependencies = {
        "nylasinbox": ["markdown2"],
        "notion_tool": ["requests"],
        "readwise_tool": ["requests"]
    }
    deps = known_dependencies.get(tool_name, [])
    dep_result = install_dependencies(deps)
    if dep_result["status"] != "success":
        return dep_result

    # === Step 4: Register tool + actions directly
    reg_result = register_tool_and_actions(rel_path, tool_name)
    if reg_result["status"] != "success":
        return reg_result

    # === Step 5: Debit credits and update user ledger
    user["referral_credits"] = available_credits - cost
    user["tools_unlocked"] = list(set(user.get("tools_unlocked", []) + [tool_name]))
    put_ledger(ledger)
    save_unlock_status({
        "unlock_credits": user["referral_credits"],
        "tools_unlocked": user["tools_unlocked"]
    })

    return {
        "status": "success",
        "message": f"✅ '{tool_name}' fully installed, registered, and ready to use.",
        "actions": reg_result.get("message")
    }




# === Entrypoint Router ===
def run(params, action):
    try:
        tool_name = params.get("tool_name")
        if action == "unlock_tool":
            return unlock_tool(tool_name)
        elif action == "unlock_marketplace_tool":
            return unlock_marketplace_tool(tool_name)
        else:
            return {"status": "error", "message": f"Unknown action '{action}'"}
    except Exception as e:
        return {"status": "error", "message": "Execution failed", "details": str(e)}

if __name__ == "__main__":
    parser = sys.argv
    if len(parser) < 3 or not parser[1] in ["unlock_tool", "unlock_marketplace_tool"]:
        print(json.dumps({
            "status": "error",
            "message": "Usage: python unlock_tool.py <action> --params '{\"tool_name\": \"calendar_tool\"}'"
        }, indent=2))
        sys.exit(1)

    raw_params = json.loads(parser[3]) if parser[2] == "--params" else {}
    result = run(raw_params, parser[1])
    print(json.dumps(result, indent=2))
