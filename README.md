# InternPilot 🚀

InternPilot is an AI-powered platform designed to help users discover internships and optimize their resumes using LLM-based insights. It focuses on IT, AI, and ML roles and is tailored for students targeting opportunities in Germany.

---

## 🔥 Features

- 🔍 Fetch internships from multiple company sources
- 🤖 AI Resume Advisor (LLM-powered suggestions)
- 🌍 Focus on IT / AI / ML roles (Germany-ready)
- ⚡ FastAPI backend
- 🧠 Modular architecture (scrapers + AI modules)

---

## 🛠 Tech Stack

- Python
- FastAPI
- Streamlit (optional frontend)
- PostgreSQL
- SQLAlchemy
- Ollama (LLM)

---

## 📁 Project Structure
InterPilot/
│
├── backend/
│ ├── app/
│ │ ├── main.py # FastAPI entry point
│ │ ├── job_fetchers.py # Internship scraping logic
│ │ ├── company_sources.py # Company career sources
│ │ ├── llm_resume_advisor.py # AI resume analysis
│ │ └── utils.py # Helper functions
│ │
│ ├── requirements.txt
│ └── .env

---

## ⚙️ Setup & Run

### 1. Clone the repository

```bash
git clone https://github.com/Namidok/internPilot.git
cd InterPilot/backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/dbname
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.1
MAX_CONTEXT_MESSAGES=50

uvicorn app.main:app --reload

http://127.0.0.1:8000/docs

