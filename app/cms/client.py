"""HTTP REST Client for upstream Clinic Management System (CMS)."""

from __future__ import annotations

import httpx
from typing import Any


class CMSClient:
    """REST client connecting to the existing Clinic Management System."""

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_consultation(self, encounter_id: str, auth_token: str | None = None) -> dict[str, Any]:
        """Fetch consultation data from CMS system of record."""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/consultations/{encounter_id}",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

