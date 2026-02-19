"""BirdView CLI — minimal terminal Twitter/X client."""

from __future__ import annotations

import click
from rich.console import Console

from . import __version__
from .config import load_creds, load_bookmarks, remove_bookmark, save_creds
from .client import BirdViewClient
from .render import (
    render_tweet_list,
    render_user_header,
    render_bookmarks,
    console,
)
from .interactive import browse_tweets

# Lazy-init client (avoids loading creds for --help)
_client: BirdViewClient | None = None


def _get_client() -> BirdViewClient:
    global _client
    if _client is None:
        creds = load_creds()
        _client = BirdViewClient(creds)
    return _client


@click.group()
@click.version_option(version=__version__, prog_name="birdview")
def main():
    """🐦 BirdView — Minimal terminal Twitter/X client."""
    pass


@main.command()
def init():
    """Set up Twitter API credentials (interactive)."""
    console.print("[bold]🐦 BirdView Setup[/bold]\n")
    console.print("Enter your Twitter/X API credentials.\n")

    consumer_key = click.prompt("Consumer Key")
    consumer_secret = click.prompt("Consumer Secret")
    bearer_token = click.prompt("Bearer Token")
    access_token = click.prompt("Access Token")
    access_token_secret = click.prompt("Access Token Secret")

    path = save_creds(consumer_key, consumer_secret, bearer_token, access_token, access_token_secret)
    console.print(f"\n[green]✓ Credentials saved to {path}[/green]")
    console.print("[dim]File permissions set to owner-only (600).[/dim]")
    console.print("\nTry: [bold]birdview whoami[/bold]")


@main.command()
@click.option("-n", "--count", default=20, help="Number of tweets to fetch.")
@click.option("--no-interactive", is_flag=True, help="Disable interactive mode.")
def timeline(count: int, no_interactive: bool):
    """View your home timeline."""
    client = _get_client()
    me = client.me
    console.print(f"[dim]Logged in as @{me.username}[/dim]")
    console.print("[dim]Loading timeline...[/dim]")

    tweets = client.timeline(count=count)
    if no_interactive:
        render_tweet_list(tweets, title="🏠 Home Timeline")
    else:
        browse_tweets(tweets, title="🏠 Home Timeline", client=client)


@main.command()
@click.argument("username")
@click.option("-n", "--count", default=20, help="Number of tweets to fetch.")
@click.option("--no-interactive", is_flag=True, help="Disable interactive mode.")
def user(username: str, count: int, no_interactive: bool):
    """View a user's recent tweets."""
    username = username.lstrip("@")
    client = _get_client()
    console.print(f"[dim]Loading @{username}...[/dim]")

    try:
        info = client.get_user_info(username)
        render_user_header(info)
    except Exception:
        pass  # Continue even if header fails

    tweets = client.user_tweets(username, count=count)
    if no_interactive:
        render_tweet_list(tweets, title=f"@{username}")
    else:
        browse_tweets(tweets, title=f"📝 @{username}", client=client)


@main.command()
@click.argument("tweet_id")
def thread(tweet_id: str):
    """View a tweet thread/conversation."""
    client = _get_client()
    console.print("[dim]Loading thread...[/dim]")

    tweets = client.thread(tweet_id)
    browse_tweets(tweets, title="🧵 Thread", client=client)


@main.command()
@click.argument("query")
@click.option("-n", "--count", default=20, help="Number of results.")
@click.option("--no-interactive", is_flag=True, help="Disable interactive mode.")
def search(query: str, count: int, no_interactive: bool):
    """Search recent tweets."""
    client = _get_client()
    console.print(f'[dim]Searching: "{query}"...[/dim]')

    tweets = client.search(query, count=count)
    if no_interactive:
        render_tweet_list(tweets, title=f'🔍 "{query}"')
    else:
        browse_tweets(tweets, title=f'🔍 "{query}"', client=client)


@main.command()
@click.option("--remove", "-r", type=int, help="Remove bookmark by index number.")
def bookmarks(remove: int | None):
    """View or manage local bookmarks."""
    if remove is not None:
        bm = load_bookmarks()
        if 0 <= remove < len(bm):
            entry = bm[remove]
            remove_bookmark(entry["tweet_id"])
            console.print(f"[green]✓ Removed bookmark #{remove}[/green]")
        else:
            console.print(f"[red]Invalid bookmark index: {remove}[/red]")
        return

    bm = load_bookmarks()
    render_bookmarks(bm)


@main.command()
def whoami():
    """Show authenticated user info."""
    client = _get_client()
    me = client.me
    info = {
        "username": me.username,
        "name": me.name,
        "followers": me.public_metrics["followers_count"],
        "following": me.public_metrics["following_count"],
        "tweets": me.public_metrics["tweet_count"],
    }
    render_user_header(info)


if __name__ == "__main__":
    main()
