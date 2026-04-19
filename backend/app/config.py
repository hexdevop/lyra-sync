from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://lyrasync:lyrasync@postgres:5432/lyrasync"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO / S3
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "lyrasync"

    # Genius API
    genius_token: str = ""

    # Whisper
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"  # cpu | cuda

    # Limits
    max_file_size_mb: int = 50
    max_duration_sec: int = 900  # 15 min

    # Rate limiting
    rate_limit_per_minute: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
