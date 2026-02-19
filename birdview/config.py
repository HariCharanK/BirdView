"""Credential loading and configuration for BirdView."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path.home() / ".birdview"
BOOKMARKS_FILE = APP_DIR / "bookmarks.json"

REQUIRED_KEYS = [
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_BEARER_TOKEN",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
]


@dataclass(frozen=True)
class TwitterCreds:
    consumer_key: str
    consumer_secret: str
    bearer_token: str
    access_token: str
    access_token_secret: str


def load_creds() -> TwitterCreds:
    """Load Twitter API credentials from environment or ~/.env file."""
    # Try ~/.env first, then .env in cwd
    home_env = Path.home() / ".env"
    if home_env.exists():
        load_dotenv(home_env)
    load_dotenv()  # .env in cwd (overrides if present)

    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        raise SystemExit(
            f"Missing Twitter credentials: {', '.join(missing)}\n"
            f"Set them in ~/.env or as environment variables.\n"
            f"Required: {', '.join(REQUIRED_KEYS)}"
        )

    return TwitterCreds(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        bearer_token=os.environ["TWITTER_BEARER_TOKEN"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )


def ensure_app_dir() -> Path:
    """Create ~/.birdview/ if it doesn't exist."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return APP_DIR


def load_bookmarks() -> list[dict]:
    """Load locally-saved bookmarks."""
    if not BOOKMARKS_FILE.exists():
        return []
    with open(BOOKMARKS_FILE) as f:
        return json.load(f)


def save_bookmark(tweet_id: str, author: str, text: str, url: str) -> None:
    """Save a tweet as a local bookmark."""
    ensure_app_dir()
    bookmarks = load_bookmarks()

    # Don't duplicate
    if any(b["tweet_id"] == tweet_id for b in bookmarks):
        return

    bookmarks.append({
        "tweet_id": tweet_id,
        "author": author,
        "text": text[:280],
        "url": url,
        "saved_at": __import__("datetime").datetime.now().isoformat(),
    })

    with open(BOOKMARKS_FILE, "w") as f:
        json.dump(bookmarks, f, indent=2)


def remove_bookmark(tweet_id: str) -> bool:
    """Remove a local bookmark. Returns True if found and removed."""
    bookmarks = load_bookmarks()
    new = [b for b in bookmarks if b["tweet_id"] != tweet_id]
    if len(new) == len(bookmarks):
        return False
    ensure_app_dir()
    with open(BOOKMARKS_FILE, "w") as f:
        json.dump(new, f, indent=2)
    return True
