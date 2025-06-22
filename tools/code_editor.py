import json
import os
import argparse
import ast
import astor


def is_protected_file(filename):
    protected_names = {'system_settings.ndjson', 'command_center.json',
        'compositions_index.json', 'files.json', 'srini_notes.json',
        'working_memory.json', 'credentials.json', 'tokens.json'}
    return any(protected in filename for protected in protected_names)


def create_code_blueprint(params):
    filename = params.get('filename')
    imports = params.get('imports', [])
    if not filename.endswith('.json'):
        filename = filename.replace('.py', '').replace('.sh', '') + '.json'
    if is_protected_file(filename):
        return {'status': 'error', 'message':
            '❌ This file is protected and cannot be modified.'}
    if 'filename' in params and '.sh' in params['filename']:
        output_script = filename.replace('.json', '.sh')
    else:
        output_script = filename.replace('.json', '.py')
    internal_path = os.path.abspath(os.path.join('generated_tools',
        output_script))
    blueprint = {'filename': internal_path, 'imports': imports, 'functions':
        {}, 'router': {}}
    filepath = os.path.join('code_blueprints', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(blueprint, f, indent=4)
    return {'status': 'success', 'message':
        f'✅ Created code blueprint at {filepath}'}


def add_function_to_blueprint(params):
    filename = params.get('filename')
    function_name = params.get('function_name')
    function_params = params.get('params', [])
    body = params.get('body', '')
    if is_protected_file(filename):
        return {'status': 'error', 'message':
            '❌ This file is protected and cannot be modified.'}
    path = os.path.join('code_blueprints', filename)
    with open(path, 'r') as f:
        data = json.load(f)
    data['functions'][function_name] = {'params': function_params, 'body': body
        }
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    return {'status': 'success', 'message':
        f"✅ Function '{function_name}' added to {filename}."}


def update_function_in_blueprint_file(params):
    filename = params.get('filename')
    function_name = params.get('function_name')
    function_params = params.get('params', [])
    body = params.get('body', '')
    if is_protected_file(filename):
        return {'status': 'error', 'message':
            '❌ This file is protected and cannot be modified.'}
    path = os.path.join('code_blueprints', filename)
    with open(path, 'r') as f:
        data = json.load(f)
    if function_name not in data['functions']:
        return {'status': 'error', 'message':
            f"⚠️ Function '{function_name}' not found."}
    data['functions'][function_name] = {'params': function_params, 'body': body
        }
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    return {'status': 'success', 'message':
        f"✅ Function '{function_name}' updated in {filename}."}


def remove_function_from_blueprint(params):
    filename = params.get('filename')
    function_name = params.get('function_name')
    if is_protected_file(filename):
        return {'status': 'error', 'message':
            '❌ This file is protected and cannot be modified.'}
    path = os.path.join('code_blueprints', filename)
    with open(path, 'r') as f:
        data = json.load(f)
    if function_name in data['functions']:
        del data['functions'][function_name]
    else:
        return {'status': 'error', 'message':
            f"⚠️ Function '{function_name}' not found."}
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    return {'status': 'success', 'message':
        f"🗑️ Function '{function_name}' removed from {filename}."}


def read_blueprint_file(params):
    path = params['json_path']
    with open(path, 'r') as f:
        data = json.load(f)
    return {'status': 'success', 'code_file': data}


def read_function_from_blueprint(params):
    path = params['json_path']
    fn = params['function_name']
    with open(path, 'r') as f:
        data = json.load(f)
    if fn not in data['functions']:
        return {'status': 'error', 'message': f"❌ Function '{fn}' not found."}
    return {'status': 'success', 'function': {'name': fn, 'params': data[
        'functions'][fn]['params'], 'body': data['functions'][fn]['body']}}


def list_functions_in_blueprint(params):
    path = params['json_path']
    with open(path, 'r') as f:
        data = json.load(f)
    return {'status': 'success', 'functions': list(data.get('functions', {}
        ).keys())}


def configure_router_in_blueprint(params):
    filename = params.get('filename')
    router = params.get('router', {})
    if is_protected_file(filename):
        return {'status': 'error', 'message':
            '❌ This file is protected and cannot be modified.'}
    path = os.path.join('code_blueprints', filename)
    with open(path, 'r') as f:
        data = json.load(f)
    data['router'] = router
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    return {'status': 'success', 'message':
        f'✅ Router configured in {filename}.'}


def compile_blueprint_to_script_file(params):
    path = params['json_path']
    with open(path, 'r') as f:
        data = json.load(f)
    filename = data.get('filename', '')
    is_shell = filename.endswith('.sh')
    lines = []
    if not is_shell:
        lines.extend(data.get('imports', []))
        lines.append('\n# --- Core Functions ---')
        for fn_name, fn_data in data['functions'].items():
            params_str = ', '.join(fn_data['params'])
            lines.append(f'\ndef {fn_name}({params_str}):')
            for line in fn_data['body'].splitlines():
                lines.append(f'    {line}')
        lines.append('\n# --- Action Router ---')
        lines.append('def main():')
        lines.append('    import argparse, json')
        lines.append('    parser = argparse.ArgumentParser()')
        lines.append('    parser.add_argument("action")')
        lines.append('    parser.add_argument("--params")')
        lines.append('    args = parser.parse_args()')
        lines.append(
            '    params = json.loads(args.params) if args.params else {}')
        router = data.get('router') or {fn: fn for fn in data['functions']}
        for i, (action, fn) in enumerate(router.items()):
            keyword = 'if' if i == 0 else 'elif'
            lines.append(f'    {keyword} args.action == "{action}":')
            lines.append(f'        result = {fn}(**params)')
        lines.append('    else:')
        lines.append(
            '        result = {"status": "error", "message": f"Unknown action {args.action}"}'
            )
        lines.append('    print(json.dumps(result, indent=2))')
        lines.append('\nif __name__ == "__main__":')
        lines.append('    main()')
    else:
        for fn_data in data['functions'].values():
            lines.append(fn_data['body'])
    output_path = os.path.abspath(os.path.join('generated_tools', os.path.
        basename(filename)))
    os.makedirs('generated_tools', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    return {'status': 'success', 'message': f'✅ Compiled {output_path}'}



def read_code_file(params):
    path = params.get('path')
    if not path:
        return {'status': 'error', 'message': '❌ Path parameter is required.'}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'status': 'success', 'code': content}
    except Exception as e:
        return {'status': 'error', 'message': f'❌ Failed to read file: {str(e)}'}



def add_function_to_code_file(params):
    filename = params['filename']
    function_name = params['function_name']
    param_list = params.get('params', [])
    body = params['body']
    function_header = f"\ndef {function_name}({', '.join(param_list)}):\n"
    function_body = '\n'.join([f'    {line}' for line in body.splitlines()])
    full_function = function_header + function_body + '\n'
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        insert_index = None
        for i, line in enumerate(lines):
            if '# --- Action Router ---' in line or 'if __name__' in line:
                insert_index = i
                break
        if insert_index is None:
            insert_index = len(lines)
        lines.insert(insert_index, full_function)
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return {'status': 'success', 'message':
            f"✅ Function '{function_name}' added to {filename}"}
    except Exception as e:
        return {'status': 'error', 'message':
            f'❌ Failed to add function: {str(e)}'}


def patch_code_function_in_file(params):
    import ast, astor, os

    filename = params.get('filename')
    function_name = params.get('function_name')
    new_body = params.get('body')
    param_list = params.get('params', ['params'])

    if not filename or not function_name or not new_body:
        return {'status': 'error', 'message': '❌ Missing required fields.'}

    # Resolve relative to /tools
    filepath = filename if os.path.isfile(filename) else os.path.join('tools', filename)
    if not os.path.exists(filepath):
        return {'status': 'error', 'message': f'❌ File not found: {filepath}'}

    # --- Normalize: Strip outer def and dedent ---
    lines = new_body.strip().splitlines()
    if lines and lines[0].lstrip().startswith("def "):
        base_indent = (
            len(lines[1]) - len(lines[1].lstrip())
            if len(lines) > 1 else 4
        )
        lines = lines[1:]
        new_body = '\n'.join(
            line[base_indent:] if line.startswith(' ' * base_indent) else line
            for line in lines
        )

    # --- Parse original source ---
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return {'status': 'error', 'message': f'❌ Failed to parse file: {str(e)}'}

    # --- Function rewrite ---
    class FunctionPatcher(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == function_name:
                try:
                    patched_body = ast.parse(new_body).body
                except Exception as e:
                    raise ValueError(f'❌ Failed to parse new body: {str(e)}')
                return ast.FunctionDef(
                    name=function_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg=p) for p in param_list],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[]
                    ),
                    body=patched_body,
                    decorator_list=[]
                )
            return node

    try:
        patcher = FunctionPatcher()
        modified_tree = patcher.visit(tree)
        ast.fix_missing_locations(modified_tree)
        updated_code = astor.to_source(modified_tree)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_code)

        return {'status': 'success', 'message': f"✅ Patched '{function_name}' in {filename}"}
    except Exception as e:
        return {'status': 'error', 'message': f'❌ Patch failed: {str(e)}'}


