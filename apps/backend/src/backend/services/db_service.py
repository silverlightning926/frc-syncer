import os
from datetime import datetime

from dotenv import load_dotenv
from models.db.event import Event
from models.db.tba_page_etag import TBAPageEtag
from models.db.team import Team
from models.tba.district import District
from models.tba.event_simple import EventSimple
from models.tba.team_simple import TeamSimple
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_teams(teams: list[TeamSimple]):

    teams = [Team(
        key=team.key,
        number=team.team_number,
        name=team.nickname,
        city=team.city,
        state_prov=team.state_prov,
        country=team.country,
    ) for team in teams]

    supabase.table("teams").upsert(
        [team.model_dump() for team in teams]).execute()


def _upsert_districts(districts: list[District]):
    supabase.table("districts").upsert(
        [district.model_dump() for district in districts]).execute()


def get_event_keys() -> list[str]:
    response = supabase.table("events").select("key").execute()
    return [event["key"] for event in response.data]


def upsert_events(events: list[EventSimple]):

    districts = list(
        {event.district.key: event.district for event in events if event.district}.values())
    _upsert_districts(districts)

    events = [Event(
        key=event.key,
        name=event.name,
        event_code=event.event_code,
        event_type=event.get_event_type_str(),
        district=event.district.key if event.district else None,
        city=event.city,
        state_prov=event.state_prov,
        country=event.country,
        start_date=event.start_date,
        end_date=event.end_date,
        year=event.year,
    ) for event in events]

    supabase.table("events").upsert(
        [event.model_dump() for event in events]).execute()


def upsert_event_teams(event_key: str, teams: list[str]):
    supabase.table("event-teams").upsert(
        [{"event_key": event_key, "team_key": team} for team in teams]).execute()


def upsert_tba_page_etag(etag: TBAPageEtag) -> None:

    supabase.table("tba-pages-etags").upsert(
        [etag.model_dump()]).execute()


def get_tba_teams_page_etag(page_num: int) -> TBAPageEtag:

    response = supabase.table("tba-pages-etags").select(
        "etag", "endpoint").eq("page_num", page_num).eq("endpoint", "teams").limit(1).execute()

    if len(response.data) == 0:
        return None

    etag_data = response.data[0]
    return TBAPageEtag(
        page_num=page_num,
        etag=etag_data["etag"],
        endpoint=etag_data["endpoint"],
    )


def get_tba_events_page_etag() -> TBAPageEtag:

    response = supabase.table("tba-pages-etags").select(
        "etag", "endpoint").eq("endpoint", "events").limit(1).execute()

    if len(response.data) == 0:
        return None

    etag_data = response.data[0]
    return TBAPageEtag(
        page_num=0,
        etag=etag_data["etag"],
        endpoint=etag_data["endpoint"],
    )


def get_tba_event_teams_page_etag(event_key: str) -> TBAPageEtag:

    response = supabase.table("tba-pages-etags").select(
        "etag", "endpoint").eq("endpoint", f"event-teams-{event_key}").limit(1).execute()

    if len(response.data) == 0:
        return None

    etag_data = response.data[0]
    return TBAPageEtag(
        page_num=0,
        etag=etag_data["etag"],
        endpoint=etag_data["endpoint"],
    )


def get_last_synced() -> datetime:

    response = supabase.table(
        "tba-sync").select("synced_on").order("id", desc=True).limit(1).execute()

    if len(response.data) == 0:
        return None

    last_synced_data = response.data[0]
    return datetime.fromisoformat(last_synced_data["synced_on"])


def insert_last_sync():
    supabase.table("tba-sync").insert(
        [{"synced_on": datetime.now().isoformat()}]).execute()


def validate_team_key(team_key: str) -> bool:
    response = supabase.table("teams").select(
        "key").eq("key", team_key).limit(1).execute()

    return len(response.data) > 0


def validate_event_key(event_key: str) -> bool:
    response = supabase.table("events").select(
        "key").eq("key", event_key).limit(1).execute()

    return len(response.data) > 0
