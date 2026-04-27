from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:latest")


def build_resume_prompt(
    job_title: str,
    company_name: str,
    job_description: str,
    job_skills: List[str],
    resume_text: str,
    matched_keywords: List[str],
    missing_keywords: List[str],
) -> str:
    return f"""
You are an expert technical resume reviewer and internship application strategist.

Your task:
Analyze the user's CV against a specific internship role and return practical, truthful, highly targeted advice.

Rules:
- Be specific, not generic.
- Do not invent experience the candidate does not have.
- Suggest improvements using the candidate's likely background only if supported by resume text.
- Optimize for internships in software engineering, Python, AI, ML, backend, full-stack, or data roles.
- Prefer concise, recruiter-friendly writing.
- If the candidate already has a strong point, say so.
- Focus on what should be changed in the CV before applying.

Return valid JSON only with this exact structure:
{{
  "fit_summary": "2-4 sentence summary",
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "exact_changes": ["...", "..."],
  "rewritten_summary": "A tailored 2-3 line professional summary",
  "rewritten_bullets": [
    "Bullet rewrite 1",
    "Bullet rewrite 2",
    "Bullet rewrite 3"
  ],
  "project_order_advice": "Short suggestion on which project to move higher and why",
  "final_verdict": "ready_to_apply | apply_after_minor_edits | needs_major_tailoring"
}}

Job title:
{job_title}

Company:
{company_name}

Job skills:
{", ".join(job_skills) if job_skills else "Not explicitly extracted"}

Matched keywords:
{", ".join(matched_keywords) if matched_keywords else "None"}

Missing keywords:
{", ".join(missing_keywords) if missing_keywords else "None"}

Job description:
{job_description}

Resume text:
{resume_text}
""".strip()


async def generate_llm_resume_advice(
    job_title: str,
    company_name: str,
    job_description: str,
    job_skills: List[str],
    resume_text: str,
    matched_keywords: List[str],
    missing_keywords: List[str],
) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return {
            "fit_summary": "LLM advice is unavailable because OPENAI_API_KEY is not set.",
            "strengths": [],
            "weaknesses": [],
            "exact_changes": [],
            "rewritten_summary": "",
            "rewritten_bullets": [],
            "project_order_advice": "",
            "final_verdict": "apply_after_minor_edits",
        }

    prompt = build_resume_prompt(
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
        job_skills=job_skills,
        resume_text=resume_text,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
    )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "You are a precise technical resume optimizer. Output only valid JSON.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    }
                ],
            },
        ],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    text_output = ""

    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text_output += content.get("text", "")

    text_output = text_output.strip()

    try:
        return json.loads(text_output)
    except Exception:
        return {
            "fit_summary": "The LLM returned a non-JSON response. Review the raw advice below.",
            "strengths": [],
            "weaknesses": [],
            "exact_changes": [text_output] if text_output else [],
            "rewritten_summary": "",
            "rewritten_bullets": [],
            "project_order_advice": "",
            "final_verdict": "apply_after_minor_edits",
        }