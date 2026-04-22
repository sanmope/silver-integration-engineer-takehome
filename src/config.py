from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # connector
    base_url: str = "https://api.threatvendor.example.com"
    timeout: float = 30.0
    max_retries: int = 3

    # celery
    broker_url: str = "redis://localhost:6379/0"
    backend_url: str = "redis://localhost:6379/1"
    sync_interval_seconds: int = 900  # 15 min

    # credential store local
    credentials_path: str = "credentials.enc"
    
    # fernet key and aws missing

    # s3
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_prefix: str = "feeds/"

config = Config() # singleton - accessible from any module
