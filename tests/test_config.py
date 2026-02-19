"""Tests for config module — bookmarks and credential loading."""

import json
import os
from pathlib import Path

import pytest

from birdview.config import (
    load_bookmarks,
    save_bookmark,
    remove_bookmark,
    load_creds,
    save_creds,
    REQUIRED_KEYS,
)


@pytest.fixture
def tmp_bookmarks(tmp_path, monkeypatch):
    """Redirect bookmarks to a temp directory."""
    monkeypatch.setattr("birdview.config.APP_DIR", tmp_path)
    monkeypatch.setattr("birdview.config.BOOKMARKS_FILE", tmp_path / "bookmarks.json")
    return tmp_path / "bookmarks.json"


@pytest.fixture
def tmp_creds(tmp_path, monkeypatch):
    """Redirect credentials to a temp directory."""
    monkeypatch.setattr("birdview.config.APP_DIR", tmp_path)
    monkeypatch.setattr("birdview.config.CREDS_FILE", tmp_path / "credentials.json")
    return tmp_path / "credentials.json"


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
    def test_missing_file_exits(self, tmp_creds):
        with pytest.raises(SystemExit) as exc_info:
            load_creds()
        assert "Credentials not found" in str(exc_info.value)

    def test_missing_keys_exits(self, tmp_creds):
        tmp_creds.write_text(json.dumps({"consumer_key": "ck"}))
        with pytest.raises(SystemExit) as exc_info:
            load_creds()
        assert "Missing keys" in str(exc_info.value)

    def test_loads_from_file(self, tmp_creds):
        data = {
            "consumer_key": "ck",
            "consumer_secret": "cs",
            "bearer_token": "bt",
            "access_token": "at",
            "access_token_secret": "ats",
        }
        tmp_creds.write_text(json.dumps(data))
        creds = load_creds()
        assert creds.consumer_key == "ck"
        assert creds.bearer_token == "bt"

    def test_save_and_load(self, tmp_creds, monkeypatch):
        path = save_creds("ck", "cs", "bt", "at", "ats")
        assert path.exists()
        assert oct(path.stat().st_mode)[-3:] == "600"
        creds = load_creds()
        assert creds.consumer_key == "ck"
        assert creds.access_token_secret == "ats"
