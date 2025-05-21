import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from requests_oauthlib import OAuth1Session
import requests
import mimetypes
import os


def post_to_platform(content, link, image_url):
    if link:
        content = f'{content.strip()}\n{link.strip()}'
    if not content:
        return {'status': 'error', 'message': '❌ Content is required.'}
    from system_settings import load_credential
    TWITTER_API_KEY = load_credential('twitter_api_key')
    TWITTER_API_SECRET = load_credential('twitter_api_secret')
    TWITTER_ACCESS_TOKEN = load_credential('twitter_access_token')
    TWITTER_ACCESS_SECRET = load_credential('twitter_access_secret')
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_SECRET]):
        return {'status': 'error', 'message':
            '❌ Missing one or more Twitter API credentials.'}
    oauth = OAuth1Session(TWITTER_API_KEY, TWITTER_API_SECRET,
        TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    media_id = None
    if image_url:
        try:
            img_data = requests.get(image_url).content
            mime_type, _ = mimetypes.guess_type(image_url)
            files = {'media': (os.path.basename(image_url), img_data, 
                mime_type or 'application/octet-stream')}
            media_upload = oauth.post(
                'https://upload.twitter.com/1.1/media/upload.json', files=files
                )
            media_upload.raise_for_status()
            media_id = media_upload.json().get('media_id_string')
        except Exception as e:
            return {'status': 'error', 'message': '❌ Image upload failed',
                'error': str(e)}
    payload = {'text': content.strip()}
    if media_id:
        payload['media'] = {'media_ids': [media_id]}
    try:
        response = oauth.post('https://api.twitter.com/2/tweets', json=payload)
        response.raise_for_status()
        return {'status': 'success', 'message':
            '✅ Tweet posted successfully', 'data': response.json()}
    except Exception as e:
        return {'status': 'error', 'message': '❌ Twitter API error',
            'error': str(e)}


def buffer_loop():
    while True:
        try:
            with open('data/campaign_rules.json', 'r') as f:
                rules = json.load(f).get('entries', {})
            with open('data/post_queue.json', 'r') as f:
                queue = json.load(f).get('entries', {})
            now = datetime.now(ZoneInfo('America/Los_Angeles'))
            today = now.strftime('%a').lower()
            now_time = now.strftime('%H:%M')
            for campaign_id, rule in rules.items():
                if today not in rule.get('days', []):
                    continue
                allowed_slots = rule.get('timeslots', [])
                max_posts = rule.get('max_posts_per_day', 1)
                published_today = [p for p in queue.values() if p.get(
                    'campaign_id') == campaign_id and p.get('status') ==
                    'published' and p.get('published_time', '').startswith(
                    now.strftime('%Y-%m-%d'))]
                published_count = len(published_today)
                slots_ready = [s for s in allowed_slots if now_time >= s]
                slots_remaining = max(0, min(len(slots_ready), max_posts -
                    published_count))
                if slots_remaining == 0:
                    continue
                for post in queue.values():
                    if slots_remaining == 0:
                        break
                    if post.get('campaign_id') != campaign_id or post.get(
                        'status') != 'scheduled':
                        continue
                    content = post.get('content', '').strip()
                    link = post.get('link', '').strip()
                    image_url = post.get('image_url')
                    result = post_to_platform(content, link=link, image_url
                        =image_url)
                    post['status'] = 'published'
                    post['published_time'] = now.isoformat()
                    post['response'] = result
                    slots_remaining -= 1
            with open('data/post_queue.json', 'w') as f:
                json.dump({'entries': queue}, f, indent=2)
        except Exception as e:
            print(f'❌ Loop error: {e}')
        time.sleep(60)


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}
    if args.action == 'buffer_loop':
        result = buffer_loop(**params)
    if args.action == 'post_to_platform':
        result = post_to_platform(**params)
    else:
        result = {'status': 'error', 'message': f'Unknown action {args.action}'
            }
    print(json.dumps(result, indent=2))
