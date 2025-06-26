import os
import subprocess
import json
import argparse
from typing import List

# === Load GitHub token ===
CREDENTIAL_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
def load_credential(key):
    try:
        with open(CREDENTIAL_PATH, "r") as f:
            return json.load(f).get(key)
    except Exception:
        return None

GITHUB_TOKEN = load_credential("github_access_token")

# === Git Functions ===

def clone_repo(url, path):
    try:
        subprocess.run(["git", "clone", url, path], check=True)
        return {"status": "success", "message": f"✅ Cloned to {path}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Clone failed: {str(e)}"}

def init_repo(path):
    os.makedirs(path, exist_ok=True)
    try:
        subprocess.run(["git", "init"], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Initialized Git repo at {path}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Init failed: {str(e)}"}

def set_remote(path, url):
    try:
        subprocess.run(["git", "remote", "add", "origin", url], cwd=path, check=True)
        return {"status": "success", "message": f"🔗 Remote set to {url}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Remote config failed: {str(e)}"}

def add_files(path, files: List[str]):
    try:
        subprocess.run(["git", "add"] + files, cwd=path, check=True)
        return {"status": "success", "message": f"✅ Added files to staging."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ git add failed: {str(e)}"}

def commit_repo(path, message):
    try:
        subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Commit successful."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Commit failed: {str(e)}"}

def push_repo(path, branch="main"):
    patch = patch_remote_token(path)
    if patch["status"] != "success":
        return patch
    try:
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Pushed to {branch}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Push failed: {str(e)}"}

def pull_repo(path, branch="main"):
    try:
        subprocess.run(["git", "pull", "origin", branch], cwd=path, check=True)
        return {"status": "success", "message": f"✅ Pulled from {branch}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Pull failed: {str(e)}"}

def patch_remote_token(path):
    if not GITHUB_TOKEN:
        return {"status": "error", "message": "❌ GitHub token not found."}
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], cwd=path, capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        if "@" not in url:
            authed = url.replace("https://", f"https://{GITHUB_TOKEN}@")
            subprocess.run(["git", "remote", "set-url", "origin", authed], cwd=path, check=True)
        return {"status": "success"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Failed to patch token: {str(e)}"}

def list_repos(root="./projects"):
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=dirpath, capture_output=True, text=True)
            entries.append({
                "name": os.path.basename(dirpath),
                "path": dirpath,
                "branch": branch.stdout.strip() if branch.returncode == 0 else "unknown"
            })
            dirnames[:] = []  # Don't recurse further
    return {"status": "success", "repos": entries}

# === Dispatch ===

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--params")
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}

    actions = {
        "clone_repo": clone_repo,
        "init_repo": init_repo,
        "set_remote": set_remote,
        "add_files": add_files,
        "commit_repo": commit_repo,
        "push_repo": push_repo,
        "pull_repo": pull_repo,
        "list_repos": list_repos
    }

    func = actions.get(args.action)
    if not func:
        result = {"status": "error", "message": f"❌ Unknown action: {args.action}"}
    else:
        try:
            result = func(**params)
        except Exception as e:
            result = {"status": "error", "message": f"Exception: {str(e)}"}

    print(json.dumps(result, indent=2))
