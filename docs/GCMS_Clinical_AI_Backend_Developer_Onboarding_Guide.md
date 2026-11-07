# GCMS Clinical AI Backend — Developer Onboarding & Run Guide

> **Target Audience:** New Backend Engineers, Full-Stack Developers, DevOps  
> **Prerequisites:** Python 3.11+, Docker Desktop / Colima, Ollama (native macOS / Linux)  
> **Repository:** `https://github.com/HponeMyatThu/Clinic-ai.git`

---

## 1. Quick Prerequisites

Before running the project, ensure you have:
1. **Python 3.11 or 3.12** installed (`brew install python@3.12` on macOS).
2. **Docker & Docker Compose** (Docker Desktop or Colima) running for PostgreSQL 16 and Redis.
3. **Ollama** installed natively on your host machine (`brew install ollama`).

---

## 2. Step-by-Step Setup

### Step 2.1: Clone and Create Virtual Environment

```bash
git clone https://github.com/HponeMyatThu/Clinic-ai.git gcms_ai_backend
cd gcms_ai_backend

python3 -m venv .venv
source .venv/bin/activate
```

### Step 2.2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2.3: Environment Configuration

```bash
cp .env.example .env
```

---

## 3. Starting Supporting Services

### Step 3.1: Start PostgreSQL and Redis (Docker)

```bash
docker compose up -d
```
Verify the container status:
```bash
docker compose ps
```

### Step 3.2: Start Local Ollama and Pull Model

```bash
# Start daemon in terminal
ollama serve

# In a separate terminal, pull the recommended 8B reasoning model:
ollama pull qwen3:8b
# (Alternative tested model: ollama pull llama3.1:8b)
```

---

## 4. Database Seeding & Schema Verification

Populate the local PostgreSQL database with 50 primary care SNOMED CT concepts and 40 Singapore Drug Dictionary (SDD) medications:

```bash
python -m scripts.seed_dev_data
```

Verify in Docker:
```bash
docker exec -it gcms-postgres psql -U gcms -d gcms_ai -c "
SELECT 'snomed_concepts' AS table, count(*) FROM snomed_concepts
UNION ALL
SELECT 'sdd_medications', count(*) FROM sdd_medications;
"
```
Should output:
```text
      table      | count 
-----------------+-------
 snomed_concepts |    50
 sdd_medications |    40
```

---

## 5. Running the Application & Testing APIs

### Step 5.1: Launch FastAPI Server

```bash
uvicorn app.main:app --reload --port 8000
```

### Step 5.2: Endpoints & Interactive Docs

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Step 5.3: Sample cURL Commands

```bash
# 1. Search SNOMED CT:
curl "http://127.0.0.1:8000/api/v1/terminology/snomed/search?q=asthma"

# 2. Search Singapore Drug Dictionary:
curl "http://127.0.0.1:8000/api/v1/terminology/sdd/search?q=panadol"

# 3. AI Diagnosis Suggestions:
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/ai/diagnoses/suggest' \
  -H 'Content-Type: application/json' \
  -d '{
    "consultation_context": {
      "chief_complaint": "Productive cough and fever for 3 days",
      "symptoms": ["Cough", "Fever", "Throat pain"],
      "symptom_duration": "3 days"
    },
    "max_suggestions": 3
  }'

# 4. AI Medication Suggestions:
curl -X 'POST' 'http://127.0.0.1:8000/api/v1/ai/medications/suggest' \
  -H 'Content-Type: application/json' \
  -d '{
    "selected_diagnosis": {
      "display": "Acute upper respiratory tract infection",
      "snomed_concept_id": "386661006"
    },
    "consultation_context": {
      "chief_complaint": "Fever and cough",
      "allergies": ["Penicillin"],
      "current_medications": []
    }
  }'
```

---

## 6. Running Unit Tests

```bash
python -m unittest discover tests/unit
```

---

## 7. Common Troubleshooting

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `relation "snomed_descriptions" does not exist` | Database tables not seeded | Run `python -m scripts.seed_dev_data` |
| `Cannot connect to PostgreSQL on localhost:5432` | Docker container stopped | Run `docker compose up -d` |
| `ModuleNotFoundError: No module named 'sqlalchemy'` | Virtual environment not active | Run `source .venv/bin/activate` |
| `Ollama unreachable in /health` | Ollama daemon not started | Run `ollama serve` in a terminal |

