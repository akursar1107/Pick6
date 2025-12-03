"""NFL data ingestion service"""

import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class NFLIngestService:
    """Service for ingesting NFL data from BallDontLie API"""

    def __init__(self):
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = settings.BALLDONTLIE_API_KEY

    async def fetch_games(
        self,
        season: Optional[int] = None,
        week: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch games from BallDontLie API"""
        # TODO: Implement actual API call
        # This is a placeholder
        async with httpx.AsyncClient() as client:
            params = {}
            if season:
                params["seasons[]"] = season
            if week:
                params["per_page"] = 100  # Adjust as needed
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await client.get(
                f"{self.base_url}/games",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def fetch_teams(self) -> Dict[str, Any]:
        """Fetch teams from BallDontLie API"""
        # TODO: Implement actual API call
        async with httpx.AsyncClient() as client:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await client.get(
                f"{self.base_url}/teams",
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def fetch_players(self, team_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch players from BallDontLie API"""
        # TODO: Implement actual API call
        async with httpx.AsyncClient() as client:
            params = {}
            if team_id:
                params["team_ids[]"] = team_id
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await client.get(
                f"{self.base_url}/players",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

