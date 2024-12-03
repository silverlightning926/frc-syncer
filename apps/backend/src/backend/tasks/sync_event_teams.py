import os
import time

import requests
from models.db.tba_page_etag import TBAPageEtag
from prefect import task
from services.db_service import (
    get_event_keys,
    get_tba_event_teams_page_etag,
    upsert_event_teams,
    upsert_tba_page_etag,
)

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task
def prepare_event_teams_headers(event_key: str):
    etag = get_tba_event_teams_page_etag(event_key)
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task
def fetch_event_teams_data(headers, event_key: str) -> requests.Response:
    url = f"https://www.thebluealliance.com/api/v3/event/{
        event_key}/teams/keys"
    return requests.get(url, headers=headers)


@task
def process_event_teams_response(response):
    if response.status_code == 304:
        print("Event Teams: ETAG match. Skipping.")
        return None
    elif response.status_code != 200:
        print(
            f"Event Teams: Failed to fetch event teams. Status Code: {
              response.status_code}"
        )
        return None
    return response.json()


@task
def upsert_event_teams_data(event_key, event_teams, response):
    if event_teams:
        upsert_event_teams(event_key=event_key, teams=event_teams)
        new_etag = TBAPageEtag(
            page_num=0,
            etag=response.headers.get("ETag"),
            endpoint=f"event-teams-{event_key}",
        )
        upsert_tba_page_etag(new_etag)
        print(
            f"Event Teams ({event_key}): Fetched {
              len(event_teams)} event teams."
        )


@task
def throttle_request(interval_secs):
    time.sleep(interval_secs)


@task(
    name="Sync Event Teams",
    description="Syncs teams for all events in the current season.",
    tags=["tba"],
    version="1.0",
)
def sync_event_teams():
    event_keys: list[str] = get_event_keys()

    for event_key in event_keys:
        headers = prepare_event_teams_headers(event_key)
        response = fetch_event_teams_data(headers, event_key)
        event_teams = process_event_teams_response(response)
        upsert_event_teams_data(
            event_key=event_key, event_teams=event_teams, response=response
        )

        throttle_request(10)
