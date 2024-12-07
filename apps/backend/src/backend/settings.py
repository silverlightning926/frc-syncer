from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    historic_seasons: list[int] = [
        2016,
        2017,
        2018,
        2019,
        2020,
        2022,
        2023,
        2024,
    ]


settings = Settings()
