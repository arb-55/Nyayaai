# NyayaAI

**AI-Assisted Multi-Agent Legal Document Analysis System for Indian Court Cases**

> ⚠️ NyayaAI is an **assistive analytical tool**. It does NOT replace judges, make legally binding decisions, or produce autonomous legal rulings. All AI-generated observations are clearly labeled as machine-generated assistive output.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS v3 |
| Backend | Python, FastAPI |
| AI Agents | LangGraph, Google Gemini |
| NLP | spaCy, OpenNyAI |
| Database | PostgreSQL 16 |
| PDF Processing | pdfplumber |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone & Configure

```bash
git clone <repo-url>
cd nyayaai
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

## Project Structure

```
nyayaai/
├── backend/          # FastAPI + LangGraph + NLP
├── frontend/         # React + Tailwind
├── docs/             # Documentation
└── docker-compose.yml
```

## Team

Final Year B.Tech Project
