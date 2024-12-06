import os

import requests
from models.db.tba_page_etag import TBAPageEtag
from models.tba.event import Event
from prefect import task
from services.db_service import (
    get_tba_page_etag,
    upsert_events,
    upsert_tba_page_etag,
)

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task
def prepare_event_headers(year: int):
    etag = get_tba_page_etag(page_num=0, year=year, endpoint="events")
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task
def fetch_event_data(headers, year: int):
    url = f"https://www.thebluealliance.com/api/v3/events/{year}"
    return requests.get(url, headers=headers)


@task
def process_event_response(response):
    if response.status_code == 304:
        print("Events: ETAG match. Skipping.")
        return None
    elif response.status_code != 200:
        print(
            f"Events: Failed to fetch events. Status Code: {
              response.status_code}"
        )
        return None
    return [Event(**event) for event in response.json()]


@task
def filter_offseasons(events: list[Event]):
    return [
        event
        for event in events
        if event.event_type != 99
        and event.event_type != 100
        and event.event_type != -1
        and event.event_type != 7
    ]


@task
def upsert_event_data(events, response, year: int):
    if events:
        upsert_events(events)
        new_etag = TBAPageEtag(
            page_num=0,
            etag=response.headers.get("ETag"),
            endpoint="events",
            year=year,
        )
        upsert_tba_page_etag(new_etag)
        print(f"Events: Fetched {len(events)} events.")


@task(
    name="Fetch Events For Year",
    description="Fetches all events for the current season.",
    tags=["tba"],
    version="1.0",
)
def fetch_events(year: int):
    headers = prepare_event_headers(year)
    response = fetch_event_data(headers, year)
    events = process_event_response(response)

    if events:
        events = filter_offseasons(events)

    upsert_event_data(events, response, year)
