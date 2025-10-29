#!/usr/bin/env python3
"""
Simple keep-alive script to prevent Render free tier from sleeping
Run this on a separate server/service to ping your app every 10 minutes
"""
import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Render app URL
APP_URL = "https://ptsa-tracker.onrender.com"

def ping_app():
    """Ping the app to keep it awake"""
    try:
        response = requests.get(f"{APP_URL}/", timeout=30)
        if response.status_code == 200:
            logger.info(f"✅ App is alive - Status: {response.status_code}")
        else:
            logger.warning(f"⚠️ App responded with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to ping app: {e}")

def main():
    """Main keep-alive loop"""
    logger.info("🚀 Starting keep-alive service for PTSA Tracker")
    
    while True:
        ping_app()
        # Wait 10 minutes (600 seconds)
        time.sleep(600)

if __name__ == "__main__":
    main()
