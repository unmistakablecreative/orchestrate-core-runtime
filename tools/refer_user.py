import os
import json
import requests
import shutil
import argparse
import subprocess
from zipfile import ZipFile
from datetime import datetime

# === DYNAMIC PATH DETECTION ===
def find_orchestrate_installation():
    """Find OrchestrateEngine installation for any user on the system"""
    
    # Check common user directory locations
    user_base_dirs = ["/Users", "/home"]
    
    for base_dir in user_base_dirs:
        if not os.path.exists(base_dir):
            continue
            
        # Scan all user directories
        try:
            for username in os.listdir(base_dir):
                user_home = os.path.join(base_dir, username)
                
                # Skip if not a directory or system directories
                if not os.path.isdir(user_home) or username.startswith('.'):
                    continue
                
                # Check for OrchestrateEngine installation
                orchestrate_state = os.path.join(user_home, "Library", "Application Support", "OrchestrateEngine", "state")
                credentials_file = os.path.join(orchestrate_state, "system_identity.json")
                
                if os.path.exists(credentials_file):
                    # Found valid installation
                    secondbrain_file = os.path.join(orchestrate_state, "secondbrain.json")
                    repo_dir = os.path.join(user_home, "repos", "orchestrate-user-referrals")
                    
                    return {
                        "user_home": user_home,
                        "username": username,
                        "credentials_path": credentials_file,
                        "secondbrain_path": secondbrain_file,
                        "repo_dir": repo_dir,
                        "dmg_path": os.path.join(repo_dir, "orchestrate_engine_final.dmg")
                    }
        except PermissionError:
            # Skip directories we can't read
            continue
    
    # If no installation found, return None
    return None

# === GET PATHS ===
INSTALL_INFO = find_orchestrate_installation()

if not INSTALL_INFO:
    print("ERROR: No OrchestrateEngine installation found on this system")
    exit(1)

# Extract paths from installation info
CREDENTIALS_PATH = INSTALL_INFO["credentials_path"]
SECONDBRAIN_PATH = INSTALL_INFO["secondbrain_path"]
REPO_DIR = INSTALL_INFO["repo_dir"]
DMG_SOURCE_PATH = INSTALL_INFO["dmg_path"]
USER_HOME = INSTALL_INFO["user_home"]
USERNAME = INSTALL_INFO["username"]

# === AIRTABLE CONFIG ===
AIRTABLE_API_KEY = "patyuDyrmZz0s6bLO.7e4f3c3ca7f3a4be93d9d4f3b57c2635fd0aab5dce43bb1de2aa37ceeeda886d"
AIRTABLE_BASE_ID = "appoNbgV6oY603cjb"
AIRTABLE_TABLE_ID = "tblpa06yXMKwflL7m"

def refer_user(params):
    name = params.get("name")
    email = params.get("email")
    
    if not name or not email:
        return {"status": "error", "message": "Missing name or email"}
    
    # Debug info
    print(f"Found OrchestrateEngine for user: {USERNAME}")
    print(f"User home: {USER_HOME}")
    print(f"Credentials path: {CREDENTIALS_PATH}")
    print(f"Repo directory: {REPO_DIR}")
    
    # Verify paths exist
    if not os.path.exists(CREDENTIALS_PATH):
        return {
            "status": "error", 
            "message": f"Credentials file not found: {CREDENTIALS_PATH}"
        }
    
    if not os.path.exists(REPO_DIR):
        return {
            "status": "error", 
            "message": f"Repository directory not found: {REPO_DIR}"
        }
        
    if not os.path.exists(DMG_SOURCE_PATH):
        return {
            "status": "error", 
            "message": f"DMG file not found: {DMG_SOURCE_PATH}"
        }
    
    # Load user identity
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            identity = json.load(f)
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to read credentials: {str(e)}"
        }
    
    referrer_id = identity.get("user_id")
    if not referrer_id:
        return {
            "status": "error", 
            "message": "No user_id found in system_identity.json"
        }
    
    # Load referrer name from secondbrain
    referrer_name = "Unknown Referrer"
    if os.path.exists(SECONDBRAIN_PATH):
        try:
            with open(SECONDBRAIN_PATH, 'r') as f:
                brain = json.load(f)
            referrer_name = brain.get("entries", {}).get("user_profile", {}).get("full_name", "Unknown Referrer")
        except Exception:
            pass  # Use default name if secondbrain can't be read
    
    # === Create referral package ===
    safe_name = name.lower().replace(" ", "_").replace(".", "_")
    zip_name = f"Orchestrate_Installer_for_{safe_name}.zip"
    zip_path = os.path.join(REPO_DIR, zip_name)
    temp_dir = f"/tmp/referral_build_{safe_name}"
    
    # Clean up any existing temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy DMG to temp directory
        shutil.copy2(DMG_SOURCE_PATH, os.path.join(temp_dir, "orchestrate_engine_final.dmg"))
        
        # Create referrer file
        with open(os.path.join(temp_dir, "referrer.txt"), "w") as f:
            f.write(referrer_id)
        
        # Create ZIP package
        with ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to create referral package: {str(e)}"
        }
    
    # === Push to GitHub ===
    try:
        # Change to repo directory
        os.chdir(REPO_DIR)
        
        # Git operations
        subprocess.run(["git", "pull", "origin", "main"], check=True, capture_output=True)
        subprocess.run(["git", "add", zip_name], check=True)
        subprocess.run(["git", "commit", "-m", f"Add referral package for {name}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error", 
            "message": f"Git operation failed: {e.stderr.decode() if e.stderr else str(e)}"
        }
    
    # GitHub download URL
    zip_url = f"https://github.com/unmistakablecreative/orchestrate-user-referrals/raw/main/{zip_name}"
    
    # === Submit to Airtable ===
    airtable_data = {
        "fields": {
            "referrer_id": referrer_id,
            "referrer_name": referrer_name,
            "recipient_name": name,
            "recipient_email": email,
            "zip_url": zip_url
        }
    }
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    
    try:
        response = requests.post(airtable_url, headers=headers, json=airtable_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            "status": "error", 
            "message": f"Failed to submit to Airtable: {str(e)}"
        }
    
    return {
        "status": "success",
        "message": f"Referral package created for {name} ({email})",
        "zip_url": zip_url,
        "referrer_id": referrer_id,
        "referrer_name": referrer_name
    }

# === CLI Interface ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create referral packages for OrchestrateEngine")
    parser.add_argument("action", help="Action to perform (refer_user)")
    parser.add_argument("--params", required=True, help="JSON parameters with name and email")
    
    args = parser.parse_args()
    
    try:
        if args.action == "refer_user":
            params = json.loads(args.params)
            result = refer_user(params)
        else:
            result = {"status": "error", "message": f"Unknown action: {args.action}"}
            
    except json.JSONDecodeError as e:
        result = {"status": "error", "message": f"Invalid JSON parameters: {str(e)}"}
    except Exception as e:
        result = {"status": "error", "message": f"Unexpected error: {str(e)}"}
    
    print(json.dumps(result, indent=2))
