from pydantic import BaseModel


class District(BaseModel):
    abbreviation: str
    display_name: str
    key: str
    year: int
