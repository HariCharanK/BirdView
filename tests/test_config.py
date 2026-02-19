"""Tests for config module — bookmarks and credential loading."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from birdview.config import (
    load_bookmarks,
    save_bookmark,
    remove_bookmark,
    load_creds,
    REQUIRED_KEYS,
)


@pytest.fixture
def tmp_bookmarks(tmp_path, monkeypatch):
    """Redirect bookmarks to a temp directory."""
    monkeypatch.setattr("birdview.config.APP_DIR", tmp_path)
    monkeypatch.setattr("birdview.config.BOOKMARKS_FILE", tmp_path / "bookmarks.json")
    return tmp_path / "bookmarks.json"


class TestBookmarks:
    def test_load_empty(self, tmp_bookmarks):
        assert load_bookmarks() == []

    def test_save_and_load(self, tmp_bookmarks):
        save_bookmark("111", "alice", "Hello world", "https://x.com/alice/status/111")
        bm = load_bookmarks()
        assert len(bm) == 1
        assert bm[0]["tweet_id"] == "111"
        assert bm[0]["author"] == "alice"
        assert bm[0]["url"] == "https://x.com/alice/status/111"

    def test_no_duplicates(self, tmp_bookmarks):
        save_bookmark("111", "alice", "Hello", "https://x.com/alice/status/111")
        save_bookmark("111", "alice", "Hello", "https://x.com/alice/status/111")
        assert len(load_bookmarks()) == 1

    def test_multiple_bookmarks(self, tmp_bookmarks):
        save_bookmark("111", "alice", "Hello", "https://x.com/alice/status/111")
        save_bookmark("222", "bob", "World", "https://x.com/bob/status/222")
        assert len(load_bookmarks()) == 2

    def test_remove(self, tmp_bookmarks):
        save_bookmark("111", "alice", "Hello", "https://x.com/alice/status/111")
        save_bookmark("222", "bob", "World", "https://x.com/bob/status/222")
        assert remove_bookmark("111") is True
        bm = load_bookmarks()
        assert len(bm) == 1
        assert bm[0]["tweet_id"] == "222"

    def test_remove_nonexistent(self, tmp_bookmarks):
        assert remove_bookmark("999") is False

    def test_text_truncation(self, tmp_bookmarks):
        long_text = "x" * 500
        save_bookmark("111", "alice", long_text, "https://x.com/alice/status/111")
        bm = load_bookmarks()
        assert len(bm[0]["text"]) == 280


class TestCredentials:
    def test_missing_creds_exits(self, monkeypatch):
        # Clear all env vars
        for key in REQUIRED_KEYS:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setattr("birdview.config.load_dotenv", lambda *a, **kw: None)

        with pytest.raises(SystemExit):
            load_creds()

    def test_loads_from_env(self, monkeypatch):
        monkeypatch.setattr("birdview.config.load_dotenv", lambda *a, **kw: None)
        monkeypatch.setenv("TWITTER_CONSUMER_KEY", "ck")
        monkeypatch.setenv("TWITTER_CONSUMER_SECRET", "cs")
        monkeypatch.setenv("TWITTER_BEARER_TOKEN", "bt")
        monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "at")
        monkeypatch.setenv("TWITTER_ACCESS_TOKEN_SECRET", "ats")

        creds = load_creds()
        assert creds.consumer_key == "ck"
        assert creds.bearer_token == "bt"
