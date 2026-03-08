import os
import json
import logging
import subprocess
import traceback
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOUL_FILE = os.path.join(BASE_DIR, "soul.md")

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
    log(f"Loading: {path}")
    with open(path) as f:
        return f.read()


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
            "--json",
            "--no-workspace",
        ],
        capture_output=True,
        text=True,
    )

    log(f"Return code: {result.returncode}")

    if result.returncode != 0:
        raise Exception(result.stderr)

    try:
        data = json.loads(result.stdout)

        # Extract response from OpenClaw format
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
            raise Exception("No usable text in response")

        log(f"Generated text length: {len(text)}")
        return text.strip()

    except Exception:
        log("JSON parse failed, returning raw output")
        return result.stdout.strip()


# Engineering topic pool
TOPICS = [
    "binary numbers",
    "timeouts in distributed systems",
    "why abstractions leak",
    "debugging production systems",
    "thread scheduling",
    "cache invalidation",
    "memory fragmentation",
    "latency vs throughput",
    "why distributed systems fail",
    "garbage collection pauses",
    "database indexes",
    "the cost of abstraction",
    "observability vs monitoring",
    "eventual consistency",
    "message queues",
    "system complexity",
    "any other interesting topics with respect to system design, java etc"
]

# Topic angles (makes posts interesting)
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


def generate_title(article):
    prompt = f"""
Generate a short title for this engineering reflection.

Rules:
Max 8 words.
No clickbait.

TEXT:
{article}

Return only the title.
"""

    title = run_openclaw(prompt)
    return title.replace('"', "").strip()


def generate_post(soul, topic):

    prompt = f"""
{soul}

Topic: {topic}

Write a short engineering reflection.

Structure:
Observation → Reframe → Insight

Rules:
120-200 words
One core idea
No lists
Natural prose
Calm tone

Return markdown only.
"""

    return run_openclaw(prompt)


def save_post(title, article):

    today = datetime.now().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-")

    filename = f"{today}-{slug}.md"
    path = os.path.join(POSTS_DIR, filename)

    frontmatter = create_frontmatter(title)

    with open(path, "w") as f:
        f.write(frontmatter + article)

    log(f"Post written: {path}")


def git_publish(title):

    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Post: {title}"], check=True)
    subprocess.run(["git", "push"], check=True)


def main():

    try:

        log("===== OPENCLAW BLOG ENGINE START =====")

        soul = load_text(SOUL_FILE)

        topic = generate_topic()
        log(f"Topic: {topic}")

        article = generate_post(soul, topic)

        words = len(article.split())
        log(f"Word count: {words}")

        if words < 80:
            log("Article too short, skipping.")
            return

        title = generate_title(article)
        log(f"Title: {title}")

        save_post(title, article)

        git_publish(title)

        log("Post published successfully.")
        log("===== ENGINE END =====")

    except Exception as e:

        log("ENGINE CRASHED")
        log(str(e))
        log(traceback.format_exc())


if __name__ == "__main__":
    main()
