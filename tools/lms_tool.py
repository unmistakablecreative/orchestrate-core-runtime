import json
import os
import argparse

# --- Constants (Set Output Directory) ---
COURSES_DIR = "/Users/srinivas/Orchestrate Github/Orchestrate_Hackathon/courses"


def slugify(text):
    """
    Converts text into a safe slug.
    """
    return text.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")


def read_course_file(params):
    course_file = params.get("filename")
    if not course_file:
        return {"status": "error", "message": "❌ Missing filename."}

    path = os.path.join(COURSES_DIR, course_file)
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ File not found: {path}"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            if course_file.endswith(".json"):
                content = json.load(f)
                return {"status": "success", "data": content}
            else:
                content = f.read()
                return {"status": "success", "data": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def add_exercise_to_lesson(params):
    lesson_id = params.get("lesson_id")
    prompt = params.get("prompt")
    answer = params.get("answer")
    if not lesson_id or not prompt or not answer:
        return {"status": "error", "message": "❌ Missing lesson ID, prompt, or answer."}

    block = f"\n\n---\n\n### Exercise\n\n**Prompt:** {prompt}\n\n**Answer:** {answer}"
    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ Lesson file not found: {path}"}

    with open(path, "a", encoding="utf-8") as f:
        f.write(block)

    return {"status": "success", "message": f"✅ Exercise added to {path}"}

def add_content_to_lesson(params):
    lesson_id = params.get("lesson_id")
    content = params.get("content")
    if not lesson_id or not content:
        return {"status": "error", "message": "❌ Missing lesson ID or content."}

    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ Lesson file not found: {path}"}

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n\n{content}")

    return {"status": "success", "message": f"✅ Content added to {path}"}

def create_lesson_markdown(params):
    lesson_id = params.get("lesson_id")
    title = params.get("title")
    if not lesson_id or not title:
        return {"status": "error", "message": "❌ Missing lesson ID or title."}

    content = f"# {title}\n\n## Overview\n\nWrite your lesson summary here.\n\n---\n\n## Content\n\n..."
    filename = f"{lesson_id}.md"
    path = os.path.join(COURSES_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "success", "message": f"✅ Lesson markdown created at {path}"}

def add_lesson_to_index(params):
    course_title = params.get("course_title")
    lesson_id = params.get("lesson_id")
    lesson_title = params.get("lesson_title")
    if not course_title or not lesson_id or not lesson_title:
        return {"status": "error", "message": "❌ Missing required parameters."}

    course_filename = slugify(course_title) + ".course.json"
    course_path = os.path.join(COURSES_DIR, course_filename)

    if not os.path.exists(course_path):
        return {"status": "error", "message": f"❌ Course index not found: {course_path}"}

    with open(course_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    new_entry = {"id": lesson_id, "title": lesson_title}
    index["lessons"].append(new_entry)

    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    # Auto-create lesson file stub
    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    content = f"# {lesson_title}\n\n## Overview\n\n..."
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "success", "message": f"✅ Lesson added and file created at {path}"}

def create_course_index(params):
    course_title = params.get("course_title")
    description = params.get("description")
    if not course_title or not description:
        return {"status": "error", "message": "❌ Missing course title or description."}

    index = {
        "course_title": course_title,
        "description": description,
        "lessons": []
    }

    filename = slugify(course_title) + ".course.json"
    course_path = os.path.join(COURSES_DIR, filename)

    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    return {"status": "success", "message": f"✅ Course index created at {course_path}"}

def add_exercise_to_lesson(params):
    lesson_id = params.get("lesson_id")
    prompt = params.get("prompt")
    answer = params.get("answer")
    if not lesson_id or not prompt or not answer:
        return {"status": "error", "message": "❌ Missing lesson ID, prompt, or answer."}

    block = f"\n\n---\n\n### Exercise\n\n**Prompt:** {prompt}\n\n**Answer:** {answer}"
    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ Lesson file not found: {path}"}

    with open(path, "a", encoding="utf-8") as f:
        f.write(block)

    return {"status": "success", "message": f"✅ Exercise added to {path}"}

def add_content_to_lesson(params):
    lesson_id = params.get("lesson_id")
    content = params.get("content")
    if not lesson_id or not content:
        return {"status": "error", "message": "❌ Missing lesson ID or content."}

    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ Lesson file not found: {path}"}

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n\n{content}")

    return {"status": "success", "message": f"✅ Content added to {path}"}

def create_lesson_markdown(params):
    lesson_id = params.get("lesson_id")
    title = params.get("title")
    if not lesson_id or not title:
        return {"status": "error", "message": "❌ Missing lesson ID or title."}

    content = f"# {title}\n\n## Overview\n\nWrite your lesson summary here.\n\n---\n\n## Content\n\n..."
    filename = f"{lesson_id}.md"
    path = os.path.join(COURSES_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "success", "message": f"✅ Lesson markdown created at {path}"}

def add_lesson_to_index(params):
    course_title = params.get("course_title")
    lesson_id = params.get("lesson_id")
    lesson_title = params.get("lesson_title")
    if not course_title or not lesson_id or not lesson_title:
        return {"status": "error", "message": "❌ Missing required parameters."}

    course_filename = slugify(course_title) + ".course.json"
    course_path = os.path.join(COURSES_DIR, course_filename)

    if not os.path.exists(course_path):
        return {"status": "error", "message": f"❌ Course index not found: {course_path}"}

    with open(course_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    new_entry = {"id": lesson_id, "title": lesson_title}
    index["lessons"].append(new_entry)

    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    # Auto-create lesson file stub
    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    content = f"# {lesson_title}\n\n## Overview\n\n..."
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "success", "message": f"✅ Lesson added and file created at {path}"}

def create_course_index(params):
    course_title = params.get("course_title")
    description = params.get("description")
    if not course_title or not description:
        return {"status": "error", "message": "❌ Missing course title or description."}

    index = {
        "course_title": course_title,
        "description": description,
        "lessons": []
    }

    filename = slugify(course_title) + ".course.json"
    course_path = os.path.join(COURSES_DIR, filename)

    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    return {"status": "success", "message": f"✅ Course index created at {course_path}"}

def add_exercise_to_lesson(params):
    lesson_id = params.get("lesson_id")
    prompt = params.get("prompt")
    answer = params.get("answer")
    if not lesson_id or not prompt or not answer:
        return {"status": "error", "message": "❌ Missing lesson ID, prompt, or answer."}

    block = f"\n\n---\n\n### Exercise\n\n**Prompt:** {prompt}\n\n**Answer:** {answer}"
    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ Lesson file not found: {path}"}

    with open(path, "a", encoding="utf-8") as f:
        f.write(block)

    return {"status": "success", "message": f"✅ Exercise added to {path}"}

def add_content_to_lesson(params):
    lesson_id = params.get("lesson_id")
    content = params.get("content")
    if not lesson_id or not content:
        return {"status": "error", "message": "❌ Missing lesson ID or content."}

    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    if not os.path.exists(path):
        return {"status": "error", "message": f"❌ Lesson file not found: {path}"}

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n\n{content}")

    return {"status": "success", "message": f"✅ Content added to {path}"}

def create_lesson_markdown(params):
    lesson_id = params.get("lesson_id")
    title = params.get("title")
    if not lesson_id or not title:
        return {"status": "error", "message": "❌ Missing lesson ID or title."}

    content = f"# {title}\n\n## Overview\n\nWrite your lesson summary here.\n\n---\n\n## Content\n\n..."
    filename = f"{lesson_id}.md"
    path = os.path.join(COURSES_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "success", "message": f"✅ Lesson markdown created at {path}"}

def add_lesson_to_index(params):
    course_title = params.get("course_title")
    lesson_id = params.get("lesson_id")
    lesson_title = params.get("lesson_title")
    if not course_title or not lesson_id or not lesson_title:
        return {"status": "error", "message": "❌ Missing required parameters."}

    course_filename = slugify(course_title) + ".course.json"
    course_path = os.path.join(COURSES_DIR, course_filename)

    if not os.path.exists(course_path):
        return {"status": "error", "message": f"❌ Course index not found: {course_path}"}

    with open(course_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    new_entry = {"id": lesson_id, "title": lesson_title}
    index["lessons"].append(new_entry)

    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    # Auto-create lesson file stub
    path = os.path.join(COURSES_DIR, f"{lesson_id}.md")
    content = f"# {lesson_title}\n\n## Overview\n\n..."
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"status": "success", "message": f"✅ Lesson added and file created at {path}"}

def create_course_index(params):
    course_title = params.get("course_title")
    description = params.get("description")
    if not course_title or not description:
        return {"status": "error", "message": "❌ Missing course title or description."}

    index = {
        "course_title": course_title,
        "description": description,
        "lessons": []
    }

    filename = slugify(course_title) + ".course.json"
    course_path = os.path.join(COURSES_DIR, filename)

    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    return {"status": "success", "message": f"✅ Course index created at {course_path}"}

# --- Action Router ---
def main():
    parser = argparse.ArgumentParser(description="Orchestrate Tool Template")
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("--params", type=str, required=False, help="JSON-encoded parameters for the action")
    args = parser.parse_args()

    # Safe JSON parsing
    try:
        params = json.loads(args.params) if args.params else {}
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "❌ Invalid JSON format."}, indent=4))
        return

    # Action Routing
    if args.action == "create_course_index":
        result = create_course_index(params)
    elif args.action == "add_lesson_to_index":
        result = add_lesson_to_index(params)
    elif args.action == "create_lesson_markdown":
        result = create_lesson_markdown(params)
    elif args.action == "add_content_to_lesson":
        result = add_content_to_lesson(params)
    elif args.action == "add_exercise_to_lesson":
        result = add_exercise_to_lesson(params)
    elif args.action == "create_course":
        result = create_course(params)
    elif args.action == "add_lesson":
        result = add_lesson(params)
    elif args.action == "update_course_index":
        result = update_course_index(params)
    elif args.action == "slugify":
        result = slugify(params)
    elif args.action == "read_course_file":
        result = read_course_file(params)
    else:
        result = {"status": "error", "message": f"❌ Unknown action: {args.action}"}

    # Always output JSON
    print(json.dumps(result, indent=4))

# --- Main Execution ---
if __name__ == "__main__":
    main()
