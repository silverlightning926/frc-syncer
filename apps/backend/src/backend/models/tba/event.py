from typing import Optional

from models.tba.district import District
from pydantic import BaseModel


class Event(BaseModel):
    key: str
    name: str
    event_code: str
    event_type: int
    district: Optional[District] = None
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
    start_date: str
    end_date: str
    year: int
    short_name: Optional[str] = None
    event_type_string: Optional[str] = None
    week: Optional[int] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    gmaps_place_id: Optional[str] = None
    gmaps_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    location_name: Optional[str] = None
    timezone: Optional[str] = None
    website: Optional[str] = None
    first_event_code: Optional[str] = None
    webcasts: list[dict] = []
    division_keys: list[str] = []
    parent_event_key: Optional[str] = None
    playoff_type: Optional[int] = None
    playoff_type_string: Optional[str] = None
