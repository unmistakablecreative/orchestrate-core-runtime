import json
import os
import argparse


def read_file(params):
    filename = params.get('filename')
    if not filename:
        return {'status': 'error', 'message': "❌ 'filename' param is required."
            }
    filename = os.path.basename(filename)
    search_dirs = ['/app/data', '/app/code_blueprints', '/app/compositions']
    for directory in search_dirs:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                return {'status': 'success', 'data': content}
            except Exception as e:
                return {'status': 'error', 'message':
                    f'❌ Failed to read file: {str(e)}'}
    return {'status': 'error', 'message':
        '❌ File not found in known directories.'}


def main():
    parser = argparse.ArgumentParser(description='Orchestrate Tool Template')
    parser.add_argument('action', help='Action to perform')
    parser.add_argument('--params', type=str, required=False, help=
        'JSON-encoded parameters for the action')
    args = parser.parse_args()
    try:
        params = json.loads(args.params) if args.params else {}
    except json.JSONDecodeError:
        print(json.dumps({'status': 'error', 'message':
            '❌ Invalid JSON format.'}, indent=4))
        return
    if args.action == 'read_file':
        result = read_file(params)
    else:
        result = {'status': 'error', 'message':
            f'❌ Unknown action: {args.action}'}
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
