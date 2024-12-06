from typing import Optional

from pydantic import BaseModel


class Alliance(BaseModel):
    match_key: str
    color: str
    score: int
    score_breakdown: Optional[str] = None
