from typing import Optional

from pydantic import BaseModel


class EventDivision(BaseModel):
    parent_event_key: str
    division_event_key: str

    def to_db(self):
        return self.model_dump()


class District(BaseModel):
    abbreviation: str
    display_name: str
    key: str
    year: int

    @classmethod
    def from_tba(cls, district: dict) -> "District":
        return cls(
            abbreviation=district["abbreviation"],
            display_name=district["display_name"],
            key=district["key"],
            year=district["year"],
        )

    def to_db(self):
        return self.model_dump()


class Event(BaseModel):
    key: str
    name: str
    event_code: str
    event_type: Optional[str] = None
    district: Optional[District] = None
    city: Optional[str] = None
    state_prov: Optional[str] = None
    country: Optional[str] = None
    start_date: str
    end_date: str
    year: int
    short_name: Optional[str] = None
    week: Optional[int] = None
    location_name: Optional[str] = None
    timezone: Optional[str] = None
    playoff_type: Optional[str] = None
    divisions: list[EventDivision] = []

    @classmethod
    def from_tba(cls, event: dict) -> "Event":
        return cls(
            key=event["key"],
            name=event["name"],
            event_code=event["event_code"],
            event_type=event["event_type_string"],
            district=(
                District.from_tba(event["district"])
                if event["district"]
                else None
            ),
            city=event["city"],
            state_prov=event["state_prov"],
            country=event["country"],
            start_date=event["start_date"],
            end_date=event["end_date"],
            year=event["year"],
            short_name=event["short_name"],
            week=event["week"],
            location_name=event["location_name"],
            timezone=event["timezone"],
            playoff_type=event["playoff_type_string"],
            divisions=[
                EventDivision(
                    parent_event_key=event["key"], division_event_key=division
                )
                for division in event.get("division_keys", [])
            ],
        )

    def to_db(self):
        result = self.model_dump(exclude={"divisions", "district"})
        result.update(
            {"district_key": self.district.key if self.district else None}
        )
        return result
