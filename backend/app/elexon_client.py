import httpx
from typing import List, Dict, Any
from .config import Config
from .cache import cache

class ElexonClient:
    def __init__(self, base_url: str = Config.ELEXON_BASE_URL):
        self.base_url = base_url

    async def get_actual_generation(self, settlement_date: str) -> List[Dict[str, Any]]:
        """
        Fetch FUELHH actual wind generation for a specific settlement date (YYYY-MM-DD).
        """
        cache_key = f"FUELHH_{settlement_date}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/datasets/FUELHH/stream"
        params = {
            "settlementDateFrom": settlement_date,
            "settlementDateTo": settlement_date,
            "fuelType": "WIND"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        cache.set(cache_key, data)
        return data

    async def get_forecasts(self, publish_from: str, publish_to: str) -> List[Dict[str, Any]]:
        """
        Fetch WINDFOR wind forecasts published within a specific window.
        """
        cache_key = f"WINDFOR_{publish_from}_{publish_to}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/datasets/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": publish_from,
            "publishDateTimeTo": publish_to
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        cache.set(cache_key, data)
        return data

elexon_client = ElexonClient()
