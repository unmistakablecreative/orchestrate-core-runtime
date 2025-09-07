import os
import sys
import json
import requests
import shutil
import argparse
import subprocess
from zipfile import ZipFile
from datetime import datetime

# === CONTAINER PATHS (Docker environment) ===
CREDENTIALS_PATH = "/container_state/system_identity.json"
SECONDBRAIN_PATH = "/container_state/secondbrain.json"  # if it exists
USER_MOUNT_DIR = "/orchestrate_user"
TEMP_DIR = "/tmp"

# === REPO CONFIG ===
REPO_NAME = "orchestrate-user-referrals"
REPO_URL = f"https://github.com/unmistakablecreative/{REPO_NAME}.git"
LOCAL_REPO_DIR = f"/tmp/{REPO_NAME}"
DMG_FILENAME = "orchestrate_engine_final.dmg"

# === GITHUB & AIRTABLE CONFIG ===
GITHUB_TOKEN = "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"
AIRTABLE_API_KEY = "patyuDyrmZz0s6bLO.7e4f3c3ca7f3a4be93d9d4f3b57c2635fd0aab5dce43bb1de2aa37ceeeda886d"
AIRTABLE_BASE_ID = "appoNbgV6oY603cjb"
AIRTABLE_TABLE_ID = "tblpa06yXMKwflL7m"

