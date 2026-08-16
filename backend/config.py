from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROWLARR_URL: str = "http://localhost:9696"
    PROWLARR_API_KEY: str = ""
    SCRAPE_INTERVAL_HOURS: int = 6


settings = Settings()
