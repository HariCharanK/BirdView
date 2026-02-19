"""Terminal rendering for tweets using rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns

from .client import Tweet


console = Console()


def _format_count(n: int) -> str:
    """Format large numbers: 1200 → 1.2K, 1500000 → 1.5M."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def render_tweet(tweet: Tweet, index: int | None = None, compact: bool = False) -> Panel:
    """Render a single tweet as a rich Panel."""
    # Header: @handle · age
    header = Text()
    if index is not None:
        header.append(f"[{index}] ", style="dim")
    if tweet.is_retweet and tweet.retweeted_by:
        header.append(f"🔁 @{tweet.retweeted_by} retweeted\n", style="dim italic")

    header.append(f"@{tweet.author_handle}", style="bold cyan")
    header.append(f" · {tweet.age}", style="dim")

    # Body
    body = Text(tweet.text)

    # Quoted tweet
    quote_section = None
    if tweet.quoted_tweet:
        qt = tweet.quoted_tweet
        qt_text = Text()
        qt_text.append(f"  @{qt.author_handle}", style="bold dim cyan")
        qt_text.append(f" · {qt.age}\n", style="dim")
        qt_text.append(f"  {qt.text[:200]}", style="dim")
        quote_section = Panel(qt_text, border_style="dim", padding=(0, 1))

    # URLs
    url_section = None
    if tweet.urls:
        url_text = Text()
        for u in tweet.urls[:3]:
            url_text.append(f"  🔗 {u}\n", style="blue underline")
        url_section = url_text

    # Metrics bar
    metrics = Text()
    metrics.append(f"♥ {_format_count(tweet.likes)}", style="red")
    metrics.append("  ")
    metrics.append(f"🔁 {_format_count(tweet.retweets)}", style="green")
    metrics.append("  ")
    metrics.append(f"💬 {_format_count(tweet.replies)}", style="blue")
    if tweet.quotes:
        metrics.append("  ")
        metrics.append(f"✍ {_format_count(tweet.quotes)}", style="yellow")

    # Assemble
    content = Text()
    content.append_text(header)
    content.append("\n")
    content.append_text(body)
    if quote_section:
        content.append("\n")
    if url_section:
        content.append("\n")
        content.append_text(url_section)
    content.append("\n")
    content.append_text(metrics)

    border = "dim blue" if not tweet.is_retweet else "dim green"
    if tweet.is_reply:
        border = "dim yellow"

    panel = Panel(
        content,
        border_style=border,
        padding=(0, 1),
        expand=True,
    )

    return panel


def render_tweet_list(tweets: list[Tweet], title: str = "") -> None:
    """Render a list of tweets to the console."""
    if not tweets:
        console.print("[dim]No tweets found.[/dim]")
        return

    if title:
        console.print(f"\n[bold]{title}[/bold]\n")

    for i, tweet in enumerate(tweets):
        console.print(render_tweet(tweet, index=i))


def render_user_header(info: dict) -> None:
    """Render a user profile header."""
    console.print()
    header = Text()
    header.append(f"  {info['name']}", style="bold")
    header.append(f"  @{info['username']}\n", style="cyan")
    header.append(f"  {_format_count(info['followers'])} followers", style="dim")
    header.append("  ·  ", style="dim")
    header.append(f"{_format_count(info['following'])} following", style="dim")
    header.append("  ·  ", style="dim")
    header.append(f"{_format_count(info['tweets'])} tweets", style="dim")

    console.print(Panel(header, border_style="cyan", padding=(0, 1)))


def render_bookmarks(bookmarks: list[dict]) -> None:
    """Render local bookmarks."""
    if not bookmarks:
        console.print("[dim]No bookmarks saved yet.[/dim]")
        return

    console.print(f"\n[bold]📑 Bookmarks ({len(bookmarks)})[/bold]\n")

    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Author", style="cyan", width=16)
    table.add_column("Tweet", ratio=1)
    table.add_column("Saved", style="dim", width=12)

    for i, b in enumerate(bookmarks):
        saved = b.get("saved_at", "")[:10]
        table.add_row(str(i), f"@{b['author']}", b["text"][:100], saved)

    console.print(table)


def render_help_bar() -> None:
    """Render the interactive help bar."""
    help_text = Text()
    help_text.append(" [b]b", style="yellow")
    help_text.append("ookmark  ", style="dim")
    help_text.append("[c]", style="yellow")
    help_text.append("opy link  ", style="dim")
    help_text.append("[o]", style="yellow")
    help_text.append("pen in browser  ", style="dim")
    help_text.append("[t]", style="yellow")
    help_text.append("hread  ", style="dim")
    help_text.append("[n/p]", style="yellow")
    help_text.append(" next/prev page  ", style="dim")
    help_text.append("[q]", style="yellow")
    help_text.append("uit", style="dim")
    console.print(Panel(help_text, border_style="dim"))
