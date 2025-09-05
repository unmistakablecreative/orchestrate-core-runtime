# ✅ REFACTORED system_settings.py — fully Execution Hub–compatible, handles .md files, returns consistent output

import os
import json
import argparse
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TOOLS_DIR, ".."))

SETTINGS_FILE = os.path.join(ROOT_DIR, "system_settings.ndjson")
CREDENTIALS_FILE = os.path.join(TOOLS_DIR, "credentials.json")
MEMORY_INDEX_FILE = os.path.join(ROOT_DIR, "memory_index.json")
ROUTER_MAP_FILE = os.path.join(TOOLS_DIR, "router_map.json")
WORKING_MEMORY_PATH = os.path.join(ROOT_DIR, "data", "working_memory.json")

def output(data):
    print(json.dumps(data, indent=2))
    sys.exit(0)

def error(message):
    print(json.dumps({"status": "error", "message": message}, indent=2))
    sys.exit(1)

# === Credentials ===
def set_credential(params):
    key, value = params.get("key"), params.get("value")
    if not key or not value:
        error("Missing 'key' or 'value'")
    creds = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds = json.load(f)
    creds[key] = value
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    return {"status": "success", "message": f"Credential '{key}' set."}


def load_credential(key):
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE, "r") as f:
        creds = json.load(f)
    return creds.get(key)



# === CLI Routes ===
def add_cli_route(params):
    name, command = params.get("action_name"), params.get("command")
    if not name or not command:
        error("Missing 'action_name' or 'command'")
    routes = {}
    if os.path.exists(ROUTER_MAP_FILE):
        with open(ROUTER_MAP_FILE, "r") as f:
            routes = json.load(f)
    routes[name] = command
    with open(ROUTER_MAP_FILE, "w") as f:
        json.dump(routes, f, indent=2)
    return {"status": "success", "message": f"CLI route '{name}' added."}

def remove_cli_route(params):
    name = params.get("action_name")
    if not name:
        error("Missing 'action_name'")
    if not os.path.exists(ROUTER_MAP_FILE):
        error("router_map.json not found.")
    with open(ROUTER_MAP_FILE, "r") as f:
        routes = json.load(f)
    if name not in routes:
        error(f"CLI route '{name}' not found.")
    del routes[name]
    with open(ROUTER_MAP_FILE, "w") as f:
        json.dump(routes, f, indent=2)
    return {"status": "success", "message": f"CLI route '{name}' removed."}

def list_cli_routes(_):
    if not os.path.exists(ROUTER_MAP_FILE):
        return {"status": "success", "routes": {}}
    with open(ROUTER_MAP_FILE, "r") as f:
        return {"status": "success", "routes": json.load(f)}

