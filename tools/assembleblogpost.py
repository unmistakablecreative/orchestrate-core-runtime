import os
import json


def load_manifest(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f'Manifest file not found: {path}')
    with open(path, 'r') as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError('Manifest must be a list of entries.')
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON in manifest: {e}')


def inject_image(md_text, image_url):
    if not md_text or not image_url:
        raise ValueError('Both markdown text and image URL are required.')
    lines = md_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('## '):
            lines.insert(i + 1, f'![Image]({image_url})')
            break
    else:
        lines.insert(0, f'![Image]({image_url})')
    return '\n'.join(lines)



def assemble_post(manifest):
    if not manifest:
        raise ValueError('Manifest is empty.')
    sections = []
    for entry in manifest:
        path = entry.get('file')
        img = entry.get('image_url')
        if not path or not img:
            raise ValueError("Each manifest entry must have 'file' and 'image_url'.")

        # Resolve relative paths to full container path
        if not os.path.isabs(path):
            path = os.path.join('/orchestrate_user/orchestrate_exports/markdown', path)

        if not os.path.exists(path):
            raise FileNotFoundError(f'Markdown file not found: {path}')

        with open(path, 'r') as f:
            content = f.read()

        injected = inject_image(content, img)
        sections.append(injected)
    return '\n\n'.join(sections)



def write_final(output_path, content):
    if not output_path or not content:
        raise ValueError('Output path and content are required.')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(content)
    return {
        'status': 'success',
        'message': f'Final blog post written to {output_path}',
        'path': output_path
    }


def main(params):
    import sys
    slug = params.get("slug")
    if not slug:
        return {'status': 'error', 'message': '❌ Missing slug.'}

    md_dir = '/orchestrate_user/orchestrate_exports/markdown'
    manifest_path = os.path.join(os.getcwd(), 'data', f'manifest_{slug}.json')
    output_path = os.path.join(md_dir, f'compiled_{slug}.md')

    print(f'🔍 Checking for manifest at: {manifest_path}', file=sys.stderr)

    if not os.path.exists(manifest_path):
        return {'status': 'error', 'message': f'Manifest not found: {manifest_path}'}

    try:
        with open(manifest_path, 'r') as f:
            manifest_obj = json.load(f)
        if isinstance(manifest_obj, dict) and 'entries' in manifest_obj:
            manifest = list(manifest_obj['entries'].values())
        elif isinstance(manifest_obj, list):
            manifest = manifest_obj
        else:
            return {'status': 'error', 'message': 'Manifest format invalid.'}
    except Exception as e:
        return {'status': 'error', 'message': f'Manifest load failed: {str(e)}'}

    try:
        content = assemble_post(manifest)
        return write_final(output_path, content)
    except Exception as e:
        return {'status': 'error', 'message': f'Assembly failed: {str(e)}'}




def cli():
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}

    if args.action == 'main':
        result = main(params)
    else:
        result = {'status': 'error', 'message': f'Unknown action {args.action}'}

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    cli()
