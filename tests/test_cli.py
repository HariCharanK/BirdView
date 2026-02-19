"""Tests for CLI commands — click integration tests."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from click.testing import CliRunner

from birdview.cli import main
from birdview.client import Tweet


def _make_tweet(id="100", text="Hello world", handle="alice"):
    return Tweet(
        id=id,
        text=text,
        author_handle=handle,
        author_name=handle.title(),
        created_at=datetime.now(timezone.utc),
        likes=42,
        retweets=10,
        replies=5,
    )


@patch("birdview.cli._get_client")
def test_timeline_no_interactive(mock_client):
    client = MagicMock()
    client.me = MagicMock(username="testuser")
    client.timeline.return_value = [_make_tweet()]
    mock_client.return_value = client

    runner = CliRunner()
    result = runner.invoke(main, ["timeline", "--no-interactive"])
    assert result.exit_code == 0
    assert "Hello world" in result.output
    assert "alice" in result.output


@patch("birdview.cli._get_client")
def test_user_no_interactive(mock_client):
    client = MagicMock()
    client.get_user_info.return_value = {
        "username": "bob",
        "name": "Bob",
        "followers": 100,
        "following": 50,
        "tweets": 200,
    }
    client.user_tweets.return_value = [_make_tweet(handle="bob", text="Bob's tweet")]
    mock_client.return_value = client

    runner = CliRunner()
    result = runner.invoke(main, ["user", "bob", "--no-interactive"])
    assert result.exit_code == 0
    assert "Bob's tweet" in result.output


@patch("birdview.cli._get_client")
def test_search_no_interactive(mock_client):
    client = MagicMock()
    client.search.return_value = [_make_tweet(text="Found it")]
    mock_client.return_value = client

    runner = CliRunner()
    result = runner.invoke(main, ["search", "test query", "--no-interactive"])
    assert result.exit_code == 0
    assert "Found it" in result.output


def test_bookmarks_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("birdview.config.BOOKMARKS_FILE", tmp_path / "bm.json")
    runner = CliRunner()
    result = runner.invoke(main, ["bookmarks"])
    assert result.exit_code == 0
    assert "No bookmarks" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
