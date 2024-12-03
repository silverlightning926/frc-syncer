import os

import requests
from models.db.tba_page_etag import TBAPageEtag
from models.tba.event_simple import EventSimple
from prefect import task
from services.db_service import (get_tba_events_page_etag, upsert_events,
                                 upsert_tba_page_etag)
from settings import settings

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task(
    name="Fetch Events",
    description="Fetches all events for the current season.",
    tags=["tba"],
    version="1.0"
)
def fetch_events():
    etag: TBAPageEtag = get_tba_events_page_etag()
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag

    try:
        response = requests.get(
            f"https://www.thebluealliance.com/api/v3/events/{
                settings.season}/simple",
            headers=headers
        )

        if response.status_code == 304:
            print("Events: ETAG match. Skipping.")
        elif response.status_code != 200:
            print(f"Events: Failed Getting Events. Status Code {
                  response.status_code}.")
        else:
            events = [EventSimple(**event) for event in response.json()]

            upsert_events(events)
            new_etag = TBAPageEtag(
                page_num=0, etag=response.headers.get("ETag"), endpoint="events"
            )
            if new_etag:
                upsert_tba_page_etag(new_etag)

            print(f"Events: Fetched {len(events)} events.")

    except requests.RequestException as e:
        print(f"Events: Error fetching events - {e}")
