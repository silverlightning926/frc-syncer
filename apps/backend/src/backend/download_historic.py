from datetime import datetime

from flows.sync_tba_year import sync_tba_data_for_year
from settings import settings

if __name__ == "__main__":
    for season in settings.historic_seasons:
        sync_tba_data_for_year(season)
        print(f"Synced data for {season} at {datetime.now()}")
