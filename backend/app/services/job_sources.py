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


async def fetch_adzuna_jobs(
    query: str,
    location: Optional[str] = None,
    salary_min: Optional[float] = None,
    page: int = 1,
    results_per_page: int = 20,
) -> list[dict]:
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
    if salary_min:
        params["salary_min"] = salary_min

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Adzuna rechazo la peticion ({e.response.status_code}). "
                "Revisa que ADZUNA_APP_ID / ADZUNA_APP_KEY sean correctos."
            ) from e
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


JOOBLE_BASE_URL = "https://jooble.org/api"


def _parse_jooble_salary(salary_str: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    """Jooble regresa el salario como texto libre (ej. '17,600 UAH' o '$25,000 - $35,000').
    Se intenta extraer un numero simple; si no se puede, se deja vacio (no se inventa)."""
    if not salary_str:
        return None, None
    import re
    numbers = re.findall(r"[\d,]+", salary_str)
    numbers = [float(n.replace(",", "")) for n in numbers if n.replace(",", "").isdigit()]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers), max(numbers)


async def fetch_jooble_jobs(
    query: str,
    location: Optional[str] = None,
    salary_min: Optional[float] = None,
    page: int = 1,
) -> list[dict]:
    """Regresa vacantes normalizadas desde la API gratuita de Jooble (jooble.org/api/about).
    Jooble agrega vacantes de miles de fuentes distintas a las de Adzuna, ampliando cobertura."""
    if not settings.jooble_api_key:
        raise RuntimeError(
            "Falta configurar JOOBLE_API_KEY. Registrate gratis en "
            "https://jooble.org/api/about y llena esa variable en .env"
        )

    url = f"{JOOBLE_BASE_URL}/{settings.jooble_api_key}"
    body = {"keywords": query, "page": str(page)}
    if location:
        body["location"] = location
    if salary_min:
        body["salary"] = int(salary_min)

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, json=body)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Jooble rechazo la peticion ({e.response.status_code}). "
                "Revisa que JOOBLE_API_KEY sea correcta."
            ) from e
        data = resp.json()

    jobs = []
    for item in data.get("jobs", []):
        sal_min, sal_max = _parse_jooble_salary(item.get("salary"))
        jobs.append({
            "source": "jooble",
            "external_id": str(item.get("id")),
            "title": (item.get("title") or "").strip(),
            "company": item.get("company"),
            "location": item.get("location"),
            "description": item.get("snippet", ""),
            "url": item.get("link", ""),
            "salary_min": sal_min,
            "salary_max": sal_max,
            "remote": "remoto" in (item.get("title", "") + item.get("snippet", "")).lower()
                      or "remote" in (item.get("title", "") + item.get("snippet", "")).lower(),
            "posted_at": _parse_date(item.get("updated")),
        })
    return jobs
