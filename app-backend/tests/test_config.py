from app.core.config import Settings


def test_placeholder_google_client_id_is_treated_as_unset():
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///./tests/test.db",
        SECRET_KEY="test-secret-key",
        GOOGLE_CLIENT_ID="REPLACE_ME",
    )

    assert settings.GOOGLE_CLIENT_ID is None


def test_real_google_client_id_is_preserved():
    value = "1234567890-example.apps.googleusercontent.com"
    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///./tests/test.db",
        SECRET_KEY="test-secret-key",
        GOOGLE_CLIENT_ID=value,
    )

    assert settings.GOOGLE_CLIENT_ID == value
