# src/app/services
import asyncio
import os
import time
from typing import Any

import httpx
from fastapi import HTTPException


class OpenCorporatesClient:
    BASE_URL = "https://api.opencorporates.com/v0.4"

    # Class-level state to enforce the 2 calls/s limit globally across the app
    _last_call_time = 0.0
    _lock = asyncio.Lock()

    async def _enforce_rate_limit(self):
        """Ensures rate of 2 requests /s (0.5s between calls) is never exceeded."""
        async with self._lock:
            now = time.time()
            time_since_last = now - self._last_call_time
            if time_since_last < 0.5:
                await asyncio.sleep(0.5 - time_since_last)
            OpenCorporatesClient._last_call_time = time.time()

    # TODO: Enforce max 100 API calls per day as per UTC
    # TODO: Enforce max 5000 API calls per month as per UTC

    async def get_company_details(self, company_number: str,
                                  jurisdiction_code: str = "gb") -> dict[str, Any]:
        """Fetches official company data from OpenCorporates."""

        await self._enforce_rate_limit()

        url = f"{self.BASE_URL}/companies/{jurisdiction_code}/{company_number}"

        # Inject the API token if it exists in the environment
        api_token = os.environ.get("OPENCORPORATES_API_KEY")
        params = {"api_token": api_token} if api_token else {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404, detail=f"Company {company_number} not found.")
            elif response.status_code == 403:
                raise HTTPException(
                    status_code=429, detail="OpenCorporates API rate limit exceeded.")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=502, detail="External API error.")

            data = response.json()
            return data.get("results", {}).get("company", {})
