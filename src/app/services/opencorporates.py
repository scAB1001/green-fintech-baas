# src/app/services/opencorporates.py
import asyncio
import os
import time
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.logger import logger


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
                sleep_time = 0.5 - time_since_last
                logger.debug(
                    f"Rate limiting active: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
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

        logger.info(
            f"Calling external API: \
                OpenCorporates ({jurisdiction_code}/{company_number})")

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params)
            except httpx.RequestError as e:
                logger.error(
                    f"Network error while connecting to OpenCorporates: {e!s}")
                raise HTTPException(
                    status_code=502, detail="External API network error.") from None

            if response.status_code == 404:
                logger.warning(
                    f"OpenCorporates lookup failed: \
                        Company {company_number} not found.")
                raise HTTPException(
                    status_code=404, detail=f"Company {company_number} not found.")
            elif response.status_code == 403:
                logger.error(
                    "OpenCorporates rate limit exceeded or \
                        API key invalid (403 Forbidden).")
                raise HTTPException(
                    status_code=429, detail="OpenCorporates API rate limit exceeded.")
            elif response.status_code != 200:
                logger.error(
                    f"OpenCorporates returned \
                        unexpected status code: {response.status_code}")
                raise HTTPException(
                    status_code=502, detail="External API error.")

            logger.debug(
                f"Successfully retrieved OpenCorporates payload for {company_number}")
            data = response.json()
            return data.get("results", {}).get("company", {})
