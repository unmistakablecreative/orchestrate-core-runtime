import os
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Inline dispatcher ---
def dispatch_extension_action(action):
    action_type = action.get("type")
    params = action.get("params", {})

    if action_type == "create_referral_zip":
        from json_manager import create_referral_zip
        return create_referral_zip(**params)

    return {"status": "error", "message": f"Unknown action type: {action_type}"}

# --- Core Functions ---

def load_extensions():
    exts = []
    DATA_PATH = 'data'
    if not os.path.exists(DATA_PATH):
        return exts
    for file in os.listdir(DATA_PATH):
        if file.endswith('_sync.json'):
            try:
                with open(os.path.join(DATA_PATH, file)) as f:
                    raw = json.load(f)
                    container = raw.get('entries', raw)
                    for key, ext in container.items():
                        print(f'📄 Loaded: {file} → {key} → {ext}')
                        exts.append(ext)
            except Exception as e:
                print(f'⚠️ Failed to load {file}: {e}')
    return exts

def handle_trigger(extension):
    action = extension.get('action', {})
    if not action:
        print("⚠️ No action specified in extension.")
        return
    result = dispatch_extension_action(action)
    print(f"✅ Action result: {result}")

def start_extension_watcher():
    extensions = load_extensions()
    
    class ExtensionEventHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith('.json'):
                filename = os.path.basename(event.src_path)
                matching = [ext for ext in extensions if ext.get('watch_file') == filename]
                for ext in matching:
                    print(f'🔁 Change detected in {filename} → triggering extension')
                    handle_trigger(ext)
    
    observer = Observer()
    observer.schedule(ExtensionEventHandler(), path='data', recursive=True)
    observer.start()
    print('🧠 Extension watcher running...')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --- CLI Interface ---

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs="?", default="watch")
    parser.add_argument("--params")
    args = parser.parse_args()
    if args.action == "watch":
        start_extension_watcher()
    else:
        print(f"❌ Unknown action '{args.action}'")

if __name__ == "__main__":
    main()
