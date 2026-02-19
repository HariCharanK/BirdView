# 🐦 BirdView

Minimal terminal Twitter/X client. Read-only, interactive, no bloat.

## Install

```bash
pip install -e .
```

## Setup

```bash
birdview init
```

This prompts for your Twitter API credentials and saves them to
`~/.birdview/credentials.json` (owner-only permissions).

Or create the file manually:

```bash
mkdir -p ~/.birdview
cat > ~/.birdview/credentials.json << 'EOF'
{
  "consumer_key": "your_consumer_key",
  "consumer_secret": "your_consumer_secret",
  "bearer_token": "your_bearer_token",
  "access_token": "your_access_token",
  "access_token_secret": "your_access_token_secret"
}
EOF
chmod 600 ~/.birdview/credentials.json
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
