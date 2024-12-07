from typing import Optional

from pydantic import BaseModel


class Event(BaseModel):
    key: str
    name: str
    event_code: str
    event_type: str | None
    district: Optional[str] = None
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
    start_date: str
    end_date: str
    year: int
    short_name: Optional[str] = None
    week: Optional[int] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    gmaps_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    location_name: Optional[str] = None
    timezone: Optional[str] = None
    first_event_code: Optional[str] = None
    playoff_type: Optional[str] = None
