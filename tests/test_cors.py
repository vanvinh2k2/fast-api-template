from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.main import app


def test_settings_parses_comma_separated_cors_origins():
    settings = Settings(
        DATABASE_URL="sqlite+pysqlite://",
        SECRET_KEY="test-secret",
        BACKEND_CORS_ORIGINS="http://localhost:5173, http://127.0.0.1:5173",
    )

    assert settings.cors_origins == [
        "http://localhost:5173/",
        "http://127.0.0.1:5173/",
    ]


def test_cors_middleware_uses_parsed_origins():
    cors_middleware = next(m for m in app.user_middleware if m.cls is CORSMiddleware)

    assert cors_middleware.kwargs["allow_origins"] == [
        "http://localhost:5173/",
        "http://127.0.0.1:5173/",
    ]
