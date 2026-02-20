"""Twitter API wrapper — read-only operations."""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import tweepy

from .config import TwitterCreds

# Standard tweet fields to request from API
TWEET_FIELDS = [
    "created_at",
    "public_metrics",
    "conversation_id",
    "referenced_tweets",
    "entities",
    "in_reply_to_user_id",
    "note_tweet",
]
USER_FIELDS = ["username", "name", "public_metrics", "profile_image_url"]
EXPANSIONS = [
    "author_id",
    "referenced_tweets.id",
    "referenced_tweets.id.author_id",
]


@dataclass
class Tweet:
    """Normalized tweet object for rendering."""

    id: str
    text: str
    author_handle: str
    author_name: str
    created_at: Optional[datetime]
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    is_retweet: bool = False
    is_reply: bool = False
    is_quote: bool = False
    retweeted_by: Optional[str] = None
    quoted_tweet: Optional["Tweet"] = None
    conversation_id: Optional[str] = None
    urls: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"https://x.com/{self.author_handle}/status/{self.id}"

    @property
    def age(self) -> str:
        if not self.created_at:
            return ""
        from datetime import timezone

        delta = datetime.now(timezone.utc) - self.created_at
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs}s"
        mins = secs // 60
        if mins < 60:
            return f"{mins}m"
        hours = mins // 60
        if hours < 24:
            return f"{hours}h"
        days = hours // 24
        if days < 30:
            return f"{days}d"
        return self.created_at.strftime("%b %d")


