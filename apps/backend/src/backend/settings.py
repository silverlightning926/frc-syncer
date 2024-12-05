from datetime import timedelta

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    historic_seasons: list[int] = [2022, 2023, 2024]

    sync_delta: timedelta = timedelta(weeks=1)

    teams_blacklist: list[str] = ["frc0"]


settings = Settings()
