import json
import argparse
import os

DROPZONE_DIR = '/orchestrate_user/dropzone'

class FileFinder:
    def search_files(self, params):
        keyword = params.get('keyword', '').lower()
        matched_files = []

        for filename in os.listdir(DROPZONE_DIR):
            path = os.path.join(DROPZONE_DIR, filename)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if keyword in content:
                        matched_files.append(filename)
            except Exception:
                continue  # Skip unreadable files

        return {'status': 'success', 'matched_files': matched_files}

    def execute(self, action, params):
        if action == 'search_files':
            return self.search_files(params)
        return {'status': 'error', 'message': '❌ Unsupported action'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params', required=True)
    args = parser.parse_args()

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError:
        print(json.dumps({'status': 'error', 'message': '❌ Invalid JSON.'}, indent=4))
        exit()

    tool = FileFinder()
    result = tool.execute(args.action, params)
    print(json.dumps(result, indent=4))
