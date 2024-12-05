import os
import time

import requests
from models.db.tba_page_etag import TBAPageEtag
from models.tba.match_simple import MatchSimple
from prefect import task
from services.db_service import (
    get_event_keys,
    get_tba_event_matches_page_etag,
    upsert_event_matches,
    upsert_tba_page_etag,
)
from settings import settings

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task
def prepare_event_matches_headers(event_key):
    etag = get_tba_event_matches_page_etag(event_key)
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task
def fetch_event_matches_page_data(
    event_key: str, headers
) -> requests.Response:
    url = f"https://www.thebluealliance.com/api/v3/event/{
        event_key}/matches/simple"
    return requests.get(url, headers=headers)


@task
def process_event_teams_response(response):
    if response.status_code == 304:
        print("Event Matches: ETAG match. Skipping.")
        return None
    elif response.status_code != 200:
        print(
            f"Event Matches: Failed to fetch event teams. Status Code: {
              response.status_code}"
        )
        return None

    return [MatchSimple(**match) for match in response.json()]


@task
def upsert_event_matches_data(event_key, matches, response):
    if matches:
        upsert_event_matches(matches)
        new_etag = TBAPageEtag(
            page_num=0,
            etag=response.headers.get("ETag"),
            endpoint=f"events/{event_key}/matches",
        )
        upsert_tba_page_etag(new_etag)
        print(f"Event Matches ({event_key}): Fetched {len(matches)} matches.")


@task
def filter_matches(matches: list[MatchSimple]):
    filtered_matches = []

    for match in matches:
        should_exclude = any(
            any(
                team_key in alliance.team_keys
                or team_key in alliance.surrogate_team_keys
                or team_key in alliance.dq_team_keys
                for team_key in settings.teams_blacklist
            )
            for alliance in match.alliances.values()
        )

        if not should_exclude:
            filtered_matches.append(match)

    return filtered_matches


@task
def throttle_request(interval_secs=15):
    time.sleep(interval_secs)


@task
def sync_event_matches(event_key: str):
    headers = prepare_event_matches_headers(event_key)
    response = fetch_event_matches_page_data(event_key, headers)
    matches = process_event_teams_response(response)

    if matches:
        matches = filter_matches(matches)

    upsert_event_matches_data(event_key, matches, response)
    throttle_request()


@task(
    name="Fetch Event Matches",
    description="Fetches all matches for all events.",
    tags=["tba"],
    version="1.0",
)
def sync_all_event_matches():
    event_keys = get_event_keys()

    for event_key in event_keys:
        sync_event_matches(event_key)
