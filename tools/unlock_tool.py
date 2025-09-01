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

    # === Config: tools that require API credentials
    credential_warnings = {
        "outline_editor": "⚠️ This tool requires your Outline API key. Use system_settings.set_credential() to set it.",
        "ideogram_tool": "⚠️ This tool requires your Ideogram API key.",
        "buffer_engine": "⚠️ This tool requires your Twitter API credentials.",
        "readwise_tool": "⚠️ This tool requires your Readwise API key.",
        "nylasinbox": "⚠️ This tool requires your Nylas API credentials.",
        "notion_tool": "⚠️ This tool requires your Notion API token."
    }

    def infer_dependencies_from_script(script_path):
        inferred = set()
        with open(script_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("import "):
                    parts = line.split()
                    if len(parts) >= 2:
                        inferred.add(parts[1].split(".")[0])
                elif line.startswith("from "):
                    parts = line.split()
                    if len(parts) >= 2:
                        inferred.add(parts[1].split(".")[0])
        return list(inferred)

    def install_dependencies(dependencies):
        installed = []
        skipped = []
        stdlib_modules = set(sys.builtin_module_names).union(set(dir(builtins)))

        for dep in dependencies:
            if dep in stdlib_modules:
                skipped.append(dep)
                continue
            if importlib.util.find_spec(dep) is not None:
                skipped.append(dep)
                continue
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
        return {
            "status": "success",
            "message": f"✅ Installed: {', '.join(installed)} | Skipped: {', '.join(skipped)}"
        }

    # === Load ledger and user
    user_id = load_system_identity()
    ledger = get_ledger()

    if user_id not in ledger["installs"]:
        save_unlock_status({})
        return {
            "status": "error",
            "message": "❌ User not found in install_ledger"
        }

    user = ledger["installs"][user_id]
    available_credits = user.get("referral_credits", 0)

    # === Load app store metadata
    app_store_path = "/opt/orchestrate-core-runtime/data/orchestrate_app_store.json"
    if not os.path.exists(app_store_path):
        return {
            "status": "error",
            "message": "❌ App store metadata not found in container."
        }

    with open(app_store_path, "r") as f:
        store_data = json.load(f)

    store_entry = store_data.get("entries", {}).get(tool_name)
    if not store_entry:
        return {
            "status": "error",
            "message": f"❌ Tool '{tool_name}' not found in orchestrate_app_store.json"
        }

    cost = store_entry.get("referral_unlock_cost", 1)
    if available_credits < cost:
        return {
            "status": "locked",
            "message": f"🚫 You need {cost} credits to unlock '{tool_name}'."
        }

    # === STEP 1: Pull script from GitHub
    github_url = f"https://raw.githubusercontent.com/unmistakablecreative/orchestrate-core-runtime/main/tools/{tool_name}.py"
    dest_path = f"/opt/orchestrate-core-runtime/tools/{tool_name}.py"

    try:
        response = requests.get(github_url)
        response.raise_for_status()
        with open(dest_path, "w") as f:
            f.write(response.text)
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Failed to fetch tool from GitHub: {str(e)}"
        }

    # === STEP 2: Install inferred dependencies
    inferred_deps = infer_dependencies_from_script(dest_path)
    dep_result = install_dependencies(inferred_deps)
    if dep_result["status"] != "success":
        return dep_result

    # === STEP 3: Register tool + actions
    SETTINGS_FILE = "/opt/orchestrate-core-runtime/system_settings.ndjson"

    def load_settings():
        with open(SETTINGS_FILE, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    def save_settings(data):
        with open(SETTINGS_FILE, "w") as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")

    def register_tool(tool_name, script_path):
        settings = load_settings()
        tool_entry_found = False
        for entry in settings:
            if entry["tool"] == tool_name and entry["action"] == "__tool__":
                entry["locked"] = False
                entry["referral_unlock_cost"] = 0
                tool_entry_found = True
                break
        if not tool_entry_found:
            settings.append({
                "tool": tool_name,
                "action": "__tool__",
                "script_path": script_path,
                "locked": False,
                "referral_unlock_cost": 0
            })
        return settings

    def extract_actions_from_script(script_path, tool_name):
        with open(script_path, "r") as f:
            tree = ast.parse(f.read(), filename=script_path)

        actions = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                fn_name = node.name
                if fn_name in ("main", "run", "error") or fn_name.startswith("_"):
                    continue

                inferred_params = []
                for arg in node.args.args:
                    if arg.arg not in ("self", "params"):
                        inferred_params.append(arg.arg)

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if (
                            isinstance(child.func, ast.Attribute)
                            and isinstance(child.func.value, ast.Name)
                            and child.func.value.id == "params"
                            and child.func.attr == "get"
                            and len(child.args) >= 1
                            and isinstance(child.args[0], ast.Str)
                        ):
                            key = child.args[0].s
                            if key not in inferred_params:
                                inferred_params.append(key)

                        if (
                            isinstance(child.func, ast.Attribute)
                            and isinstance(child.func.value, ast.Call)
                            and isinstance(child.func.value.func, ast.Attribute)
                            and isinstance(child.func.value.func.value, ast.Name)
                            and child.func.value.func.value.id == "params"
                            and child.func.value.func.attr == "get"
                            and isinstance(child.func.value.args[0], ast.Str)
                            and len(child.args) >= 1
                            and isinstance(child.args[0], ast.Str)
                        ):
                            nested = child.args[0].s
                            parent = child.func.value.args[0].s
                            flat_key = f"{parent}.{nested}"
                            if flat_key not in inferred_params:
                                inferred_params.append(flat_key)

                example = {
                    "tool_name": tool_name,
                    "action": fn_name,
                    "params": {k: f"<{k}>" for k in inferred_params}
                }

                actions.append({
                    "tool": tool_name,
                    "action": fn_name,
                    "script_path": f"tools/{tool_name}.py",
                    "params": inferred_params,
                    "example": example
                })

        return actions

    script_path = f"tools/{tool_name}.py"
    abs_path = dest_path

    try:
        settings = register_tool(tool_name, script_path)
        actions = extract_actions_from_script(abs_path, tool_name)
        settings.extend(actions)
        save_settings(settings)
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Failed to register tool + actions: {str(e)}"
        }

    # === STEP 4: Debit credits + update ledger
    user["referral_credits"] = available_credits - cost
    user["tools_unlocked"] = list(set(user.get("tools_unlocked", []) + [tool_name]))
    put_ledger(ledger)
    save_unlock_status({
        "unlock_credits": user["referral_credits"],
        "tools_unlocked": user["tools_unlocked"]
    })

    # === Optional credential notice
    credential_msg = credential_warnings.get(tool_name)

    return {
        "status": "success",
        "message": f"✅ '{tool_name}' fully installed, unlocked, and ready to use.",
        "actions": [a["action"] for a in actions],
        "dependencies": dep_result.get("message"),
        "credentials": credential_msg if credential_msg else "—"
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
