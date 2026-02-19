# 🐦 BirdView

Minimal terminal Twitter/X client. Read-only, interactive, no bloat.

## Install

```bash
pip install -e .
```

## Setup

Create `~/.env` with your Twitter API credentials:

```env
TWITTER_CONSUMER_KEY=your_key
TWITTER_CONSUMER_SECRET=your_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

## Usage

```bash
# Home timeline (interactive)
birdview timeline

# User's tweets
birdview user @elonmusk

# Search
birdview search "python programming"

# View a thread
birdview thread 1234567890

# Local bookmarks
birdview bookmarks

# Who am I?
birdview whoami
```

## Interactive Controls

When viewing tweets, you can:

| Key | Action |
|-----|--------|
| `<number>` | View tweet detail |
| `b<number>` | Bookmark tweet |
| `c<number>` | Copy tweet link |
| `o<number>` | Open in browser |
| `t<number>` | View thread |
| `n` / `p` | Next / previous page |
| `q` | Quit |

## Bookmarks

Bookmarks are stored locally at `~/.birdview/bookmarks.json`. No Twitter API
bookmark permissions needed.

```bash
birdview bookmarks          # View all
birdview bookmarks -r 0     # Remove bookmark #0
```

## Requirements

- Python 3.10+
- Twitter API credentials (Basic tier recommended for home timeline)
