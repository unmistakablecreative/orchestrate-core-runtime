# refer_user.py — Final corrected version with flat zip structure

import argparse
import json
import os
import subprocess
import zipfile
import base64
import requests
import tempfile
from io import BytesIO

INSTALLER_REPO = "https://github.com/unmistakablecreative/OrchestrateOS_Installer.git"
REFERRAL_RELAY_URL = "https://referral-relay-fzc4u40pd-srinivas-rao-s-projects.vercel.app/referral"
SYSTEM_ID_PATH = "/tmp/orchestrate/system_identity.json"

def get_referrer_id():
    with open(SYSTEM_ID_PATH, "r") as f:
        return json.load(f)["user_id"]

def clone_installer():
    target_dir = tempfile.mkdtemp()
    subprocess.run(["git", "clone", INSTALLER_REPO, target_dir], check=True)
    return target_dir

def inject_referrer(installer_path, referrer_id):
    ref_path = os.path.join(installer_path, "referrer.txt")
    with open(ref_path, "w") as f:
        f.write(referrer_id)

def build_flat_zip(installer_path):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(installer_path):
            for file in files:
                full = os.path.join(root, file)
                rel = os.path.relpath(full, installer_path)  # flatten
                zipf.write(full, arcname=rel)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def refer_user(name, email, referrer_id):
    installer_path = clone_installer()
    inject_referrer(installer_path, referrer_id)
    encoded_zip = build_flat_zip(installer_path)

    payload = {
        "name": name,
        "email": email,
        "referrer_id": referrer_id,
        "bundle": encoded_zip
    }

    r = requests.post(REFERRAL_RELAY_URL, json=payload)
    print("✅ Status:", r.status_code)
    try:
        print("🌐 Response:", r.json())
    except:
        print("❌ Invalid response:", r.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    referrer_id = get_referrer_id()
    refer_user(args.name, args.email, referrer_id)
