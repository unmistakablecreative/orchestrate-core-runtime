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
        if len(matches) == 1:
            return matches[0]
        else:
            print("⚠️ Multiple matches found. Returning the first:")
            print("\n".join(matches))
            return matches[0]
    else:
        raise FileNotFoundError(f"❌ No file matching '{filename_fragment}' found in dropzone.")

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--destination_dir")
    parser.add_argument("--filename")
    parser.add_argument("--new_name")
    args = parser.parse_args()

    if args.key == "find_file":
        print(find_file(args.filename))
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
