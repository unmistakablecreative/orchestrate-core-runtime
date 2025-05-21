import json
import argparse
import os

class FileFinder:
    def search_files(self, params):
        keyword = params.get('keyword', '').lower()
        matched_files = []
        data_dir = '/app/data'
        for filename in os.listdir(data_dir):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if keyword in content:
                        matched_files.append(filename)
            except:
                continue
        return {'status': 'success', 'matched_files': matched_files}

    def execute(self, action, params):
        if action == 'search_files':
            return self.search_files(params)
        return {'error': 'Unsupported action'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params', required=True)
    args = parser.parse_args()

    params = json.loads(args.params)
    tool = FileFinder()
    result = tool.execute(args.action, params)
    print(json.dumps(result, indent=4))