"""
Reel uploader module using Playwright browser automation.
Uploads reels via Instagram's web interface.
"""

import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def build_caption(original_caption: str, creator_username: str) -> str:
    """Build repost caption with credit."""
    parts = []
    if original_caption.strip():
        parts.append(original_caption.strip())
    parts.append(f"\n📸 Credit: @{creator_username}")
    parts.append("🔄 Reposted via DM")
    return "\n".join(parts)


def upload_reel(page, video_path: str, caption: str) -> bool:
    """
    Upload a video as a Reel via Instagram's web interface.
    """
    try:
        video_path = os.path.abspath(video_path)
        if not os.path.exists(video_path):
            logger.error(f"  ❌ Video file not found: {video_path}")
            return False

        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        logger.info(f"  📤 Uploading reel ({file_size_mb:.1f} MB)...")

        # Navigate to Instagram home
        page.goto("https://www.instagram.com/", wait_until="load", timeout=30000)
        page.wait_for_timeout(3000)

        # Click the "Create" button (opens a dropdown menu)
        logger.info("  Clicking Create...")
        create_btn = page.locator('svg[aria-label="New post"]')
        if create_btn.count() > 0:
            create_btn.first.click()
        else:
            create_span = page.locator('span:text-is("Create")')
            if create_span.count() > 0:
                create_span.first.click()
            else:
                logger.error("  ❌ Could not find Create button.")
                return False

        page.wait_for_timeout(2000)

        # Click "Post" from the dropdown menu
        logger.info("  Clicking 'Post' from dropdown...")
        post_option = page.locator('span:text-is("Post")')
        try:
            post_option.first.click(timeout=5000)
        except Exception:
            # Maybe it went straight to the upload dialog
            logger.info("  No dropdown — may have opened upload dialog directly.")
        
        page.wait_for_timeout(3000)

        # Now the upload dialog should be open
        # Look for file input OR "Select from computer" button
        file_input = page.locator('input[type="file"]')
        
        if file_input.count() == 0:
            # Try clicking "Select from computer" or "Select from gallery"
            for btn_text in ["Select from computer", "Select From Computer", "Select from gallery"]:
                try:
                    btn = page.locator(f'button:has-text("{btn_text}")')
                    if btn.first.is_visible(timeout=3000):
                        btn.first.click()
                        page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

        # Re-check for file input
        file_input = page.locator('input[type="file"]')
        if file_input.count() == 0:
            logger.error("  ❌ File input not found after opening upload dialog.")
            page.screenshot(path="debug_upload_fail.png")
            return False

        logger.info("  Setting file on input...")
        file_input.first.set_input_files(video_path)
        
        logger.info("  File set, waiting for processing...")
        page.wait_for_timeout(5000)

        # Click through the Next/Continue buttons and handle cropping/aspect ratio
        for step in range(5):
            page.wait_for_timeout(2000)
            
            # Look for and dismiss "Video posts are now shared as reels" OK button
            try:
                ok_btn = page.locator('button:has-text("OK")')
                if ok_btn.first.is_visible(timeout=3000):
                    ok_btn.first.click(force=True)
                    logger.info("  Dismissed 'shared as reels' modal")
                    page.wait_for_timeout(2000)
            except Exception:
                pass
            
            # Step 1: Cropping step. Select original aspect ratio.
            if step == 0:
                try:
                    # Click aspect ratio button (SVG with aria-label="Select crop")
                    aspect_btn = page.locator('svg[aria-label="Select crop"]')
                    if aspect_btn.count() > 0 and aspect_btn.first.is_visible(timeout=2000):
                        # Click the button containing the SVG
                        page.evaluate("(el) => el.closest('button').click()", aspect_btn.first.element_handle())
                        page.wait_for_timeout(1000)
                        
                        # Click "Original" (usually the first option or specifically labeled)
                        page.evaluate('''() => {
                            const spans = Array.from(document.querySelectorAll('span, div'));
                            const orig = spans.find(el => el.textContent.trim() === 'Original');
                            if (orig) orig.click();
                        }''')
                        logger.info("  Set aspect ratio to Original (9:16)")
                        page.wait_for_timeout(1000)
                except Exception as e:
                    logger.warning(f"  ⚠️ Could not set aspect ratio: {e}")

            try:
                # Look for Next button
                next_btn = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")')
                if next_btn.first.is_visible(timeout=3000):
                    next_btn.first.click(force=True)
                    logger.info(f"  Clicked Next (step {step + 1})")
                else:
                    break
            except Exception:
                break

        # Fill in the caption
        try:
            caption_area = page.locator('div[aria-label="Write a caption..."], div[role="textbox"]')
            if caption_area.first.is_visible(timeout=5000):
                caption_area.first.click(force=True)
                page.wait_for_timeout(500)
                page.keyboard.type(caption, delay=5)
                logger.info("  Caption filled.")
                page.wait_for_timeout(1000)
        except Exception as e:
            logger.warning(f"  ⚠️ Could not fill caption: {e}")

        # Click Share
        try:
            share_btn = page.locator('div[role="button"]:has-text("Share"), button:has-text("Share")')
            if share_btn.first.is_visible(timeout=5000):
                share_btn.first.click(force=True)
                logger.info("  Clicked Share!")
            else:
                logger.error("  ❌ Share button not found.")
                page.screenshot(path="debug_no_share.png")
                return False
        except Exception as e:
            logger.error(f"  ❌ Could not click Share: {e}")
            return False

        # Wait for upload to complete
        logger.info("  Waiting for upload to complete (this may take a few minutes)...")
        try:
            # We look for the "Your reel has been shared" or similar success indicator
            # Increased timeout to 3 minutes to handle slower Instagram processing
            success = page.locator('span:has-text("Your reel has been shared"), span:has-text("Post shared"), img[alt*="checkmark"], span:has-text("Reel shared")')
            success.first.wait_for(state="visible", timeout=180000)
            logger.info("  ✅ Reel uploaded successfully!")
            return True
        except Exception as e:
            logger.error(f"  ❌ Upload timed out. Did not see success confirmation within 3 minutes: {e}")
            page.screenshot(path="debug_upload_timeout.png")
            return False

    except Exception as e:
        logger.error(f"  ❌ Upload failed: {e}")
        return False
