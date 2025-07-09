import os
import shutil
import json
import argparse

SEARCH_DIRS = [
    "/orchestrate_user/dropzone",
    "/orchestrate_user/vault/watch_books",
    "/orchestrate_user/vault/watch_transcripts",
    "/orchestrate_user/orchestrate_exports/markdown",
    "/opt/orchestrate-core-runtime/code_blueprints",
    "/opt/orchestrate-core-runtime/compositions",
    "/app"
]

def resolve_path(filename):
    for dir in SEARCH_DIRS:
        full_path = os.path.join(dir, filename)
        if os.path.exists(full_path):
            return full_path
    raise FileNotFoundError(f"'{filename}' not found in any configured search path.")

def read_file(params):
    try:
        path = resolve_path(params["filename"])
        with open(path, 'r', encoding='utf-8') as f:
            return {
                "status": "success",
                "filename": os.path.basename(path),
                "data": f.read()
            }
    except Exception as e:
        return {"status": "error", "message": f"❌ Read error: {str(e)}"}

def rename_file(params):
    try:
        path = resolve_path(params["filename"])
        dest_path = os.path.join(os.path.dirname(path), params["new_name"])
        os.rename(path, dest_path)
        return {
            "status": "success",
            "message": f"✅ Renamed '{params['filename']}' to '{params['new_name']}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"❌ Rename error: {str(e)}"}

def move_file(params):
    try:
        path = resolve_path(params["filename"])
        os.makedirs(params["destination_dir"], exist_ok=True)
        dest_path = os.path.join(params["destination_dir"], os.path.basename(path))
        shutil.move(path, dest_path)
        return {
            "status": "success",
            "message": f"✅ Moved '{params['filename']}' to '{params['destination_dir']}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"❌ Move error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--params", type=str)
    args = parser.parse_args()

    try:
        params = json.loads(args.params) if args.params else {}
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "❌ Invalid JSON."}, indent=4))
        return

    if args.action == "read_file":
        result = read_file(params)
    elif args.action == "rename_file":
        result = rename_file(params)
    elif args.action == "move_file":
        result = move_file(params)
    else:
        result = {"status": "error", "message": f"❌ Unknown action: {args.action}"}

    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()
