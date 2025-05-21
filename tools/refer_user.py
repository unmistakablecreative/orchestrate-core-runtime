import requests
import json
import os
import zipfile
import subprocess

# Airtable config
AIRTABLE_API_KEY = "patoUXMeRPzU1ufwc.7e4c9e54adc2679be441927970bcd0e69481e2e48b225a7cecfb193cebf2bad6"
AIRTABLE_BASE_ID = "appHggDD1APShGNiZ"
AIRTABLE_TABLE_NAME = "Users"

# Paths
INSTALLER_SOURCE = "/app"
REFERRAL_REPO_PATH = "/Users/srinivas/Orchestrate Github/orchestrate-user-referrals"
GITHUB_USERNAME = "unmistakablecreative"
GITHUB_REPO = "orchestrate-user-referrals"

EXCLUDE_NAMES = {
    "_paste_into_gpt.txt",
    "custom_instructions.json",
    "openapi.yaml",
    "referrer.txt",
    "orchestrate-core-runtime"
}

def get_referrer_id():
    container_path = "/tmp/orchestrate/system_identity.json"
    if os.path.exists(container_path):
        with open(container_path, "r") as f:
            return json.load(f)["user_id"]
    raise RuntimeError("❌ Referrer ID not found — container not initialized properly.")

def create_zip(referrer_id, recipient_name):
    os.makedirs(REFERRAL_REPO_PATH, exist_ok=True)
    formatted_name = recipient_name.replace(" ", "_")
    zip_name = f"Orchestrate_Installer_for_{formatted_name}.zip"
    zip_path = os.path.join(REFERRAL_REPO_PATH, zip_name)
    bundle_target_path = os.path.join(REFERRAL_REPO_PATH, "Orchestrate_OS_Installer")

    subprocess.run(["rm", "-rf", bundle_target_path], check=True)
    subprocess.run(["cp", "-R", INSTALLER_SOURCE, bundle_target_path], check=True)

    with open(os.path.join(bundle_target_path, "referrer.txt"), "w") as f:
        f.write(referrer_id)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(bundle_target_path):
            for file in files:
                if file in EXCLUDE_NAMES:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, REFERRAL_REPO_PATH)
                zipf.write(full_path, arcname=rel_path)

    subprocess.run(["rm", "-rf", bundle_target_path], check=True)
    return zip_name

def push_zip_to_github(zip_file):
    subprocess.run(["git", "add", zip_file], cwd=REFERRAL_REPO_PATH, check=True)
    subprocess.run(["git", "commit", "-m", f"Add referral zip: {zip_file}"], cwd=REFERRAL_REPO_PATH, check=True)
    subprocess.run(["git", "push"], cwd=REFERRAL_REPO_PATH, check=True)
    return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{zip_file}"

def submit_to_airtable(name, email, referrer_id, zip_url):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "records": [
            {
                "fields": {
                    "Name": name,
                    "Email": email,
                    "Status": "pending",
                    "Referrer ID": referrer_id,
                    "Stub Link": zip_url
                }
            }
        ]
    }
    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()

def refer_user(name, email):
    referrer_id = get_referrer_id()
    zip_file = create_zip(referrer_id, name)
    zip_url = push_zip_to_github(zip_file)
    submit_to_airtable(name, email, referrer_id, zip_url)
    print(f"✅ Referral created:\n📦 {zip_file}\n🔗 {zip_url}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    refer_user(args.name, args.email)
