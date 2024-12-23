import os

import requests
from prefect import task
from models.tba.event import Event
from models.tba.tba_page_etag import TBAPageEtag
from services.db_service import (
    get_tba_page_etag,
    upsert_events,
    upsert_tba_page_etag,
)

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task(
    name="Event Sync: Prepare Headers",
    retries=3,
    retry_delay_seconds=15,
)
def prepare_event_headers(year: int):
    etag = get_tba_page_etag(page_num=None, year=year, endpoint="events")
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task(
    name="Event Sync: Fetch Event Data",
    retries=3,
    retry_delay_seconds=15,
)
def fetch_event_data(headers, year: int):
    url = f"https://www.thebluealliance.com/api/v3/events/{year}"
    return requests.get(url, headers=headers)


@task(
    name="Event Sync: Process Event Response",
    retries=3,
    retry_delay_seconds=15,
)
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
    return [Event.from_tba(item) for item in response.json()]


@task(
    name="Event Sync: Filter Offseasons",
    retries=3,
    retry_delay_seconds=15,
)
def filter_events(events: list[Event]):

    event_blacklist = [
        "2020dar",
        "2020carv",
        "2020gal",
        "2020hop",
        "2020new",
        "2020roe",
        "2020tur",
    ]

    events = [
        event
        for event in events
        if event.event_type != "Offseason"
        and event.event_type != "Preseason"
        and event.event_type != "Unlabeled"
        and event.event_type != "Unknown"
        and event.event_type != "Remote"
        and event.event_type != "--"
    ]

    for event in events:
        if event.key in event_blacklist:
            events.remove(event)

        event.divisions = [
            division
            for division in event.divisions
            if division.division_event_key not in event_blacklist
            and division.parent_event_key not in event.key
        ]

    return events


@task(name="Event Sync: Upsert Event Data", retries=3, retry_delay_seconds=15)
def upsert_event_data(events, response, year: int):
    if events:
        upsert_events(events)
        print(f"Events: Fetched {len(events)} events.")

    if response.status_code == 200:
        existing_etag = get_tba_page_etag(
            page_num=None,
            year=year,
            endpoint="events",
        )

        etag = response.headers.get("ETag")
        upsert_tba_page_etag(
            TBAPageEtag(
                id=existing_etag.id if existing_etag else None,
                page_num=None,
                year=year,
                endpoint="events",
                etag=etag,
            )
        )


@task(
    name="Fetch Events For Year",
    description="Fetches all events for the current season.",
    tags=["tba"],
    version="1.0",
    retries=3,
    retry_delay_seconds=15,
)
def fetch_events(year: int):
    headers = prepare_event_headers(year)
    response = fetch_event_data(headers, year)
    events = process_event_response(response)

    if events:
        events = filter_events(events)

    upsert_event_data(events, response, year)
