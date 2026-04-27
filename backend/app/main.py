from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PyPDF2 import PdfReader
from docx import Document
from app.llm_resume_advisor import generate_llm_resume_advice

from app.company_sources import COMPANY_SOURCES
from app.job_fetchers import (
    fetch_greenhouse_jobs,
    fetch_greenhouse_job_detail,
    fetch_ashby_jobs,
    fetch_lever_jobs,
    fetch_custom_jobs,
)
from app.utils import extract_skills, is_germany_only, is_it_role


app = FastAPI(title="InternPilot API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Internship(BaseModel):
    id: int
    external_id: str
    company_name: str
    source: str
    title: str
    location: str
    description: str
    skills_required: List[str]
    apply_url: str
    posted_date: Optional[str] = None
    fetched_at: str


class ATSResult(BaseModel):
    internship_id: int
    file_name: str
    ats_score: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggestions: List[str]
    extracted_preview: str
    fit_summary: str = ""
    strengths: List[str] = []
    weaknesses: List[str] = []
    exact_changes: List[str] = []
    rewritten_summary: str = ""
    rewritten_bullets: List[str] = []
    project_order_advice: str = ""
    final_verdict: str = ""


LIVE_INTERNSHIPS: List[Internship] = []
LAST_REFRESH_AT: Optional[str] = None


async def refresh_jobs() -> Dict[str, str]:
    global LIVE_INTERNSHIPS, LAST_REFRESH_AT

    all_jobs: List[Internship] = []
    next_id = 1

    for source in COMPANY_SOURCES:
        try:
            provider = source["provider"]
            jobs: List[Dict] = []

            if provider == "greenhouse":
                jobs = await fetch_greenhouse_jobs(source)

                if source.get("board_token"):
                    detailed_jobs: List[Dict] = []

                    for job in jobs:
                        try:
                            detail = await fetch_greenhouse_job_detail(
                                source["board_token"],
                                job["external_id"],
                            )
                            job["description"] = detail["description"]
                            job["skills_required"] = detail["skills_required"]

                            if not is_germany_only(
                                job.get("location", ""),
                                job.get("description", ""),
                                source.get("location_hint", ""),
                            ):
                                continue

                            if not is_it_role(
                                job.get("title", ""),
                                job.get("description", ""),
                            ):
                                continue

                            detailed_jobs.append(job)

                        except Exception as detail_exc:
                            print(
                                f"Failed to fetch Greenhouse detail for {source['name']} job {job.get('external_id')}: {detail_exc}"
                            )
                            continue

                    jobs = detailed_jobs

            elif provider == "ashby":
                jobs = await fetch_ashby_jobs(source)

            elif provider == "lever":
                jobs = await fetch_lever_jobs(source)

            else:
                jobs = await fetch_custom_jobs(source)

            for job in jobs:
                all_jobs.append(
                    Internship(
                        id=next_id,
                        external_id=job["external_id"],
                        company_name=job["company_name"],
                        source=job["source"],
                        title=job["title"],
                        location=job["location"],
                        description=job["description"],
                        skills_required=job["skills_required"],
                        apply_url=job["apply_url"],
                        posted_date=job.get("posted_date"),
                        fetched_at=datetime.utcnow().isoformat(),
                    )
                )
                next_id += 1

        except Exception as exc:
            print(f"Failed to fetch jobs for {source['name']}: {exc}")

    LIVE_INTERNSHIPS = all_jobs
    LAST_REFRESH_AT = datetime.utcnow().isoformat()

    return {
        "status": "ok",
        "jobs_count": str(len(LIVE_INTERNSHIPS)),
        "refreshed_at": LAST_REFRESH_AT or "",
    }


def extract_text_from_file_bytes(file_name: str, file_bytes: bytes) -> str:
    lower_name = file_name.lower()

    if lower_name.endswith(".pdf"):
        reader = PdfReader(BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    if lower_name.endswith(".docx"):
        doc = Document(BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()

    return file_bytes.decode("utf-8", errors="ignore").strip()



async def analyze_resume_against_job(
    internship: Internship,
    resume_text: str,
    file_name: str,
) -> ATSResult:
    resume_lower = resume_text.lower()
    job_text = (
        f"{internship.title} {internship.description} {' '.join(internship.skills_required)}"
    ).lower()

    target_keywords = sorted(set(extract_skills(job_text)))
    matched = [kw for kw in target_keywords if kw in resume_lower]
    missing = [kw for kw in target_keywords if kw not in resume_lower]

    keyword_score = int((len(matched) / len(target_keywords)) * 60) if target_keywords else 0
    project_score = 15 if "project" in resume_lower or "projects" in resume_lower else 0
    experience_score = 15 if "experience" in resume_lower else 0
    structure_score = 10 if all(word in resume_lower for word in ["skills", "education"]) else 0

    ats_score = min(keyword_score + project_score + experience_score + structure_score, 100)

    suggestions: List[str] = []

    if missing:
        suggestions.append(
            f"Add or strengthen these keywords where truthful and relevant: {', '.join(missing[:10])}."
        )
    if "fastapi" in job_text and "fastapi" not in resume_lower:
        suggestions.append("Add a bullet showing API work with FastAPI or similar backend frameworks.")
    if "docker" in job_text and "docker" not in resume_lower:
        suggestions.append("Mention containerization or deployment experience if you have used Docker.")
    if "react" in job_text and "react" not in resume_lower:
        suggestions.append("Highlight React-based frontend work in your projects or experience section.")
    if "sql" in job_text and "sql" not in resume_lower:
        suggestions.append("Make SQL and database work more visible in your technical skills and project bullets.")
    if len(resume_text.split()) < 180:
        suggestions.append("Your CV may be too light for ATS matching. Add stronger project bullets with impact and tools used.")
    if "templeswiki" not in resume_lower:
        suggestions.append("Include your TemplesWiki project clearly, especially backend APIs, React UI, database work, and deployment details.")
    if not suggestions:
        suggestions.append(
            "Your CV is reasonably aligned. Tailor the top summary and first two project bullets to mirror the job language more closely."
        )

    llm_advice = await generate_llm_resume_advice(
        job_title=internship.title,
        company_name=internship.company_name,
        job_description=internship.description,
        job_skills=internship.skills_required,
        resume_text=resume_text[:12000],
        matched_keywords=matched,
        missing_keywords=missing,
    )

    return ATSResult(
        internship_id=internship.id,
        file_name=file_name,
        ats_score=ats_score,
        matched_keywords=matched,
        missing_keywords=missing,
        suggestions=suggestions,
        extracted_preview=resume_text[:400] if resume_text else "No text extracted.",
        fit_summary=llm_advice.get("fit_summary", ""),
        strengths=llm_advice.get("strengths", []),
        weaknesses=llm_advice.get("weaknesses", []),
        exact_changes=llm_advice.get("exact_changes", []),
        rewritten_summary=llm_advice.get("rewritten_summary", ""),
        rewritten_bullets=llm_advice.get("rewritten_bullets", []),
        project_order_advice=llm_advice.get("project_order_advice", ""),
        final_verdict=llm_advice.get("final_verdict", ""),
    )

@app.on_event("startup")
async def startup_refresh() -> None:
    await refresh_jobs()


@app.get("/")
def root():
    return {
        "message": "InternPilot live API",
        "jobs_loaded": len(LIVE_INTERNSHIPS),
        "last_refresh_at": LAST_REFRESH_AT,
    }


@app.post("/refresh-jobs")
async def refresh_jobs_endpoint():
    return await refresh_jobs()


@app.get("/internships", response_model=List[Internship])
def get_internships():
    return LIVE_INTERNSHIPS


@app.get("/internships/{internship_id}", response_model=Internship)
def get_internship(internship_id: int):
    internship = next((job for job in LIVE_INTERNSHIPS if job.id == internship_id), None)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship


@app.post("/ats/analyze", response_model=ATSResult)
async def ats_analyze(
    internship_id: int = Form(...),
    file: UploadFile = File(...),
):
    internship = next((job for job in LIVE_INTERNSHIPS if job.id == internship_id), None)
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    file_bytes = await file.read()
    resume_text = extract_text_from_file_bytes(file.filename, file_bytes)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file")

    return await analyze_resume_against_job(internship, resume_text, file.filename)