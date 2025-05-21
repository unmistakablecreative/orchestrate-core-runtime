import os
import subprocess
import json
import argparse
from system_settings import load_credential

GITHUB_TOKEN = load_credential("github_token")
if GITHUB_TOKEN:
    os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN


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

def push(path, branch):
    if not os.path.isdir(path):
        return {"status": "error", "message": f"❌ Invalid repo path: {path}"}
    
    branch = branch or "main"
    try:
        subprocess.run(["git", "push", "origin", branch], cwd=path, check=True)
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
    import argparse, json
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