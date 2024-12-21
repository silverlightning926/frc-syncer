from datetime import datetime

from prefect import flow

from tasks.sync_tba_year import sync_tba_data_for_year
from settings import settings


@flow(
    name="Download Historic Data",
    description="Downloads historic data for all seasons.",
    version="1.0",
    retries=3,
    retry_delay_seconds=15,
)
def download_historic():
    for season in settings.HISTORIC_SEASONS:
        sync_tba_data_for_year(season)
        print(f"Synced data for {season} at {datetime.now()}")


if __name__ == "__main__":
    download_historic()
