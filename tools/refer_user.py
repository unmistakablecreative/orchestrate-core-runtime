import argparse
import json
import os
import subprocess
import zipfile
import requests
import tempfile

INSTALLER_REPO = "https://github.com/unmistakablecreative/OrchestrateOS_Installer.git"
REFERRAL_RELAY_URL = "https://referral-relay-fzc4u40pd-srinivas-rao-s-projects.vercel.app/referral"
SYSTEM_ID_PATH = "/tmp/orchestrate/system_identity.json"

def get_referrer_id():
    with open(SYSTEM_ID_PATH, "r") as f:
        return json.load(f)["user_id"]

def clone_and_extract_installer():
    tmpdir = tempfile.mkdtemp()
    subprocess.run(["git", "clone", INSTALLER_REPO, tmpdir], check=True)
    zip_path = os.path.join(tmpdir, "Orchestrate_OS_Installer.zip")
    extract_dir = os.path.join(tmpdir, "unzipped")
    os.makedirs(extract_dir, exist_ok=True)
    subprocess.run(["unzip", zip_path, "-d", extract_dir], check=True)
    return os.path.join(extract_dir, "Orchestrate_OS_Installer")

def inject_referrer(installer_path, referrer_id):
    with open(os.path.join(installer_path, "referrer.txt"), "w") as f:
        f.write(referrer_id)

def upload_to_gofile(installer_path):
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(tmp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(installer_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, installer_path)
                zipf.write(full_path, arcname=arcname)
    with open(tmp_zip.name, "rb") as f:
        r = requests.post("https://store1.gofile.io/uploadFile", files={"file": f})
        r.raise_for_status()
        return r.json()["data"]["downloadPage"]

def refer_user(name, email, referrer_id):
    path = clone_and_extract_installer()
    inject_referrer(path, referrer_id)
    bundle = upload_to_gofile(path)

    payload = {
        "name": name,
        "email": email,
        "referrer_id": referrer_id,
        "bundle": bundle
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
    refer_user(args.name, args.email, get_referrer_id())
