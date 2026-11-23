import logging

import pytest

from app.main import app


def test_request_is_logged_with_method_path_status(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.request"):
        client.get("/health")
    assert any(
        r.getMessage().startswith("GET /health 200") and r.getMessage().endswith("ms")
        for r in caplog.records
    )


def test_unhandled_error_is_logged_as_500(client, caplog):
    @app.get("/_boom")
    def boom():
        raise RuntimeError("x")

    with (
        caplog.at_level(logging.INFO, logger="app.request"),
        pytest.raises(RuntimeError),
    ):
        client.get("/_boom")
    assert any("GET /_boom 500" in r.getMessage() for r in caplog.records)
