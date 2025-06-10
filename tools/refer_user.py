import argparse
import json
import os
import subprocess
import zipfile
import base64
import requests
import tempfile
import sys
from io import BytesIO

# === Constants ===
INSTALLER_REPO = "https://github.com/unmistakablecreative/OrchestrateOS_Installer.git"
REFERRAL_RELAY_URL = "https://referral-relay-7ugyt7c5z-srinivas-rao-s-projects.vercel.app/referral"
SYSTEM_ID_PATH = "/container_state/system_identity.json"
EXCLUDED_PATTERNS = [".git", ".DS_Store", "__MACOSX"]

def get_referrer_id():
    with open(SYSTEM_ID_PATH, "r") as f:
        return json.load(f)["user_id"]

def clone_and_extract_installer():
    clone_dir = tempfile.mkdtemp()
    subprocess.run(["git", "clone", INSTALLER_REPO, clone_dir], check=True)

    zip_path = os.path.join(clone_dir, "Orchestrate_OS_Installer.zip")
    extract_path = os.path.join(clone_dir, "unzipped")
    os.makedirs(extract_path, exist_ok=True)

    subprocess.run(["unzip", zip_path, "-d", extract_path], check=True)
    return os.path.join(extract_path, "Orchestrate_OS_Installer")


def inject_referrer(installer_path, referrer_id):
    with open(os.path.join(installer_path, "referrer.txt"), "w") as f:
        f.write(referrer_id)

    # Remove quarantine flag to prevent App Translocation
    subprocess.run([
        "xattr", "-dr", "com.apple.quarantine",
        os.path.join(installer_path, "Launch Orchestrate.app")
    ])



def build_clean_zip(installer_path):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(installer_path):
            for file in files:
                if any(skip in file for skip in EXCLUDED_PATTERNS):
                    continue
                full = os.path.join(root, file)
                if any(skip in full for skip in EXCLUDED_PATTERNS):
                    continue
                rel = os.path.relpath(full, installer_path)
                zipf.write(full, arcname=rel)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def refer_user(name, email, referrer_id, silent=False):
    installer_path = clone_and_extract_installer()
    inject_referrer(installer_path, referrer_id)
    encoded_zip = build_clean_zip(installer_path)

    payload = {
        "name": name,
        "email": email,
        "referrer_id": referrer_id,
        "bundle": encoded_zip
    }

    r = requests.post(REFERRAL_RELAY_URL, json=payload)
    if not silent:
        print("✅ Status:", r.status_code)
        try:
            print("🌐 Response:", r.json())
        except:
            print("❌ Invalid response:", r.text)
    return {"status": "success", "message": f"📨 Referral sent for {name}", "http_status": r.status_code}

def run(params):
    referrer_id = get_referrer_id()
    return refer_user(params["name"], params["email"], referrer_id, silent=True)

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "refer_user" and sys.argv[2] == "--params":
        input_data = json.loads(sys.argv[3])
        result = run(input_data)
        print(json.dumps(result, indent=2))
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--name", required=True)
        parser.add_argument("--email", required=True)
        args = parser.parse_args()
        referrer_id = get_referrer_id()
        refer_user(args.name, args.email, referrer_id)
