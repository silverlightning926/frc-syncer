from pydantic import BaseModel
from typing import Optional


class Alliance(BaseModel):
    match_key: str
    color: str
    score: int
    score_breakdown: Optional[str] = None