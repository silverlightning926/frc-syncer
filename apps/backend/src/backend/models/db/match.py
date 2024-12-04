from pydantic import BaseModel


class Match(BaseModel):
    key: str
    comp_level: str
    set_number: int
    match_number: int
    winning_alliance: str | None
    event_key: str
    time: str | None
    actual_time: str | None
    predicted_time: str | None
