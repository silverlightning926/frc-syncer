from typing import Optional

from pydantic import BaseModel


class Team(BaseModel):
    key: str
    number: int
    name: str
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
