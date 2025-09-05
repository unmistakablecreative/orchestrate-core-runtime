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
    import ast
    import builtins
    import requests
    import json
    import os
    import sys

    SETTINGS_FILE = "/opt/orchestrate-core-runtime/system_settings.ndjson"
    TOOLS_DIR = "/opt/orchestrate-core-runtime/tools"
    APP_STORE_PATH = "/opt/orchestrate-core-runtime/data/orchestrate_app_store.json"

    # === Config: tools that require warnings
    credential_warnings = {
        "outline_editor": "⚠️ This tool requires your Outline API key. Use system_settings.set_credential() to set it.",
        "ideogram_tool": "⚠️ This tool requires your Ideogram API key.",
        "buffer_engine": "⚠️ This tool requires your Twitter API credentials.",
        "readwise_tool": "⚠️ This tool requires your Readwise API key.",
        "nylasinbox": "⚠️ This tool requires your Nylas API credentials.",
        "notion_tool": "⚠️ This tool requires your Notion API token."
    }

    # === Step 1: Load ledger + user
    user_id = load_system_identity()
    ledger = get_ledger()
    user = ledger["installs"].get(user_id, {})
    available_credits = user.get("referral_credits", 0)

    # === Step 2: Load app store metadata
    if not os.path.exists(APP_STORE_PATH):
        return {"status": "error", "message": "❌ App store metadata not found."}

    with open(APP_STORE_PATH, "r") as f:
        store_data = json.load(f)

    store_entry = store_data.get("entries", {}).get(tool_name)
    if not store_entry:
        return {"status": "error", "message": f"❌ Tool '{tool_name}' not found in app store."}

    cost = store_entry.get("referral_unlock_cost", 1)
    description = store_entry.get("description", "No description available.")

    if available_credits < cost:
        return {"status": "locked", "message": f"🚫 You need {cost} credits to unlock '{tool_name}'."}

    # === Step 3: Pull script from GitHub
    github_url = f"https://raw.githubusercontent.com/unmistakablecreative/orchestrate-core-runtime/main/tools/{tool_name}.py"
    dest_path = os.path.join(TOOLS_DIR, f"{tool_name}.py")

    try:
        response = requests.get(github_url)
        response.raise_for_status()
        with open(dest_path, "w") as f:
            f.write(response.text)
    except Exception as e:
        return {"status": "error", "message": f"❌ Failed to fetch tool script: {str(e)}"}

    # === Step 4: Install dependencies
    def infer_dependencies(path):
        required = set()
        with open(path, "r") as f:
            for line in f:
                if line.startswith("import ") or line.startswith("from "):
                    parts = line.replace(",", " ").split()
                    if parts[0] in ("import", "from") and len(parts) > 1:
                        required.add(parts[1].split(".")[0])
        return list(required)

    def install_deps(deps):
        installed, skipped = [], []
        stdlib = set(sys.builtin_module_names).union(set(dir(builtins)))
        for dep in deps:
            if dep in stdlib or importlib.util.find_spec(dep):
                skipped.append(dep)
                continue
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                installed.append(dep)
            except Exception as e:
                return {"status": "error", "message": f"❌ Failed to install {dep}", "details": str(e)}
        return {"status": "success", "message": f"✅ Installed: {installed or 'None'} | Skipped: {skipped or 'None'}"}

    dep_result = install_deps(infer_dependencies(dest_path))
    if dep_result["status"] != "success":
        return dep_result

    # === Step 5: Extract actions
    def extract_actions(script_path, tool_name):
        with open(script_path, "r") as f:
            tree = ast.parse(f.read(), filename=script_path)

        actions = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_") and node.name not in ("main", "run", "error"):
                param_keys = [arg.arg for arg in node.args.args if arg.arg not in ("self", "params")]
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and hasattr(child.func, "attr") and child.func.attr == "get":
                        if child.args and isinstance(child.args[0], ast.Str):
                            key = child.args[0].s
                            if key not in param_keys:
                                param_keys.append(key)

                example = {
                    "tool_name": tool_name,
                    "action": node.name,
                    "params": {k: f"<{k}>" for k in param_keys}
                }

                actions.append({
                    "tool": tool_name,
                    "action": node.name,
                    "script_path": f"tools/{tool_name}.py",
                    "params": param_keys,
                    "example": example
                })
        return actions

    # === Step 6: Update system_settings.ndjson
    def load_settings():
        with open(SETTINGS_FILE, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    def save_settings(data):
        with open(SETTINGS_FILE, "w") as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")

    settings = load_settings()
    keys = {(s["tool"], s["action"]) for s in settings}

    # Inject __tool__ entry with description
    tool_key = (tool_name, "__tool__")
    if tool_key not in keys:
        settings.append({
            "tool": tool_name,
            "action": "__tool__",
            "script_path": f"tools/{tool_name}.py",
            "locked": False,
            "referral_unlock_cost": cost,
            "description": description
        })

    # Inject actions
    actions = extract_actions(dest_path, tool_name)
    for a in actions:
        key = (a["tool"], a["action"])
        if key not in keys:
            settings.append(a)

    save_settings(settings)

    # === Step 7: Debit user + save
    user["referral_credits"] -= cost
    user.setdefault("tools_unlocked", []).append(tool_name)
    user["tools_unlocked"] = list(set(user["tools_unlocked"]))
    ledger["installs"][user_id] = user
    put_ledger(ledger)
    save_unlock_status({
        "unlock_credits": user["referral_credits"],
        "tools_unlocked": user["tools_unlocked"]
    })

    # === Final response
    return {
        "status": "success",
        "message": f"✅ '{tool_name}' fully installed, unlocked, and ready to use.",
        "actions": [a["action"] for a in actions],
        "dependencies": dep_result.get("message"),
        "credentials": credential_warnings.get(tool_name, "—")
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
