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
            raise ValueError(
                "Each manifest entry must have 'file' and 'image_url'.")
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
    return {'status': 'success', 'message':
        f'Final blog post written to {output_path}', 'path': output_path}


def main():
    manifest = load_manifest('manifest.json')
    content = assemble_post(manifest)
    result = write_final('compiled_posts/final.md', content)
    return result


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}
    if args.action == 'main':
        result = main()
    else:
        result = {'status': 'error', 'message': f'Unknown action {args.action}'
            }
    print(json.dumps(result, indent=2))