class BirdViewClient:
    """Read-only Twitter API client."""

    def __init__(self, creds: TwitterCreds) -> None:
        # Client with both auth methods — tweepy picks the right one
        self._client = tweepy.Client(
            consumer_key=creds.consumer_key,
            consumer_secret=creds.consumer_secret,
            access_token=creds.access_token,
            access_token_secret=creds.access_token_secret,
            bearer_token=creds.bearer_token,
            wait_on_rate_limit=True,
        )
        self._me: tweepy.User | None = None

    @property
    def me(self) -> tweepy.User:
        if self._me is None:
            resp = self._client.get_me(user_fields=USER_FIELDS)
            self._me = resp.data
        return self._me

    @staticmethod
    def _full_text(tweet) -> str:
        """Extract full text, preferring note_tweet for long posts."""
        note = getattr(tweet, "note_tweet", None)
        if note and isinstance(note, dict) and note.get("text"):
            text = note["text"]
        else:
            text = tweet.text
        return html.unescape(text)

    def _parse_tweets(self, response: tweepy.Response) -> list[Tweet]:
        """Parse a tweepy Response into a list of Tweet objects."""
        if not response.data:
            return []

        users = {}
        ref_tweets = {}
        if response.includes:
            for u in response.includes.get("users", []):
                users[u.id] = u
            for t in response.includes.get("tweets", []):
                ref_tweets[t.id] = t

        # Handle single tweet responses (e.g., get_tweet)
        data = response.data
        if not isinstance(data, list):
            data = [data]

        tweets = []
        for t in data:
            author = users.get(t.author_id)
            handle = author.username if author else "unknown"
            name = author.name if author else "Unknown"

            metrics = t.public_metrics or {}
            refs = t.referenced_tweets or []

            is_rt = any(r.type == "retweeted" for r in refs)
            is_reply = any(r.type == "replied_to" for r in refs)
            is_quote = any(r.type == "quoted" for r in refs)

            # For retweets, get the original tweet's author
            retweeted_by = None
            actual_text = self._full_text(t)
            actual_handle = handle
            actual_name = name
            actual_metrics = metrics
            actual_id = str(t.id)
            actual_created = t.created_at

            if is_rt:
                retweeted_by = handle
                rt_ref = next((r for r in refs if r.type == "retweeted"), None)
                if rt_ref and rt_ref.id in ref_tweets:
                    orig = ref_tweets[rt_ref.id]
                    orig_author = users.get(orig.author_id)
                    if orig_author:
                        actual_handle = orig_author.username
                        actual_name = orig_author.name
                    actual_text = self._full_text(orig)
                    actual_metrics = orig.public_metrics or metrics
                    actual_id = str(orig.id)
                    actual_created = orig.created_at or t.created_at

            # Extract URLs from entities
            urls = []
            if t.entities and "urls" in t.entities:
                for u in t.entities["urls"]:
                    expanded = u.get("expanded_url", u.get("url", ""))
                    # Skip t.co self-referencing URLs
                    if "twitter.com" not in expanded and "x.com" not in expanded:
                        urls.append(expanded)

            # Handle quoted tweet
            quoted_tweet = None
            if is_quote:
                qt_ref = next((r for r in refs if r.type == "quoted"), None)
                if qt_ref and qt_ref.id in ref_tweets:
                    qt = ref_tweets[qt_ref.id]
                    qt_author = users.get(qt.author_id)
                    quoted_tweet = Tweet(
                        id=str(qt.id),
                        text=self._full_text(qt),
                        author_handle=qt_author.username if qt_author else "unknown",
                        author_name=qt_author.name if qt_author else "Unknown",
                        created_at=qt.created_at,
                        likes=(qt.public_metrics or {}).get("like_count", 0),
                        retweets=(qt.public_metrics or {}).get("retweet_count", 0),
                        replies=(qt.public_metrics or {}).get("reply_count", 0),
                    )

            tweets.append(
                Tweet(
                    id=actual_id,
                    text=actual_text,
                    author_handle=actual_handle,
                    author_name=actual_name,
                    created_at=actual_created,
                    likes=actual_metrics.get("like_count", 0),
                    retweets=actual_metrics.get("retweet_count", 0),
                    replies=actual_metrics.get("reply_count", 0),
                    quotes=actual_metrics.get("quote_count", 0),
                    is_retweet=is_rt,
                    is_reply=is_reply,
                    is_quote=is_quote,
                    retweeted_by=retweeted_by,
                    quoted_tweet=quoted_tweet,
                    conversation_id=str(t.conversation_id) if t.conversation_id else None,
                    urls=urls,
                )
            )

        return tweets

    def timeline(self, count: int = 20) -> list[Tweet]:
        """Get home timeline (reverse chronological)."""
        resp = self._client.get_home_timeline(
            max_results=min(count, 100),
            tweet_fields=TWEET_FIELDS,
            expansions=EXPANSIONS,
            user_fields=USER_FIELDS,
        )
        return self._parse_tweets(resp)

    def user_tweets(self, username: str, count: int = 20) -> list[Tweet]:
        """Get a user's recent tweets."""
        user_resp = self._client.get_user(username=username, user_fields=USER_FIELDS)
        if not user_resp.data:
            raise ValueError(f"User @{username} not found")

        resp = self._client.get_users_tweets(
            id=user_resp.data.id,
            max_results=min(count, 100),
            tweet_fields=TWEET_FIELDS,
            expansions=EXPANSIONS,
            user_fields=USER_FIELDS,
        )
        return self._parse_tweets(resp)

    def search(self, query: str, count: int = 20) -> list[Tweet]:
        """Search recent tweets."""
        resp = self._client.search_recent_tweets(
            query=query,
            max_results=max(10, min(count, 100)),
            tweet_fields=TWEET_FIELDS,
            expansions=EXPANSIONS,
            user_fields=USER_FIELDS,
        )
        return self._parse_tweets(resp)

    def thread(self, tweet_id: str) -> list[Tweet]:
        """Get a tweet and its reply thread."""
        # 1. Get the root tweet
        root_resp = self._client.get_tweet(
            id=tweet_id,
            tweet_fields=TWEET_FIELDS,
            expansions=EXPANSIONS,
            user_fields=USER_FIELDS,
        )
        root_tweets = self._parse_tweets(root_resp)

        # 2. Get the conversation (replies)
        conv_id = root_resp.data.conversation_id if root_resp.data else tweet_id
        try:
            replies_resp = self._client.search_recent_tweets(
                query=f"conversation_id:{conv_id}",
                max_results=100,
                tweet_fields=TWEET_FIELDS,
                expansions=EXPANSIONS,
                user_fields=USER_FIELDS,
            )
            reply_tweets = self._parse_tweets(replies_resp)
        except Exception:
            reply_tweets = []

        # Combine: root first, then replies sorted by time
        all_tweets = root_tweets + sorted(
            reply_tweets,
            key=lambda t: t.created_at or datetime.min.replace(
                tzinfo=__import__("datetime").timezone.utc
            ),
        )

        return all_tweets

    def get_user_info(self, username: str) -> dict:
        """Get user profile info."""
        resp = self._client.get_user(username=username, user_fields=USER_FIELDS)
        if not resp.data:
            raise ValueError(f"User @{username} not found")
        u = resp.data
        return {
            "username": u.username,
            "name": u.name,
            "followers": u.public_metrics["followers_count"],
            "following": u.public_metrics["following_count"],
            "tweets": u.public_metrics["tweet_count"],
        }
