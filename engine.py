import os
import json
import logging
import subprocess
import traceback
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOUL_FILE = os.path.join(BASE_DIR, "soul.md")
STATE_FILE = os.path.join(BASE_DIR, "state.json")

POSTS_DIR = os.path.join(BASE_DIR, "_posts")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "engine.log")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def log(msg):
    print(msg)
    logging.info(msg)


def load_text(path):
    with open(path) as f:
        return f.read()


# -------------------------
# STATE MANAGEMENT
# -------------------------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"thought_number": 1}

    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# -------------------------
# OPENCLAW CALL
# -------------------------

def run_openclaw(prompt):
    log("Calling OpenClaw...")

    result = subprocess.run(
        [
            "openclaw",
            "agent",
            "--agent",
            "main",
            "--message",
            prompt,
            "--local",
            "--json"
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise Exception(result.stderr)

    try:
        data = json.loads(result.stdout)

        if "payloads" in data and len(data["payloads"]) > 0:
            text = data["payloads"][0].get("text")

        else:
            text = (
                data.get("response")
                or data.get("output")
                or data.get("content")
                or data.get("message")
            )

        if not text:
            raise Exception("Empty response")

        return text.strip()

    except Exception:
        log("JSON parse failed. Returning raw output.")
        return result.stdout.strip()


# -------------------------
# TOPIC GENERATION
# -------------------------

TOPICS = [
    "binary numbers",
    "timeouts in distributed systems",
    "why abstractions leak",
    "debugging production systems",
    "thread scheduling",
    "cache invalidation",
    "memory fragmentation",
    "latency vs throughput",
    "distributed system failures",
    "garbage collection pauses",
    "database indexing",
    "the cost of abstraction",
    "observability vs monitoring",
    "eventual consistency",
    "message queues",
    "system complexity",
    "java garbage collectors",
    "jvm performance",
    "cpu cache behavior",
    "an interesting rare tip about system design, data structure, algorithm, observability or exciting"
]

ANGLES = [
    "Something engineers misunderstand about",
    "A strange property of",
    "A debugging lesson about",
    "Why systems fail because of",
    "The hidden cost of",
    "What engineers forget about",
]


def generate_topic():
    topic = random.choice(TOPICS)
    angle = random.choice(ANGLES)
    return f"{angle} {topic}"


# -------------------------
# POST GENERATION
# -------------------------

def generate_post(soul, topic):

    prompt = f"""
{soul}

Topic: {topic}

Write a short engineering reflection.

Structure:
Observation → Reframe → Insight

Rules:
120-200 words
Short paragraphs
One core idea
No bullet points
Calm tone

Return markdown only.
"""

    return run_openclaw(prompt)


# -------------------------
# FRONTMATTER
# -------------------------

def create_frontmatter(title):

    today = datetime.now().strftime("%Y-%m-%d")

    return f"""---
layout: default
title: "{title}"
date: {today}
categories: [engineering]
---

# {title}

"""


# -------------------------
# SAVE POST
# -------------------------

def save_post(title, thought_number, article):

    today = datetime.now().strftime("%Y-%m-%d")

    slug = f"engineering-thought-{thought_number}"
    filename = f"{today}-{slug}.md"

    path = os.path.join(POSTS_DIR, filename)

    frontmatter = create_frontmatter(title)

    with open(path, "w") as f:
        f.write(frontmatter + article)

    log(f"Post written: {path}")


# -------------------------
# GIT PUBLISH
# -------------------------

def git_publish(title):

    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"{title}"], check=True)
    subprocess.run(["git", "push"], check=True)


# -------------------------
# MAIN ENGINE
# -------------------------

def main():

    try:

        log("===== OPENCLAW BLOG ENGINE START =====")

        soul = load_text(SOUL_FILE)

        state = load_state()
        thought_number = state["thought_number"]

        title = f"Engineering Thought #{thought_number}"

        topic = generate_topic()

        log(f"Thought: {thought_number}")
        log(f"Topic: {topic}")

        article = generate_post(soul, topic)

        words = len(article.split())
        log(f"Word count: {words}")

        if words < 80:
            log("Article too short. Skipping.")
            return

        save_post(title, thought_number, article)

        git_publish(title)

        state["thought_number"] += 1
        save_state(state)

        log("Post published successfully.")
        log("===== ENGINE END =====")

    except Exception as e:

        log("ENGINE CRASHED")
        log(str(e))
        log(traceback.format_exc())


if __name__ == "__main__":
    main()
