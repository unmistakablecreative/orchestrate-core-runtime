import os
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tools.json_manager import dispatch_extension_action

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

def main():
    start_extension_watcher()

# --- Action Router ---
def main():
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--params")
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}
    if args.action == "load_extensions":
        result = load_extensions(**params)
    elif args.action == "handle_trigger":
        result = handle_trigger(**params)
    elif args.action == "start_extension_watcher":
        result = start_extension_watcher(**params)
    elif args.action == "main":
        result = main(**params)
    else:
        result = {"status": "error", "message": f"Unknown action {args.action}"}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()