from pydantic import BaseModel


class Alliance(BaseModel):
    match_key: str
    color: str
    score: int
