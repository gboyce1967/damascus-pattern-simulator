"""
Logging Configuration for Damascus 3D Simulator
================================================

Provides comprehensive debug logging with both console and file handlers.
All function calls, parameter values, vertex transformations, and state
changes are recorded for analysis and troubleshooting.

Usage:
    from lib.logging_config import logger, LOGS_DIR
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def _get_runtime_root() -> Path:
    """
    Return runtime root for generated artifacts.

    - Source runs: project root (parent of lib/)
    - Frozen runs: directory containing the executable
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # lib/ lives one level below project root
    return Path(__file__).resolve().parent.parent


RUNTIME_ROOT = _get_runtime_root()
LOGS_DIR = RUNTIME_ROOT / "logs"


def setup_logging(debug_level: str = "DEBUG") -> logging.Logger:
    """
    Configure comprehensive logging for debugging.

    Creates both console and file handlers with detailed formatting.
    Log file is saved to logs/damascus_3d_debug_<timestamp>.log

    DEBUG CAPABILITY:
    ----------------
    - All function calls are logged
    - All parameter values are logged
    - Vertex transformation calculations are logged
    - Performance metrics are tracked
    - State changes are recorded

    Args:
        debug_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    _logger = logging.getLogger('Damascus3D')
    _logger.setLevel(getattr(logging, debug_level.upper()))

    # Avoid duplicate handlers
    if _logger.handlers:
        _logger.handlers.clear()

    # Console handler - INFO and above (user-facing messages)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    console_handler.setFormatter(console_format)

    # File handler - DEBUG and above (everything for debugging)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f'damascus_3d_debug_{timestamp}.log'
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-25s | Line %(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    _logger.addHandler(console_handler)
    _logger.addHandler(file_handler)

    _logger.info("=" * 70)
    _logger.info("Damascus 3D Simulator - Debug Session Started")
    _logger.info(f"Timestamp: {datetime.now().isoformat()}")
    _logger.info(f"Log file: {log_path}")
    _logger.info("=" * 70)

    return _logger


# Initialize global logger
logger = setup_logging("DEBUG")
