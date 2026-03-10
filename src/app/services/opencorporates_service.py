# src/app/services/opencorporates_service.py
"""
OpenCorporates API Client.

This module provides a thread-safe, asynchronous client for interacting with
the OpenCorporates REST API. It handles jurisdiction-based lookups,
authentication via environment variables, and enforces strict rate-limiting
to comply with the OpenCorporates 'Shared' tier constraints.
"""

import asyncio
import os
import time
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.logger import logger


class OpenCorporatesClient:
    """
    Asynchronous client for fetching verified legal entity data.

    Attributes:
        BASE_URL (str): The root v0.4 API endpoint.
        _last_call_time (float): Class-level timestamp of the most recent API call.
        _lock (asyncio.Lock):
            Global lock to prevent race conditions during rate limiting.
    """
    BASE_URL = "https://api.opencorporates.com/v0.4"

    # Class-level state to enforce the 2 calls/s limit globally across the app.
    # Essential for preventing 403 Forbidden responses during concurrent registrations.
    _last_call_time = 0.0
    _lock = asyncio.Lock()

    async def _enforce_rate_limit(self) -> None:
        """
        Ensures a maximum rate of 2 requests per second.

        Calculates the delta since the last call and forces an asyncio.sleep
        if the request frequency is too high.
        """
        async with self._lock:
            now = time.time()
            time_since_last = now - self._last_call_time
            if time_since_last < 0.5:
                sleep_time = 0.5 - time_since_last
                logger.debug(
                    f"Rate limiting active: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            OpenCorporatesClient._last_call_time = time.time()

    # TODO: Enforce max 100 API calls per day as per UTC (Daily Quota Management)
    # TODO: Enforce max 5000 API calls per month as per UTC (Monthly Quota Management)

    async def get_company_details(
        self, company_number: str, jurisdiction_code: str = "gb"
    ) -> Any | dict[str, Any]:
        """
        Fetches official company data from the OpenCorporates registry.

        Args:
            company_number (str): The official registration number (e.g., '00002067').
            jurisdiction_code (str): The 2-letter ISO country/state code.
                                     Defaults to 'gb'.

        Returns:
            dict: The 'company' nested dictionary from the OpenCorporates response.

        Raises:
            HTTPException:
                - 404: Company not found.
                - 429: Rate limit exceeded (mapped from 403 Forbidden).
                - 502: External network or upstream API error.
        """

        await self._enforce_rate_limit()

        url = f"{self.BASE_URL}/companies/{jurisdiction_code}/{company_number}"

        # API token is retrieved from env; if missing, calls are made anonymously
        # (subject to even stricter rate limits).
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
                    status_code=502, detail="External API network error."
                ) from None

            # Error Handling Matrix
            if response.status_code == 404:
                logger.warning(
                    f"OpenCorporates lookup failed: \
                        Company {company_number} not found.")
                raise HTTPException(
                    status_code=404, detail=f"Company {company_number} not found."
                )
            elif response.status_code == 403:
                # OpenCorporates often returns 403 when the rate limit is hit
                # instead of a 429, so we map it for better API semantics.
                logger.error(
                    "OpenCorporates rate limit exceeded or \
                        API key invalid (403 Forbidden).")
                raise HTTPException(
                    status_code=429, detail="OpenCorporates API rate limit exceeded."
                )
            elif response.status_code != 200:
                logger.error(
                    f"OpenCorporates returned unexpected status code: \
                        {response.status_code}")
                raise HTTPException(
                    status_code=502, detail="External API error.")

            logger.debug(
                f"Successfully retrieved OpenCorporates payload for {company_number}")
            data = response.json()

            # Navigate the nested JSON structure: results -> company
            return data.get("results", {}).get("company", {})
