import os
from datetime import datetime
from json import dumps
import pprint

from dotenv import load_dotenv
from python_models.team import Team
from python_models.tba_page_etag import TBAPageEtag
from python_models.event import Event
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert_teams(teams: list[Team]):

    supabase.table("teams").upsert(
        [team.to_db()
        for team in teams],
    ).execute()


# def get_event_keys_for_year(year: int) -> list[str]:
#     response = (
#         supabase.table("events").select("key").eq("year", year).execute()
#     )
#     return [event["key"] for event in response.data]

def upsert_events(events: list[Event]):
    supabase.table("districts").upsert(
        [district.to_db() for district in {district.key: district for district in [event.district for event in events if event.district]}.values()],
    ).execute()

    supabase.table("events").upsert(
        [event.to_db() for event in events]
    ).execute()
    
    supabase.table("event-divisions").upsert(
        [division.to_db() for event in events for division in event.divisions]
    ).execute()


# def upsert_event_matches(matches: list[TBAMatch]):

#     db_matches = [
#         DBMatch(
#             key=match.key,
#             comp_level=match.comp_level,
#             set_number=match.set_number,
#             match_number=match.match_number,
#             winning_alliance=(
#                 match.winning_alliance if match.winning_alliance else None
#             ),
#             event_key=match.event_key,
#             time=(
#                 datetime.fromtimestamp(match.time).isoformat()
#                 if match.time
#                 else None
#             ),
#             actual_time=(
#                 datetime.fromtimestamp(match.actual_time).isoformat()
#                 if match.actual_time
#                 else None
#             ),
#             predicted_time=(
#                 datetime.fromtimestamp(match.predicted_time).isoformat()
#                 if match.predicted_time
#                 else None
#             ),
#             post_result_time=(
#                 datetime.fromtimestamp(match.post_result_time).isoformat()
#                 if match.post_result_time
#                 else None
#             ),
#         )
#         for match in matches
#     ]

#     supabase.table("matches").upsert(
#         [match.model_dump() for match in db_matches]
#     ).execute()

#     db_alliance = [
#         Alliance(
#             match_key=match.key,
#             color=alliance_color,
#             score=alliance.score,
#             score_breakdown=(
#                 dumps(match.score_breakdown[alliance_color])
#                 if match.score_breakdown
#                 else None
#             ),
#         )
#         for match in matches
#         for alliance_color, alliance in match.alliances.items()
#     ]

#     supabase.table("match-alliances").upsert(
#         [alliance.model_dump() for alliance in db_alliance]
#     ).execute()

#     db_alliance_normal_teams = [
#         AllianceTeam(
#             team_key=team_key,
#             alliance=supabase.table("match-alliances")
#             .select("id")
#             .eq("match_key", match.key)
#             .eq("color", alliance_color)
#             .execute()
#             .data[0]["id"],
#             type="normal",
#         )
#         for match in matches
#         for alliance_color, alliance in match.alliances.items()
#         for team_key in alliance.team_keys
#     ]

#     db_alliance_surrogate_teams = [
#         AllianceTeam(
#             team_key=team_key,
#             alliance=supabase.table("match-alliances")
#             .select("id")
#             .eq("match_key", match.key)
#             .eq("color", alliance_color)
#             .execute()
#             .data[0]["id"],
#             type="surrogate",
#         )
#         for match in matches
#         for alliance_color, alliance in match.alliances.items()
#         for team_key in alliance.surrogate_team_keys
#     ]

#     db_alliance_dq_teams = [
#         AllianceTeam(
#             team_key=team_key,
#             alliance=supabase.table("match-alliances")
#             .select("id")
#             .eq("match_key", match.key)
#             .eq("color", alliance_color)
#             .execute()
#             .data[0]["id"],
#             type="dq",
#         )
#         for match in matches
#         for alliance_color, alliance in match.alliances.items()
#         for team_key in alliance.dq_team_keys
#     ]

#     supabase.table("alliance-teams").upsert(
#         [
#             alliance_team.model_dump()
#             for alliance_team in db_alliance_normal_teams
#             + db_alliance_surrogate_teams
#             + db_alliance_dq_teams
#         ]
#     ).execute()


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
