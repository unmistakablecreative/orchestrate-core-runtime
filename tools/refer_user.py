
import argparse
import json
import os
import zipfile
import base64
import requests
from io import BytesIO

def refer_user(name, email, referrer_id):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("referrer.txt", referrer_id)
        zipf.writestr("README.txt", f"Installer for {name}")

    b64_zip = base64.b64encode(buffer.getvalue()).decode("utf-8")

    payload = {
        "name": name,
        "email": email,
        "referrer_id": referrer_id,
        "bundle": b64_zip
    }

    url = os.environ["REFERRAL_RELAY_URL"]
    r = requests.post(url, json=payload)
    print("✅ Status:", r.status_code)
    print("🌐 Response:", r.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    with open("/tmp/orchestrate/system_identity.json", "r") as f:
        referrer_id = json.load(f)["user_id"]

    refer_user(args.name, args.email, referrer_id)
