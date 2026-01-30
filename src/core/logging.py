"""Logging configuration."""

from loguru import logger
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger.add(os.path.join(LOG_DIR, "app.log"), rotation="100 MB", retention="10 days", level="DEBUG")
