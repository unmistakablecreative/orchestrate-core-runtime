import os
import json
import time
import shutil
from zipfile import ZipFile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Core Functions ---

def build_referral_zip(referrer_id, email):
    TEMP_DIR = '/tmp/referral_build'
    BASE_DIR = '/opt/orchestrate-core-runtime/referral_base'
    DEPLOY_DIR = '/opt/orchestrate-core-runtime/app'
    
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    for file in os.listdir(BASE_DIR):
        src = os.path.join(BASE_DIR, file)
        dest = os.path.join(TEMP_DIR, file)
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
    
    with open(os.path.join(TEMP_DIR, 'referrer.txt'), 'w') as f:
        f.write(referrer_id)
    
    os.makedirs(DEPLOY_DIR, exist_ok=True)
    zip_path = os.path.join(DEPLOY_DIR, f'referral_{referrer_id}.zip')
    with ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, TEMP_DIR)
                zipf.write(abs_path, arcname)
    
    print(f'✅ Built referral zip: {zip_path}')

def watch_referrals_file():
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class ReferralHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('referrals.json'):
                with open(event.src_path) as f:
                    data = json.load(f)
                    for key, value in data.items():
                        referrer_id = key
                        email = value.get('email', 'demo@example.com')
                        build_referral_zip(referrer_id, email)
    
    observer = Observer()
    observer.schedule(ReferralHandler(), path='/opt/orchestrate-core-runtime/data', recursive=False)
    observer.start()
    print('👀 Watching referrals.json for changes...')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --- Action Router ---
def main():
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--params")
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}
    if args.action == "build_referral_zip":
        result = build_referral_zip(**params)
    elif args.action == "watch_referrals_file":
        result = watch_referrals_file(**params)
    else:
        result = {"status": "error", "message": f"Unknown action {args.action}"}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
