import requests
import argparse
import json
import redis

NYLAS_BASE_URL = 'https://api.us.nylas.com/v3/grants/8faa0d81-5fc7-4643-aef2-07677ba4152b'
HEADERS = {
    'Authorization': 'Bearer nyk_v0_WVuMq1MiKKUf5OWo1MM5Gdg4t22zyyx0GRHuzbf6SIJ3H2rM4S3gJYkrUHyocKcw',
    'Content-Type': 'application/json'
}

def list_message_headers(limit=10, folder="IMPORTANT", unread=None):
    SPAM_DOMAINS = {
        "mailmanhq.com",
        "nootropicsmexico.mx",
        "throttlehq.com",
        "kiwi.com",
        "newsletters.example.com",
        "marketing.yourjunk.com"
    }

    params = {"limit": limit}
    if folder:
        params["in"] = folder
    if unread is not None:
        params["unread"] = unread

    r = requests.get(f"{NYLAS_BASE_URL}/messages", headers=HEADERS, params=params)
    raw = r.json()

    clean = []
    for msg in raw.get("data", []):
        sender = msg.get("from", [{}])[0]
        sender_email = sender.get("email", "")
        domain = sender_email.split("@")[-1].lower()

        if domain in SPAM_DOMAINS:
            continue

        clean.append({
            "subject": msg.get("subject"),
            "from": sender,
            "date": msg.get("date")
        })

    return {"messages": clean}

def read_message(message_id):
    return requests.get(f"{NYLAS_BASE_URL}/messages/{message_id}/clean", headers=HEADERS).json()

def get_message(message_id):
    return requests.get(f"{NYLAS_BASE_URL}/messages/{message_id}", headers=HEADERS).json()

def get_thread(thread_id):
    return requests.get(f"{NYLAS_BASE_URL}/threads/{thread_id}", headers=HEADERS).json()

def list_threads(limit=10, filters=None):
    params = {"limit": limit}
    if filters:
        params.update(filters)
    return requests.get(f"{NYLAS_BASE_URL}/threads", headers=HEADERS, params=params).json()

def send_email(to, subject, body, cc=None, bcc=None, reply_to=None):
    data = {'to': [{'email': to}], 'subject': subject, 'body': body}
    if cc: data['cc'] = [{'email': cc}] if isinstance(cc, str) else cc
    if bcc: data['bcc'] = [{'email': bcc}] if isinstance(bcc, str) else bcc
    if reply_to: data['reply_to'] = reply_to
    return requests.post(f"{NYLAS_BASE_URL}/messages/send", headers=HEADERS, json=data).json()

def reply_to_email(message_id, body):
    original = get_message(message_id)
    data = {
        'to': original.get('from'),
        'subject': 'Re: ' + original.get('subject', ''),
        'body': body,
        'reply_to_message_id': message_id,
        'headers': {
            'In-Reply-To': original.get('message_id'),
            'References': original.get('message_id')
        }
    }
    return requests.post(f"{NYLAS_BASE_URL}/messages/send", headers=HEADERS, json=data).json()

def schedule_email(to, subject, body, send_at):
    data = {'to': [{'email': to}], 'subject': subject, 'body': body, 'send_at': send_at}
    return requests.post(f"{NYLAS_BASE_URL}/messages/send", headers=HEADERS, json=data).json()

def clean_message(message_id):
    return requests.get(
        f"{NYLAS_BASE_URL}/messages/{message_id}/clean",
        headers=HEADERS,
        params={'ignore_images': True, 'ignore_tables': True}
    ).json()

def tag_email(message_id, metadata):
    return requests.post(f"{NYLAS_BASE_URL}/messages/{message_id}/metadata", headers=HEADERS, json=metadata).json()

def archive_email(message_id):
    return requests.put(f"{NYLAS_BASE_URL}/messages/{message_id}", headers=HEADERS, json={'folder': 'archive'}).json()

def classify_email(message_id):
    body = clean_message(message_id).get('body', '').lower()
    if 'invoice' in body:
        return {'status': 'success', 'tag': 'finance'}
    elif 'unsubscribe' in body:
        return {'status': 'success', 'tag': 'marketing'}
    return {'status': 'success', 'tag': 'general'}

def delete_email_from_cache(message_id):
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.delete(f"email_cache:{message_id}")
    return {'status': 'success', 'message': f'Deleted cached email {message_id}'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()

    try:
        params = json.loads(args.params) if args.params else {}
    except Exception as e:
        print(json.dumps({'status': 'error', 'message': f'Invalid params: {str(e)}'}))
        exit(1)

    actions = {
        'headers': list_message_headers,
        'read': read_message,
        'get': get_message,
        'thread': get_thread,
        'threads': list_threads,
        'send': send_email,
        'reply': reply_to_email,
        'schedule': schedule_email,
        'clean': clean_message,
        'tag': tag_email,
        'archive': archive_email,
        'classify': classify_email,
        'forget': delete_email_from_cache
    }

    fn = actions.get(args.action)
    if not fn:
        result = {'status': 'error', 'message': f'Unknown action: {args.action}'}
    else:
        try:
            result = fn(**params)
        except Exception as e:
            result = {'status': 'error', 'message': str(e)}

    print(json.dumps(result, indent=2))