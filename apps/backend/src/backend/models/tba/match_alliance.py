from pydantic import BaseModel


class MatchAlliance(BaseModel):
    score: int
    team_keys: list[str]
    surrogate_team_keys: list[str]
    dq_team_keys: list[str]
