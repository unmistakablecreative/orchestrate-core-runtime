from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import subprocess, json, os, logging, shutil

# === BASE DIR ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from tools import json_manager
from tools.smart_json_dispatcher import orchestrate_write
from system_guard import validate_action, ContractViolation

# === Init ===
app = FastAPI()

SYSTEM_REGISTRY = f"{BASE_DIR}/system_settings.ndjson"
WORKING_MEMORY_PATH = f"{BASE_DIR}/data/working_memory.json"
EXEC_HUB_PATH = f"{BASE_DIR}/execution_hub.py"
UPDATE_MESSAGE_PATH = os.path.join(BASE_DIR, "data", "update_message.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Auto-Sync Runtime on Boot ===
@app.on_event("startup")
def sync_runtime_from_github():
    repo_url = "https://github.com/unmistakablecreative/orchestrate-core-runtime.git"
    temp_dir = "/tmp/orchestrate_update"

    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        subprocess.run(["git", "clone", "--depth=1", repo_url, temp_dir], check=True)

        for name in ["system_settings.ndjson", "tools", "data/update_message.json"]:
            src = os.path.join(temp_dir, name)
            dst = os.path.join(BASE_DIR, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

        logging.info("✅ Runtime sync from GitHub complete.")
    except Exception as e:
        logging.warning(f"⚠️ Runtime sync failed: {e}")

# === Tool Executor ===
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

# === GPT Task Dispatcher ===
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

# === Action Registry with Optional Update Banner ===
@app.get("/get_supported_actions")
def get_supported_actions():
    try:
        with open(SYSTEM_REGISTRY, "r") as f:
            entries = [json.loads(line.strip()) for line in f if line.strip()]

        update_message = None
        if os.path.exists(UPDATE_MESSAGE_PATH):
            with open(UPDATE_MESSAGE_PATH) as msg_file:
                message_data = json.load(msg_file)
                if message_data.get("visible", False):
                    update_message = message_data

        return {
            "status": "success",
            "supported_actions": entries,
            "update": update_message
        }

    except Exception as e:
        logging.error(f"🚨 Failed to load registry: {e}")
        raise HTTPException(status_code=500, detail="Could not load registry.")

# === Memory Loader ===
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

# === Health Check ===
@app.get("/")
def root():
    return {"status": "Jarvis core is online."}
