import os
import json
import time
import shutil
import subprocess
from zipfile import ZipFile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# 🛠 Config
BASE_DIR = '/opt/orchestrate-core-runtime/referral_base'
TEMP_DIR = '/tmp/referral_build'
OUTPUT_DIR = '/opt/orchestrate-core-runtime/app'
WATCH_PATH = '/opt/orchestrate-core-runtime/data'
NETLIFY_SITE = '36144ab8-5036-40bf-837e-c678a5da2be0'  # Netlify Site ID

def build_and_deploy_zip(referrer_id, name, email):
    import requests

    for file in os.listdir(OUTPUT_DIR):
        if file.endswith(".zip"):
            os.remove(os.path.join(OUTPUT_DIR, file))

    safe_name = name.replace(" ", "_").lower()
    zip_name = f'referral_{safe_name}.zip'
    zip_path = os.path.join(OUTPUT_DIR, zip_name)

    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    if not os.path.exists(BASE_DIR):
        print(f"❌ BASE_DIR not found: {BASE_DIR}")
        return

    for file in os.listdir(BASE_DIR):
        src = os.path.join(BASE_DIR, file)
        dest = os.path.join(TEMP_DIR, file)
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)

    identity_path = '/container_state/system_identity.json'
    user_id = "unknown"
    if os.path.exists(identity_path):
        with open(identity_path) as idf:
            try:
                identity = json.load(idf)
                user_id = identity.get("user_id", "unknown")
            except Exception as e:
                print(f"⚠️ Failed to read system identity: {e}")

    with open(os.path.join(TEMP_DIR, 'referrer.txt'), 'w') as f:
        f.write(user_id)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(TEMP_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, TEMP_DIR)
                zipf.write(abs_path, arcname)

    print(f"✅ Built referral zip: {zip_path}")

    os.chdir(OUTPUT_DIR)
    deploy_cmd = [
        "/usr/local/bin/netlify", "deploy",
        "--dir=.", "--prod",
        "--message", f"referral_{referrer_id}",
        "--site", NETLIFY_SITE
    ]

    print("🚚 Deploying to Netlify...")
    result = subprocess.run(deploy_cmd, capture_output=True, text=True)

    print("---- NETLIFY STDOUT ----")
    print(result.stdout)
    print("---- NETLIFY STDERR ----")
    print(result.stderr)

    if result.returncode == 0:
        referral_url = f"https://stalwart-kangaroo-dd7c11.netlify.app/{zip_name}"
        print(f"🌐 Live URL: {referral_url}")

        WEBHOOK_URL = "https://hooks.airtable.com/workflows/v1/genericWebhook/appHggDD1APShGNiZ/wflGBzCgFTzCbwJud/wtrQuynZz6WuEUGSB"
        payload = {
            "referrer_id": referrer_id,
            "name": name,
            "email": email,
            "referral_url": referral_url
        }
        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                print("✅ Webhook delivered successfully")
            else:
                print(f"❌ Webhook failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Exception sending webhook: {e}")
    else:
        print("❌ Netlify deploy failed.")


class ReferralHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('referrals.json'):
            with open(event.src_path) as f:
                try:
                    data = json.load(f)
                    entries = data.get("entries", {})
                    for key, value in entries.items():
                        name = value.get('name', 'Unknown User')
                        email = value.get('email', 'demo@example.com')
                        build_and_deploy_zip(key, name, email)
                except Exception as e:
                    print(f"❌ Failed to process referrals.json: {e}")


def start_referral_watcher():
    observer = Observer()
    handler = ReferralHandler()
    observer.schedule(handler, path=WATCH_PATH, recursive=False)
    observer.start()
    print('👀 Watching referrals.json for changes...')

    def monitor():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    monitor()  # ✅ BLOCK the main thread so it doesn't exit


if __name__ == "__main__":
    start_referral_watcher()