def rename_function_in_file(params):
    filename = params['filename']
    old_name = params['old_name']
    new_name = params['new_name']
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    if f'def {old_name}(' not in content:
        return {'status': 'error', 'message':
            f"❌ Function '{old_name}' not found."}
    updated = content.replace(f'def {old_name}(', f'def {new_name}(')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(updated)
    return {'status': 'success', 'message':
        f"✅ Renamed '{old_name}' to '{new_name}' in {filename}"}


def replace_in_code_file(params):
    filename = params['filename']
    old_text = params['old_text']
    new_text = params['new_text']
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_text not in content:
            return {'status': 'error', 'message':
                '❌ Old text not found in file.'}
        updated_content = content.replace(old_text, new_text)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return {'status': 'success', 'message': '✅ Text replaced in file.'}
    except Exception as e:
        return {'status': 'error', 'message':
            f'❌ Failed to replace text: {str(e)}'}


def replace_tail_from_line(params):
    filename = params['filename']
    start_pattern = params['start_pattern']
    replacement = params['replacement']
    try:
        if start_pattern.strip() != 'if __name__ == "__main__":':
            return {'status': 'error', 'message':
                'replace_tail_from_line may only be used to replace __main__ blocks.'
                }
        with open(filename, 'r') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if start_pattern in line:
                new_lines = lines[:i] + [replacement + '\n']
                break
        else:
            return {'status': 'error', 'message':
                f"Pattern '{start_pattern}' not found."}
        with open(filename, 'w') as f:
            f.writelines(new_lines)
        return {'status': 'success', 'message': 'Tail replaced from pattern.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def add_endpoint_to_fastapi_file(params):
    filename = params['filename']
    method = params.get('method', 'get').lower()
    route = params['route']
    function_name = params['function_name']
    body_code = params['body']
    with open(filename, 'r') as f:
        lines = f.readlines()
    if any(f'def {function_name}(' in line for line in lines):
        return {'status': 'error', 'message':
            f"❌ Function '{function_name}' already exists."}
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('@app.'):
            insert_idx = i
    insert_idx += 2
    decorator = f'@app.{method}("{route}")\n'
    def_line = f'async def {function_name}():\n'
    body_lines = [f'    {line}\n' for line in body_code.strip().splitlines()]
    new_block = ['\n', decorator, def_line] + body_lines + ['\n']
    updated_lines = lines[:insert_idx] + new_block + lines[insert_idx:]
    with open(filename, 'w') as f:
        f.writelines(updated_lines)
    return {'status': 'success', 'message':
        f"✅ Endpoint '{route}' inserted via {method.upper()} method."}


def add_import_statement_to_file(params):
    filename = params['filename']
    import_line = params['import_statement']
    with open(filename, 'r') as f:
        lines = f.readlines()
    if any(import_line.strip() in line.strip() for line in lines):
        return {'status': 'success', 'message': '⚠️ Import already exists.'}
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import') or line.strip().startswith('from'
            ):
            insert_idx = i
    insert_idx += 1
    updated_lines = lines[:insert_idx] + [import_line + '\n'] + lines[
        insert_idx:]
    with open(filename, 'w') as f:
        f.writelines(updated_lines)
    return {'status': 'success', 'message': f'✅ Import added: {import_line}'}


