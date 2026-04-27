from __future__ import annotations

from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup

from app.utils import (
    is_internship_title,
    is_germany_only,
    is_it_role,
    extract_skills,
    clean_html_to_text,
)


async def fetch_greenhouse_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    board_token = config["board_token"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    jobs: List[Dict[str, Any]] = []

    for job in payload.get("jobs", []):
        title = job.get("title", "")
        location = (job.get("location") or {}).get("name", "")

        if not is_internship_title(title):
            continue

        # We fetch details later to do stricter filtering
        jobs.append(
            {
                "external_id": str(job.get("id")),
                "company_name": config["name"],
                "source": "greenhouse",
                "title": title,
                "location": location,
                "description": "",
                "skills_required": [],
                "apply_url": job.get("absolute_url", ""),
                "posted_date": None,
            }
        )

    return jobs


async def fetch_greenhouse_job_detail(board_token: str, job_id: str) -> Dict[str, Any]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    content = payload.get("content", "")
    description = clean_html_to_text(content)

    return {
        "description": description,
        "skills_required": extract_skills(description),
    }


async def fetch_ashby_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    org = config["organization_slug"]
    url = f"https://api.ashbyhq.com/posting-api/job-board/{org}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    jobs: List[Dict[str, Any]] = []

    for section in payload.get("jobPostings", []):
        title = section.get("title", "")
        description = clean_html_to_text(section.get("descriptionHtml", ""))
        location = ""

        # Ashby location formats vary
        if isinstance(section.get("location"), dict):
            location = section["location"].get("name", "")
        elif isinstance(section.get("location"), str):
            location = section.get("location", "")
        elif section.get("locationId"):
            location = str(section.get("locationId"))

        if not is_internship_title(title):
            continue

        if not is_germany_only(location, description, config.get("location_hint", "")):
            continue

        if not is_it_role(title, description):
            continue

        jobs.append(
            {
                "external_id": str(section.get("id")),
                "company_name": config["name"],
                "source": "ashby",
                "title": title,
                "location": location or "Germany",
                "description": description,
                "skills_required": extract_skills(description),
                "apply_url": section.get("jobUrl", ""),
                "posted_date": None,
            }
        )

    return jobs


async def fetch_lever_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    account = config["account"]
    url = f"https://api.lever.co/v0/postings/{account}?mode=json"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    jobs: List[Dict[str, Any]] = []

    for job in payload:
        title = job.get("text", "")
        categories = job.get("categories", {}) or {}
        location = categories.get("location", "")

        description = clean_html_to_text(
            job.get("descriptionPlain", "") or job.get("description", "")
        )

        if not is_internship_title(title):
            continue

        if not is_germany_only(location, description, config.get("location_hint", "")):
            continue

        if not is_it_role(title, description):
            continue

        jobs.append(
            {
                "external_id": str(job.get("id")),
                "company_name": config["name"],
                "source": "lever",
                "title": title,
                "location": location,
                "description": description,
                "skills_required": extract_skills(description),
                "apply_url": job.get("hostedUrl", ""),
                "posted_date": None,
            }
        )

    return jobs


async def fetch_custom_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    careers_url = config["careers_url"]

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(careers_url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")
    _ = soup.get_text(" ", strip=True)

    # No fake jobs returned here.
    # Custom providers need company-specific parsers later.
    return []