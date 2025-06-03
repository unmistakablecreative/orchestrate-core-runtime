from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import subprocess, json, os, logging

# === BASE DIR ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from tools import json_manager
from tools.smart_json_dispatcher import orchestrate_write
from system_guard import validate_action, ContractViolation

# === Init ===
app = FastAPI()

SYSTEM_REGISTRY = f"{BASE_DIR}/system_settings.ndjson"
WORKING_MEMORY_PATH = f"{BASE_DIR}/data/working_memory.json"
REFERRAL_PATH = f"{BASE_DIR}/container_state/referrals.json"
NGROK_CONFIG_PATH = os.path.join(BASE_DIR, "data", "ngrok.json")
EXEC_HUB_PATH = f"{BASE_DIR}/execution_hub.py"
TOOLS_DIR = f"{BASE_DIR}/tools"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# === Git Auto-Sync + Registry Merge ===
def sync_repo_and_merge_registry():
    try:
        logging.info("🔄 Syncing Orchestrate repo...")
        subprocess.run(["git", "-C", BASE_DIR, "pull"], check=True)

        # Merge registry with unlocked tools
        with open(SYSTEM_REGISTRY, "r") as f:
            updated_registry = [json.loads(line.strip()) for line in f if line.strip()]

        unlocked_tools = set()
        if os.path.exists(REFERRAL_PATH):
            with open(REFERRAL_PATH, "r") as f:
                referral_data = json.load(f)
            unlocked_tools = set(referral_data.get("tools_unlocked", []))

        for entry in updated_registry:
            if entry.get("tool") in unlocked_tools:
                entry["unlocked"] = True

        with open(SYSTEM_REGISTRY, "w") as f:
            for entry in updated_registry:
                f.write(json.dumps(entry) + "\n")

        # Force update of update_messages.json
        repo_path = os.path.join(BASE_DIR, "data", "update_messages.json")
        git_path = os.path.join(BASE_DIR, ".git", "..", "data", "update_message.json")
        if os.path.exists(git_path):
            subprocess.run(["cp", git_path, repo_path])
            logging.info("📢 update_messages.json refreshed from git.")

        logging.info("✅ Repo + registry sync complete.")

    except Exception as e:
        logging.error(f"❌ Repo sync failed: {e}")






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


# === Ngrok Auto-Relaunch ===
@app.on_event("startup")
def startup_routines():
    try:
        sync_repo_and_merge_registry()
    except Exception as e:
        logging.warning(f"⚠️ Sync failed on startup: {e}")

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


# === /execute_task ===
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


# === /get_supported_actions ===
@app.get("/get_supported_actions")
def get_supported_actions():
    try:
        sync_repo_and_merge_registry()

        # Load supported actions
        with open(SYSTEM_REGISTRY, "r") as f:
            entries = [json.loads(line.strip()) for line in f if line.strip()]

        # Load update messages
        update_messages_path = os.path.join(BASE_DIR, "data", "update_messages.json")
        if os.path.exists(update_messages_path):
            with open(update_messages_path, "r") as f:
                update_messages = json.load(f)
        else:
            update_messages = []

        return {
            "status": "success",
            "supported_actions": entries,
            "update_messages": update_messages
        }

    except Exception as e:
        logging.error(f"🚨 Failed to load registry or update messages: {e}")
        raise HTTPException(status_code=500, detail="Could not load registry or update messages.")





# === /load_memory ===
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


# === /
@app.get("/")
def root():
    return {"status": "Jarvis core is online."}
