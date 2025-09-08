import json
import requests


def create_doc(params):
    title = params.get('title')
    content = params.get('content')
    collectionId = params.get('collectionId')
    parentDocumentId = params.get('parentDocumentId', None)
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    if not collectionId:
        collectionId = '6a798b00-6302-42eb-9bbf-b38bef766cd9'
    payload = {'title': title, 'text': content, 'collectionId':
        collectionId, 'publish': True}
    if parentDocumentId:
        payload['parentDocumentId'] = parentDocumentId
    res = requests.post(f'{api_base}/documents.create', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def get_doc(doc_id):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    res = requests.post(f'{api_base}/documents.info', json={'id': doc_id},
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def update_doc(params):
    doc_id = params.get('doc_id')
    title = params.get('title')
    text = params.get('text')
    append = params.get('append')
    publish = params.get('publish')
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    if append:
        payload_append = True
        text = '\n\n' + text.strip()
    else:
        payload_append = False
    payload = {'id': doc_id, 'title': title, 'text': text, 'publish': publish}
    if payload_append:
        payload['append'] = True
    res = requests.post(f'{api_base}/documents.update', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def export_doc(params):
    import requests, os, json
    from system_settings import load_credential
    doc_id = params.get('doc_id')
    filename = params.get('filename')
    if not filename:
        doc = get_doc(doc_id)
        title = doc.get('title', f'doc_{doc_id}')
        filename = f"{title.replace(' ', '_').lower()}.md"
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'id': doc_id, 'exportType': 'markdown'}
    res = requests.post(f'{api_base}/documents.export', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    try:
        raw = json.loads(res.text)
        markdown = raw.get('data', '')
    except json.JSONDecodeError:
        markdown = res.text
    output_dir = os.path.join('/orchestrate_user/orchestrate_exports',
        'markdown')
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)
    return {'status': 'success', 'message': f'✅ Exported to {filepath}'}


def delete_doc(doc_id):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    res = requests.post(f'{api_base}/documents.delete', json={'id': doc_id},
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def list_docs(limit, offset, sort, direction, collectionId):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'limit': limit, 'offset': offset, 'sort': sort, 'direction':
        direction}
    if collectionId:
        payload['collectionId'] = collectionId
    res = requests.post(f'{api_base}/documents.list', headers=headers, json
        =payload, verify=False)
    res.raise_for_status()
    return res.json()


def search_docs(query, limit, offset):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'query': query, 'limit': limit, 'offset': offset}
    res = requests.post(f'{api_base}/documents.search', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def get_url(doc_id):
    return {'status': 'success', 'url': f'https://getoutline.com/doc/{doc_id}'}


def patch_section(doc_id, section, new_text):
    from time import sleep
    doc = get_doc(doc_id)
    if not doc or not doc.get('text'):
        return {'status': 'error', 'message': 'Original document fetch failed.'
            }
    text = doc['text']
    if section not in text:
        return {'status': 'error', 'message': 'Section not found in document.'}
    updated = text.replace(section, new_text)
    sleep(1)
    return update_doc(doc_id=doc_id, title=doc['title'], text=updated,
        append=False, publish=True)


def append_section(doc_id, new_text):
    doc = get_doc(doc_id)
    if not doc or not doc.get('text'):
        return {'status': 'error', 'message': 'Original document fetch failed.'
            }
    updated = doc['text'].rstrip() + '\n\n' + new_text.strip()
    return update_doc(doc_id=doc_id, title=doc['title'], text=updated,
        append=False, publish=True)


def import_doc_from_file(file_path, collectionId, parentDocumentId,
    template, publish):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}'}
    files = {'file': open(file_path, 'rb')}
    data = {'collectionId': collectionId or
        '6a798b00-6302-42eb-9bbf-b38bef766cd9', 'parentDocumentId': 
        parentDocumentId or '', 'template': str(template).lower(),
        'publish': str(publish).lower()}
    res = requests.post(f'{api_base}/documents.import', headers=headers,
        files=files, data=data, verify=False)
    res.raise_for_status()
    return res.json()


def move_doc(doc_id, collectionId, parentDocumentId):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'id': doc_id, 'collectionId': collectionId}
    if parentDocumentId:
        payload['parentDocumentId'] = parentDocumentId
    res = requests.post(f'{api_base}/documents.move', json=payload, headers
        =headers, verify=False)
    res.raise_for_status()
    return res.json()


def create_collection(name, description, permission, icon, color, sharing):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'name': name, 'description': description, 'permission':
        permission, 'icon': icon, 'color': color, 'sharing': sharing}
    res = requests.post(f'{api_base}/collections.create', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def get_collection(collection_id):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'id': collection_id}
    res = requests.post(f'{api_base}/collections.info', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def update_collection(collection_id, name, description, permission, icon,
    color, sharing):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'id': collection_id, 'name': name, 'description':
        description, 'permission': permission, 'icon': icon, 'color': color,
        'sharing': sharing}
    res = requests.post(f'{api_base}/collections.update', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()


def delete_collection(collection_id):
    from system_settings import load_credential
    api_base = 'https://app.getoutline.com/api'
    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message':
            '❌ Missing Outline API token in credentials.json'}
    headers = {'Authorization': f'Bearer {token}', 'Content-Type':
        'application/json'}
    payload = {'id': collection_id}
    res = requests.post(f'{api_base}/collections.delete', json=payload,
        headers=headers, verify=False)
    res.raise_for_status()
    return res.json()





def ask_outline_ai(query):
    import requests
    from system_settings import load_credential

    token = load_credential('outline_api_key')
    if not token:
        return {'status': 'error', 'message': '❌ Missing Outline API token in credentials.json'}

    url = "https://app.getoutline.com/api/documents.answerQuestion"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"query": query}

    res = requests.post(url, headers=headers, json=payload, verify=False)
    if res.status_code != 200:
        return {'status': 'error', 'message': res.text}

    return {'status': 'success', 'data': res.json()}




def main():
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}

    if args.action == 'create_doc':
        result = create_doc(params)
    elif args.action == 'get_doc':
        result = get_doc(**params)
    elif args.action == 'update_doc':
        result = update_doc(params)
    elif args.action == 'delete_doc':
        result = delete_doc(**params)
    elif args.action == 'list_docs':
        result = list_docs(**params)
    elif args.action == 'search_docs':
        result = search_docs(**params)
    elif args.action == 'get_url':
        result = get_url(**params)
    elif args.action == 'patch_section':
        result = patch_section(**params)
    elif args.action == 'append_section':
        result = append_section(**params)
    elif args.action == 'export_doc':
        result = export_doc(params)
    elif args.action == 'import_doc_from_file':
        result = import_doc_from_file(**params)
    elif args.action == 'move_doc':
        result = move_doc(**params)
    elif args.action == 'create_collection':
        result = create_collection(**params)
    elif args.action == 'get_collection':
        result = get_collection(**params)
    elif args.action == 'update_collection':
        result = update_collection(**params)
    elif args.action == 'delete_collection':
        result = delete_collection(**params)
    elif args.action == 'ask_outline_ai':
        result = ask_outline_ai(**params)
    else:
        result = {'status': 'error', 'message': f'Unknown action {args.action}'}

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
