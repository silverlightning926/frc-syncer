from typing import Dict, Optional

from models.tba.match_alliance import MatchAlliance
from pydantic import BaseModel


class Videos(BaseModel):
    type: str
    key: str


class Match(BaseModel):
    key: str
    comp_level: str
    set_number: int
    match_number: int
    alliances: Dict[str, MatchAlliance]
    winning_alliance: Optional[str] = None
    event_key: str
    time: Optional[int] = None
    actual_time: Optional[int] = None
    predicted_time: Optional[int] = None
    post_result_time: Optional[int] = None
    score_breakdown: Optional[dict] = None
    videos: Optional[list[Videos]] = None
