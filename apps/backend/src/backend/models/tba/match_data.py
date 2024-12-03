from typing import List

from models.tba.team_data import TeamData
from pydantic import BaseModel


class Alliances(BaseModel):
    blue: List[TeamData]
    red: List[TeamData]


class MatchData(BaseModel):
    alliances: Alliances
    key: str
    times: List[float]
