import os
import json
import argparse
import logging
import uuid
from datetime import datetime, timedelta

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
CALENDAR_FILE = "tools/calendar.json"
INVITE_DIR = "tools/calendar_invites"

# Ensure required directories and files exist
os.makedirs(INVITE_DIR, exist_ok=True)
if not os.path.exists(CALENDAR_FILE):
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)

def load_calendar():
    try:
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_calendar(data):
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def generate_ics(meeting_id, title, date_str, time_str, email, name):
    """Creates and saves an ICS file for the given meeting details."""
    start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
    end_dt = start_dt + timedelta(hours=1)
    uid = f"{meeting_id}@orchestrate.ai"

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Orchestrate//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
DTSTART:{start_dt.strftime("%Y%m%dT%H%M%SZ")}
DTEND:{end_dt.strftime("%Y%m%dT%H%M%SZ")}
SUMMARY:{title}
DESCRIPTION:Auto-scheduled via Orchestrate.
ORGANIZER;CN={name}:MAILTO:{email}
END:VEVENT
END:VCALENDAR
""".strip()

    filename = f"{title.replace(' ', '_')}_{date_str}.ics"
    filepath = os.path.join(INVITE_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ics_content)

    return filename

def add_meeting(params):
    required_fields = {"name", "date", "time", "email", "contact_name", "title"}
    if not required_fields.issubset(params):
        return {"status": "error", "message": "Missing required fields."}

    calendar = load_calendar()
    meeting_id = str(uuid.uuid4())

    calendar[meeting_id] = {
        "name": params["name"],
        "date": params["date"],
        "time": params["time"],
        "email": params["email"],
        "contact_name": params["contact_name"],
        "title": params["title"],
        "created_at": datetime.utcnow().isoformat()
    }

    # Save calendar
    save_calendar(calendar)

    # Generate ICS file
    ics_filename = generate_ics(
        meeting_id=meeting_id,
        title=params["title"],
        date_str=params["date"],
        time_str=params["time"],
        email=params["email"],
        name=params["contact_name"]
    )

    return {
        "status": "success",
        "message": "Meeting booked.",
        "meeting_id": meeting_id,
        "ics_file": ics_filename
    }

def main():
    parser = argparse.ArgumentParser(description="Calendar Tool for Execution Hub")
    parser.add_argument("action", help="Action to perform (add_meeting)")
    parser.add_argument("--params", type=str, required=False, help="JSON-encoded parameters")
    args = parser.parse_args()

    if args.action == "add_meeting":
        try:
            params_dict = json.loads(args.params) if args.params else {}
            result = add_meeting(params_dict)
            print(json.dumps(result, indent=4))
        except Exception as e:
            logging.error(f"🚨 ERROR: {e}")
            print(json.dumps({"status": "error", "message": str(e)}, indent=4))
    else:
        print(json.dumps({"status": "error", "message": "❌ Invalid action."}, indent=4))

if __name__ == "__main__":
    main()
