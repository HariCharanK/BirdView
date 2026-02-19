"""Interactive tweet browser with keyboard controls."""

from __future__ import annotations

import os
import sys
import webbrowser
from typing import Callable, Optional

from rich.console import Console
from rich.prompt import Prompt

from .client import Tweet, BirdViewClient
from .config import save_bookmark, load_bookmarks, remove_bookmark
from .render import render_tweet, render_tweet_list, render_help_bar, render_bookmarks, console


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard. Returns True on success."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        # Fallback: try pbcopy (macOS) or xclip (Linux)
        try:
            if sys.platform == "darwin":
                os.popen("pbcopy", "w").write(text)
            else:
                os.popen("xclip -selection clipboard", "w").write(text)
            return True
        except Exception:
            return False


def browse_tweets(
    tweets: list[Tweet],
    title: str = "",
    client: Optional[BirdViewClient] = None,
    page_size: int = 10,
) -> None:
    """Interactive tweet browser with pagination and actions."""
    if not tweets:
        console.print("[dim]No tweets to display.[/dim]")
        return

    page = 0
    total_pages = (len(tweets) + page_size - 1) // page_size

    while True:
        console.clear()
        start = page * page_size
        end = min(start + page_size, len(tweets))
        page_tweets = tweets[start:end]

        # Title with page info
        page_title = title
        if total_pages > 1:
            page_title += f"  [dim](page {page + 1}/{total_pages})[/dim]"

        render_tweet_list(page_tweets, title=page_title)
        render_help_bar()

        # Prompt
        try:
            cmd = Prompt.ask(
                "[bold]>[/bold]",
                default="",
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if not cmd or cmd == "q":
            break

        # Navigation
        elif cmd == "n":
            if page < total_pages - 1:
                page += 1
            else:
                console.print("[dim]Already on last page.[/dim]")
        elif cmd == "p":
            if page > 0:
                page -= 1
            else:
                console.print("[dim]Already on first page.[/dim]")

        # Actions on a specific tweet by index
        elif cmd.startswith("b") or cmd.startswith("c") or cmd.startswith("o") or cmd.startswith("t"):
            action = cmd[0]
            rest = cmd[1:].strip()

            # Parse tweet index
            if not rest:
                rest = Prompt.ask("Tweet #", default="0")
            try:
                idx = int(rest)
            except ValueError:
                console.print("[red]Invalid tweet number.[/red]")
                _pause()
                continue

            # Map to absolute index
            abs_idx = start + idx
            if abs_idx < 0 or abs_idx >= len(tweets):
                console.print(f"[red]Tweet #{idx} not on this page.[/red]")
                _pause()
                continue

            tweet = tweets[abs_idx]

            if action == "b":
                save_bookmark(tweet.id, tweet.author_handle, tweet.text, tweet.url)
                console.print(f"[green]✓ Bookmarked @{tweet.author_handle}'s tweet[/green]")
                _pause()

            elif action == "c":
                if _copy_to_clipboard(tweet.url):
                    console.print(f"[green]✓ Copied: {tweet.url}[/green]")
                else:
                    console.print(f"[yellow]Link: {tweet.url}[/yellow]")
                    console.print("[dim](clipboard not available — copy manually)[/dim]")
                _pause()

            elif action == "o":
                console.print(f"[blue]Opening {tweet.url}...[/blue]")
                webbrowser.open(tweet.url)
                _pause()

            elif action == "t":
                if client:
                    console.print("[dim]Loading thread...[/dim]")
                    try:
                        thread_tweets = client.thread(tweet.id)
                        browse_tweets(
                            thread_tweets,
                            title=f"🧵 Thread from @{tweet.author_handle}",
                            client=client,
                            page_size=page_size,
                        )
                    except Exception as e:
                        console.print(f"[red]Error loading thread: {e}[/red]")
                        _pause()
                else:
                    console.print("[dim]Client not available for thread view.[/dim]")
                    _pause()

        # Direct number — show tweet detail
        elif cmd.isdigit():
            idx = int(cmd)
            abs_idx = start + idx
            if 0 <= abs_idx < len(tweets):
                tweet = tweets[abs_idx]
                console.clear()
                console.print(render_tweet(tweet))
                console.print(f"\n[dim]Link: {tweet.url}[/dim]")
                console.print(f"[dim]Tweet ID: {tweet.id}[/dim]")
                if tweet.conversation_id:
                    console.print(f"[dim]Conversation: {tweet.conversation_id}[/dim]")
                _pause()
            else:
                console.print(f"[red]Tweet #{idx} not on this page.[/red]")
                _pause()

        else:
            console.print(f"[dim]Unknown command: {cmd}[/dim]")
            _pause()


def _pause() -> None:
    """Wait for user to press Enter."""
    try:
        input("\nPress Enter to continue...")
    except (KeyboardInterrupt, EOFError):
        pass
