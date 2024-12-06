import os
import time

import requests
from models.db.tba_page_etag import TBAPageEtag
from models.tba.match import Match
from prefect import task
from services.db_service import (
    get_event_keys_for_year,
    get_tba_page_etag,
    upsert_event_matches,
    upsert_tba_page_etag,
)

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task
def prepare_event_matches_headers(event_key, year: int):
    etag = get_tba_page_etag(
        page_num=0,
        year=year,
        endpoint=f"events/{event_key}/matches",
    )
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task
def fetch_event_matches_page_data(
    event_key: str, headers
) -> requests.Response:
    url = f"https://www.thebluealliance.com/api/v3/event/{
        event_key}/matches"
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

    return [Match(**match) for match in response.json()]


@task
def upsert_event_matches_data(event_key, matches, response, year: int):
    if matches:
        upsert_event_matches(matches)
        new_etag = TBAPageEtag(
            page_num=None,
            etag=response.headers.get("ETag"),
            endpoint=f"events/{event_key}/matches",
            year=year,
        )
        upsert_tba_page_etag(new_etag)
        print(f"Event Matches ({event_key}): Fetched {len(matches)} matches.")


@task
def filter_matches(matches: list[Match]):
    teams_blacklist: list[str] = ["frc0"]
    filtered_matches = []

    for match in matches:
        should_exclude = any(
            any(
                team_key in alliance.team_keys
                or team_key in alliance.surrogate_team_keys
                or team_key in alliance.dq_team_keys
                for team_key in teams_blacklist
            )
            for alliance in match.alliances.values()
        )

        if not should_exclude:
            filtered_matches.append(match)

    return filtered_matches


@task
def throttle_request(interval_secs=20):
    time.sleep(interval_secs)


@task
def sync_event_matches(event_key: str, year: int):
    headers = prepare_event_matches_headers(event_key, year)
    response = fetch_event_matches_page_data(event_key, headers)
    matches = process_event_teams_response(response)

    if matches:
        matches = filter_matches(matches)

    upsert_event_matches_data(event_key, matches, response, year=year)
    throttle_request()


@task(
    name="Fetch Event Matches",
    description="Fetches all matches for all events.",
    tags=["tba"],
    version="1.0",
)
def sync_all_event_matches(year: int):
    event_keys = get_event_keys_for_year(year=year)

    for event_key in event_keys:
        sync_event_matches(event_key, year)
