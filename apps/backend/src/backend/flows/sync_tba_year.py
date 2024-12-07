from time import sleep

from prefect import flow, task
from tasks.sync_event_ranks import sync_all_event_rankings, sync_event_ranks
from services.db_service import insert_sync_timestamp
from tasks.sync_event_matches import sync_all_event_matches
from tasks.sync_events import fetch_events
from tasks.sync_teams import fetch_teams


@task
def throttle_request(interval_secs=60):
    sleep(interval_secs)


@task
def log_sync_timestamp(year: int):
    insert_sync_timestamp(year=year)


@flow(
    name="Sync TBA Data For Year",
    description="Syncs data from The Blue Alliance API for a given year",
    version="1.0",
)
def sync_tba_data_for_year(year: int):
    # fetch_teams(year=year)

    # fetch_events(year=year)

    # sync_all_event_matches(year=year)
    
    sync_all_event_rankings(year=year)

    throttle_request()

    log_sync_timestamp(year=year)
