# 📸 Instagram Repost Bot

A DM-triggered Instagram bot that automatically reposts reels. Send a reel to the bot account via DM, and it downloads + reposts it — crediting the original creator.

## Setup

### 1. Clone & Install

```bash
cd instagram-repost-bot
pip install -r requirements.txt
```

### 2. Configure

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
IG_USERNAME=your_bot_account_username
IG_PASSWORD=your_bot_account_password
ALLOWED_SENDER=your_main_account_username
POLL_INTERVAL_SECONDS=60
```

| Variable | Description |
|---|---|
| `IG_USERNAME` | The bot account's Instagram username |
| `IG_PASSWORD` | The bot account's Instagram password |
| `ALLOWED_SENDER` | Your main account — only reels from this account trigger reposts |
| `POLL_INTERVAL_SECONDS` | How often to check DMs (default: 60 seconds) |

### 3. Run

```bash
python main.py
```

The bot will:
1. Log in to the bot account
2. Start monitoring DMs every 60 seconds
3. When you send a reel from your main account → it downloads and reposts it
4. Each repost includes `📸 Credit: @original_creator` in the caption

Press `Ctrl+C` to stop.

## How It Works

```
You (main account) → Send Reel via DM → Bot account detects it →
Downloads video → Re-uploads as Reel with credit → Done! 🎉
```

## Files

| File | Purpose |
|---|---|
| `main.py` | Main orchestrator & poll loop |
| `src/config.py` | Environment config loader |
| `src/auth.py` | Instagram login & session management |
| `src/dm_monitor.py` | DM inbox scanner for reel shares |
| `src/downloader.py` | Reel video downloader |
| `src/uploader.py` | Reel re-uploader with credit caption |
| `src/tracker.py` | Prevents duplicate reposts |

## Tips

- **First run**: Instagram may ask for 2FA or a challenge. The bot will prompt you interactively.
- **Session persistence**: After first login, session is saved to `session.json` so you don't re-login every time.
- **Rate limits**: The 60s poll interval is safe. Don't go below 30s.
- **Logs**: Check `bot.log` for a full history of what the bot did.
