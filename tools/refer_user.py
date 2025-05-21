import requests
import json
import os
import subprocess
import zipfile

# Airtable config
AIRTABLE_API_KEY = "patoUXMeRPzU1ufwc.7e4c9e54adc2679be441927970bcd0e69481e2e48b225a7cecfb193cebf2bad6"
AIRTABLE_BASE_ID = "appHggDD1APShGNiZ"
AIRTABLE_TABLE_NAME = "Users"

# Paths
APP_SOURCE_PATH = "/Users/srinivas/Orchestrate Github/orchestrate-installer/Orchestrate_OS_Installer"
APP_BUNDLE_NAME = "Orchestrate_OS_Installer"
GITHUB_REPO_PATH = "/Users/srinivas/Orchestrate Github/orchestrate-referrals"
GITHUB_USERNAME = "unmistakablecreative"
GITHUB_REPO = "orchestrate-referrals"
IDENTITY_FILE = os.path.expanduser("~/Orchestrate Github/orchestrate-docker/system_identity.json")

def get_referrer_id():
    with open(IDENTITY_FILE, "r") as f:
        return json.load(f)["user_id"]

def create_app_bundle(referrer_id, recipient_name):
    zip_name = f"Orchestrate_Installer_for_{recipient_name.replace(' ', '_')}.zip"
    zip_path = os.path.join(GITHUB_REPO_PATH, zip_name)

    bundle_target_path = os.path.join(GITHUB_REPO_PATH, APP_BUNDLE_NAME)
    subprocess.run(["rm", "-rf", bundle_target_path], check=True)
    subprocess.run(["cp", "-R", APP_SOURCE_PATH, GITHUB_REPO_PATH], check=True)

    ref_path = os.path.join(bundle_target_path, "referrer.txt")
    with open(ref_path, "w") as f:
        f.write(referrer_id)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(bundle_target_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, GITHUB_REPO_PATH)
                zipf.write(full_path, arcname=rel_path)

    return zip_name

def push_to_github(zip_filename):
    subprocess.run(["git", "add", zip_filename], cwd=GITHUB_REPO_PATH, check=True)
    subprocess.run(["git", "commit", "-m", f"Add referral: {zip_filename}"], cwd=GITHUB_REPO_PATH, check=True)
    subprocess.run(["git", "push"], cwd=GITHUB_REPO_PATH, check=True)
    return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{zip_filename}"

def submit_to_airtable(name, email, referrer_id, public_url):
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
                    "Stub Link": public_url
                }
            }
        ]
    }
    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()

def refer_user(name, email):
    referrer_id = get_referrer_id()
    zip_file = create_app_bundle(referrer_id, name)
    public_url = push_to_github(zip_file)
    submit_to_airtable(name, email, referrer_id, public_url)
    print(f"✅ Referral created:\n📦 {zip_file}\n🔗 {public_url}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    refer_user(args.name, args.email)