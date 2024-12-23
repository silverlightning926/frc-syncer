import os
import time

import requests
from prefect import task
from models.tba.tba_page_etag import TBAPageEtag
from models.tba.team import Team
from services.db_service import (
    get_tba_page_etag,
    upsert_tba_page_etag,
    upsert_teams,
)

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task(
    name="Team Sync: Prepare Headers",
    retries=3,
    retry_delay_seconds=15,
)
def prepare_team_headers(page_num, year: int):
    etag = get_tba_page_etag(page_num=page_num, year=year, endpoint="teams")
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task(
    name="Team Sync: Fetch Team Page Data",
    retries=3,
    retry_delay_seconds=15,
)
def fetch_team_page_data(page_num, headers, year: int):
    url = f"https://www.thebluealliance.com/api/v3/teams/{
        year}/{page_num}"
    return requests.get(url, headers=headers)


@task(
    name="Team Sync: Process Team Page Response",
    retries=3,
    retry_delay_seconds=15,
)
def process_team_page_response(page_num, response):
    if response.status_code == 304:
        print(f"Teams Page {page_num}: ETAG match. Skipping.")
        return None
    elif response.status_code != 200:
        print(
            f"Teams Page {page_num}: Failed to fetch. Status Code: {
              response.status_code}"
        )
        return None
    return [Team.from_tba(item) for item in response.json()]


@task(name="Team Sync: Upsert Team Data", retries=3, retry_delay_seconds=15)
def upsert_team_data(page_num, teams, response, year: int):
    if teams:
        upsert_teams(teams)
        print(f"Team Page {page_num}: Fetched {len(teams)} teams.")

    if response.status_code == 200:
        existing_etag = get_tba_page_etag(
            page_num=page_num, year=year, endpoint="teams"
        )

        etag = response.headers.get("ETag")
        upsert_tba_page_etag(
            TBAPageEtag(
                id=existing_etag.id if existing_etag else None,
                page_num=page_num,
                etag=etag,
                endpoint="teams",
                year=year,
            )
        )


@task(
    name="Team Sync: Throttle Request",
    retries=3,
    retry_delay_seconds=15,
)
def throttle_request(interval_secs=5):
    time.sleep(interval_secs)


@task(
    name="Fetch Teams",
    description="Fetches all teams for the current season.",
    tags=["tba"],
    version="1.0",
    retries=3,
    retry_delay_seconds=15,
)
def fetch_teams(year: int):
    page_num = 0
    while True:
        headers = prepare_team_headers(page_num, year)
        response = fetch_team_page_data(page_num, headers, year)
        teams = process_team_page_response(page_num, response)

        if not teams:
            # TODO: Fix to not break if etag page match and [] is returned
            break

        upsert_team_data(page_num, teams, response, year)

        page_num += 1
        throttle_request()
