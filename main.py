#!/usr/bin/env python3
"""
Instagram Repost Bot — Main Orchestrator (Playwright Edition)

Monitors DMs for shared reels from an allowed sender,
downloads them, and reposts them on the bot account.

Uses browser automation to avoid Instagram API challenges.

Usage:
    1. Copy .env.example to .env and fill in credentials
    2. pip install -r requirements.txt && python -m playwright install chromium
    3. python main.py
"""

import logging
import signal
import sys
import time

from playwright.sync_api import sync_playwright

from src.config import load_config
from src.auth import create_browser_context, login_if_needed
from src.tracker import Tracker
from src.dm_monitor import fetch_new_reel_shares
from src.downloader import download_reel, cleanup_file
from src.uploader import build_caption, upload_reel
from src.webhook import init_webhook, report_progress

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Graceful shutdown
# ──────────────────────────────────────────────

running = True


def shutdown_handler(sig, frame):
    global running
    logger.info("\n🛑 Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# ──────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────


def main():
    global running

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   📸 Instagram Repost Bot v1.0       ║")
    print("  ║   DM-triggered reel reposter         ║")
    print("  ║   (Playwright Edition)               ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    # Load config
    config = load_config()
    logger.info(f"⚙️  Bot account: @{config['username']}")
    logger.info(f"⚙️  Allowed sender: @{config['allowed_sender']}")
    logger.info(f"⚙️  Poll interval: {config['poll_interval']}s")

    init_webhook()
    report_progress('idle', 'Warming up browser...')

    with sync_playwright() as pw:
        # Create persistent browser context
        logger.info("🌐 Launching browser...")
        context = create_browser_context(pw, headless=True)

        # Login
        page = login_if_needed(context, config["username"], config["password"])

        # Navigate to Instagram home to be ready
        page.goto("https://www.instagram.com/", wait_until="load", timeout=30000)
        page.wait_for_timeout(2000)

        # Initialize tracker
        tracker = Tracker()

        logger.info("")
        logger.info("🚀 Bot is running! Monitoring DMs for reel shares...")
        logger.info("   Press Ctrl+C to stop.")
        logger.info("")
        report_progress('idle', 'Monitoring DMs for reel shares...')

        poll_count = 0

        while running:
            poll_count += 1
            logger.info(f"── Poll #{poll_count} ──────────────────────────")

            try:
                # 1. Check for new reel shares
                new_reels = fetch_new_reel_shares(page, config["allowed_sender"], tracker)

                if not new_reels:
                    logger.info("   No new reel shares found.")
                else:
                    logger.info(f"   Found {len(new_reels)} new reel(s) to process!")

                    for i, reel_data in enumerate(new_reels, 1):
                        logger.info(f"\n   ━━━ Processing reel {i}/{len(new_reels)} ━━━")

                        message_id = reel_data["message_id"]
                        shortcode = reel_data.get("shortcode", "")
                        media_id = reel_data.get("media_id", "")

                        if not shortcode and not media_id:
                            logger.error("   No shortcode or media_id — skipping.")
                            tracker.mark_processed(message_id)
                            continue

                        # 2. Download the reel
                        report_progress('downloading', f'Fetching reel info...', reel_id=message_id, sender=config['allowed_sender'])
                        result = download_reel(page, shortcode, media_id)

                        if not result:
                            logger.error("   Skipping reel (download failed).")
                            tracker.mark_processed(message_id)
                            continue

                        # 3. Build caption with credit
                        caption = build_caption(
                            original_caption=result["caption"],
                            creator_username=result["creator_username"],
                        )

                        # 4. Upload as reel on bot account
                        report_progress('uploading', 'Uploading and processing video...', reel_id=message_id, sender=config['allowed_sender'])
                        success = upload_reel(page, result["video_path"], caption)

                        # 5. Mark as processed
                        tracker.mark_processed(message_id)

                        if success:
                            logger.info("   🎉 Reel reposted successfully!")
                            report_progress('completed', 'Reel reposted successfully!', reel_id=message_id, sender=config['allowed_sender'])
                        else:
                            logger.error("   ❌ Failed to repost reel.")
                            report_progress('error', 'Failed to repost reel.', reel_id=message_id, sender=config['allowed_sender'])

                        # 6. Clean up
                        cleanup_file(result["video_path"])

                        # Navigate back home for next iteration
                        page.goto("https://www.instagram.com/", wait_until="load", timeout=30000)
                        page.wait_for_timeout(2000)

                        # Small delay between multiple reposts
                        if i < len(new_reels):
                            logger.info("   ⏳ Waiting 10s before next reel...")
                            time.sleep(10)

            except Exception as e:
                logger.error(f"❌ Error during poll: {e}", exc_info=True)
                report_progress('error', f'Error during poll: {str(e)[:50]}...', sender=config['allowed_sender'])

                # Try to recover by navigating home
                try:
                    page.goto("https://www.instagram.com/", wait_until="load", timeout=30000)
                except Exception:
                    pass

            # Wait before next poll
            if running:
                logger.info(f"\n   💤 Sleeping {config['poll_interval']}s until next poll...\n")
                if poll_count % 5 == 0:
                    report_progress('idle', f'Sleeping {config["poll_interval"]}s... (Poll #{poll_count})')
                for _ in range(config["poll_interval"]):
                    if not running:
                        break
                    time.sleep(1)

        # Cleanup
        logger.info("Closing browser...")
        context.close()

    logger.info("👋 Bot stopped. Goodbye!")


if __name__ == "__main__":
    main()
