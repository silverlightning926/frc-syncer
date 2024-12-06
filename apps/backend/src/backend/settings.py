from datetime import timedelta

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    historic_seasons: list[int] = [2016, 2017, 2018, 2019, 2022, 2023, 2024]

    sync_delta: timedelta = timedelta(weeks=1)


settings = Settings()
