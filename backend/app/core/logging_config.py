import logging

from pythonjsonlogger.json import JsonFormatter


def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Configure the root logger.

    fmt="json"  → structured JSON output (production / Docker).
    fmt="text"  → human-readable plain text (local dev via LOG_FORMAT=text in .env).
    """
    handler = logging.StreamHandler()

    if fmt == "json":
        formatter: logging.Formatter = JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)
