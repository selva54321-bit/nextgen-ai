from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SPRING_BOOT_BASE_URL: str = "http://localhost:8080"
    SPRING_BOOT_TIMEOUT_SECONDS: int = 10
    DATABASE_URL: str = "postgresql+asyncpg://postgres.rgkngmdpoylnupcebqlf:HarishSathiya%4007@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    LOG_LEVEL: str = "INFO"
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
