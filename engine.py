import os
import json
import yaml
from datetime import datetime
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATE_FILE = os.path.join(BASE_DIR, "state.json")
CURRICULUM_FILE = os.path.join(BASE_DIR, "curriculum.yaml")
SOUL_FILE = os.path.join(BASE_DIR, "soul.md")
SYSTEM_PROMPT_FILE = os.path.join(BASE_DIR, "system_prompt.txt")
CONSTRAINTS_FILE = os.path.join(BASE_DIR, "constraints.yaml")

POSTS_DIR = os.path.join(BASE_DIR, "posts")


# ----------------------------
# Utility Loaders
# ----------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def load_text(path):
    with open(path) as f:
        return f.read()


# ----------------------------
# Curriculum Logic
# ----------------------------

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


# ----------------------------
# OpenClaw Invocation
# ----------------------------

def run_openclaw(prompt):
    # Replace with actual OpenClaw CLI command
    result = subprocess.run(
        ["openclaw", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout


# ----------------------------
# Quality Checks
# ----------------------------

def validate_article(article, constraints):
    words = len(article.split())

    if words < constraints["min_words"]:
        return False, "Too short"

    for section in constraints["required_sections"]:
        if section not in article:
            return False, f"Missing section: {section}"

    return True, "OK"


# ----------------------------
# Main Engine
# ----------------------------

def main():
    state = load_json(STATE_FILE)
    curriculum = load_yaml(CURRICULUM_FILE)
    constraints = load_yaml(CONSTRAINTS_FILE)

    soul = load_text(SOUL_FILE)
    system_prompt = load_text(SYSTEM_PROMPT_FILE)

    phase_name, topic = get_next_topic(state, curriculum)

    base_prompt = f"""
{soul}

{system_prompt}

Phase: {phase_name}
Topic: {topic}

Write a complete article in Markdown.
"""

    article = run_openclaw(base_prompt)

    # Self-Critique Pass
    critique_prompt = f"""
Review the following article.
Strengthen technical rigor.
Add missing tradeoffs.
Deepen production insights.
Fix logical inconsistencies.

ARTICLE:
{article}
"""

    improved_article = run_openclaw(critique_prompt)

    valid, reason = validate_article(improved_article, constraints)

    if not valid:
        print(f"Validation failed: {reason}")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{topic.replace(' ', '-').lower()}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    with open(filepath, "w") as f:
        f.write(improved_article)

    state = advance_state(state, curriculum)
    save_json(STATE_FILE, state)

    # Git push
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"Daily Post: {topic}"])
    subprocess.run(["git", "push"])

    print("Post published successfully.")


if __name__ == "__main__":
    main()
