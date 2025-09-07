import os
import sys
import json
import requests
import shutil
import argparse
from zipfile import ZipFile
from datetime import datetime

# === CONTAINER PATHS (Docker environment) ===
CREDENTIALS_PATH = "/container_state/system_identity.json"
SECONDBRAIN_PATH = "/container_state/secondbrain.json"
USER_MOUNT_DIR = "/orchestrate_user"
RUNTIME_DIR = "/opt/orchestrate-core-runtime"

# === DMG CONFIG ===
DMG_FILENAME = "orchestrate_engine_final.dmg"
DMG_SOURCE_PATH = os.path.join(RUNTIME_DIR, DMG_FILENAME)

# === DROPBOX CONFIG ===
DROPBOX_ACCESS_TOKEN = "sl.u.AF-EcUL8ZRy49uy6tdWzKfggQ9z1Mlvlhg497ZC0ucOXArIpofveLTUMI6JQs_ZHH_Tk2fVGjsngq8gj0S7QkNx06yL66bO0Q7IiwGNKTc0-QYvaPKPkZWsfVyKNDwaq0V3JfPie1wGV86hYBwcgspULFZDZSGEdN3Co9Cn9BA-XiEExrr6BIjs7QOLwHKoYK1uOo6V5zSj95R_l0wujSMMKNOWxftOtGiZ5m3__qNw2ELsMf4pyT_qAeHlhz-5GhrzMr--eYdCvrq_j3L5URMxHnqZFCg2xcC0_vKMoJghDQ5NYhWCFkazWGNkVA1Ja4jl9Pt1ST-S6m_TCnBej7PcR-eM1r3iOzWucp-ckM0y6m73s-ss0qPO4LSrzP70bqJTWcu1TlTgA5knM-Pt8pIoCAR0Y3P5RK0eY4PG8Kq1-0URnu2vsjjUfq_sdK2iZshk9q8XSNcDU1srAhK1ceM_emWvsx9WsVxkD1lt3rdQIIsH1MJyzFRXOZbVZHC2dBcBOqAQmakX7YExIrJfNg233CKhP_bh-5FHp42XVhz2jwtXlqtVVUrmRSh5Ojk1CBfMzuPd0an1fnw5_QN8_VT7DZJHxKFLOFCGApJ5LLZ26rGm1zsYlQJvDuHBgkbx7r_A1DYzP80t5mER0jd1vCQNpsad66MEejb00K8GugOtYe6zS5TPKrj--LE1r5p2VF4-U94njGjk-FLWd_LVINzD7I-cY9GdiPP-F3AGfhVwcklAJiyKFpRhmZbxSD5vDuFk9XqvcQgASIbtH38p1QSSEN_YimU23ftf5uOcDa1KWhzCTAvtiux9klfITTatWdKqjnMF7YDIjkJJFdw0NzYZz2ClXDe81OLZeImuWaOYpTVOWNDRCOxwS4yLB1migpK2QXmG2Nd1m134ny2nRK0FwIfPu8B0zQPAt2OsqM0v1bPQusBoKA0h41N29r_dMPJl43AbZa531ZZaLWvzOAd9e5X_vhK-MxO3wKAFQ76EogR0350SSgafY6XFWYBWXGKSTwJ-INzZ7PxbOJCiecxoJtj9JhzkQNpV951SokzeRZHV-kBrOAX75cV2a0w8fBXpp1EPgEv7OvByFKQ3MiAq-ZXoJEyZk5a7lIXymP4VYhTc0qRY8Xr710AP_QpQqB9OjIIJC8JpHr_qRZ98Ja5bHJVJbZb1kXxNk0nuX7MXskxbQ-WEI9O6IseCOSqX2iqbQch8BWUPs5L2lF9S5dG1E658Gv24ns03ymgnEzv7_H-FOK1hmdK4iPGFCGhAzc3UdPyV92QCqowVbIHpvOL1D"  # Replace with actual token

# === AIRTABLE CONFIG ===
AIRTABLE_API_KEY = "patyuDyrmZz0s6bLO.7e4f3c3ca7f3a4be93d9d4f3b57c2635fd0aab5dce43bb1de2aa37ceeeda886d"
AIRTABLE_BASE_ID = "appoNbgV6oY603cjb"
AIRTABLE_TABLE_ID = "tblpa06yXMKwflL7m"

