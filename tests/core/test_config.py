from app.core.config import Settings, get_settings


def test_defaults():
    s = Settings(_env_file=None)
    assert s.categorizer == "rules"
    assert s.jwt_expire_minutes == 60
    assert s.llm_api_key is None


def test_env_overrides_defaults(monkeypatch):
    monkeypatch.setenv("CATEGORIZER", "chain")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "5")
    s = Settings(_env_file=None)
    assert s.categorizer == "chain"
    assert s.jwt_expire_minutes == 5


def test_get_settings_is_singleton():
    assert get_settings() is get_settings()
