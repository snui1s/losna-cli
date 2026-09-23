"""
logger.py — Centralized logging and error tracking subsystem for Losna CLI.

Manages rotating file logs at ~/.losna/logs/losna.log, captures full tracebacks
for errors, hangs, timeouts, crashes (via sys.excepthook), and provides utilities
for inspecting recent errors via the /logs slash command.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, List, Dict, Any

# Default log directory and file
DEFAULT_LOG_DIR = Path.home() / ".losna" / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "losna.log"

_LOGGER_INITIALIZED = False
_LOGGER_NAME = "losna"


def get_log_path() -> Path:
    """Returns the resolved Path to the active log file."""
    env_path = os.environ.get("LOSNA_LOG_FILE")
    if env_path:
        return Path(env_path).resolve()
    return DEFAULT_LOG_FILE


def setup_logging(
    log_level: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Initializes root and 'losna' loggers with a RotatingFileHandler.
    Also registers sys.excepthook and threading.excepthook to capture fatal unhandled exceptions.

    Args:
        log_level (str, optional): Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        max_bytes (int): Max file size before rotating (default: 5MB).
        backup_count (int): Number of backup log files to keep (default: 5).

    Returns:
        logging.Logger: Configured logger instance.
    """
    global _LOGGER_INITIALIZED
    logger = logging.getLogger(_LOGGER_NAME)

    if _LOGGER_INITIALIZED:
        return logger

    # Resolve log level
    if not log_level:
        log_level = os.environ.get("LOSNA_LOG_LEVEL", "INFO").upper()

    level = getattr(logging, log_level, logging.INFO)
    logger.setLevel(level)

    # Ensure log directory exists
    log_file = get_log_path()
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Fallback to local logs directory if user home is not writable
        fallback_file = Path("losna.log").resolve()
        log_file = fallback_file

    # Configure RotatingFileHandler
    try:
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(level)

        # Standard informative log format: timestamp, level, module:line, message
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        # Remove existing file handlers if any to avoid duplication
        for h in list(logger.handlers):
            if isinstance(h, (logging.FileHandler, RotatingFileHandler)):
                logger.removeHandler(h)

        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not initialize log file at {log_file}: {e}\n")

    # Install global exception hooks to capture uncaught crashes & freezes
    _install_exception_hooks(logger)

    _LOGGER_INITIALIZED = True
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a child logger or the primary losna logger.
    Ensures setup_logging() has been called.
    """
    if not _LOGGER_INITIALIZED:
        setup_logging()

    if name:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)


def _install_exception_hooks(logger: logging.Logger):
    """Registers uncaught exception handlers for main process and daemon threads."""
    original_excepthook = sys.excepthook

    def _unhandled_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            logger.warning("Application interrupted by user (KeyboardInterrupt / Ctrl+C)")
            original_excepthook(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "FATAL: Unhandled crash in main process:\n"
            f"Exception Type: {exc_type.__name__}\n"
            f"Exception Value: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = _unhandled_exception_handler

    # Python 3.8+ threading exception hook
    import threading
    if hasattr(threading, "excepthook"):
        original_thread_hook = threading.excepthook

        def _threading_exception_handler(args):
            if issubclass(args.exc_type, KeyboardInterrupt):
                return
            logger.error(
                f"FATAL: Unhandled exception in thread '{args.thread.name}':\n"
                f"Exception Type: {args.exc_type.__name__}\n"
                f"Exception Value: {args.exc_value}",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
            )
            original_thread_hook(args)

        threading.excepthook = _threading_exception_handler


def read_recent_logs(lines: int = 35, errors_only: bool = False) -> List[str]:
    """
    Reads the last `lines` from the active log file.

    Args:
        lines (int): Max number of lines to return.
        errors_only (bool): If True, filters only lines containing ERROR or CRITICAL or WARNING.

    Returns:
        list of string lines.
    """
    log_path = get_log_path()
    if not log_path.exists():
        return []

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()

        if errors_only:
            # Filter lines that start an error log or belong to an error/traceback block
            matched_lines = []
            capturing_traceback = False
            for line in all_lines:
                if any(lvl in line for lvl in ("[ERROR]", "[CRITICAL]", "[WARNING]")):
                    capturing_traceback = True
                    matched_lines.append(line)
                elif capturing_traceback:
                    if line.startswith("[") and any(lvl in line for lvl in ("[INFO]", "[DEBUG]")):
                        capturing_traceback = False
                    else:
                        matched_lines.append(line)
            return matched_lines[-lines:] if lines > 0 else matched_lines

        return all_lines[-lines:] if lines > 0 else all_lines
    except Exception as e:
        return [f"[System Error]: Failed to read log file: {e}\n"]


def clear_logs() -> bool:
    """
    Clears the active log file content.

    Returns:
        bool: True if cleared successfully, False otherwise.
    """
    log_path = get_log_path()
    if not log_path.exists():
        return True

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.truncate(0)
        logger = get_logger()
        logger.info("Log file cleared by user request.")
        return True
    except Exception as e:
        sys.stderr.write(f"Failed to clear log file: {e}\n")
        return False
