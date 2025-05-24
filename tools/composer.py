import json
import os
import argparse


def get_output_url(params):
    filename = params.get('filename', 'output_url.json')
    path = os.path.join('compositions', filename)
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        key = params.get('key')
        if key:
            for part in key.split('.'):
                data = data.get(part)
                if data is None:
                    return {'status': 'error', 'message':
                        f"❌ Key '{key}' not found in file."}
            return {'status': 'success', 'url': data}
        url = data.get('url')
        if not url:
            return {'status': 'error', 'message': '❌ URL not found in file.'}
        return {'status': 'success', 'url': url}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def store_output_url(params):
    import re
    url = params.get('url')
    key = params.get('key')
    filename = params.get('filename', 'output_urls.json')
    if not url or not key:
        return {'status': 'error', 'message':
            "❌ Missing 'url' or 'key' parameter."}
    if isinstance(url, str) and url.startswith('$0.'
        ) and '_prev_results' in params:
        try:
            parts = url.replace('$0.', '').split('.')
            result = params['_prev_results'][0]
            for part in parts:
                if part.endswith(']'):
                    match = re.match('(\\w+)\\[(\\d+)\\]', part)
                    if match:
                        key, idx = match.group(1), int(match.group(2))
                        result = result[key][idx]
                else:
                    result = result[part]
            url = result
        except Exception as e:
            return {'status': 'error', 'message':
                f'❌ Failed to resolve dynamic URL: {str(e)}'}
    path = os.path.join('compositions', filename)
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        if 'output_urls' not in data:
            data['output_urls'] = {}
        data['output_urls'][key] = url
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message':
            f"✅ Stored URL under key '{key}' in {filename}."}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def update_composition_placeholder(filename: str, placeholder: str, value: str
    ) ->dict:
    try:
        with open(filename, 'r') as f:
            content = f.read()
        if placeholder not in content:
            return {'status': 'error', 'message':
                f"❌ Placeholder '{placeholder}' not found in {filename}."}
        content = content.replace(placeholder, value)
        with open(filename, 'w') as f:
            f.write(content)
        return {'status': 'success', 'message':
            f"✅ Updated '{placeholder}' to '{value}' in {filename}."}
    except Exception as e:
        return {'status': 'error', 'message':
            f'❌ Failed to update {filename}: {str(e)}'}


def add_composition_delay(params):
    import time
    seconds = params.get('seconds', 1)
    time.sleep(seconds)
    return {'status': 'success', 'message': f'⏱️ Delayed {seconds} seconds.'}


