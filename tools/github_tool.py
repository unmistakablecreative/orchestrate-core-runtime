import os
import subprocess
import datetime
import zipfile


def git_add_images():
    try:
        subprocess.run(['git', 'add', 'orchestrate-blog-assets/*.png'],
            shell=True, check=True)
        return {'status': 'success', 'message':
            'All PNGs in orchestrate-blog-assets staged.'}
    except subprocess.CalledProcessError as e:
        return {'status': 'error', 'message': str(e)}


def git_commit(params):
    message = params.get('message')
    if not message:
        return {'status': 'error', 'message': 'Commit message is required.'}
    try:
        subprocess.run(['git', 'commit', '-m', message], check=True)
        return {'status': 'success', 'message': 'Commit successful.'}
    except subprocess.CalledProcessError as e:
        return {'status': 'error', 'message': str(e)}


def git_push(params):
    branch = params.get('branch', 'main')
    try:
        subprocess.run(['git', 'push', 'origin', branch], check=True)
        return {'status': 'success', 'message': f'Pushed to {branch}'}
    except subprocess.CalledProcessError as e:
        return {'status': 'error', 'message': str(e)}


def git_pull(params):
    branch = params.get('branch', 'main')
    try:
        subprocess.run(['git', 'pull', 'origin', branch], check=True)
        return {'status': 'success', 'message': f'Pulled latest from {branch}'}
    except subprocess.CalledProcessError as e:
        return {'status': 'error', 'message': str(e)}


def git_status():
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], check=
            True, capture_output=True, text=True)
        return {'status': 'success', 'output': result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {'status': 'error', 'message': str(e)}


def backup_repo():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'repo_backup_{timestamp}.zip'
    try:
        with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as backup:
            for root, _, files in os.walk('.'):
                for file in files:
                    if file == backup_name:
                        continue
                    path = os.path.join(root, file)
                    backup.write(path)
        return {'status': 'success', 'backup_file': backup_name}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}
    if args.action == 'git_add_images':
        result = git_add_images()
    elif args.action == 'git_commit':
        result = git_commit(params)
    elif args.action == 'git_push':
        result = git_push(params)
    elif args.action == 'git_pull':
        result = git_pull(params)
    elif args.action == 'git_status':
        result = git_status()
    elif args.action == 'backup_repo':
        result = backup_repo()
    else:
        result = {'status': 'error', 'message': f'Unknown action {args.action}'
            }
    print(json.dumps(result, indent=2))
