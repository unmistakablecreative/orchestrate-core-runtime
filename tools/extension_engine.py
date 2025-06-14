import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from zipfile import ZipFile
import shutil


def load_extensions():
    exts = []
    DATA_PATH = '/opt/orchestrate-core-runtime/data'
    if not os.path.exists(DATA_PATH):
        return exts
    for file in os.listdir(DATA_PATH):
        if file.endswith('_sync.json'):
            try:
                with open(os.path.join(DATA_PATH, file)) as f:
                    raw = json.load(f)
                    container = raw.get('entries', raw)
                    for key, ext in container.items():
                        print(
                            f'📄 Loading: {file} → key: {key} → type: {type(ext)} → contents: {ext}'
                            )
                        exts.append(ext)
            except Exception as e:
                print(f'⚠️ Failed to load {file}: {e}')
    print(
        f"🔎 Loaded extensions: {[e.get('watch_file') for e in exts if isinstance(e, dict)]}"
        )
    return exts


def on_modified_handler(event):
    if not event.is_directory and event.src_path.endswith('.json'):
        filename = os.path.basename(event.src_path)
        extensions = load_extensions()
        for ext in extensions:
            if ext.get('watch_file') == filename:
                print(f'🔁 Detected change in {filename} → running action')
                handle_trigger(ext)


def start_watcher():
    loaded_extensions = load_extensions()


    class ExtensionEventHandler(FileSystemEventHandler):
        VALID_EVENTS = {'modified', 'closed'}

        def on_any_event(self, event):
            print(f'📡 Event: {event.event_type} → {event.src_path}')
            if event.event_type not in self.VALID_EVENTS:
                return
            if not event.is_directory and event.src_path.endswith('.json'):
                filename = os.path.basename(event.src_path)
                matching_exts = [ext for ext in loaded_extensions if ext.
                    get('watch_file') == filename]
                if not matching_exts:
                    return
                for ext in matching_exts:
                    print(f'🔁 Detected change in {filename} → running action')
                    handle_trigger(ext)
    WATCH_FOLDERS = ['/opt/orchestrate-core-runtime/data/']
    observer = Observer()
    for folder in WATCH_FOLDERS:
        observer.schedule(ExtensionEventHandler(), folder, recursive=True)
    observer.start()
    print('🧠 Extension Engine watching folders (watchdog mode)...')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def handle_trigger(extension):
    action = extension.get('action', {})
    type = action.get('type')
    if type == 'create_referral_zip':
        build_referral_zip(extension)


def get_referrer_id():
    IDENTITY_FILE = '/container_state/system_identity.json'
    if not os.path.exists(IDENTITY_FILE):
        print('❌ system_identity.json not found')
        return 'unknown'
    with open(IDENTITY_FILE) as f:
        data = json.load(f)
        return data.get('user_id', 'unknown')


def build_referral_zip(extension):
    referrer_id = get_referrer_id()
    if referrer_id == 'unknown':
        return
    REFERRAL_BASE = '/opt/orchestrate-core-runtime/referral_base'
    TEMP_DIR = '/tmp/referral_build'
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    for file in os.listdir(REFERRAL_BASE):
        src_file = os.path.join(REFERRAL_BASE, file)
        dest_path = os.path.join(TEMP_DIR, file)
        if os.path.isdir(src_file):
            shutil.copytree(src_file, dest_path)
        elif os.path.isfile(src_file):
            shutil.copy(src_file, dest_path)
    IDENTITY_FILE = '/container_state/system_identity.json'
    user_id = referrer_id
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE) as f:
            identity_data = json.load(f)
            user_id = identity_data.get('user_id', referrer_id)
    with open(os.path.join(TEMP_DIR, 'referrer.txt'), 'w') as f:
        f.write(user_id)
    ZIP_OUTPUT_PATH = '/app'
    os.makedirs(ZIP_OUTPUT_PATH, exist_ok=True)
    zip_filename = f'referral_{user_id}.zip'
    zip_path = os.path.join(ZIP_OUTPUT_PATH, zip_filename)
    with ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, TEMP_DIR)
                zipf.write(abs_path, arcname)
    email = extension.get('action', {}).get('email', 'test@demo.com')
    os.system(
        f'curl -F "file=@{zip_path}" -F "email={email}" https://orchestraterelay-au67ugk7o-srinivas-rao-s-projects.vercel.app/upload'
        )


def main():
    start_watcher()


if __name__ == '__main__':
    main()
