import json
import os
import argparse
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
ARCHIVE_LABEL = "CATEGORY_PROMOTIONS"

def load_credentials():
    """Loads OAuth credentials from credentials.json."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds = json.load(f)
        return Credentials(
            token=creds.get("gmail_access_token"),
            refresh_token=creds.get("gmail_refresh_token"),
            client_id=creds.get("gmail_client_id"),
            client_secret=creds.get("gmail_client_secret"),
            token_uri=creds.get("gmail_token_uri")
        )
    return None

def fetch_filtered_emails_v2(service, query):
    """Fetches only real conversations, excluding junk."""
    try:
        full_query = f"{query} -category:promotions -category:updates -from:noreply@* -from:newsletter@*"
        results = service.users().messages().list(userId="me", q=full_query).execute()
        messages = results.get("messages", [])
        
        full_emails = []
        for msg in messages:
            msg_id = msg.get("id")
            email_data = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            headers = email_data.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")
            body = email_data.get("snippet", "(No preview available)")
            
            full_emails.append({"id": msg_id, "sender": sender, "subject": subject, "body": body})
        
        return {"status": "success", "emails": full_emails}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def execute_action(action, params):
    """Executes Gmail API actions."""
    creds = load_credentials()
    if not creds:
        return json.dumps({"status": "error", "message": "Missing OAuth token. Authenticate first."})
    
    service = build("gmail", "v1", credentials=creds)
    
    try:
        if action == "fetch_filtered":
            query = params.get("input", "")
            return json.dumps(fetch_filtered_emails(service, query))
        else:
            return json.dumps({"status": "error", "message": "Invalid action or missing parameters."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def main():
    parser = argparse.ArgumentParser(description="Gmail Tool")
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("--params", type=str, required=True, help="JSON-encoded parameters")
    args = parser.parse_args()
    
    try:
        params_dict = json.loads(args.params)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Invalid JSON format."}, indent=4))
        return
    
    result = execute_action(args.action, params_dict)
    print(result)

if __name__ == "__main__":
    main()

def test_insert_safety(params):
    return {"status": "ok", "message": "Function inserted without nesting."}

