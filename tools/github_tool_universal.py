import os
import subprocess
import json
import argparse

# === Load GitHub token from local credentials.json ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIAL_PATH = os.path.join(SCRIPT_DIR, "credentials.json")

def load_credential(key):
    try:
        with open(CREDENTIAL_PATH, "r") as f:
            data = json.load(f)
            return data.get(key)
    except Exception:
        return None

GITHUB_TOKEN = load_credential("github_access_token")

# --- Core Functions ---

def init_repo(path):
    if not os.path.exists(path):
        os.makedirs(path)
    
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ '{path}' is not a valid directory."}
    
    try:
        subprocess.run(["git", "init"], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Initialized git repo at {path}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Git init failed: {str(e)}"}

def add_file(path, file):
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Repo path not found: {path}"}
    
    try:
        subprocess.run(["git", "add", file], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Added {file} to staging."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ git add failed: {str(e)}"}

def commit(path, message):
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Invalid repo path: {path}"}
    if not message:
        return {"status": "error", "message": "❌ Commit message is required."}
    
    try:
        subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)
        return {"status": "success", "message": "✅ Commit successful."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

def patch_remote_url(path):
    if not GITHUB_TOKEN:
        return {"status": "error", "message": "❌ GitHub token not found in credentials."}
    
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], cwd=path, capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        if "@" not in url:
            patched_url = url.replace("https://", f"https://{GITHUB_TOKEN}@")
            subprocess.run(["git", "remote", "set-url", "origin", patched_url], cwd=path, check=True)
        return {"status": "success"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Failed to patch remote URL: {str(e)}"}

def push(path, branch):
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Invalid repo path: {path}"}
    
    patch_result = patch_remote_url(path)
    if patch_result["status"] != "success":
        return patch_result

    branch = branch or "main"
    try:
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Pushed to {branch}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

def pull(path, branch):
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Invalid repo path: {path}"}
    
    branch = branch or "main"
    try:
        subprocess.run(["git", "pull", "origin", branch], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Pulled latest from {branch}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

def status(path):
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Invalid repo path: {path}"}
    
    try:
        result = subprocess.run(["git", "status", "--porcelain"], cwd=path, check=True, capture_output=True, text=True)
        return {"status": "success", "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

def archive_repo(path):
    import zipfile
    import datetime
    
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Path does not exist: {path}"}
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"repo_backup_{timestamp}.zip"
    
    try:
        with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as backup:
            for root, _, files in os.walk(path):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, path)
                    backup.write(abs_path, rel_path)
        return {"status": "success", "backup_file": backup_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Action Router ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--params")
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}

    if args.action == "init_repo":
        result = init_repo(**params)
    elif args.action == "add_file":
        result = add_file(**params)
    elif args.action == "commit":
        result = commit(**params)
    elif args.action == "push":
        result = push(**params)
    elif args.action == "pull":
        result = pull(**params)
    elif args.action == "status":
        result = status(**params)
    elif args.action == "archive_repo":
        result = archive_repo(**params)
    else:
        result = {"status": "error", "message": f"Unknown action {args.action}"}

    print(json.dumps(result, indent=2))
