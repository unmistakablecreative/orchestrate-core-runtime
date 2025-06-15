import os
import json
import time
import shutil
import subprocess
from zipfile import ZipFile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def build_and_deploy_zip(referrer_id, email):
    import os
    import shutil
    from zipfile import ZipFile
    import subprocess

    BASE_DIR = '/opt/orchestrate-core-runtime/referral_base'
    TEMP_DIR = '/tmp/referral_build'
    OUTPUT_DIR = '/opt/orchestrate-core-runtime/app'
    ZIP_NAME = f'referral_{referrer_id}.zip'
    ZIP_PATH = os.path.join(OUTPUT_DIR, ZIP_NAME)

    # Reset temp build dir
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Copy referral_base contents
    for file in os.listdir(BASE_DIR):
        src = os.path.join(BASE_DIR, file)
        dest = os.path.join(TEMP_DIR, file)
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)

    # Add referrer.txt
    with open(os.path.join(TEMP_DIR, 'referrer.txt'), 'w') as f:
        f.write(f"Referrer ID: {referrer_id}\nEmail: {email}")

    # Build ZIP
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with ZipFile(ZIP_PATH, 'w') as zipf:
        for root, _, files in os.walk(TEMP_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, TEMP_DIR)
                zipf.write(abs_path, arcname)

    print(f"✅ Built referral zip: {ZIP_PATH}")

    # Deploy to Netlify using absolute path to avoid 'not found' error
    deploy_dir = OUTPUT_DIR
    os.chdir(deploy_dir)

    deploy_cmd = [
        "/usr/local/bin/netlify", "deploy",
        "--dir=.", "--prod",
        f"--message=referral_{referrer_id}"
    ]

    result = subprocess.run(deploy_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("🌐 Referral deployed successfully.")
        print(result.stdout)
    else:
        print("❌ Netlify deploy failed:")
        print(result.stderr)




class ReferralHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('referrals.json'):
            with open(event.src_path) as f:
                data = json.load(f)
                for key, value in data.items():
                    email = value.get('email', 'demo@example.com')
                    build_and_deploy_zip(key, email)

def watch_referrals_file():
    observer = Observer()
    handler = ReferralHandler()
    observer.schedule(handler, path='/opt/orchestrate-core-runtime/data', recursive=False)
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
