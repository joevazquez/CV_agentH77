"""
Fuente de vacantes: Adzuna API (https://developer.adzuna.com/).
Es gratuita (con registro) y permite buscar vacantes por pais/palabra clave
de forma legitima -> no requiere scraping ni automatizar navegadores.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx

from app.config import settings

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


async def fetch_adzuna_jobs(query: str, location: Optional[str] = None, page: int = 1, results_per_page: int = 20) -> list[dict]:
    """Regresa una lista de vacantes normalizadas (dicts) listas para guardar como Job."""
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise RuntimeError(
            "Faltan credenciales de Adzuna. Registrate gratis en "
            "https://developer.adzuna.com/ y llena ADZUNA_APP_ID / ADZUNA_APP_KEY en .env"
        )

    url = f"{ADZUNA_BASE_URL}/{settings.adzuna_country}/search/{page}"
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "results_per_page": results_per_page,
        "what": query,
    }
    if location:
        params["where"] = location

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("results", []):
        jobs.append({
            "source": "adzuna",
            "external_id": str(item.get("id")),
            "title": item.get("title", "").strip(),
            "company": (item.get("company") or {}).get("display_name"),
            "location": (item.get("location") or {}).get("display_name"),
            "description": item.get("description", ""),
            "url": item.get("redirect_url", ""),
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "remote": "remoto" in (item.get("title", "") + item.get("description", "")).lower()
                      or "remote" in (item.get("title", "") + item.get("description", "")).lower(),
            "posted_at": _parse_date(item.get("created")),
        })
    return jobs


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
