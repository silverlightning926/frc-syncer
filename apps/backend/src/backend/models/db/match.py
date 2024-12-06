from typing import Optional

from pydantic import BaseModel


class Match(BaseModel):
    key: str
    comp_level: str
    set_number: int
    match_number: int
    winning_alliance: Optional[str] = None
    event_key: str
    time: Optional[str] = None
    actual_time: Optional[str] = None
    predicted_time: Optional[str] = None
    post_result_time: Optional[str] = None