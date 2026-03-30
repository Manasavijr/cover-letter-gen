from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())
    APP_NAME: str = "cover-letter-gen"
    VERSION: str = "1.0.0"
    PORT: int = 8081

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TEMPERATURE: float = 0.4  # slightly higher for creative writing

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    TOP_K_MATCHES: int = 8
    FRONTEND_URL: str = "http://localhost:3001"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
