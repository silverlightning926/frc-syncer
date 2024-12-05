from prefect import flow
from tasks.sync_event_matches import sync_all_event_matches
from tasks.sync_events import fetch_events
from tasks.sync_teams import fetch_teams


@flow(
    name="Sync TBA Data For Year",
    description="Syncs data from The Blue Alliance API for a given year",
    version="1.0",
)
def sync_tba_data_for_year(year: int):
    fetch_teams(year=year)

    fetch_events(year=year)

    sync_all_event_matches(year=year)
