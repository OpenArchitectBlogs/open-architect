import os
import json
import yaml
from datetime import datetime

# === CONFIG ===
POSTS_DIR = "posts"
STATE_FILE = "state.json"
CURRICULUM_FILE = "curriculum.yaml"
SOUL_FILE = "soul.md"
SYSTEM_PROMPT_FILE = "system_prompt.txt"

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_curriculum():
    with open(CURRICULUM_FILE) as f:
        return yaml.safe_load(f)

def load_file(path):
    with open(path) as f:
        return f.read()

def get_next_topic(state, curriculum):
    phase = curriculum["phases"][state["current_phase"]]
    topic = phase["topics"][state["current_topic_index"]]
    return phase["name"], topic

def advance_state(state, curriculum):
    phase = curriculum["phases"][state["current_phase"]]
    state["current_topic_index"] += 1

    if state["current_topic_index"] >= len(phase["topics"]):
        state["current_phase"] += 1
        state["current_topic_index"] = 0

    state["total_posts"] += 1
    return state

def generate_article(prompt):
    # Replace this with actual OpenClaw CLI call
    return os.popen(f'openclaw "{prompt}"').read()

def main():
    state = load_state()
    curriculum = load_curriculum()
    soul = load_file(SOUL_FILE)
    system_prompt = load_file(SYSTEM_PROMPT_FILE)

    phase_name, topic = get_next_topic(state, curriculum)

    full_prompt = f"""
{soul}

{system_prompt}

Phase: {phase_name}
Topic: {topic}

Write a complete Markdown article.
"""

    article = generate_article(full_prompt)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{POSTS_DIR}/{date_str}-{topic.replace(' ', '-').lower()}.md"

    with open(filename, "w") as f:
        f.write(article)

    state = advance_state(state, curriculum)
    save_state(state)

    os.system("git add .")
    os.system(f'git commit -m "Daily Post: {topic}"')
    os.system("git push")

if __name__ == "__main__":
    main()