def append_code_to_file(filename: str, code: str) ->dict:
    try:
        with open(filename, 'a') as f:
            f.write('\n' + code + '\n')
        return {'status': 'success', 'message': 'Code appended to file.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def remove_function_from_code_file(params):
    filename = params['filename']
    function_name = params['function_name']
    with open(filename, 'r') as f:
        lines = f.readlines()
    new_lines = []
    in_function = False
    indent_level = None
    for line in lines:
        if line.strip().startswith(f'def {function_name}('):
            in_function = True
            indent_level = len(line) - len(line.lstrip())
            continue
        if in_function:
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip())
            if (stripped and current_indent <= indent_level and not
                stripped.startswith('#')):
                in_function = False
        if not in_function:
            new_lines.append(line)
    with open(filename, 'w') as f:
        f.writelines(new_lines)
    return {'status': 'success', 'message':
        f"🗑️ Function '{function_name}' removed from {filename} (without nuking the file)."
        }


def add_to_action_map_in_file(params):
    filename = params['filename']
    action_name = params['action_name']
    function_name = params['function_name']
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
            tree = ast.parse(source)


        class ActionMapUpdater(ast.NodeTransformer):

            def visit_Assign(self, node):
                if isinstance(node.targets[0], ast.Name) and node.targets[0
                    ].id == 'action_map':
                    if not isinstance(node.value, ast.Dict):
                        raise ValueError("❌ 'action_map' is not a dictionary.")
                    keys = [k.s for k in node.value.keys if isinstance(k,
                        ast.Str)]
                    if action_name in keys:
                        raise ValueError(
                            f"⚠️ Action '{action_name}' already exists.")
                    node.value.keys.append(ast.Str(s=action_name))
                    node.value.values.append(ast.Name(id=function_name, ctx
                        =ast.Load()))
                return node
        updater = ActionMapUpdater()
        updated_tree = updater.visit(tree)
        ast.fix_missing_locations(updated_tree)
        new_source = astor.to_source(updated_tree)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_source)
        return {'status': 'success', 'message':
            f"✅ Inserted: '{action_name}': {function_name}"}
    except ValueError as ve:
        return {'status': 'error', 'message': str(ve)}
    except Exception as e:
        return {'status': 'error', 'message':
            f'❌ Failed to update action_map: {str(e)}'}





