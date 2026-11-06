import logging as _logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once; safe to call repeatedly."""
    _logging.basicConfig(level=level.upper(), format=_FORMAT, force=True)
