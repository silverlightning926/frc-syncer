from pydantic import BaseModel


class Ranking(BaseModel):
    event_key: str
    team_key: str
    rank: int

    @classmethod
    def from_tba(cls, rankings: dict, event_key: str) -> "Ranking":
        return cls(
            event_key=event_key,
            team_key=rankings["team_key"],
            rank=rankings["rank"],
        )

    def to_db(self):
        return self.model_dump()
