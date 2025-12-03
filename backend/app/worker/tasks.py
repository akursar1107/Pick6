"""Background tasks for data ingestion"""

import asyncio
from datetime import datetime
from app.services.nfl_ingest import NFLIngestService
from app.db.session import AsyncSessionLocal
from app.services.game_service import GameService


async def sync_nfl_schedule():
    """Sync NFL schedule from BallDontLie API"""
    ingest_service = NFLIngestService()
    
    # Get current season (approximate)
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # NFL season typically runs from September to February
    if current_month >= 9:
        season = current_year
    else:
        season = current_year - 1
    
    try:
        games_data = await ingest_service.fetch_games(season=season)
        # TODO: Process and store games in database
        print(f"Fetched {len(games_data.get('data', []))} games for season {season}")
    except Exception as e:
        print(f"Error syncing NFL schedule: {e}")


async def sync_nfl_teams():
    """Sync NFL teams from BallDontLie API"""
    ingest_service = NFLIngestService()
    
    try:
        teams_data = await ingest_service.fetch_teams()
        # TODO: Process and store teams in database
        print(f"Fetched {len(teams_data.get('data', []))} teams")
    except Exception as e:
        print(f"Error syncing NFL teams: {e}")


async def sync_nfl_players():
    """Sync NFL players from BallDontLie API"""
    ingest_service = NFLIngestService()
    
    try:
        players_data = await ingest_service.fetch_players()
        # TODO: Process and store players in database
        print(f"Fetched {len(players_data.get('data', []))} players")
    except Exception as e:
        print(f"Error syncing NFL players: {e}")


# Example: Run sync tasks periodically
# This would typically be set up with Celery Beat or similar
if __name__ == "__main__":
    asyncio.run(sync_nfl_schedule())

