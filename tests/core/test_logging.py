import logging

from app.core.logging import setup_logging


def test_setup_logging_sets_level_and_is_repeatable():
    setup_logging("debug")
    setup_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
