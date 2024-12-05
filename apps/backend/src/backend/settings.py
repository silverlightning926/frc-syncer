from datetime import timedelta

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    season: int = 2024

    sync_delta: timedelta = timedelta(weeks=1)
    
    teams_blacklist: list[str] = ["frc0"]


settings = Settings()
