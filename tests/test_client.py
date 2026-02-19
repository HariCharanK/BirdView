"""Tests for client module — tweet parsing and data normalization."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from birdview.client import Tweet, BirdViewClient


class TestTweet:
    def test_url(self):
        t = Tweet(
            id="123",
            text="Hello",
            author_handle="alice",
            author_name="Alice",
            created_at=None,
        )
        assert t.url == "https://x.com/alice/status/123"

    def test_age_seconds(self):
        now = datetime.now(timezone.utc)
        t = Tweet(id="1", text="", author_handle="a", author_name="A", created_at=now)
        assert t.age in ("0s", "1s", "2s")

    def test_age_minutes(self):
        from datetime import timedelta

        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        t = Tweet(id="1", text="", author_handle="a", author_name="A", created_at=past)
        assert t.age == "5m"

    def test_age_hours(self):
        from datetime import timedelta

        past = datetime.now(timezone.utc) - timedelta(hours=3)
        t = Tweet(id="1", text="", author_handle="a", author_name="A", created_at=past)
        assert t.age == "3h"

    def test_age_days(self):
        from datetime import timedelta

        past = datetime.now(timezone.utc) - timedelta(days=7)
        t = Tweet(id="1", text="", author_handle="a", author_name="A", created_at=past)
        assert t.age == "7d"

    def test_age_none(self):
        t = Tweet(id="1", text="", author_handle="a", author_name="A", created_at=None)
        assert t.age == ""


class TestParseTweets:
    def _make_user(self, id, username, name):
        u = MagicMock()
        u.id = id
        u.username = username
        u.name = name
        return u

    def _make_tweet_data(self, id, text, author_id, **kwargs):
        t = MagicMock()
        t.id = id
        t.text = text
        t.author_id = author_id
        t.created_at = kwargs.get("created_at")
        t.public_metrics = kwargs.get("public_metrics", {"like_count": 0, "retweet_count": 0, "reply_count": 0, "quote_count": 0})
        t.referenced_tweets = kwargs.get("referenced_tweets", [])
        t.entities = kwargs.get("entities")
        t.conversation_id = kwargs.get("conversation_id", id)
        return t

    def _make_response(self, data, users=None, tweets=None):
        resp = MagicMock()
        resp.data = data
        resp.includes = {}
        if users:
            resp.includes["users"] = users
        if tweets:
            resp.includes["tweets"] = tweets
        return resp

    def test_parse_basic_tweet(self):
        user = self._make_user(1, "alice", "Alice")
        tweet = self._make_tweet_data(100, "Hello world", 1)
        resp = self._make_response([tweet], users=[user])

        creds = MagicMock()
        client = BirdViewClient.__new__(BirdViewClient)
        result = client._parse_tweets(resp)

        assert len(result) == 1
        assert result[0].text == "Hello world"
        assert result[0].author_handle == "alice"
        assert result[0].is_retweet is False

    def test_parse_retweet(self):
        user_a = self._make_user(1, "alice", "Alice")
        user_b = self._make_user(2, "bob", "Bob")

        # Original tweet
        orig_tweet = self._make_tweet_data(200, "Original text", 2)

        # Retweet reference
        ref = MagicMock()
        ref.type = "retweeted"
        ref.id = 200

        rt = self._make_tweet_data(100, "RT @bob: Original text", 1, referenced_tweets=[ref])
        resp = self._make_response([rt], users=[user_a, user_b], tweets=[orig_tweet])

        client = BirdViewClient.__new__(BirdViewClient)
        result = client._parse_tweets(resp)

        assert len(result) == 1
        assert result[0].is_retweet is True
        assert result[0].retweeted_by == "alice"
        assert result[0].author_handle == "bob"
        assert result[0].text == "Original text"

    def test_parse_empty_response(self):
        resp = MagicMock()
        resp.data = None
        client = BirdViewClient.__new__(BirdViewClient)
        assert client._parse_tweets(resp) == []

    def test_parse_single_tweet(self):
        """get_tweet returns a single object, not a list."""
        user = self._make_user(1, "alice", "Alice")
        tweet = self._make_tweet_data(100, "Single tweet", 1)
        resp = self._make_response(tweet, users=[user])  # single, not list

        client = BirdViewClient.__new__(BirdViewClient)
        result = client._parse_tweets(resp)
        assert len(result) == 1
        assert result[0].text == "Single tweet"

    def test_parse_urls(self):
        user = self._make_user(1, "alice", "Alice")
        entities = {
            "urls": [
                {"expanded_url": "https://example.com/article"},
                {"expanded_url": "https://x.com/alice/status/100"},  # self-ref, should be filtered
            ]
        }
        tweet = self._make_tweet_data(100, "Check this out", 1, entities=entities)
        resp = self._make_response([tweet], users=[user])

        client = BirdViewClient.__new__(BirdViewClient)
        result = client._parse_tweets(resp)
        assert result[0].urls == ["https://example.com/article"]
