import json
import os
import argparse

# --- Constants (Optional) ---
# DATA_DIR = "path/to/data"
# OUTPUT_DIR = "path/to/output"
# CACHE_FILE = "cache.json"

# --- Helper Functions (Optional) ---
# def autocorrect_params(params):
#     return params

# --- Core Functions or Classes ---

def main(params):
    payload_result = load_payload(params)
    if payload_result.get("status") != "success":
        return payload_result

    params["payload"] = payload_result.get("payload")
    post_result = send_post_request(params)
    return post_result

def send_post_request(params):
    import requests

    endpoint = params.get('endpoint')
    api_key = params.get('api_key')
    payload = params.get('payload')

    headers = params.get('headers', {})

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        return {"status": "success", "response": response.json()}
    except Exception as e:
        return {"status": "error", "message": f"POST request failed: {str(e)}"}

def load_payload(params):
    payload_input = params.get('payload_input')
    try:
        if payload_input.endswith('.json') and os.path.isfile(payload_input):
            with open(payload_input, 'r') as f:
                payload = json.load(f)
        else:
            payload = json.loads(payload_input)
        return {"status": "success", "payload": payload}
    except Exception as e:
        return {"status": "error", "message": f"Failed to load payload: {str(e)}"}



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Universal Integrator Direct Runner")
    parser.add_argument("--endpoint", required=True, help="API endpoint to hit")
    parser.add_argument("--payload_input", required=True, help="Inline JSON or path to JSON file")
    parser.add_argument("--method", default="POST", help="HTTP method to use (POST or GET)")
    parser.add_argument("--headers", required=False, help="JSON string of headers")
    args = parser.parse_args()

    params = {
        "endpoint": args.endpoint,
        "payload_input": args.payload_input,
        "method": args.method,
        "headers": json.loads(args.headers) if args.headers else {}
    }

    result = main(params)
    print(json.dumps(result, indent=4))