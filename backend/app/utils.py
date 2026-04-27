from typing import List
import re
import html
from bs4 import BeautifulSoup

INTERNSHIP_KEYWORDS = [
    "intern",
    "internship",
    "working student",
    "werkstudent",
    "student",
]

GERMANY_KEYWORDS = [
    "germany",
    "berlin",
    "munich",
    "münchen",
    "hamburg",
    "stuttgart",
    "cologne",
    "köln",
    "frankfurt",
    "düsseldorf",
    "duesseldorf",
    "remote germany",
    "hybrid germany",
]

IT_KEYWORDS = [
    "software",
    "developer",
    "engineer",
    "backend",
    "frontend",
    "full stack",
    "full-stack",
    "data",
    "machine learning",
    "ml",
    "ai",
    "artificial intelligence",
    "python",
    "cloud",
    "devops",
    "platform",
    "api",
    "apis",
    "analytics",
    "data engineer",
    "data engineering",
    "data scientist",
    "data science",
    "nlp",
    "llm",
    "deep learning",
    "computer vision",
    "pytorch",
    "tensorflow",
]

SKILL_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "sql",
    "postgresql",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "fastapi",
    "flask",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "nlp",
    "llm",
    "langchain",
    "rag",
    "pandas",
    "numpy",
    "spark",
    "airflow",
    "etl",
    "data pipelines",
    "api",
    "apis",
    "git",
]


def is_internship_title(title: str) -> bool:
    text = (title or "").lower()
    return any(keyword in text for keyword in INTERNSHIP_KEYWORDS)


def is_germany_only(location: str, description: str = "", hint: str = "") -> bool:
    combined = f"{location or ''} {description or ''} {hint or ''}".lower()
    return any(keyword in combined for keyword in GERMANY_KEYWORDS)


def is_it_role(title: str, description: str = "") -> bool:
    text = f"{title or ''} {description or ''}".lower()
    return any(keyword in text for keyword in IT_KEYWORDS)


def extract_skills(text: str) -> List[str]:
    lower = (text or "").lower()
    found = [skill for skill in SKILL_KEYWORDS if skill in lower]
    return sorted(set(found))


def clean_html_to_text(html_text: str) -> str:
    if not html_text:
        return ""

    decoded = html.unescape(html_text)
    soup = BeautifulSoup(decoded, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text.strip()