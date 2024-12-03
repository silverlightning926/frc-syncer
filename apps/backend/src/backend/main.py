from datetime import datetime, timedelta

from flows.sync_tba import sync_tba_data
from prefect.client.schemas.schedules import IntervalSchedule
from services.db_service import get_last_synced
from settings import settings

if __name__ == "__main__":
    last_synced: datetime = get_last_synced()

    if not last_synced or last_synced < datetime.now() - settings.sync_delta:
        print("No last sync found. Syncing data.")
        sync_tba_data()
        last_synced = datetime.now()

    else:
        print("Last sync found.")

    print("Scheduling sync.")
    sync_tba_data.serve(
        name="Sync TBA Data",
        schedules=[
            IntervalSchedule(
                anchor_date=last_synced,
                interval=settings.sync_delta,
                timezone="America/Los_Angeles",
            )
        ]
    )
