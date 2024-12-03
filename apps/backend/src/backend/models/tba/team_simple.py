from typing import Optional

from pydantic import BaseModel


class TeamSimple(BaseModel):
    key: str
    team_number: int
    nickname: str
    name: str
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
