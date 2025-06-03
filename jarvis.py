from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import subprocess, json, os, logging, shutil

from tools import json_manager
from tools.smart_json_dispatcher import orchestrate_write
from system_guard import validate_action, ContractViolation

# === Init ===
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SYSTEM_REGISTRY = f"{BASE_DIR}/system_settings.ndjson"
WORKING_MEMORY_PATH = os.path.join(BASE_DIR, "data", "working_memory.json")
EXEC_HUB_PATH = os.path.join(BASE_DIR, "execution_hub.py")
UPDATE_MESSAGE_PATH = os.path.join(BASE_DIR, "data", "update_message.json")
NGROK_CONFIG_PATH = os.path.join(BASE_DIR, "data", "ngrok.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Runtime Sync (Safe) ===
@app.on_event("startup")
def sync_runtime_from_github():
    repo_url = "https://github.com/unmistakablecreative/orchestrate-core-runtime.git"
    temp_dir = "/tmp/orchestrate_update"

    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        subprocess.run(["git", "clone", "--depth=1", repo_url, temp_dir], check=True)

        safe_files = ["system_settings.ndjson"]
        safe_dirs = ["tools"]

        for name in safe_files:
            src = os.path.join(temp_dir, name)
            dst = os.path.join(BASE_DIR, name)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                logging.info(f"✅ Updated file: {name}")

        for name in safe_dirs:
            src = os.path.join(temp_dir, name)
            dst = os.path.join(BASE_DIR, name)
            if os.path.exists(src):
                for root, dirs, files in os.walk(src):
                    rel_path = os.path.relpath(root, src)
                    dst_root = os.path.join(dst, rel_path)
                    os.makedirs(dst_root, exist_ok=True)
                    for file in files:
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(dst_root, file)
                        shutil.copy2(src_file, dst_file)
                logging.info(f"✅ Synced directory: {name}")

        logging.info("✅ Runtime sync from GitHub complete.")

    except Exception as e:
        logging.warning(f"⚠️ Runtime sync failed: {e}")

# === Relaunch ngrok Tunnel ===
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
                logging.info("🚀 ngrok tunnel relaunched.")
            else:
                logging.info("🔁 ngrok already running.")
    except Exception as e:
        logging.warning(f"⚠️ Ngrok relaunch failed: {e}")

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

# === Task Dispatcher ===
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

# === Action Registry ===
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
