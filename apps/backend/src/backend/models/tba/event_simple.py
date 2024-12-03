from typing import Optional

from models.tba.district import District
from pydantic import BaseModel


class EventSimple(BaseModel):
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

    def get_event_type_str(self) -> str:
        event_type_mapping = {
            0: "Regional",
            1: "District",
            2: "District Championship",
            3: "Championship Division",
            4: "Championship Finals",
            5: "District Championship Division",
            6: "Festival of Champions",
            7: "Remote",
            99: "Offseason",
            100: "Preseason",
            -1: "Unlabeled",
        }
        return event_type_mapping.get(self.event_type, "UNKNOWN")
