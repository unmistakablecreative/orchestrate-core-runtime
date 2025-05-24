import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from requests_oauthlib import OAuth1Session
import requests
import mimetypes
import os



TWITTER_API_KEY = 'SfZKglQnjjnpAIMOIdYO5MSAR'
TWITTER_API_SECRET = 'mB1gRiwLENAuGGZPgKb9s5ze4cDEeUJjFe3IrhyYARzXdF7e4z'
TWITTER_ACCESS_TOKEN = '108645782-nmWCBUQqQDLBemA0flYOwNUj5Ta5hkcBacGAF7hW'
TWITTER_ACCESS_SECRET = 'aN2CNL4SGXR06zHFIYatWghI2s4Bd0pXqfT3osfjblzTC'


oauth = OAuth1Session(TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)


def get_user_id(username):
    url = f'https://api.twitter.com/2/users/by/username/{username}'
    response = oauth.get(url)
    if response.status_code != 200:
        return {'status': 'error', 'message': response.text}
    data = response.json()
    return {'status': 'success', 'user_id': data.get('data', {}).get('id')}


def get_user_tweets(user_id, max_results, start_time=None):
    params = {'max_results': max_results}
    if start_time:
        params['start_time'] = start_time
    url = f'https://api.twitter.com/2/users/{user_id}/tweets'
    response = oauth.get(url, params=params)
    if response.status_code != 200:
        return {'status': 'error', 'message': response.text}
    return {'status': 'success', 'data': response.json()}


def get_user_lists(user_id):
    url = f'https://api.twitter.com/2/users/{user_id}/owned_lists'
    response = oauth.get(url)
    if response.status_code != 200:
        return {'status': 'error', 'message': response.text}
    return {'status': 'success', 'data': response.json()}


def get_list_tweets(list_id, max_results):
    url = f'https://api.twitter.com/2/lists/{list_id}/tweets'
    params = {'max_results': max_results}
    response = oauth.get(url, params=params)
    if response.status_code != 200:
        return {'status': 'error', 'message': response.text}
    return {'status': 'success', 'data': response.json()}


def search_recent_tweets(query, max_results, tweet_fields=None):
    url = 'https://api.twitter.com/2/tweets/search/recent'
    params = {'query': query, 'max_results': max_results}
    if tweet_fields:
        params['tweet.fields'] = tweet_fields
    response = oauth.get(url, params=params)
    if response.status_code != 200:
        return {'status': 'error', 'message': response.text}
    return {'status': 'success', 'data': response.json()}



def init_twitter_auth():
    from system_settings import load_credential
    from requests_oauthlib import OAuth1Session
    
    api_key = load_credential("twitter_api_key")
    api_secret = load_credential("twitter_api_secret")
    access_token = load_credential("twitter_access_token")
    access_secret = load_credential("twitter_access_secret")
    
    if all([api_key, api_secret, access_token, access_secret]):
        return OAuth1Session(api_key, api_secret, access_token, access_secret)
    else:
        return None
if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('action')
    parser.add_argument('--params')
    args = parser.parse_args()
    params = json.loads(args.params) if args.params else {}
    if args.action == 'get_user_id':
        result = get_user_id(**params)
    elif args.action == 'get_user_tweets':
        result = get_user_tweets(**params)
    elif args.action == 'get_user_lists':
        result = get_user_lists(**params)
    elif args.action == 'get_list_tweets':
        result = get_list_tweets(**params)
    elif args.action == 'search_recent_tweets':
        result = search_recent_tweets(**params)
    else:
        result = {'status': 'error', 'message': f'Unknown action {args.action}'
            }
    print(json.dumps(result, indent=2))
