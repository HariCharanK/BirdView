"""Credential loading and configuration for BirdView."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path.home() / ".birdview"
CREDS_FILE = APP_DIR / "credentials.json"
BOOKMARKS_FILE = APP_DIR / "bookmarks.json"

REQUIRED_KEYS = [
    "consumer_key",
    "consumer_secret",
    "bearer_token",
    "access_token",
    "access_token_secret",
]


@dataclass(frozen=True)
class TwitterCreds:
    consumer_key: str
    consumer_secret: str
    bearer_token: str
    access_token: str
    access_token_secret: str


def load_creds() -> TwitterCreds:
    """Load Twitter API credentials from ~/.birdview/credentials.json."""
    if not CREDS_FILE.exists():
        raise SystemExit(
            f"Credentials not found at {CREDS_FILE}\n\n"
            f"Run 'birdview init' to set up, or create the file manually:\n\n"
            f"  mkdir -p ~/.birdview\n"
            f"  cat > ~/.birdview/credentials.json << 'EOF'\n"
            f"  {{\n"
            f'    "consumer_key": "your_consumer_key",\n'
            f'    "consumer_secret": "your_consumer_secret",\n'
            f'    "bearer_token": "your_bearer_token",\n'
            f'    "access_token": "your_access_token",\n'
            f'    "access_token_secret": "your_access_token_secret"\n'
            f"  }}\n"
            f"  EOF\n"
        )

    with open(CREDS_FILE) as f:
        data = json.load(f)

    missing = [k for k in REQUIRED_KEYS if not data.get(k)]
    if missing:
        raise SystemExit(
            f"Missing keys in {CREDS_FILE}: {', '.join(missing)}\n"
            f"Required: {', '.join(REQUIRED_KEYS)}"
        )

    return TwitterCreds(
        consumer_key=data["consumer_key"],
        consumer_secret=data["consumer_secret"],
        bearer_token=data["bearer_token"],
        access_token=data["access_token"],
        access_token_secret=data["access_token_secret"],
    )


def save_creds(
    consumer_key: str,
    consumer_secret: str,
    bearer_token: str,
    access_token: str,
    access_token_secret: str,
) -> Path:
    """Save credentials to ~/.birdview/credentials.json."""
    ensure_app_dir()
    data = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "bearer_token": bearer_token,
        "access_token": access_token,
        "access_token_secret": access_token_secret,
    }
    with open(CREDS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    CREDS_FILE.chmod(0o600)  # owner-only read/write
    return CREDS_FILE


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
