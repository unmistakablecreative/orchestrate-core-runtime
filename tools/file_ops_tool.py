import subprocess
import os
import json
import sys

DROPZONE_PATH = "/orchestrate_user/dropzone"

def find_file(filename_fragment):
    result = subprocess.run(
        ['find', DROPZONE_PATH, '-iname', f'*{filename_fragment}*'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    matches = result.stdout.strip().splitlines()

    if matches:
        return json.dumps({
            "match_count": len(matches),
            "matches": matches,
            "selected": matches[0]
        })
    else:
        return json.dumps({
            "error": f"No file matching '{filename_fragment}' found in dropzone."
        })


def read_file(filename_fragment):
    path = json.loads(find_file(filename_fragment)).get("selected")
    if not path:
        return json.dumps({"error": "No matching file found to read."})
    
    result = subprocess.run(
        ['cat', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return json.dumps({
        "filename": os.path.basename(path),
        "content": result.stdout.strip()
    })


def rename_file(filename_fragment, new_name):
    path = json.loads(find_file(filename_fragment)).get("selected")
    if not path:
        return json.dumps({"error": "No matching file found to rename."})

    dest_path = os.path.join(os.path.dirname(path), new_name)
    subprocess.run(['mv', path, dest_path], check=True)
    return json.dumps({
        "renamed_from": os.path.basename(path),
        "renamed_to": new_name
    })


def move_file(filename_fragment, destination_dir):
    path = json.loads(find_file(filename_fragment)).get("selected")
    if not path:
        return json.dumps({"error": "No matching file found to move."})

    os.makedirs(destination_dir, exist_ok=True)
    dest_path = os.path.join(destination_dir, os.path.basename(path))
    subprocess.run(['mv', path, dest_path], check=True)
    return json.dumps({
        "moved_file": os.path.basename(path),
        "destination": destination_dir
    })


def main():
    try:
        if not sys.argv[1:] and not sys.stdin.isatty():
            raw = sys.stdin.read()
            data = json.loads(raw)
            key = data.get("key")
            filename = data.get("filename")
            destination_dir = data.get("destination_dir")
            new_name = data.get("new_name")
        else:
            import argparse
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

        output = ""
        if key == "find_file":
            output = find_file(filename)
        elif key == "read_file":
            output = read_file(filename)
        elif key == "rename_file":
            output = rename_file(filename, new_name)
        elif key == "move_file":
            output = move_file(filename, destination_dir)
        else:
            output = json.dumps({"error": f"Unknown key: {key}"})

        print(output)

    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