def main():
    import argparse
    parser = argparse.ArgumentParser(description='Orchestrate Code Editor Tool')
    parser.add_argument('action', help='Action to perform')
    parser.add_argument('--params', type=str, required=False, help='JSON-encoded parameters for the action')
    args = parser.parse_args()

    try:
        params = json.loads(args.params) if args.params else {}
    except json.JSONDecodeError:
        print(json.dumps({'status': 'error', 'message': '❌ Invalid JSON format.'}, indent=4))
        return

    action_map = {
        'create_code_blueprint': create_code_blueprint,
        'add_function_to_blueprint': add_function_to_blueprint,
        'update_function_in_blueprint_file': update_function_in_blueprint_file,
        'remove_function_from_blueprint': remove_function_from_blueprint,
        'read_blueprint_file': read_blueprint_file,
        'read_function_from_blueprint': read_function_from_blueprint,
        'list_functions_in_blueprint': list_functions_in_blueprint,
        'configure_router_in_blueprint': configure_router_in_blueprint,
        'compile_blueprint_to_script_file': compile_blueprint_to_script_file,
        'add_function_to_code_file': add_function_to_code_file,
        'patch_code_function_in_file': patch_code_function_in_file,
        'remove_function_from_code_file': remove_function_from_code_file,
        'rename_function_in_file': rename_function_in_file,
        'replace_in_code_file': replace_in_code_file,
        'replace_tail_from_line': replace_tail_from_line,
        'add_endpoint_to_fastapi_file': add_endpoint_to_fastapi_file,
        'add_import_statement_to_file': add_import_statement_to_file,
        'add_to_action_map_in_file': add_to_action_map_in_file,
        'append_code_to_file': append_code_to_file,
        'read_code_file': read_code_file  # ✅ Newly added action
    }

    if args.action in action_map:
        result = action_map[args.action](params)
    else:
        result = {'status': 'error', 'message': f'❌ Unknown action: {args.action}'}

    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