def upload_to_dropbox(file_path, dropbox_path):
    """Upload file to Dropbox and return download URL"""
    try:
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Upload to Dropbox
        upload_url = "https://content.dropboxapi.com/2/files/upload"
        headers = {
            "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path,
                "mode": "overwrite"
            })
        }
        
        print(f"DEBUG: Uploading to Dropbox: {dropbox_path}")
        response = requests.post(upload_url, headers=headers, data=file_content, timeout=60)
        response.raise_for_status()
        
        print("DEBUG: Dropbox upload successful")
        
        # Create shareable link
        share_url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
        share_headers = {
            "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        share_data = {
            "path": dropbox_path,
            "settings": {
                "requested_visibility": "public"
            }
        }
        
        print("DEBUG: Creating Dropbox share link...")
        share_response = requests.post(share_url, headers=share_headers, json=share_data, timeout=30)
        
        if share_response.status_code == 200:
            share_result = share_response.json()
            # Convert share URL to direct download URL
            share_link = share_result["url"]
            download_url = share_link.replace("dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
            print(f"DEBUG: Dropbox download URL: {download_url}")
            return download_url
        else:
            print(f"DEBUG: Share link creation failed: {share_response.text}")
            # Return a basic download URL format
            return f"https://dl.dropboxusercontent.com/s/placeholder{dropbox_path}"
            
    except Exception as e:
        raise Exception(f"Dropbox upload failed: {str(e)}")

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
            "dmg_exists": os.path.exists(DMG_SOURCE_PATH),
            "working_dir": os.getcwd()
        }
        print(f"DEBUG INFO: {json.dumps(debug_info, indent=2)}")
        
        # Check required paths
        if not os.path.exists(CREDENTIALS_PATH):
            return {
                "status": "error", 
                "message": f"Credentials file not found: {CREDENTIALS_PATH}"
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
        
        # === Create referral package ===
        safe_name = name.lower().replace(" ", "_").replace(".", "_")
        zip_name = f"Orchestrate_Installer_for_{safe_name}.zip"
        temp_build_dir = f"/tmp/referral_build_{safe_name}"
        zip_path = os.path.join(temp_build_dir, zip_name)
        
        print(f"DEBUG: Creating package {zip_name}")
        
        # Clean up any existing temp directory
        if os.path.exists(temp_build_dir):
            shutil.rmtree(temp_build_dir)
        os.makedirs(temp_build_dir, exist_ok=True)
        
        try:
            # Copy DMG to temp directory
            print("DEBUG: Copying DMG file...")
            dmg_temp_path = os.path.join(temp_build_dir, DMG_FILENAME)
            shutil.copy2(DMG_SOURCE_PATH, dmg_temp_path)
            
            # Create referrer file
            print("DEBUG: Creating referrer.txt...")
            referrer_temp_path = os.path.join(temp_build_dir, "referrer.txt")
            with open(referrer_temp_path, "w") as f:
                f.write(referrer_id)
            
            # Create ZIP package
            print("DEBUG: Creating ZIP package...")
            with ZipFile(zip_path, 'w') as zipf:
                zipf.write(dmg_temp_path, DMG_FILENAME)
                zipf.write(referrer_temp_path, "referrer.txt")
            
            print("DEBUG: ZIP package created successfully")
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to create referral package: {str(e)}"
            }
        
        # === Upload to Dropbox ===
        try:
            dropbox_path = f"/referrals/{zip_name}"
            download_url = upload_to_dropbox(zip_path, dropbox_path)
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to upload to Dropbox: {str(e)}"
            }
        finally:
            # Clean up temp directory
            if os.path.exists(temp_build_dir):
                shutil.rmtree(temp_build_dir)
        
        # === Submit to Airtable ===
        print("DEBUG: Submitting to Airtable...")
        airtable_data = {
            "fields": {
                "referrer_id": referrer_id,
                "referrer_name": referrer_name,
                "recipient_name": name,
                "recipient_email": email,
                "zip_url": download_url
            }
        }
        
        airtable_headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
        
        try:
            response = requests.post(airtable_url, headers=airtable_headers, json=airtable_data, timeout=30)
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
            "download_url": download_url,
            "referrer_id": referrer_id,
            "referrer_name": referrer_name
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
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
        print(f'{{"status": "error", "message": "JSON output failed: {str(e)}"}}')
        sys.stdout.flush()
