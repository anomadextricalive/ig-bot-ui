"""
DM monitoring module using Playwright browser automation.
Scans the bot account's inbox for shared reels.
"""

import json
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


def fetch_new_reel_shares(page, allowed_sender: str, tracker) -> List[Dict]:
    """
    Check the DM inbox for new reel shares from the allowed sender.
    Uses the Instagram web API via browser fetch requests.
    
    Returns a list of dicts with:
      - message_id: str
      - media_id: str (the reel media ID)
      - reel_url: str (direct link to the reel)
    """
    new_reels = []

    try:
        # Use Instagram's web API to fetch DM inbox
        logger.info("  Fetching DM inbox...")
        inbox_data = page.evaluate("""
            async () => {
                try {
                    const resp = await fetch('/api/v1/direct_v2/inbox/?persistentBadging=true&folder=&limit=20&thread_message_limit=10', {
                        headers: {
                            'x-ig-app-id': '936619743392459',
                            'x-requested-with': 'XMLHttpRequest',
                        },
                        credentials: 'include',
                    });
                    return await resp.json();
                } catch(e) {
                    return {error: e.message};
                }
            }
        """)

        if not inbox_data or "error" in inbox_data:
            logger.error(f"  Failed to fetch inbox: {inbox_data}")
            return []

        inbox = inbox_data.get("inbox", {})
        threads = inbox.get("threads", [])
        logger.info(f"  Found {len(threads)} DM threads.")

        for thread in threads:
            # Get users in this thread
            users = thread.get("users", [])
            usernames = [u.get("username", "").lower() for u in users]

            # Only process threads with the allowed sender
            if allowed_sender.lower() not in usernames:
                continue

            items = thread.get("items", [])
            for item in items:
                item_id = item.get("item_id", "")

                # Skip already processed
                if tracker.is_processed(item_id):
                    continue

                # Check for media share (reel/post shared via DM)
                reel_info = _extract_reel_from_item(item)
                if reel_info:
                    logger.info(f"  🎬 Found reel share! Item: {item_id}")
                    new_reels.append({
                        "message_id": item_id,
                        "media_id": reel_info.get("media_id", ""),
                        "reel_url": reel_info.get("reel_url", ""),
                        "shortcode": reel_info.get("shortcode", ""),
                    })
                else:
                    # Not a reel — mark as processed
                    tracker.mark_processed(item_id)

    except Exception as e:
        logger.error(f"  Error fetching DM inbox: {e}")

    return new_reels


def _extract_reel_from_item(item: dict) -> dict:
    """
    Extract reel info from a DM item if it contains a shared reel.
    
    DM items with shared media have item_type = "media_share" or "clip".
    """
    item_type = item.get("item_type", "")

    # media_share — shared post or reel
    if item_type == "media_share":
        media = item.get("media_share", {})
        if not media:
            return None
        media_type = media.get("media_type", 0)
        product_type = media.get("product_type", "")

        # media_type 2 = video, product_type "clips" = reel
        if media_type == 2 or product_type == "clips":
            code = media.get("code", "")
            pk = media.get("pk", "")
            return {
                "media_id": str(pk),
                "reel_url": f"https://www.instagram.com/reel/{code}/" if code else "",
                "shortcode": code,
            }

    # clip — dedicated reel share
    if item_type == "clip":
        clip = item.get("clip", {})
        clip_media = clip.get("clip", {})
        if not clip_media:
            clip_media = clip
        code = clip_media.get("code", "")
        pk = clip_media.get("pk", "")
        return {
            "media_id": str(pk),
            "reel_url": f"https://www.instagram.com/reel/{code}/" if code else "",
            "shortcode": code,
        }

    # felix_share — IGTV/reel
    if item_type == "felix_share":
        felix = item.get("felix_share", {})
        video = felix.get("video", {})
        code = video.get("code", "")
        pk = video.get("pk", "")
        return {
            "media_id": str(pk),
            "reel_url": f"https://www.instagram.com/reel/{code}/" if code else "",
            "shortcode": code,
        }

    return None
