from pydantic import BaseModel


class AllianceTeam(BaseModel):
    team_key: str
    alliance: int
    type: str
