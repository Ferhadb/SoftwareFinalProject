def test_ci_rejects_failure():
    """Deliberately fail to demonstrate CI enforcement."""
    assert False, "Intentional failure for CI demonstration; do not merge"
