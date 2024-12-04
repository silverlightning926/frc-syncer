import os
import time

import requests
from models.db.tba_page_etag import TBAPageEtag
from models.tba.team_simple import TeamSimple
from prefect import task
from services.db_service import (
    get_tba_teams_page_etag,
    upsert_tba_page_etag,
    upsert_teams,
)
from settings import settings

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task
def prepare_team_headers(page_num):
    etag = get_tba_teams_page_etag(page_num)
    headers = HEADERS.copy()
    if etag:
        headers["If-None-Match"] = etag.etag
    return headers


@task
def fetch_team_page_data(page_num, headers):
    url = f"https://www.thebluealliance.com/api/v3/teams/{
        settings.season}/{page_num}/simple"
    return requests.get(url, headers=headers)


@task
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
    return [TeamSimple(**team) for team in response.json()]


@task
def upsert_team_data(page_num, teams, response):
    if teams:
        upsert_teams(teams)
        new_etag = TBAPageEtag(
            page_num=page_num,
            etag=response.headers.get("ETag"),
            endpoint="teams",
        )
        upsert_tba_page_etag(new_etag)
        print(f"Team Page {page_num}: Fetched {len(teams)} teams.")


@task
def throttle_request(interval_secs=10):
    time.sleep(interval_secs)


@task(
    name="Fetch Teams",
    description="Fetches all teams for the current season.",
    tags=["tba"],
    version="1.0",
)
def fetch_teams():
    page_num = 0
    while True:
        headers = prepare_team_headers(page_num)
        response = fetch_team_page_data(page_num, headers)
        teams = process_team_page_response(page_num, response)

        if not teams:
            # TODO: Fix to not break if etag page match and [] is returned
            break

        upsert_team_data(page_num, teams, response)

        page_num += 1
        throttle_request()