# === Tool Registry ===
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return []
    with open(SETTINGS_FILE, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")

def add_tool(params):
    tool, path = params.get("tool"), params.get("path")
    if not tool or not path:
        error("Missing 'tool' or 'path'")

    entry = {
        "tool": tool,
        "action": "__tool__",
        "script_path": path
    }

    # ✅ Optional lock flags
    if "locked" in params:
        entry["locked"] = params["locked"]
    if "referral_unlock_cost" in params:
        entry["referral_unlock_cost"] = params["referral_unlock_cost"]

    data = load_settings()
    data.append(entry)
    save_settings(data)

    return {"status": "success", "message": f"Tool '{tool}' registered."}



def remove_tool(params):
    tool = params.get("tool")
    if not tool:
        error("Missing 'tool'")
    data = load_settings()
    updated = [d for d in data if d["tool"] != tool]
    save_settings(updated)
    return {"status": "success", "message": f"Tool '{tool}' and all actions removed."}

def list_tools(_):
    return {"status": "success", "tools": [d for d in load_settings() if d["action"] == "__tool__"]}



def add_action(params):
    required = ["tool", "action", "script", "params", "example"]
    if not all(k in params for k in required):
        error("Missing one of: tool, action, script, params, example")
    
    data = load_settings()
    
    # Add the new action
    data.append({
        "tool": params["tool"],
        "action": params["action"],
        "script_path": params["script"],
        "params": params["params"],
        "example": params["example"]
    })
    
    # 🔧 Sort all actions: first by tool, then by action name
    data.sort(key=lambda x: (x["tool"], x["action"]))
    
    save_settings(data)
    
    return {"status": "success", "message": f"Action '{params['action']}' added to '{params['tool']}'."}







def list_actions(params):
    tool = params.get("tool")
    all_actions = [d for d in load_settings() if d["action"] != "__tool__"]
    return {"status": "success", "actions": [a for a in all_actions if a["tool"] == tool] if tool else all_actions}


# === Memory Index ===

def load_memory_index():
    """Load memory_index.json and return the 'entries' list. Compatible with schema and legacy list fallback."""
    if not os.path.exists(MEMORY_INDEX_FILE):
        return []
    try:
        with open(MEMORY_INDEX_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "entries" in data:
                return data["entries"]
            elif isinstance(data, list):
                return data  # legacy fallback
    except Exception:
        return []
    return []

def save_memory_index(index):
    """Always write valid schema: { 'entries': [ ... ] }"""
    with open(MEMORY_INDEX_FILE, "w") as f:
        json.dump({"entries": index}, f, indent=2)

def add_memory_file(params):
    path = params.get("path")
    if not path:
        error("Missing 'path'")
    index = load_memory_index()
    if path not in index:
        index.append(path)
        save_memory_index(index)
    return {"status": "success", "message": f"Memory file '{path}' added."}

def remove_memory_file(params):
    path = params.get("path")
    if not path:
        error("Missing 'path'")
    index = load_memory_index()
    if path in index:
        index.remove(path)
        save_memory_index(index)
        return {"status": "success", "message": f"Memory file '{path}' removed."}
    return {"status": "error", "message": f"File '{path}' not found in memory index."}

def list_memory_files(_):
    return {"status": "success", "memory_files": load_memory_index()}

def build_working_memory(_):
    index = load_memory_index()
    memory = {}

    for rel_path in index:
        key = rel_path if not rel_path.startswith("/") else os.path.relpath(rel_path, ROOT_DIR)
        abs_path = os.path.join(ROOT_DIR, rel_path) if not os.path.isabs(rel_path) else rel_path

        if not os.path.exists(abs_path):
            memory[key] = f"<<ERROR: File not found — {rel_path}>>"
            continue

        try:
            with open(abs_path, "r") as f:
                if abs_path.endswith(".ndjson"):
                    memory[key] = [json.loads(line) for line in f if line.strip()]
                elif abs_path.endswith(".json"):
                    memory[key] = json.load(f)
                else:
                    memory[key] = f.read()
        except Exception as e:
            memory[key] = f"<<ERROR: {str(e)}>>"

    os.makedirs(os.path.dirname(WORKING_MEMORY_PATH), exist_ok=True)
    with open(WORKING_MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)

    return {
        "status": "success",
        "message": f"Working memory rebuilt clean at {WORKING_MEMORY_PATH}"
    }



def install_tool(params):
    import importlib.util
    import re

    script_path = params.get("script_path")
    if not script_path:
        error("Missing 'script_path'")

    abs_path = os.path.join(ROOT_DIR, script_path)
    if not os.path.exists(abs_path):
        error(f"Script path not found: {abs_path}")

    module_name = os.path.splitext(os.path.basename(abs_path))[0]

    # === Step 1: Register tool metadata
    tool_entry = {
        "tool": module_name,
        "action": "__tool__",
        "script_path": script_path
    }

    settings = load_settings()
    settings.append(tool_entry)

    # === Step 2: Load script and parse for functions
    try:
        with open(abs_path, "r") as f:
            code = f.read()
    except Exception as e:
        error(f"Failed to read script: {str(e)}")

    pattern = r"def (\w+)\(params\):"
    matches = re.findall(pattern, code)

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

    # === Step 3: Append actions to settings
    settings.extend(actions)
    save_settings(settings)

    return {
        "status": "success",
        "message": f"✅ Installed tool '{module_name}' with {len(actions)} actions.",
        "actions": [a["action"] for a in actions]
    }




def list_supported_actions(_):
    return {"status": "success", "supported": list(dispatch_map.keys())}


## App Store Refresh

def refresh_orchestrate_runtime(_):
    import os
    import requests
    import json
    import ast
    from pathlib import Path

    ROOT_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT_DIR / "data"
    TOOLS_DIR = ROOT_DIR / "tools"
    SETTINGS_PATH = ROOT_DIR / "system_settings.ndjson"

    BASE_RAW = "https://raw.githubusercontent.com/unmistakablecreative/orchestrate-core-runtime/main/"
    GITHUB_API_TOOLS = "https://api.github.com/repos/unmistakablecreative/orchestrate-core-runtime/contents/tools"

    results = []
    updated = 0
    new_actions = []

    # === Refresh shared data files ===
    data_files = {
        "data/orchestrate_app_store.json": DATA_DIR / "orchestrate_app_store.json",
        "data/update_messages.json": DATA_DIR / "update_messages.json"
    }

    for remote_path, local_path in data_files.items():
        try:
            url = BASE_RAW + remote_path
            response = requests.get(url)
            response.raise_for_status()
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(response.text)
            results.append(f"✅ Refreshed {remote_path}")
        except Exception as e:
            results.append(f"❌ Failed to refresh {remote_path}: {e}")

    # === Load app store metadata ===
    try:
        with open(DATA_DIR / "orchestrate_app_store.json", "r") as f:
            app_store = json.load(f).get("entries", {})
    except Exception as e:
        app_store = {}
        results.append(f"❌ Failed to load app store: {e}")

    # === Ensure credentials.json exists but never overwrite ===
    creds_path = TOOLS_DIR / "credentials.json"
    if not creds_path.exists():
        creds_path.write_text("{}")
        results.append("🛡️ Created blank credentials.json")
    else:
        results.append("⏭️ Skipped credentials.json (already exists)")

    # === Load existing system settings ===
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, "r") as f:
            existing_lines = f.readlines()
        try:
            settings = [json.loads(line) for line in existing_lines]
        except Exception as e:
            results.append(f"❌ Failed to parse existing system_settings.ndjson: {e}")
            settings = []
    else:
        settings = []

    existing_keys = {(s["tool"], s["action"]) for s in settings}

    # === Helper to extract functions from tool ===
    def extract_actions(path):
        with open(path, "r") as f:
            tree = ast.parse(f.read())
        return [
            {"action": node.name, "params": [arg.arg for arg in node.args.args if arg.arg != "_"]}
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]

    # === Pull tools from GitHub ===
    try:
        tool_entries = requests.get(GITHUB_API_TOOLS).json()
        for entry in tool_entries:
            name = entry.get("name", "")
            if not name.endswith(".py") or name == "credentials.json":
                continue

            tool_name = name.replace(".py", "")
            is_marketplace = tool_name in app_store
            is_free = app_store.get(tool_name, {}).get("referral_unlock_cost", 1) == 0

            if is_marketplace and not is_free:
                # Tool is paid — skip unless unlocked manually
                results.append(f"⏭️ Skipped locked marketplace tool: {tool_name}")
                continue

            try:
                tool_code = requests.get(entry["download_url"]).text
                tool_path = TOOLS_DIR / name
                tool_path.write_text(tool_code)
                results.append(f"🔁 Updated tool: {name}")
                updated += 1

                actions = extract_actions(tool_path)
                for act in actions:
                    key = (tool_name, act["action"])
                    if key not in existing_keys:
                        entry_obj = {
                            "tool": tool_name,
                            "action": act["action"],
                            "script_path": f"tools/{name}",
                            "params": act["params"]
                        }
                        settings.append(entry_obj)
                        existing_keys.add(key)
                        new_actions.append(f"{tool_name}.{act['action']}")

            except Exception as e:
                results.append(f"❌ Failed to process {name}: {e}")
    except Exception as e:
        results.append(f"❌ Could not fetch tools: {e}")

    # === Write merged system_settings.ndjson ===
    try:
        with open(SETTINGS_PATH, "w") as f:
            for entry in settings:
                f.write(json.dumps(entry) + "\n")
        results.append(f"✅ Saved merged system_settings.ndjson with {len(settings)} actions")
    except Exception as e:
        results.append(f"❌ Failed to write system_settings.ndjson: {e}")

    summary = f"🧩 {updated} tools updated | ➕ {len(new_actions)} new actions registered"
    results.append(summary)

    return {
        "status": "complete" if updated or new_actions else "noop",
        "messages": results
    }




# === Dispatch Map ===
dispatch_map = {
    "set_credential": set_credential,
    "load_credential": load_credential,
    "add_tool": add_tool,
    "remove_tool": remove_tool,
    "list_tools": list_tools,
    "add_action": add_action,
    "list_actions": list_actions,
    "add_cli_route": add_cli_route,
    "remove_cli_route": remove_cli_route,
    "list_cli_routes": list_cli_routes,
    "add_memory_file": add_memory_file,
    "remove_memory_file": remove_memory_file,
    "list_memory_files": list_memory_files,
    "build_working_memory": build_working_memory,
    "list_supported_actions": list_supported_actions,
    "refresh_orchestrate_runtime": refresh_orchestrate_runtime,
    "install_tool": install_tool
}



# === Entrypoint ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--params", required=False)
    args = parser.parse_args()

    try:
        action = args.action
        params = json.loads(args.params) if args.params else {}
        if action not in dispatch_map:
            error(f"Unsupported action '{action}'")
        result = dispatch_map[action](params)
        output(result)
    except Exception as e:
        error(str(e))