def create_composer_action_template(params):
    template_name = params.get('template_name')
    action_data = params.get('action_data')
    if not template_name or not action_data:
        return {'status': 'error', 'message':
            "Missing 'template_name' or 'action_data'."}
    path = f'compositions/{template_name}'
    try:
        import os
        import json
        with open(path, 'w') as f:
            json.dump(action_data, f, indent=2)
        return {'status': 'success', 'message':
            f"Template '{template_name}' created.", 'path': path}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def insert_composer_action_from_template(params):
    filename = params.get('filename')
    index = params.get('index')
    template_name = params.get('template_name')
    if not filename or index is None or not template_name:
        return {'status': 'error', 'message':
            "Missing 'filename', 'index', or 'template_name'."}
    try:
        template_path = f'compositions/{template_name}'
        with open(template_path, 'r') as f:
            import json
            action_data = json.load(f)
        file_path = f'compositions/{filename}'
        with open(file_path, 'r') as f:
            data = json.load(f)
        actions = data.get('actions', [])
        if not isinstance(actions, list):
            return {'status': 'error', 'message':
                "Invalid dispatcher structure: 'actions' must be a list."}
        if index < 0 or index > len(actions):
            return {'status': 'error', 'message':
                f'Index {index} out of bounds.'}
        actions.insert(index, action_data)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message':
            f"Inserted action from template '{template_name}' at index {index}."
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def validate_composer_batch(params):
    filename = params.get('filename')
    if not filename:
        return {'status': 'error', 'message': "Missing 'filename' parameter."}
    path = f'compositions/{filename}'
    try:
        with open(path, 'r') as f:
            import json
            data = json.load(f)
        errors = []
        if data.get('status') != 'ready':
            errors.append("'status' must be 'ready'")
        actions = data.get('actions')
        if not isinstance(actions, list):
            errors.append("'actions' must be a list")
        else:
            for i, action in enumerate(actions):
                if not all(k in action for k in ('tool_name', 'action',
                    'params')):
                    errors.append(
                        f'Action at index {i} missing required fields')
        if errors:
            return {'status': 'error', 'message': 'Validation failed',
                'errors': errors}
        return {'status': 'success', 'message': 'Dispatcher batch is valid.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def list_composer_actions(params):
    filename = params.get('filename')
    if not filename:
        return {'status': 'error', 'message': "Missing 'filename' parameter."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
            actions = data.get('actions', [])
            indexed_actions = [{'index': i, 'tool': a.get('tool_name'),
                'action': a.get('action')} for i, a in enumerate(actions)]
            return {'status': 'success', 'data': indexed_actions}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def read_composer_action(params):
    filename = params.get('filename')
    index = params.get('index')
    if filename is None or index is None:
        return {'status': 'error', 'message':
            "Missing 'filename' or 'index' parameter."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
            actions = data.get('actions', [])
            if index < 0 or index >= len(actions):
                return {'status': 'error', 'message':
                    f'Index {index} out of range.'}
            return {'status': 'success', 'data': actions[index]}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def remove_composer_action(params):
    filename = params.get('filename')
    index = params.get('index')
    if not filename or index is None:
        return {'status': 'error', 'message':
            "Missing 'filename' or 'index' parameter."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
        actions = data.get('actions', [])
        if index < 0 or index >= len(actions):
            return {'status': 'error', 'message':
                f'Index {index} out of range.'}
        removed_action = actions.pop(index)
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message':
            f'Removed action at index {index}.', 'data': removed_action}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def update_composer_action(params):
    filename = params.get('filename')
    index = params.get('index')
    new_action = params.get('new_action_data')
    if not filename or index is None or not new_action:
        return {'status': 'error', 'message':
            "Missing 'filename', 'index', or 'new_action_data'."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
        actions = data.get('actions', [])
        if index < 0 or index >= len(actions):
            return {'status': 'error', 'message':
                f'Index {index} out of range.'}
        old_action = actions[index]
        actions[index] = new_action
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message':
            f'Updated action at index {index}.', 'data': {'old': old_action,
            'new': new_action}}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def batch_update_composer_actions(params):
    filename = params.get('filename')
    updates = params.get('updates')
    if not filename or not updates:
        return {'status': 'error', 'message':
            "Missing 'filename' or 'updates'."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
        actions = data.get('actions', [])
        count = 0
        for index_str, patch in updates.items():
            index = int(index_str)
            if 0 <= index < len(actions):
                for field, patch_data in patch.items():
                    if field in actions[index] and isinstance(actions[index
                        ][field], dict):
                        actions[index][field].update(patch_data)
                    else:
                        actions[index][field] = patch_data
                count += 1
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message':
            f"✅ Safely patched {count} actions in '{filename}'."}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def insert_composer_action(params):
    filename = params.get('filename')
    index = params.get('index')
    action_data = params.get('action_data')
    if not filename or index is None or not action_data:
        return {'status': 'error', 'message':
            "Missing 'filename', 'index', or 'action_data'."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
        actions = data.get('actions', [])
        if not isinstance(actions, list):
            return {'status': 'error', 'message': "'actions' is not a list."}
        if index < 0 or index > len(actions):
            return {'status': 'error', 'message':
                f'Index {index} out of range.'}
        actions.insert(index, action_data)
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message':
            f'Inserted action at index {index}.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def add_composer_action(params):
    filename = params.get('filename')
    action_data = params.get('action_data')
    if not filename or not action_data:
        return {'status': 'error', 'message':
            "Missing 'filename' or 'action_data'."}
    full_path = f'compositions/{filename}'
    try:
        with open(full_path, 'r') as f:
            import json
            data = json.load(f)
        actions = data.get('actions', [])
        if not isinstance(actions, list):
            return {'status': 'error', 'message': "'actions' is not a list."}
        actions.append(action_data)
        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
        return {'status': 'success', 'message': 'Action added.', 'index': 
            len(actions) - 1}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def create_composer_batch_from_template(params):
    template_name = params.get('template_name')
    new_filename = params.get('new_filename')
    if not template_name or not new_filename:
        return {'status': 'error', 'message':
            "Missing 'template_name' or 'new_filename'."}
    try:
        template_path = f'compositions/{template_name}'
        new_path = f'compositions/{new_filename}'
        with open(template_path, 'r') as template_file:
            import json
            content = json.load(template_file)
        with open(new_path, 'w') as new_file:
            json.dump(content, new_file, indent=2)
        return {'status': 'success', 'message':
            f'Created dispatcher from template at {new_path}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def create_composer_batch(params):
    filename = params.get('filename')
    if not filename:
        return {'status': 'error', 'message': "Missing 'filename' parameter."}
    full_path = os.path.join(os.getcwd(), 'compositions', filename)
    default_payload = {'status': 'ready', 'actions': []}
    try:
        with open(full_path, 'w') as f:
            import json
            json.dump(default_payload, f, indent=2)
        return {'status': 'success', 'message':
            f'Created dispatcher batch at {full_path}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


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
    if args.action == 'create_composer_batch':
        result = create_composer_batch(params)
    elif args.action == 'create_composer_batch_from_template':
        result = create_composer_batch_from_template(params)
    elif args.action == 'add_composer_action':
        result = add_composer_action(params)
    elif args.action == 'insert_composer_action':
        result = insert_composer_action(params)
    elif args.action == 'update_composer_action':
        result = update_composer_action(params)
    elif args.action == 'batch_update_composer_actions':
        result = batch_update_composer_actions(params)
    elif args.action == 'remove_composer_action':
        result = remove_composer_action(params)
    elif args.action == 'read_composer_action':
        result = read_composer_action(params)
    elif args.action == 'list_composer_actions':
        result = list_composer_actions(params)
    elif args.action == 'validate_composer_batch':
        result = validate_composer_batch(params)
    elif args.action == 'insert_composer_action_from_template':
        result = insert_composer_action_from_template(params)
    elif args.action == 'create_composer_action_template':
        result = create_composer_action_template(params)
    elif args.action == 'add_composition_delay':
        result = add_composition_delay(params)
    elif args.action == 'update_composition_placeholder':
        result = update_composition_placeholder(**params)
    elif args.action == 'get_output_url':
        result = get_output_url(params)
    elif args.action == 'store_output_url':
        result = store_output_url(params)
    else:
        result = {'status': 'error', 'message':
            f'❌ Unknown action: {args.action}'}
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
