import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
os.environ.setdefault("TESTING", "1")

pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.app_client",
]
