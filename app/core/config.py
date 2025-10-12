from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, TypeAdapter
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Template"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BACKEND_CORS_ORIGINS: str
    ENVIRONMENT: str = "local"
    JWT_ALGORITHM: Literal["HS256", "RS256", "ES256"] = "HS256"

    @property
    def cors_origins(self) -> List[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()
        if not raw:
            return []
        items = [data.strip() for data in raw.split(",") if data.strip()]
        validated = TypeAdapter(List[AnyHttpUrl]).validate_python(items)
        return [str(u) for u in validated]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
