from typing import Optional

from pydantic import BaseModel


class Event(BaseModel):
    key: str
    name: str
    event_code: str
    event_type: str
    district: Optional[str] = None
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
    start_date: str
    end_date: str
    year: int
