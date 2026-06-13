from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests


class CedaApiError(RuntimeError):
    """Raised when the CEDA API request cannot be completed."""


@dataclass
class CedaAgmarknetClient:
    base_url: str = "https://api.ceda.ashoka.edu.in/v1"
    token: str | None = None
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.token = self.token or os.getenv("CEDA_API_TOKEN")

    def commodities(self) -> dict[str, Any]:
        return self._request("GET", "/agmarknet/commodities")

    def geographies(self) -> dict[str, Any]:
        return self._request("GET", "/agmarknet/geographies")

    def markets(
        self,
        commodity_id: int,
        state_id: int,
        district_id: int,
        indicator: str = "price",
    ) -> dict[str, Any]:
        payload = {
            "commodity_id": commodity_id,
            "state_id": state_id,
            "district_id": district_id,
            "indicator": indicator,
        }
        return self._request("POST", "/agmarknet/markets", json=payload)

    def prices(
        self,
        commodity_id: int,
        state_id: int,
        from_date: str,
        to_date: str,
        district_ids: list[int] | None = None,
        market_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "commodity_id": commodity_id,
            "state_id": state_id,
            "from_date": from_date,
            "to_date": to_date,
        }
        if district_ids:
            payload["district_id"] = district_ids
        if market_ids:
            payload["market_id"] = market_ids
        return self._request("POST", "/agmarknet/prices", json=payload)

    def quantities(
        self,
        commodity_id: int,
        state_id: int,
        from_date: str,
        to_date: str,
        district_ids: list[int] | None = None,
        market_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "commodity_id": commodity_id,
            "state_id": state_id,
            "from_date": from_date,
            "to_date": to_date,
        }
        if district_ids:
            payload["district_id"] = district_ids
        if market_ids:
            payload["market_id"] = market_ids
        return self._request("POST", "/agmarknet/quantities", json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if not self.token:
            raise CedaApiError("CEDA_API_TOKEN is required for CEDA API requests.")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        extra_headers = kwargs.pop("headers", None)
        if extra_headers:
            headers.update(extra_headers)

        url = f"{self.base_url}{path}"
        response: requests.Response | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.timeout_seconds,
                    **kwargs,
                )
            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    raise CedaApiError(f"CEDA API request failed after retries: {exc}") from exc
                time.sleep(self.retry_backoff_seconds * attempt)
                continue

            if response.status_code not in {429, 500, 502, 503, 504}:
                break
            if attempt == self.max_retries:
                break
            time.sleep(self.retry_backoff_seconds * attempt)

        if response is None:
            raise CedaApiError("CEDA API request failed before receiving a response.")

        if response.status_code == 401:
            raise CedaApiError("CEDA API rejected the token with 401 Unauthorized.")
        if response.status_code == 429:
            raise CedaApiError("CEDA API rate limit reached with 429 Too Many Requests.")

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise CedaApiError(f"CEDA API request failed: {response.status_code}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise CedaApiError("CEDA API returned a non-JSON response.") from exc

        if not isinstance(payload, dict):
            raise CedaApiError("CEDA API returned an unexpected JSON shape.")
        return payload
