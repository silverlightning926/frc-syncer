from pydantic import BaseModel


class EventDivision(BaseModel):
    parent_event_key: str
    division_event_key: str
