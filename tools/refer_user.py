# refer_user.py

import os
import json
import requests
import shutil
from zipfile import ZipFile
from datetime import datetime

# === CONFIG ===
DMG_FILENAME = "orchestrate_engine_final.dmg"
REPO_DIR = "/Users/srinivas/repos/orchestrate-user-referrals"
DMG_SOURCE_PATH = os.path.join(REPO_DIR, DMG_FILENAME)
AIRTABLE_API_KEY = "patyuDyrmZz0s6bLO.7e4f3c3ca7f3a4be93d9d4f3b57c2635fd0aab5dce43bb1de2aa37ceeeda886d"
AIRTABLE_BASE_ID = "appoNbgV6oY603cjb"
AIRTABLE_TABLE_ID = "tblpa06yXMKwflL7m"
CREDENTIALS_PATH = os.path.expanduser("~/Library/Application Support/OrchestrateEngine/state/system_identity.json")
SECONDBRAIN_PATH = os.path.expanduser("~/Library/Application Support/OrchestrateEngine/state/secondbrain.json")
OUTPUT_FOLDER = os.path.join(REPO_DIR)


def refer_user(params):
    name = params.get("name")
    email = params.get("email")
    if not name or not email:
        return {"status": "error", "message": "Missing name or email"}

    if not os.path.exists(CREDENTIALS_PATH):
        return {"status": "error", "message": "Missing system_identity.json"}

    with open(CREDENTIALS_PATH) as f:
        identity = json.load(f)
    referrer_id = identity.get("user_id")

    with open(SECONDBRAIN_PATH) as f:
        brain = json.load(f)
    referrer_name = brain.get("entries", {}).get("user_profile", {}).get("full_name", "Unknown Referrer")

    # === Prepare ZIP ===
    safe_name = name.lower().replace(" ", "_")
    zip_name = f"Orchestrate_Installer_for_{safe_name}.zip"
    zip_path = os.path.join(OUTPUT_FOLDER, zip_name)
    temp_dir = os.path.join("/tmp", f"referral_build_{safe_name}")

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    shutil.copy2(DMG_SOURCE_PATH, os.path.join(temp_dir, DMG_FILENAME))
    with open(os.path.join(temp_dir, "referrer.txt"), "w") as f:
        f.write(referrer_id)

    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, temp_dir)
                zipf.write(abs_path, arcname)

    # === Push to GitHub ===
    os.chdir(REPO_DIR)
    os.system("git pull origin main")
    os.system(f"git add '{zip_name}' && git commit -m 'Add referral zip for {name}' && git push origin main")

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
    r = requests.post(url, headers=headers, json=airtable_payload)

    if r.status_code != 200:
        return {"status": "error", "message": f"Airtable error: {r.text}"}

    return {
        "status": "success",
        "message": f"Referral zip created and pushed. Invite sent to {name}.",
        "zip_url": zip_url
    }


# === CLI Support
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--params", type=str, required=True, help="JSON string with 'name' and 'email'")
    args = parser.parse_args()

    try:
        params = json.loads(args.params)
        result = refer_user(params)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
