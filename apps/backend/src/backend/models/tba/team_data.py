from typing import List

from pydantic import BaseModel


class TeamData(BaseModel):
    team_key: str
    xs: List[float]
    ys: List[float]
