"""
Reel downloader module using Playwright.
Downloads reel video files and extracts metadata.
"""

import json
import logging
import os
import re
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = "downloads"


def ensure_downloads_dir():
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def download_reel(page, shortcode: str, media_id: str = "") -> Optional[Dict]:
    """
    Download a reel by navigating to it and extracting the video URL.
    
    Returns dict with video_path, caption, creator_username, or None on failure.
    """
    ensure_downloads_dir()

    try:
        reel_url = f"https://www.instagram.com/reel/{shortcode}/"
        logger.info(f"  📥 Fetching reel info: {reel_url}")

        # Use Instagram's web API to get media info
        media_info = page.evaluate("""
            async (shortcode) => {
                try {
                    const resp = await fetch(`/api/v1/media/${shortcode}/info/`, {
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
        """, shortcode)

        # Try alternative endpoint if media_id is available
        if (not media_info or "error" in media_info or "items" not in media_info) and media_id:
            logger.info("  Trying alternative API endpoint...")
            media_info = page.evaluate("""
                async (mediaId) => {
                    try {
                        const resp = await fetch(`/api/v1/media/${mediaId}/info/`, {
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
            """, media_id)

        if not media_info or "items" not in media_info or not media_info["items"]:
            logger.error(f"  ❌ Could not fetch media info for {shortcode}")

            # Fallback: try to scrape the video URL from the page
            return _download_reel_from_page(page, reel_url, shortcode)

        item = media_info["items"][0]
        
        # Extract creator info
        user = item.get("user", {})
        creator_username = user.get("username", "unknown")
        caption_data = item.get("caption", {}) or {}
        original_caption = caption_data.get("text", "") if isinstance(caption_data, dict) else ""

        logger.info(f"  Creator: @{creator_username}")

        # Get video URL
        video_versions = item.get("video_versions", [])
        if not video_versions:
            logger.error("  ❌ No video versions found in media info.")
            return None

        # Pick the best quality video
        video_url = video_versions[0].get("url", "")
        if not video_url:
            logger.error("  ❌ No video URL found.")
            return None

        # Download the video
        return _download_video_file(video_url, shortcode, original_caption, creator_username)

    except Exception as e:
        logger.error(f"  ❌ Failed to download reel: {e}")
        return None


def _download_reel_from_page(page, reel_url: str, shortcode: str) -> Optional[Dict]:
    """Fallback: navigate to the reel page and scrape the video URL."""
    try:
        logger.info("  Trying page scrape fallback...")
        page.goto(reel_url, wait_until="load", timeout=20000)
        page.wait_for_timeout(3000)

        # Try to find the video element
        video_el = page.locator("video")
        if video_el.count() > 0:
            video_url = video_el.first.get_attribute("src")
            if video_url:
                # Try to get creator from the page
                creator = "unknown"
                try:
                    header_link = page.locator('header a[href*="/"]').first
                    href = header_link.get_attribute("href")
                    if href:
                        creator = href.strip("/").split("/")[-1]
                except Exception:
                    pass

                return _download_video_file(video_url, shortcode, "", creator)

        logger.error("  ❌ Could not find video on page.")
        return None
    except Exception as e:
        logger.error(f"  ❌ Page scrape failed: {e}")
        return None


def _download_video_file(video_url: str, shortcode: str, caption: str, creator: str) -> Optional[Dict]:
    """Download a video file from URL to disk."""
    try:
        logger.info("  Downloading video file...")
        filename = f"{shortcode}.mp4"
        filepath = os.path.join(DOWNLOADS_DIR, filename)

        resp = requests.get(video_url, stream=True, timeout=60)
        resp.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"  ✅ Downloaded: {filepath} ({file_size_mb:.1f} MB)")

        return {
            "video_path": filepath,
            "caption": caption,
            "creator_username": creator,
        }
    except Exception as e:
        logger.error(f"  ❌ Video download failed: {e}")
        return None


def cleanup_file(filepath):
    """Remove a downloaded file after successful upload."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"  🗑️  Cleaned up: {filepath}")
    except Exception as e:
        logger.warning(f"  ⚠️  Failed to cleanup {filepath}: {e}")
