from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Montly Playlist"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()