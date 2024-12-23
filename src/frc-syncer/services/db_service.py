import os
from datetime import datetime

from dotenv import load_dotenv
from models.tba.event import Event
from models.tba.match import Match
from models.tba.ranking import Ranking
from models.tba.tba_page_etag import TBAPageEtag
from models.tba.team import Team
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_teams(teams: list[Team]):

    new_teams = [team.to_db() for team in teams]
    if new_teams:
        supabase.table("teams").upsert(
            new_teams,
        ).execute()


def get_event_keys_for_year(year: int) -> list[str]:
    response = (
        supabase.table("events")
        .select("key")
        .eq("year", year)
        .order("key")
        .execute()
    )
    return [event["key"] for event in response.data]


def upsert_events(events: list[Event]):
    new_districts = [
        district.to_db()
        for district in {
            district.key: district
            for district in [
                event.district for event in events if event.district
            ]
        }.values()
    ]
    if new_districts:
        supabase.table("districts").upsert(
            new_districts,
        ).execute()

    new_events = [event.to_db() for event in events]
    if new_events:
        supabase.table("events").upsert(
            new_events,
        ).execute()
    else:
        return

    new_event_divisions = [
        division.to_db() for event in events for division in event.divisions
    ]
    if new_event_divisions:
        supabase.table("event-divisions").upsert(new_event_divisions).execute()


def upsert_event_matches(matches: list[Match]):

    new_matches = [match.to_db() for match in matches]
    if new_matches:
        supabase.table("matches").upsert(
            new_matches,
        ).execute()
    else:
        return

    new_alliances = [
        alliance.to_db() for match in matches for alliance in match.alliances
    ]
    if new_alliances:
        supabase.table("alliances").upsert(
            new_alliances,
        ).execute()
    else:
        return

    new_alliance_teams = [
        team.to_db()
        for match in matches
        for alliance in match.alliances
        for team in alliance.teams
    ]
    if new_alliance_teams:
        supabase.table("alliance-teams").upsert(
            new_alliance_teams,
        ).execute()


def upsert_event_rankings(rankings: list[Ranking]):
    new_rankings = [ranking.to_db() for ranking in rankings]
    if new_rankings:
        supabase.table("rankings").upsert(
            new_rankings,
        ).execute()


def upsert_tba_page_etag(etag: TBAPageEtag) -> None:
    etag_data = etag.model_dump()

    if etag.id:
        etag_data["id"] = etag.id
    else:
        etag_data.pop("id")

    supabase.table("tba-pages-etags").upsert(
        [etag_data],
    ).execute()


def get_tba_page_etag(
    page_num: int | None, endpoint: str, year: int
) -> TBAPageEtag | None:

    response = (
        supabase.table("tba-pages-etags")
        .select("id", "etag", "endpoint", "page_num", "year")
        .eq("endpoint", endpoint)
        .eq("year", year)
        .limit(1)
    )

    if page_num is not None:
        response = response.eq("page_num", page_num)

    response = response.execute()

    if len(response.data) == 0:
        return None

    etag_data = response.data[0]
    return TBAPageEtag(
        id=etag_data["id"],
        page_num=etag_data["page_num"],
        etag=etag_data["etag"],
        endpoint=etag_data["endpoint"],
        year=etag_data["year"],
    )


def insert_sync_timestamp(year: int) -> None:

    supabase.table("tba-sync").insert(
        [{"year": year, "synced_on": datetime.now().isoformat()}]
    ).execute()
