import os
import time

import requests
from prefect import task
from python_models.ranking import Ranking
from python_models.tba_page_etag import TBAPageEtag
from services.db_service import (
    get_event_keys_for_year,
    get_tba_page_etag,
    upsert_event_rankings,
    upsert_tba_page_etag,
)

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task(
    retries=3,
    retry_delay_seconds=15,
)
def prepare_event_matches_headers(event_key, year: int):
    etag = get_tba_page_etag(
        page_num=None,
        year=year,
        endpoint=f"events/{event_key}/rankings",
    )
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task(
    retries=3,
    retry_delay_seconds=15,
)
def fetch_event_rankings_page_data(
    event_key: str, headers
) -> requests.Response:
    url = f"https://www.thebluealliance.com/api/v3/event/{event_key}/rankings"
    return requests.get(url, headers=headers)


@task(
    retries=3,
    retry_delay_seconds=15,
)
def process_event_rankings_response(response, event_key: str):
    if response.status_code == 304:
        print("Event Rankings: ETAG match. Skipping.")
        return None
    elif response.status_code != 200:
        print(
            f"Event Rankings: Failed to fetch event rankings. Status Code: {
                response.status_code}"
        )
        return None

    return [
        Ranking.from_tba(rank, event_key)
        for rank in response.json()["rankings"]
    ]


@task(
    retries=3, 
    retry_delay_seconds=15
)
def upsert_event_rankings_data(event_key, rankings, response, year: int):
    if rankings:
        upsert_event_rankings(rankings)
        print(
            f"Event Rankings ({event_key}): Fetched {len(rankings)} rankings."
        )

    if response.status_code == 200:
        existing_etag = get_tba_page_etag(
            page_num=None,
            year=year,
            endpoint=f"events/{event_key}/rankings",
        )

        etag = response.headers.get("ETag")
        upsert_tba_page_etag(
            TBAPageEtag(
                id=existing_etag.id if existing_etag else None,
                page_num=None,
                year=year,
                endpoint=f"events/{event_key}/rankings",
                etag=etag,
            )
        )


@task(
    retries=3,
    retry_delay_seconds=15,
)
def throttle_request(interval_secs=5):
    time.sleep(interval_secs)


@task(
    retries=3,
    retry_delay_seconds=15,
)
def sync_event_ranks(event_key: str, year: int):
    headers = prepare_event_matches_headers(event_key, year)
    response = fetch_event_rankings_page_data(event_key, headers)
    rankings = process_event_rankings_response(response, event_key)
    upsert_event_rankings_data(event_key, rankings, response, year)
    throttle_request()


@task(
    name="Sync All Event Rankings",
    description="Syncs all event rankings for a given year",
    tags=["tba"],
    version="1.0",
    retries=3,
    retry_delay_seconds=15,
)
def sync_all_event_rankings(year: int):
    event_keys = get_event_keys_for_year(year=year)

    for event_key in event_keys:
        sync_event_ranks(event_key, year)
