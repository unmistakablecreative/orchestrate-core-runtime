import sys
import json
import subprocess
import os

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
        return {
            "match_count": len(matches),
            "matches": matches,
            "selected": matches[0]
        }
    else:
        return {
            "error": f"No file matching '{filename_fragment}' found in dropzone."
        }


def read_file(filename_fragment):
    result = find_file(filename_fragment)
    if "selected" not in result:
        return {"error": "File not found."}

    path = result["selected"]
    content = subprocess.run(
        ['cat', path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return {
        "filename": os.path.basename(path),
        "content": content.stdout.strip()
    }


def rename_file(filename_fragment, new_name):
    result = find_file(filename_fragment)
    if "selected" not in result:
        return {"error": "File not found."}

    old_path = result["selected"]
    new_path = os.path.join(os.path.dirname(old_path), new_name)
    subprocess.run(['mv', old_path, new_path], check=True)
    return {"renamed_from": os.path.basename(old_path), "renamed_to": new_name}


def move_file(filename_fragment, destination_dir):
    result = find_file(filename_fragment)
    if "selected" not in result:
        return {"error": "File not found."}

    src = result["selected"]
    os.makedirs(destination_dir, exist_ok=True)
    dest = os.path.join(destination_dir, os.path.basename(src))
    subprocess.run(['mv', src, dest], check=True)
    return {"moved_file": os.path.basename(src), "destination": destination_dir}


def main():
    try:
        action = sys.argv[1]
        params = {}

        if "--params" in sys.argv:
            idx = sys.argv.index("--params")
            raw = sys.argv[idx + 1]
            params = json.loads(raw)

        filename = params.get("filename")
        destination_dir = params.get("destination_dir")
        new_name = params.get("new_name")

        if action == "find_file":
            print(json.dumps(find_file(filename)))
        elif action == "read_file":
            print(json.dumps(read_file(filename)))
        elif action == "rename_file":
            print(json.dumps(rename_file(filename, new_name)))
        elif action == "move_file":
            print(json.dumps(move_file(filename, destination_dir)))
        else:
            print(json.dumps({"error": f"Unknown action '{action}'"}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
