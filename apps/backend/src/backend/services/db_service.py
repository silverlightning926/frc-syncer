import os
from datetime import datetime

from dotenv import load_dotenv
from models.db.alliance import Alliance
from models.db.alliance_team import AllianceTeam
from models.db.event import Event
from models.db.match import Match
from models.db.tba_page_etag import TBAPageEtag
from models.db.team import Team
from models.tba.district import District
from models.tba.event_simple import EventSimple
from models.tba.match_simple import MatchSimple
from models.tba.team_simple import TeamSimple
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_teams(teams: list[TeamSimple]):

    db_teams = [
        Team(
            key=team.key,
            number=team.team_number,
            name=team.nickname,
            city=team.city,
            state_prov=team.state_prov,
            country=team.country,
        )
        for team in teams
    ]

    supabase.table("teams").upsert(
        [team.model_dump() for team in db_teams]
    ).execute()


def _upsert_districts(districts: list[District]):
    supabase.table("districts").upsert(
        [district.model_dump() for district in districts]
    ).execute()


def get_event_keys_for_year(year: int) -> list[str]:
    response = supabase.table("events").select("key").eq("year", year).execute()
    return [event["key"] for event in response.data]


def upsert_events(events: list[EventSimple]):

    districts = list(
        {
            event.district.key: event.district
            for event in events
            if event.district
        }.values()
    )
    _upsert_districts(districts)

    db_events = [
        Event(
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
        )
        for event in events
    ]

    supabase.table("events").upsert(
        [event.model_dump() for event in db_events]
    ).execute()


def upsert_event_matches(matches: list[MatchSimple]):

    db_matches = [
        Match(
            key=match.key,
            comp_level=match.comp_level,
            set_number=match.set_number,
            match_number=match.match_number,
            winning_alliance=(
                match.winning_alliance if match.winning_alliance else None
            ),
            event_key=match.event_key,
            time=(
                datetime.fromtimestamp(match.time).isoformat()
                if match.time
                else None
            ),
            actual_time=(
                datetime.fromtimestamp(match.actual_time).isoformat()
                if match.actual_time
                else None
            ),
            predicted_time=(
                datetime.fromtimestamp(match.predicted_time).isoformat()
                if match.predicted_time
                else None
            ),
        )
        for match in matches
    ]

    supabase.table("matches").upsert(
        [match.model_dump() for match in db_matches]
    ).execute()

    db_alliance = [
        Alliance(
            match_key=match.key,
            color=alliance_color,
            score=alliance.score,
        )
        for match in matches
        for alliance_color, alliance in match.alliances.items()
    ]

    supabase.table("match-alliances").upsert(
        [alliance.model_dump() for alliance in db_alliance]
    ).execute()

    db_alliance_normal_teams = [
        AllianceTeam(
            team_key=team_key,
            alliance=supabase.table("match-alliances")
            .select("id")
            .eq("match_key", match.key)
            .eq("color", alliance_color)
            .execute()
            .data[0]["id"],
            type="normal",
        )
        for match in matches
        for alliance_color, alliance in match.alliances.items()
        for team_key in alliance.team_keys
    ]

    db_alliance_surrogate_teams = [
        AllianceTeam(
            team_key=team_key,
            alliance=supabase.table("match-alliances")
            .select("id")
            .eq("match_key", match.key)
            .eq("color", alliance_color)
            .execute()
            .data[0]["id"],
            type="surrogate",
        )
        for match in matches
        for alliance_color, alliance in match.alliances.items()
        for team_key in alliance.surrogate_team_keys
    ]

    db_alliance_dq_teams = [
        AllianceTeam(
            team_key=team_key,
            alliance=supabase.table("match-alliances")
            .select("id")
            .eq("match_key", match.key)
            .eq("color", alliance_color)
            .execute()
            .data[0]["id"],
            type="dq",
        )
        for match in matches
        for alliance_color, alliance in match.alliances.items()
        for team_key in alliance.dq_team_keys
    ]

    supabase.table("alliance-teams").upsert(
        [
            alliance_team.model_dump()
            for alliance_team in db_alliance_normal_teams
            + db_alliance_surrogate_teams
            + db_alliance_dq_teams
        ]
    ).execute()


def upsert_tba_page_etag(etag: TBAPageEtag) -> None:

    supabase.table("tba-pages-etags").upsert([etag.model_dump()]).execute()


def get_tba_page_etag(page_num: int, endpoint: str, year: int) -> TBAPageEtag | None:

    response = (
        supabase.table("tba-pages-etags")
        .select("etag", "endpoint", "page_num")
        .eq("page_num", page_num)
        .eq("endpoint", endpoint)
        .eq("year", year)
        .limit(1)
        .execute()
    )

    if len(response.data) == 0:
        return None

    etag_data = response.data[0]
    return TBAPageEtag(
        page_num=etag_data["page_num"],
        etag=etag_data["etag"],
        endpoint=etag_data["endpoint"],
        year=etag_data["year"],
    )
