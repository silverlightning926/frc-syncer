from prefect import flow
from services.db_service import insert_last_sync
from tasks.sync_events import fetch_events
from tasks.sync_teams import fetch_teams


@flow(
    name="Sync TBA Data",
    description="Syncs data from The Blue Alliance API.",
    version="1.0",
)
def sync_tba_data():
    teams = fetch_teams.submit()
    events = fetch_events.submit()

    teams.result()
    events.result()

    insert_last_sync()
