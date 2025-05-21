import requests
import json
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CONTACTOUT_API_KEY = "7BPsQLuvwhXHaUFs2NDYSsj0"
BASE_URL = "https://api.contactout.com/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {CONTACTOUT_API_KEY}"
}

class ContactOutTool:
    def __init__(self):
        if not CONTACTOUT_API_KEY or CONTACTOUT_API_KEY == "7BPsQLuvwhXHaUFs2NDYSsj0":
            logging.error("🚨 ERROR: ContactOut API key is missing or incorrect.")
            raise ValueError("ContactOut API key is missing or incorrect.")

    def search_contacts(self, params):
        url = f"{BASE_URL}/people/search"
        payload = {
            "page": params.get("page", 1),
            "name": params.get("name", ""),
            "company": params.get("company", []),
            "job_title": params.get("job_title", []),
            "output_fields": params.get("output_fields", ["name", "title", "company"])
        }
        response = requests.post(url, headers=HEADERS, json=payload)
        return self._handle_response(response)

    def _handle_response(self, response):
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {"error": "Invalid JSON response", "status_code": response.status_code}

        if response.status_code == 200:
            return response_json
        elif response.status_code == 401:
            logging.error("🚨 ERROR: Authentication failed. Check your API key.")
            return {"error": "Authentication failed. Invalid API key.", "status_code": 401}
        elif response.status_code == 403:
            logging.error("🚨 ERROR: API key does not have permission to access this endpoint.")
            return {"error": "API key is unauthorized for this action.", "status_code": 403}
        elif response.status_code == 429:
            logging.error("🚨 ERROR: Rate limit exceeded. Try again later.")
            return {"error": "Rate limit exceeded. Try again later.", "status_code": 429}
        else:
            logging.error(f"API Error {response.status_code}: {response.text}")
            return {"error": response.text, "status_code": response.status_code}

    def execute(self, action, params):
        actions = {
            "search_contacts": self.search_contacts
        }
        if action in actions:
            return actions[action](params)
        else:
            logging.error(f"Unsupported action: {action}")
            return {"error": f"Unsupported action: {action}", "available_actions": list(actions.keys())}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ContactOut Tool CLI")
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("--params", type=str, required=True, help="JSON-encoded parameters")
    args = parser.parse_args()

    if args.action == "get_supported_actions":
        output = {
            "contactout_tool": {
                "description": "Finds people and professional contact info using ContactOut API.",
                "functions": ["search_contacts"]
            }
        }
        print(json.dumps(output, indent=4))
        exit(0)

    tool = ContactOutTool()

    try:
        params_dict = json.loads(args.params)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON format"}, indent=4))
        exit(1)

    result = tool.execute(args.action, params_dict)
    print(json.dumps(result, indent=4))
