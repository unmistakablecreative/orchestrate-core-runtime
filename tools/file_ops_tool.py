import os
import shutil

# --- Container-Aware Search Paths ---
SEARCH_DIRS = [
    "/orchestrate_user/dropzone",
    "/orchestrate_user/vault/watch_books",
    "/orchestrate_user/vault/watch_transcripts",
    "/orchestrate_user/orchestrate_exports/markdown",
    "/opt/orchestrate-core-runtime/code_blueprints",
    "/opt/orchestrate-core-runtime/compositions",
    "/app"
]

# --- Core Functions ---

def resolve_path(filename):
    for dir in SEARCH_DIRS:
        full_path = os.path.join(dir, filename)
        if os.path.exists(full_path):
            return full_path
    raise FileNotFoundError(f"'{filename}' not found in container search paths.")

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

# --- CLI Entrypoint ---

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--destination_dir")
    parser.add_argument("--filename")
    parser.add_argument("--new_name")
    args = parser.parse_args()

    if args.key == "resolve_path":
        print(resolve_path(args.filename))
    elif args.key == "read_file":
        print(read_file(args.filename))
    elif args.key == "rename_file":
        print(rename_file(args.filename, args.new_name))
    elif args.key == "move_file":
        print(move_file(args.filename, args.destination_dir))
    else:
        print(f"❌ Unknown key: {args.key}")

if __name__ == "__main__":
    main()
