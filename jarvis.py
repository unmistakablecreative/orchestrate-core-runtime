from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import subprocess, json, os, logging, shutil

from tools import json_manager
from tools.smart_json_dispatcher import orchestrate_write
from system_guard import validate_action, ContractViolation

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_REGISTRY = os.path.join(BASE_DIR, "system_settings.ndjson")
WORKING_MEMORY_PATH = os.path.join(BASE_DIR, "data", "working_memory.json")
EXEC_HUB_PATH = os.path.join(BASE_DIR, "execution_hub.py")
UPDATE_MESSAGE_PATH = os.path.join(BASE_DIR, "data", "update_message.json")
NGROK_CONFIG_PATH = os.path.join(BASE_DIR, "data", "ngrok.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.on_event("startup")
def sync_tools_and_settings():
    repo_url = "https://github.com/unmistakablecreative/orchestrate-core-runtime.git"
    temp_dir = "/tmp/orchestrate_update"

    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        subprocess.run(["git", "clone", "--depth=1", repo_url, temp_dir], check=True)

        # === Sync tools/ only ===
        tools_src = os.path.join(temp_dir, "tools")
        tools_dst = os.path.join(BASE_DIR, "tools")
        for root, dirs, files in os.walk(tools_src):
            rel_path = os.path.relpath(root, tools_src)
            dest_root = os.path.join(tools_dst, rel_path)
            os.makedirs(dest_root, exist_ok=True)
            for f in files:
                shutil.copy2(os.path.join(root, f), os.path.join(dest_root, f))

        # === Merge system_settings.ndjson ===
        incoming_path = os.path.join(temp_dir, "system_settings.ndjson")
        if os.path.exists(incoming_path):
            existing = []
            if os.path.exists(SYSTEM_REGISTRY):
                with open(SYSTEM_REGISTRY, "r") as f:
                    existing = [json.loads(line.strip()) for line in f if line.strip()]
            existing_keys = {(e["tool"], e["action"]) for e in existing}
            new_entries = []

            with open(incoming_path, "r") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line.strip())
                        key = (entry.get("tool"), entry.get("action"))
                        if key not in existing_keys:
                            new_entries.append(entry)

            all_entries = existing + new_entries
            with open(SYSTEM_REGISTRY, "w") as f:
                for e in all_entries:
                    f.write(json.dumps(e) + "\n")

    except Exception as e:
        logging.warning(f"⚠️ Runtime sync failed: {e}")


@app.on_event("startup")
def restart_ngrok_if_needed():
    try:
        if os.path.exists(NGROK_CONFIG_PATH):
            with open(NGROK_CONFIG_PATH) as f:
                cfg = json.load(f)
                token = cfg.get("token")
                domain = cfg.get("domain")
            running = subprocess.getoutput("pgrep -f 'ngrok http'")
            if not running:
                subprocess.Popen(["ngrok", "config", "add-authtoken", token])
                subprocess.Popen(["ngrok", "http", "--domain=" + domain, "8000"])
    except Exception as e:
        logging.warning(f"⚠️ Ngrok relaunch failed: {e}")


def run_script(tool_name, action, params):
    command = ["python3", EXEC_HUB_PATH, "execute_task", "--params", json.dumps({
        "tool_name": tool_name,
        "action": action,
        "params": params
    })]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        return json.loads(result.stdout.strip())
    except Exception as e:
        return {"error": "Execution failed", "details": str(e)}


@app.post("/execute_task")
async def execute_task(request: Request):
    try:
        request_data = await request.json()
        tool_name = request_data.get("tool_name")
        action_name = request_data.get("action")
        params = request_data.get("params", {})

        if not tool_name or not action_name:
            raise HTTPException(status_code=400, detail="Missing tool_name or action.")

        if tool_name == "json_manager" and action_name == "orchestrate_write":
            return orchestrate_write(**params)

        params = validate_action(tool_name, action_name, params)
        result = run_script(tool_name, action_name, params)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result)
        return result

    except ContractViolation as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Execution failed", "details": str(e)})


@app.get("/get_supported_actions")
def get_supported_actions():
    try:
        with open(SYSTEM_REGISTRY, "r") as f:
            entries = [json.loads(line.strip()) for line in f if line.strip()]
        update_message = None
        if os.path.exists(UPDATE_MESSAGE_PATH):
            with open(UPDATE_MESSAGE_PATH) as f:
                data = json.load(f)
                if data.get("visible", False):
                    update_message = data
        return {
            "status": "success",
            "supported_actions": entries,
            "update": update_message
        }
    except Exception as e:
        logging.error(f"🚨 Failed to load registry: {e}")
        raise HTTPException(status_code=500, detail="Could not load registry.")


@app.post("/load_memory")
def load_memory():
    try:
        with open(WORKING_MEMORY_PATH, "r", encoding="utf-8") as f:
            memory = json.load(f)
        return {
            "status": "success",
            "loaded": len(memory),
            "memory": memory
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Cannot load working_memory.json",
            "details": str(e)
        })


@app.get("/")
def root():
    return {"status": "Jarvis core is online."}
