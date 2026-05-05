import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def setup_logging(level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)

    formatter = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level=level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
