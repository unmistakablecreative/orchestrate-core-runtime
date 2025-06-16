import os
import json
import time
import shutil
import subprocess
from zipfile import ZipFile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 🛠 Config
BASE_DIR = '/opt/orchestrate-core-runtime/referral_base'
TEMP_DIR = '/tmp/referral_build'
OUTPUT_DIR = '/opt/orchestrate-core-runtime/app'
WATCH_PATH = '/opt/orchestrate-core-runtime/data'
NETLIFY_SITE = '36144ab8-5036-40bf-837e-c678a5da2be0'  # Site ID, not slug


def build_and_deploy_zip(referrer_id, email):
    zip_name = f'referral_{referrer_id}.zip'
    zip_path = os.path.join(OUTPUT_DIR, zip_name)

    # 🔄 Reset build dir
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # 📦 Copy referral_base template
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

    # 🧠 Load system identity for referrer.txt
    identity_path = '/container_state/system_identity.json'
    user_id = "unknown"
    if os.path.exists(identity_path):
        with open(identity_path) as idf:
            try:
                identity = json.load(idf)
                user_id = identity.get("user_id", "unknown")
            except Exception as e:
                print(f"⚠️ Could not read system identity: {e}")

    # 📝 Write referrer.txt (raw ID only)
    with open(os.path.join(TEMP_DIR, 'referrer.txt'), 'w') as f:
        f.write(user_id)

    # 🗜️ Build ZIP
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(TEMP_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, TEMP_DIR)
                zipf.write(abs_path, arcname)

    print(f"✅ Built: {zip_name}")

    # 🚀 Deploy to Netlify
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
        print(f"🌐 Live URL: https://stalwart-kangaroo-dd7c11.netlify.app/{zip_name}")
    else:
        print("❌ Netlify deploy failed.")


class ReferralHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('referrals.json'):
            with open(event.src_path) as f:
                try:
                    data = json.load(f)
                    for key, value in data.items():
                        email = value.get('email', 'demo@example.com')
                        build_and_deploy_zip(key, email)
                except Exception as e:
                    print(f"❌ Failed to load referrals.json: {e}")


def watch_referrals_file():
    observer = Observer()
    handler = ReferralHandler()
    observer.schedule(handler, path=WATCH_PATH, recursive=False)
    observer.start()
    print('👀 Watching referrals.json for changes...')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    watch_referrals_file()
