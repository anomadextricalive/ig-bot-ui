import requests
import logging
import os
from .config import load_config

logger = logging.getLogger(__name__)

# Track the active webhook URL from config
_webhook_url = None

def init_webhook():
    global _webhook_url
    config = load_config()
    _webhook_url = config.get("WEBHOOK_URL", "").strip()
    if _webhook_url and not _webhook_url.endswith("/api/progress"):
        _webhook_url = _webhook_url.rstrip("/") + "/api/progress"

def report_progress(status: str, message: str, reel_id: str = None, sender: str = None):
    """
    Sends the current bot state to the Vercel progress UI.
    status: 'idle', 'downloading', 'uploading', 'completed', 'error'
    """
    if not _webhook_url:
        return
        
    try:
        payload = {
            "status": status,
            "message": message
        }
        if reel_id:
            payload["reelId"] = reel_id
        if sender:
            payload["sender"] = sender
            
        requests.post(_webhook_url, json=payload, timeout=5)
    except Exception as e:
        logger.debug(f"Webhook failed: {e}")
