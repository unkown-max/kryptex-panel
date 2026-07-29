from typing import AsyncGenerator

from pasarguard import PasarguardAPI

from .config import PASARGUARD_BASE_URL


async def get_client() -> AsyncGenerator[PasarguardAPI, None]:
    """FastAPI dependency that yields a fresh PasarGuard API client per request."""
    async with PasarguardAPI(base_url=PASARGUARD_BASE_URL, verify=True, timeout=20.0) as api:
        yield api
