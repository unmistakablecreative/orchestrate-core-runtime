import os
import json
import argparse

ALLOWED_DIRS = {
    'dropzone': '/orchestrate_user/dropzone',
    'system_docs': '/opt/orchestrate-core-runtime/system_docs'  # container path
}

def read_file(params):
    folder = params.get('folder', 'dropzone')
    filename = params.get('filename')

    if folder not in ALLOWED_DIRS:
        return {'status': 'error', 'message': f'❌ Unknown folder: {folder}'}

    dir_path = ALLOWED_DIRS[folder]

    if not os.path.isdir(dir_path):
        return {'status': 'error', 'message': f'❌ Folder path does not exist: {dir_path}'}

    if filename:
        safe_name = os.path.basename(filename)
        path = os.path.join(dir_path, safe_name)

        if not os.path.isfile(path):
            return {'status': 'error', 'message': f'❌ File not found: {safe_name} in {folder}'}
    else:
        # Default: use most recent file in target directory
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        if not files:
            return {'status': 'error', 'message': f'❌ No files found in {folder}'}
        files.sort(key=lambda f: os.path.getmtime(os.path.join(dir_path, f)), reverse=True)
        path = os.path.join(dir_path, files[0])

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            'status': 'success',
            'filename': os.path.basename(path),
            'data': content
        }
    except Exception as e:
        return {'status': 'error', 'message': f'❌ Failed to read file: {str(e)}'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params', type=str)
    args = parser.parse_args()

    try:
        params = json.loads(args.params) if args.params else {}
    except json.JSONDecodeError:
        print(json.dumps({'status': 'error', 'message': '❌ Invalid JSON.'}, indent=4))
        return

    if args.action == 'read_file':
        result = read_file(params)
    else:
        result = {'status': 'error', 'message': f'❌ Unknown action: {args.action}'}

    print(json.dumps(result, indent=4))

if __name__ == '__main__':
    main()
