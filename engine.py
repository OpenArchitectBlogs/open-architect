import os
import json
import yaml
import logging
from datetime import datetime
import subprocess
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATE_FILE = os.path.join(BASE_DIR, "state.json")
CURRICULUM_FILE = os.path.join(BASE_DIR, "curriculum.yaml")
SOUL_FILE = os.path.join(BASE_DIR, "soul.md")
SYSTEM_PROMPT_FILE = os.path.join(BASE_DIR, "system_prompt.txt")
CONSTRAINTS_FILE = os.path.join(BASE_DIR, "constraints.yaml")

POSTS_DIR = os.path.join(BASE_DIR, "_posts")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "engine.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log(msg):
    print(msg)
    logging.info(msg)


def load_json(path):
    log(f"Loading JSON: {path}")
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    log(f"Saving JSON: {path}")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_yaml(path):
    log(f"Loading YAML: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def load_text(path):
    log(f"Loading text: {path}")
    with open(path) as f:
        return f.read()


def get_next_topic(state, curriculum):
    phase = curriculum["phases"][state["current_phase"]]
    topic = phase["topics"][state["current_topic_index"]]
    log(f"Selected Phase: {phase['name']}")
    log(f"Selected Topic: {topic}")
    return phase["name"], topic


def advance_state(state, curriculum):
    log("Advancing state...")
    phase = curriculum["phases"][state["current_phase"]]
    state["current_topic_index"] += 1

    if state["current_topic_index"] >= len(phase["topics"]):
        state["current_phase"] += 1
        state["current_topic_index"] = 0

    state["total_posts"] += 1
    return state


def run_openclaw(prompt):
    log("Calling OpenClaw agent...")

    result = subprocess.run(
        [
            "openclaw", "agent",
            "--agent", "main",
            "--message", prompt,
            "--local",
            "--json"
        ],
        capture_output=True,
        text=True
    )

    log(f"Return Code: {result.returncode}")
    log(f"STDOUT (first 1500 chars):\n{result.stdout[:1500]}")
    log(f"STDERR (first 1500 chars):\n{result.stderr[:1500]}")

    if result.returncode != 0:
        log("OpenClaw returned non-zero exit code.")
        raise Exception(result.stderr)

    try:
        data = json.loads(result.stdout)
        log("JSON parsed successfully.")

        response = (
            data.get("response")
            or data.get("output")
            or data.get("content")
            or data.get("message")
        )

        if not response:
            log("JSON parsed but no usable response field found.")
            return result.stdout

        log(f"Extracted response length: {len(response)} characters")
        return response

    except json.JSONDecodeError:
        log("JSON parsing failed. Returning raw stdout.")
        return result.stdout


def validate_article(article, constraints):
    words = len(article.split())
    log(f"Article word count: {words}")

    if words < constraints["min_words"]:
        return False, "Too short"

    for section in constraints["required_sections"]:
        if section not in article:
            return False, f"Missing section: {section}"

    return True, "OK"


def create_frontmatter(title, category):
    today = datetime.now().strftime("%Y-%m-%d")

    return f"""---
layout: single
title: "{title}"
date: {today}
categories: [{category}]
---

"""


def main():
    try:
        log("========== ENGINE START ==========")

        state = load_json(STATE_FILE)
        curriculum = load_yaml(CURRICULUM_FILE)
        constraints = load_yaml(CONSTRAINTS_FILE)

        if state["current_phase"] >= len(curriculum["phases"]):
            log("Curriculum completed. Exiting.")
            return

        soul = load_text(SOUL_FILE)
        system_prompt = load_text(SYSTEM_PROMPT_FILE)

        phase_name, topic = get_next_topic(state, curriculum)

        base_prompt = f"""
You are operating in fully autonomous publishing mode.
Do not ask questions.
Do not request clarification.
Produce final article only.

Phase: {phase_name}
Topic: {topic}

Write a complete long-form Markdown article.
"""

        article = run_openclaw(base_prompt)

        log("Running critique pass...")

        critique_prompt = f"""
Improve the following article.
Strengthen rigor.
Add tradeoffs.
Add failure modes.
Output full revised article only.

ARTICLE:
{article}
"""

        improved_article = run_openclaw(critique_prompt)

        valid, reason = validate_article(improved_article, constraints)

        if not valid:
            log(f"Validation failed: {reason}")
            return

        title = topic.title()
        category = phase_name.lower().replace(" ", "-")

        frontmatter = create_frontmatter(title, category)
        final_article = frontmatter + improved_article

        os.makedirs(POSTS_DIR, exist_ok=True)

        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{topic.replace(' ', '-').lower()}.md"
        filepath = os.path.join(POSTS_DIR, filename)

        log(f"Writing file: {filepath}")

        with open(filepath, "w") as f:
            f.write(final_article)

        state = advance_state(state, curriculum)
        save_json(STATE_FILE, state)

        log("Running git add...")
        subprocess.run(["git", "add", "."], check=True)

        log("Running git commit...")
        subprocess.run(["git", "commit", "-m", f"Daily Post: {topic}"], check=True)

        log("Running git push...")
        subprocess.run(["git", "push"], check=True)

        log("Post published successfully.")
        log("========== ENGINE END ==========")

    except Exception as e:
        log("ENGINE CRASHED.")
        log(str(e))
        log(traceback.format_exc())


if __name__ == "__main__":
    main()
