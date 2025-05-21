import requests
import json
import os
import argparse

CREDENTIALS_FILE = "credentials.json"
MEM_API_URL = "https://api.mem.ai/v1/mems"  # Adjust endpoint if needed

def load_api_key():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            creds = json.load(f)
        return creds.get("mem_api_key")
    return None

def execute_action(action, params):
    api_key = load_api_key()
    if not api_key:
        return {"status": "error", "message": "Missing API key in credentials.json"}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    content = params.get("input", "")

    if action == "create_mem":
        response = requests.post(MEM_API_URL, headers=headers, json={"content": content})
        try:
            return response.json() if response.status_code == 200 else {"status": "error", "message": "API request failed"}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON response from Mem."}
    else:
        return {"status": "error", "message": "Invalid action or missing parameters."}

def main():
    parser = argparse.ArgumentParser(description="Mem Tool")
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("--params", type=str, required=True, help="JSON-encoded parameters")
    args = parser.parse_args()

    if args.action == "get_supported_actions":
        output = {
            "mem_tool": {
                "description": "Creates notes inside your Mem workspace.",
                "functions": ["create_mem"]
            }
        }
        print(json.dumps(output, indent=4))
        return

    try:
        params_dict = json.loads(args.params)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Invalid JSON format."}, indent=4))
        return

    result = execute_action(args.action, params_dict)
    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()
