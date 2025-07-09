import os
import shutil
import argparse

# --- Search Paths ---
SEARCH_DIRS = [
    "/orchestrate_user/dropzone",
    "/orchestrate_user/vault/watch_books",
    "/orchestrate_user/vault/watch_transcripts",
    "/orchestrate_user/orchestrate_exports/markdown",
    "/opt/orchestrate-core-runtime/code_blueprints",
    "/opt/orchestrate-core-runtime/compositions",
    "/app"
]

# --- Core Utilities ---
def resolve_path(filename):
    for dir in SEARCH_DIRS:
        full_path = os.path.join(dir, filename)
        if os.path.exists(full_path):
            return full_path
    raise FileNotFoundError(f"'{filename}' not found in any configured search path.")

def read_file(filename):
    path = resolve_path(filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def rename_file(filename, new_name):
    path = resolve_path(filename)
    dest_path = os.path.join(os.path.dirname(path), new_name)
    os.rename(path, dest_path)
    return f"✅ Renamed '{filename}' to '{new_name}'"

def move_file(filename, destination_dir):
    path = resolve_path(filename)
    os.makedirs(destination_dir, exist_ok=True)
    dest_path = os.path.join(destination_dir, os.path.basename(path))
    shutil.move(path, dest_path)
    return f"✅ Moved '{filename}' to '{destination_dir}'"

# --- Entrypoint ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--filename")
    parser.add_argument("--new_name")
    parser.add_argument("--destination_dir")
    args = parser.parse_args()

    dispatch = {
        "resolve_path": lambda: resolve_path(args.filename),
        "read_file": lambda: read_file(args.filename),
        "rename_file": lambda: rename_file(args.filename, args.new_name),
        "move_file": lambda: move_file(args.filename, args.destination_dir),
    }

    try:
        action = dispatch[args.key]()
        print(action)
    except KeyError:
        print(f"❌ Unknown key: {args.key}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