def setup_git_repo():
    """Clone or update the git repository with authentication"""
    if os.path.exists(LOCAL_REPO_DIR):
        print(f"DEBUG: Repo exists, pulling latest changes...")
        os.chdir(LOCAL_REPO_DIR)
        result = subprocess.run(["git", "pull", "origin", "main"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"DEBUG: Git pull failed: {result.stderr}")
            # Try fresh clone
            shutil.rmtree(LOCAL_REPO_DIR)
            return setup_git_repo()
    else:
        print(f"DEBUG: Cloning repo with authentication...")
        # Use HTTPS with token authentication
        auth_url = f"https://{GITHUB_TOKEN}@github.com/unmistakablecreative/{REPO_NAME}.git"
        result = subprocess.run(["git", "clone", auth_url, LOCAL_REPO_DIR], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        os.chdir(LOCAL_REPO_DIR)
    
    # Configure git for authenticated pushes
    subprocess.run(["git", "config", "user.email", "action@github.com"], check=False)
    subprocess.run(["git", "config", "user.name", "GitHub Action"], check=False)
    
    # Set the remote URL with token for future pushes
    auth_url = f"https://{GITHUB_TOKEN}@github.com/unmistakablecreative/{REPO_NAME}.git"
    subprocess.run(["git", "remote", "set-url", "origin", auth_url], check=False)
    
    # Verify DMG exists in repo
    dmg_path = os.path.join(LOCAL_REPO_DIR, DMG_FILENAME)
    if not os.path.exists(dmg_path):
        raise Exception(f"DMG file not found in repo: {dmg_path}")
    
    return LOCAL_REPO_DIR

def refer_user(params):
    try:
        name = params.get("name")
        email = params.get("email")
        
        if not name or not email:
            return {"status": "error", "message": "Missing name or email"}
        
        # Debug environment info
        debug_info = {
            "credentials_exists": os.path.exists(CREDENTIALS_PATH),
            "user_mount_exists": os.path.exists(USER_MOUNT_DIR),
            "working_dir": os.getcwd()
        }
        print(f"DEBUG INFO: {json.dumps(debug_info, indent=2)}")
        
        # Check required paths
        if not os.path.exists(CREDENTIALS_PATH):
            return {
                "status": "error", 
                "message": f"Credentials file not found: {CREDENTIALS_PATH}"
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
        
        print(f"DEBUG: Found referrer_id: {referrer_id}")
        
        # Load referrer name from secondbrain (optional)
        referrer_name = "Unknown Referrer"
        if os.path.exists(SECONDBRAIN_PATH):
            try:
                with open(SECONDBRAIN_PATH, 'r') as f:
                    brain = json.load(f)
                referrer_name = brain.get("entries", {}).get("user_profile", {}).get("full_name", "Unknown Referrer")
            except Exception as e:
                print(f"DEBUG: Secondbrain read failed: {str(e)}")
        
        print(f"DEBUG: Using referrer_name: {referrer_name}")
        
        # === Setup git repository ===
        try:
            print("DEBUG: Setting up git repository...")
            repo_dir = setup_git_repo()
            dmg_source_path = os.path.join(repo_dir, DMG_FILENAME)
            print(f"DEBUG: Repo ready at {repo_dir}")
            print(f"DEBUG: DMG source: {dmg_source_path}")
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to setup git repository: {str(e)}"
            }
        
        # === Create referral package ===
        safe_name = name.lower().replace(" ", "_").replace(".", "_")
        zip_name = f"Orchestrate_Installer_for_{safe_name}.zip"
        zip_path = os.path.join(repo_dir, zip_name)
        temp_build_dir = f"/tmp/referral_build_{safe_name}"
        
        print(f"DEBUG: Creating package {zip_name}")
        
        # Clean up any existing temp directory
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)
        os.makedirs(temp_build_dir, exist_ok=True)
        
        try:
            # Copy DMG to temp directory
            print("DEBUG: Copying DMG file...")
            shutil.copy2(dmg_source_path, os.path.join(temp_build_dir, DMG_FILENAME))
            
            # Create referrer file
            print("DEBUG: Creating referrer.txt...")
            with open(os.path.join(temp_build_dir, "referrer.txt"), "w") as f:
                f.write(referrer_id)
            
            # Create ZIP package
            print("DEBUG: Creating ZIP package...")
            with ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(temp_build_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_build_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temp directory
            shutil.rmtree(temp_build_dir)
            print("DEBUG: ZIP package created successfully")
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to create referral package: {str(e)}"
            }
        
        # === Push to GitHub ===
        try:
            print("DEBUG: Starting git operations...")
            os.chdir(repo_dir)
            
            # Set up the authenticated remote URL explicitly
            auth_url = f"https://{GITHUB_TOKEN}@github.com/unmistakablecreative/{REPO_NAME}.git"
            subprocess.run(["git", "remote", "set-url", "origin", auth_url], check=True)
            
            print("DEBUG: Git add...")
            subprocess.run(["git", "add", zip_name], check=True, timeout=30)
            
            print("DEBUG: Git commit...")
            subprocess.run(["git", "commit", "-m", f"Add referral package for {name}"], 
                          check=True, timeout=30)
            
            print("DEBUG: Git push with explicit authentication...")
            # Push directly to the authenticated URL
            result = subprocess.run(["git", "push", auth_url, "main"], 
                                  check=True, timeout=60, capture_output=True, text=True)
            
            print("DEBUG: Git operations completed successfully")
            
        except subprocess.TimeoutExpired as e:
            return {
                "status": "error", 
                "message": f"Git operation timed out: {str(e)}"
            }
        except subprocess.CalledProcessError as e:
            error_msg = f"Git operation failed: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return {
                "status": "error", 
                "message": error_msg
            }
        
        # GitHub download URL
        zip_url = f"https://github.com/unmistakablecreative/{REPO_NAME}/raw/main/{zip_name}"
        
        # === Submit to Airtable ===
        print("DEBUG: Submitting to Airtable...")
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
            response = requests.post(airtable_url, headers=headers, json=airtable_data, timeout=30)
            response.raise_for_status()
            print("DEBUG: Airtable submission successful")
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
        
    except Exception as e:
        # Catch any unexpected errors
        import traceback
        return {
            "status": "error",
            "message": f"Unexpected error in refer_user: {str(e)}",
            "traceback": traceback.format_exc()
        }

# === CLI Interface ===
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Create referral packages for OrchestrateEngine")
        parser.add_argument("action", help="Action to perform (refer_user)")
        parser.add_argument("--params", required=True, help="JSON parameters with name and email")
        
        args = parser.parse_args()
        
        print(f"DEBUG: Starting with action={args.action}")
        print(f"DEBUG: Params={args.params}")
        
        if args.action == "refer_user":
            params = json.loads(args.params)
            print(f"DEBUG: Parsed params: {params}")
            result = refer_user(params)
        else:
            result = {"status": "error", "message": f"Unknown action: {args.action}"}
            
    except json.JSONDecodeError as e:
        result = {"status": "error", "message": f"Invalid JSON parameters: {str(e)}"}
    except Exception as e:
        import traceback
        result = {
            "status": "error", 
            "message": f"Script initialization error: {str(e)}",
            "traceback": traceback.format_exc()
        }
    
    # Always ensure we output JSON
    try:
        print(json.dumps(result, indent=2))
        sys.stdout.flush()
    except Exception as e:
        # Fallback if JSON serialization fails
        print(f'{{"status": "error", "message": "JSON output failed: {str(e)}"}}')
        sys.stdout.flush()
