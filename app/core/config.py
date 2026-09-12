from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    database_url: str
    
    redis_broker: str
    redis_backend: str

    compress_model: str

    embedding_model: str
    embedding_dimension: int

    rerank_candidate_k: int
    reranker_model_name: str

    gemini_api_key: str
    gemini_model: str

    groq_api_key: str
    groq_model: str

    openrouter_api_key: str
    openrouter_model: str

    ai_credits_api_key: str
    ai_credits_model: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()



settings = get_settings()