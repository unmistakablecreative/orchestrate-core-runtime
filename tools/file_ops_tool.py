import os
import shutil
import json
import sys

SEARCH_DIRS = [
    "/orchestrate_user/dropzone",
    "/orchestrate_user/vault/watch_books",
    "/orchestrate_user/vault/watch_transcripts",
    "/orchestrate_user/orchestrate_exports/markdown",
    "/opt/orchestrate-core-runtime/code_blueprints",
    "/opt/orchestrate-core-runtime/compositions",
    "/app"
]

# --- Core Functions ---
def resolve_path(filename):
    for dir in SEARCH_DIRS:
        full_path = os.path.join(dir, filename)
        if os.path.exists(full_path):
            return full_path
    raise FileNotFoundError(f"'{filename}' not found in any configured search path.")

def read_file(params):
    path = resolve_path(params["filename"])
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def rename_file(params):
    path = resolve_path(params["filename"])
    dest_path = os.path.join(os.path.dirname(path), params["new_name"])
    os.rename(path, dest_path)
    return f"✅ Renamed '{params['filename']}' to '{params['new_name']}'"

def move_file(params):
    path = resolve_path(params["filename"])
    os.makedirs(params["destination_dir"], exist_ok=True)
    dest_path = os.path.join(params["destination_dir"], os.path.basename(path))
    shutil.move(path, dest_path)
    return f"✅ Moved '{params['filename']}' to '{params['destination_dir']}'"

# --- Action Map ---
ACTION_MAP = {
    "read_file": read_file,
    "rename_file": rename_file,
    "move_file": move_file,
    "resolve_path": lambda params: resolve_path(params["filename"]),
}

def main(params=None):
    if params is None:
        params = json.loads(sys.stdin.read())
    action = params.get("action")
    if action not in ACTION_MAP:
        print(f"❌ Unknown action: {action}")
        return
    try:
        result = ACTION_MAP[action](params)
        print(result)
    except Exception as e:
        print(f"❌ Error during '{action}': {e}")

# --- Entrypoint ---
if __name__ == "__main__":
    main()
