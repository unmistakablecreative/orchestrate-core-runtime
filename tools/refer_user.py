import os
import json
import requests
import shutil
import argparse
from zipfile import ZipFile
from datetime import datetime

# === CONFIG ===
DMG_FILENAME = "orchestrate_engine_final.dmg"
REPO_DIR = "/Users/srinivas/repos/orchestrate-user-referrals"
DMG_SOURCE_PATH = os.path.join(REPO_DIR, DMG_FILENAME)
AIRTABLE_API_KEY = "patyuDyrmZz0s6bLO.7e4f3c3ca7f3a4be93d9d4f3b57c2635fd0aab5dce43bb1de2aa37ceeeda886d"
AIRTABLE_BASE_ID = "appoNbgV6oY603cjb"
AIRTABLE_TABLE_ID = "tblpa06yXMKwflL7m"

# Fixed path handling with proper expansion
CREDENTIALS_PATH = os.path.expanduser("~/Library/Application Support/OrchestrateEngine/state/system_identity.json")
SECONDBRAIN_PATH = os.path.expanduser("~/Library/Application Support/OrchestrateEngine/state/secondbrain.json")
OUTPUT_FOLDER = REPO_DIR

def refer_user(params):
    name = params.get("name")
    email = params.get("email")
    
    if not name or not email:
        return {"status": "error", "message": "Missing name or email"}
    
    # Debug path checking with more info
    print(f"Detected user home: {USER_HOME}")
    print(f"Checking credentials path: {CREDENTIALS_PATH}")
    print(f"Path exists: {os.path.exists(CREDENTIALS_PATH)}")
    print(f"Repo directory: {REPO_DIR}")
    print(f"Repo exists: {os.path.exists(REPO_DIR)}")
    
    if not os.path.exists(CREDENTIALS_PATH):
        return {
            "status": "error", 
            "message": f"Missing system_identity.json at {CREDENTIALS_PATH}"
        }
    
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            identity = json.load(f)
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to read system_identity.json: {str(e)}"
        }
    
    referrer_id = identity.get("user_id")
    if not referrer_id:
        return {
            "status": "error", 
            "message": "No user_id found in system_identity.json"
        }
    
    # Handle secondbrain file
    referrer_name = "Unknown Referrer"
    if os.path.exists(SECONDBRAIN_PATH):
        try:
            with open(SECONDBRAIN_PATH, 'r') as f:
                brain = json.load(f)
            referrer_name = brain.get("entries", {}).get("user_profile", {}).get("full_name", "Unknown Referrer")
        except Exception as e:
            print(f"Warning: Could not read secondbrain.json: {e}")
    
    # === Prepare ZIP ===
    safe_name = name.lower().replace(" ", "_").replace(".", "_")
    zip_name = f"Orchestrate_Installer_for_{safe_name}.zip"
    zip_path = os.path.join(OUTPUT_FOLDER, zip_name)
    temp_dir = os.path.join("/tmp", f"referral_build_{safe_name}")
    
    # Clean up existing temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Check if DMG exists
    if not os.path.exists(DMG_SOURCE_PATH):
        return {
            "status": "error", 
            "message": f"DMG file not found at {DMG_SOURCE_PATH}"
        }
    
    try:
        # Copy DMG to temp directory
        shutil.copy2(DMG_SOURCE_PATH, os.path.join(temp_dir, DMG_FILENAME))
        
        # Create referrer file
        with open(os.path.join(temp_dir, "referrer.txt"), "w") as f:
            f.write(referrer_id)
        
        # Create ZIP
        with ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    arcname = os.path.relpath(abs_path, temp_dir)
                    zipf.write(abs_path, arcname)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to create ZIP: {str(e)}"
        }
    
    # === Push to GitHub ===
    try:
        os.chdir(REPO_DIR)
        
        # Use subprocess for better error handling
        import subprocess
        
        # Pull latest changes
        result = subprocess.run(["git", "pull", "origin", "main"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Git pull warning: {result.stderr}")
        
        # Add, commit, and push
        subprocess.run(["git", "add", zip_name], check=True)
        subprocess.run(["git", "commit", "-m", f"Add referral zip for {name}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error", 
            "message": f"Git operation failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to push to GitHub: {str(e)}"
        }
    
    zip_url = f"https://github.com/unmistakablecreative/orchestrate-user-referrals/raw/main/{zip_name}"
    
    # === Send to Airtable ===
    airtable_payload = {
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
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    
    try:
        r = requests.post(url, headers=headers, json=airtable_payload)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            "status": "error", 
            "message": f"Airtable error: {str(e)}"
        }
    
    return {
        "status": "success",
        "message": f"Referral zip created and pushed. Invite sent to {name}.",
        "zip_url": zip_url,
        "referrer_id": referrer_id,
        "zip_name": zip_name
    }

# === REQUIRED for Execution Hub ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="The action to perform")
    parser.add_argument("--params", required=True, help="JSON string with 'name' and 'email'")
    args = parser.parse_args()
    
    try:
        if args.action == "refer_user":
            parsed = json.loads(args.params)
            result = refer_user(parsed)
        else:
            result = {"status": "error", "message": f"Unknown action: {args.action}"}
    except Exception as e:
        result = {"status": "error", "message": str(e)}
    
    print(json.dumps(result, indent=2))
