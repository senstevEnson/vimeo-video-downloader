import logging
import sys
from typing import Optional

_LOGGER_CACHE = {}

def _configure_root_logger() -> None:
    root = logging.getLogger("vimeo_downloader")
    if root.handlers:
        return

    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a module-level logger configured with a sane default format.
    Loggers are cached by name to avoid duplicate configuration.
    """
    _configure_root_logger()

    if not name:
        name = "vimeo_downloader"

    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    logger = logging.getLogger(name)
    _LOGGER_CACHE[name] = logger
    return logger