import os
from datetime import datetime

from dotenv import load_dotenv
from python_models.event import Event
from python_models.match import Match
from python_models.ranking import Ranking
from python_models.tba_page_etag import TBAPageEtag
from python_models.team import Team
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_teams(teams: list[Team]):

    supabase.table("teams").upsert(
        [team.to_db() for team in teams],
    ).execute()


def get_event_keys_for_year(year: int) -> list[str]:
    response = (
        supabase.table("events").select("key").eq("year", year).order("key").execute()
    )
    return [event["key"] for event in response.data]


def upsert_events(events: list[Event]):
    supabase.table("districts").upsert(
        [
            district.to_db()
            for district in {
                district.key: district
                for district in [
                    event.district for event in events if event.district
                ]
            }.values()
        ],
    ).execute()

    supabase.table("events").upsert(
        [event.to_db() for event in events]
    ).execute()

    supabase.table("event-divisions").upsert(
        [division.to_db() for event in events for division in event.divisions]
    ).execute()


def upsert_event_matches(matches: list[Match]):

    supabase.table("matches").upsert(
        [match.to_db() for match in matches],
    ).execute()

    supabase.table("alliances").upsert(
        [
            alliance.to_db()
            for match in matches
            for alliance in match.alliances
        ],
    ).execute()

    supabase.table("alliance-teams").upsert(
        [
            team.to_db()
            for match in matches
            for alliance in match.alliances
            for team in alliance.teams
        ],
    ).execute()


def upsert_event_rankings(rankings: list[Ranking]):
    supabase.table("rankings").upsert(
        [ranking.to_db() for ranking in rankings],
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
