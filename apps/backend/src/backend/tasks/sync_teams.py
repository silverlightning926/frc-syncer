import os
import time

import requests
from models.db.tba_page_etag import TBAPageEtag
from models.tba.team_simple import TeamSimple
from prefect import task
from services.db_service import (get_tba_teams_page_etag, upsert_tba_page_etag,
                                 upsert_teams)
from settings import settings

HEADERS = {"X-TBA-Auth-Key": os.getenv("TBA_API_KEY")}


@task(
    name="Fetch Teams",
    description="Fetches all teams for the current season.",
    tags=["tba"],
    version="1.0"
)
def fetch_teams(page_interval_secs: int = 10):
    page_num = 0

    while True:
        etag: TBAPageEtag = get_tba_teams_page_etag(page_num)
        headers = HEADERS.copy()
        if etag:
            headers["If-None-Match"] = etag.etag

        try:
            response = requests.get(
                f"https://www.thebluealliance.com/api/v3/teams/{
                    settings.season}/{page_num}/simple",
                headers=headers
            )

            if response.status_code == 304:
                print(f"Teams Page {page_num}: ETAG match. Skipping.")
            elif response.status_code != 200:
                print(f"Team Page {page_num}: Failed Getting Teams From Page. Status Code {
                      response.status_code}.")
            else:
                teams = [TeamSimple(**team) for team in response.json()]

                if not teams:
                    break

                upsert_teams(teams)
                new_etag = TBAPageEtag(
                    page_num=page_num, etag=response.headers.get("ETag"), endpoint="teams"
                )
                if new_etag:
                    upsert_tba_page_etag(new_etag)

                print(f"Team Page {page_num}: Fetched {len(teams)} teams.")

            page_num += 1
            time.sleep(page_interval_secs)

        except requests.RequestException as e:
            print(f"Error fetching teams: {e}")
            break
