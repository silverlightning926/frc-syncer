from typing import Dict, Optional

from models.tba.match_alliance import MatchAlliance
from pydantic import BaseModel


class MatchSimple(BaseModel):
    key: str
    comp_level: str
    set_number: int
    match_number: int
    alliances: Dict[str, MatchAlliance]
    winning_alliance: Optional[str]
    event_key: str
    time: Optional[int]
    actual_time: Optional[int]
    predicted_time: Optional[int]
