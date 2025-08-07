import subprocess
import os

DROPZONE_PATH = "/orchestrate_user/dropzone"


def find_file(filename_fragment):
    import json
    result = subprocess.run(
        ['find', DROPZONE_PATH, '-iname', f'*{filename_fragment}*'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    matches = result.stdout.strip().splitlines()
    
    if matches:
        # Always return JSON — even with multiple results
        return json.dumps({
            "match_count": len(matches),
            "matches": matches,
            "selected": matches[0]
        })
    else:
        # Return JSON error message for consistent parsing
        return json.dumps({
            "error": f"No file matching '{filename_fragment}' found in dropzone."
        })

def read_file(filename_fragment):
    path = find_file(filename_fragment)
    result = subprocess.run(
        ['cat', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()

def rename_file(filename_fragment, new_name):
    path = find_file(filename_fragment)
    dest_path = os.path.join(os.path.dirname(path), new_name)
    subprocess.run(['mv', path, dest_path], check=True)
    return f"✅ Renamed '{os.path.basename(path)}' to '{new_name}'"

def move_file(filename_fragment, destination_dir):
    path = find_file(filename_fragment)
    os.makedirs(destination_dir, exist_ok=True)
    dest_path = os.path.join(destination_dir, os.path.basename(path))
    subprocess.run(['mv', path, dest_path], check=True)
    return f"✅ Moved '{os.path.basename(path)}' to '{destination_dir}'"


def main():
    import argparse
    import sys
    import json

    # Support JSON mode if being executed via GPT runtime
    if not sys.argv[1:] and not sys.stdin.isatty():
        raw = sys.stdin.read()
        data = json.loads(raw)
        key = data.get("key")
        filename = data.get("filename")
        destination_dir = data.get("destination_dir")
        new_name = data.get("new_name")
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--key", required=True)
        parser.add_argument("--filename")
        parser.add_argument("--destination_dir")
        parser.add_argument("--new_name")
        args = parser.parse_args()
        key = args.key
        filename = args.filename
        destination_dir = args.destination_dir
        new_name = args.new_name

    # Dispatch logic
    if key == "find_file":
        print(find_file(filename))
    elif key == "read_file":
        print(read_file(filename))
    elif key == "rename_file":
        print(rename_file(filename, new_name))
    elif key == "move_file":
        print(move_file(filename, destination_dir))
    else:
        print(f"❌ Unknown key: {key}")
