from typing import Optional

from pydantic import BaseModel


class Team(BaseModel):
    key: str
    number: int
    name: str
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
    rookie_year: Optional[int] = None

    @classmethod
    def from_tba(cls, team: dict) -> "Team":
        return cls(
            key=team["key"],
            number=team["team_number"],
            name=team["nickname"],
            city=team["city"],
            state_prov=team["state_prov"],
            country=team["country"],
            rookie_year=team["rookie_year"],
        )

    def to_db(self):
        return self.model_dump()
