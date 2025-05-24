import os
import json
import argparse

DROPZONE_DIR = '/orchestrate_user/dropzone'

def read_file(params):
    filename = params.get('filename')

    if filename:
        safe_name = os.path.basename(filename)
        path = os.path.join(DROPZONE_DIR, safe_name)
        if not os.path.isfile(path):
            return {'status': 'error', 'message': '❌ File not found in dropzone.'}
    else:
        # Fallback to most recent file
        files = [f for f in os.listdir(DROPZONE_DIR) if os.path.isfile(os.path.join(DROPZONE_DIR, f))]
        if not files:
            return {'status': 'error', 'message': '❌ Dropzone is empty.'}
        files.sort(key=lambda f: os.path.getmtime(os.path.join(DROPZONE_DIR, f)), reverse=True)
        path = os.path.join(DROPZONE_DIR, files[0])

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'status': 'success', 'filename': os.path.basename(path), 'data': content}
    except Exception as e:
        return {'status': 'error', 'message': f'❌ Failed to read file: {str(e)}'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params', type=str, required=False)
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
