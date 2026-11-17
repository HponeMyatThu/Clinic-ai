# GCMS Clinical AI Backend

> **Clinical AI Consultation Backend for GCMS (Version 1.2)**  
> Provides doctor-reviewed differential diagnosis suggestions using licensed SNOMED CT and medication candidates matched to the Singapore Drug Dictionary (SDD), with local Ollama AI inference and zero transmission of direct patient identifiers to external AI services.

---

## Architecture Overview

```
React Frontend
    │
    ▼
FastAPI Backend (BFF)
    ├── Authentication & RBAC (OIDC / JWT)
    ├── Privacy Boundary & Context Minimization (PII Filter)
    │
    ├── Terminology Services (API 1 & API 2)
    │   ├── PostgreSQL SNOMED CT Database (FTS + pg_trgm fuzzy + vector search)
    │   └── PostgreSQL SDD Database (Generic, Brand, Ingredient matching)
    │
    ├── AI Clinical Decision Support (API 3 & API 4)
    │   ├── AI Orchestrator (Ollama async client + Prompt Versioning)
    │   ├── Ground-Truth Terminology Mapping (No AI hallucinations)
    │   └── Independent Clinical Safety Engine (Allergy, Interaction, Contraindication checks)
    │
    ├── CMS Adapter (System-of-record integration)
    └── Audit & Governance Logging (Immutable non-PHI event logs)
```

---

## System Requirements & Prerequisites

Before running the project, ensure your host system satisfies the following hardware and software requirements:

### Hardware Requirements
- **CPU**: Apple Silicon (M1/M2/M3/M4) recommended for Metal GPU acceleration, or x86_64 CPU with AVX2 support.
- **RAM**: Minimum 16 GB system memory (32 GB recommended for running Ollama 8B models + Docker simultaneously).
- **Disk Space**: At least 20 GB of free SSD space for Docker container images, PostgreSQL volumes, and Ollama weights (`qwen3:8b` is ~5.2 GB, `nomic-embed-text` is ~274 MB).

### Required Software Components to Install
1. **Docker Engine & Docker Compose** (v2.20+) — Runs PostgreSQL 16 and Redis 7.
2. **Ollama** (v0.3.0+) — Native local LLM and embedding inference engine.
3. **Python 3.11+** (3.11, 3.12, or 3.14) with `pip` and `venv`.
4. **Git** — Version control.
5. **cURL / HTTP client** — For health checks and API testing.

---

## Complete Installation Guide

### Step 1: Install System Prerequisites

#### On macOS (Recommended with Homebrew):
```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Git and Python 3.12
brew install git python@3.12

# 3. Install Ollama
brew install ollama

# 4. Install Docker Desktop OR Colima (lightweight Docker container runtime)
# Option A: Docker Desktop
brew install --cask docker

# Option B: Colima (CLI-only Docker runtime)
brew install colima docker docker-compose
colima start --cpu 4 --memory 8 --disk 60
```

#### On Linux (Ubuntu / Debian):
```bash
# 1. Update package lists
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.12, venv, Git, and cURL
sudo apt install -y python3.12 python3.12-venv python3-pip git curl

# 3. Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 4. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

---

### Step 2: Clone Repository & Configure Environment

```bash
# 1. Clone the repository
git clone https://github.com/HponeMyatThu/Clinic-ai.git
cd Clinic-ai

# 2. Create Python virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# 4. Upgrade pip and install all Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
# Alternatively, install development dependencies:
# pip install -e ".[dev]"

# 5. Create environment configuration (.env)
cp .env.example .env
```

---

### Step 3: Start Docker Services (PostgreSQL, Redis & pgAdmin 4)

The project includes a `docker-compose.yml` that provisions PostgreSQL 16, Redis 7 Alpine, and pgAdmin 4 containers with volume persistence and health checks.

```bash
# Start Docker containers in the background
docker-compose up -d

# Verify containers are running and healthy
docker-compose ps
```

#### Required Docker Images:
| Image | Role | Default Port | Healthcheck / Access |
| :--- | :--- | :--- | :--- |
| `postgres:16-alpine` (or `pgvector/pgvector:pg16`) | Terminology database (`gcms_ai`) with `pg_trgm`, `uuid-ossp`, and `vector` extensions | `5432` | `pg_isready -U gcms -d gcms_ai` |
| `redis:7-alpine` | Session state, distributed rate limiting, and response caching | `6379` | `redis-cli ping` |
| `dpage/pgadmin4:latest` | Web UI for PostgreSQL database management | `5050` | `http://localhost:5050` |

#### pgAdmin 4 Web Management Access:
- **URL**: [http://localhost:5050](http://localhost:5050)
- **Email**: `admin@gcms.ai` (default)
- **Password**: `admin` (default)
- **Pre-configured Server**: `GCMS PostgreSQL (Local Docker)` is auto-loaded. When prompted to connect to the database, enter the password: `change_me_in_production` (or your configured `POSTGRES_PASSWORD`).

To stop Docker services at any time:
```bash
docker-compose down
```

---

### Step 4: Start Ollama & Pull AI Models

Ollama runs locally as a native daemon. Running it natively on macOS provides hardware acceleration via Apple Metal GPU.

```bash
# 1. Start the Ollama background daemon
ollama serve
```
*(Leave this running in a dedicated terminal or run it as a system daemon).*

In a separate terminal, pull the required generative and embedding models:

```bash
# 2. Pull the Clinical Reasoning LLM (5.2 GB)
# Used for differential diagnosis generation, medication recommendations, and query understanding
ollama pull qwen3:8b

# 3. Pull the Dense Embedding Model (274 MB)
# Used for 768-dimensional semantic terminology vector search
ollama pull nomic-embed-text

# 4. Verify installed models
ollama list
```

Expected output:
```
NAME                    ID              SIZE      MODIFIED
qwen3:8b                500a1f067a9f    5.2 GB    ...
nomic-embed-text:latest 0a109f422b47    274 MB    ...
```

---

### Step 5: Initialize & Seed the Terminology Database

Populate PostgreSQL with 50 common clinical SNOMED CT concepts (219 descriptions) and 40 Singapore Drug Dictionary (SDD) medications (45 active ingredients), including full-text search tsvectors:

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Run database seed script
python3 -m scripts.seed_dev_data
```

Expected output:
```
[INFO] Table schema verified.
[INFO] Seeding SNOMED CT dev seed concepts...
[INFO] Seeding SDD medications and active ingredients...
[INFO] Search tsvectors generated successfully.
[INFO] Seeding complete! Added 50 SNOMED concepts and 40 SDD medications.
```

---

### Step 6: Start the FastAPI Backend Server

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Launch Uvicorn ASGI server with hot-reload enabled
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 7: Verify System Health

Run a quick cURL health probe to verify that both the database and Ollama are reachable:

```bash
curl -s http://localhost:8000/api/v1/health | jq .
```

Expected response:
```json
{
  "status": "ok",
  "app_name": "gcms-ai-backend",
  "version": "1.2.0",
  "environment": "development",
  "services": {
    "database": "healthy",
    "ollama": "healthy"
  }
}
```

Interactive API documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Summary of All Components to Install

| Component | Installation Command | Purpose |
| :--- | :--- | :--- |
| **Git** | `brew install git` / `apt install git` | Repository version control |
| **Python 3.12** | `brew install python@3.12` / `apt install python3.12 python3.12-venv` | Backend application runtime |
| **Docker Desktop / Colima** | `brew install --cask docker` / `apt install docker.io` | Container runtime for PostgreSQL & Redis |
| **PostgreSQL 16 Image** | Pulled automatically via `docker-compose up -d` | Terminology relational & vector database |
| **Redis 7 Image** | Pulled automatically via `docker-compose up -d` | In-memory cache & rate limiter |
| **pgAdmin 4 Image** | Pulled automatically via `docker-compose up -d` | Database management web UI on `http://localhost:5050` |
| **Ollama Daemon** | `brew install ollama` / `curl -fsSL https://ollama.com/install.sh \| sh` | Local AI inference engine |
| **Ollama Model `qwen3:8b`** | `ollama pull qwen3:8b` | Clinical LLM reasoning & query entity parsing |
| **Ollama Model `nomic-embed-text`** | `ollama pull nomic-embed-text` | 768-dim dense semantic vector embeddings |
| **Python Packages** | `pip install -r requirements.txt` | FastAPI, SQLAlchemy, Pydantic, ReportLab, etc. |

---

## The 4 Core API Services

### 1. SNOMED CT Search API
- **Endpoint**: `GET /api/v1/terminology/snomed/search?q={keyword}&page=1&page_size=20`
- **Description**: Ground-truth search across licensed SNOMED CT concepts using PostgreSQL full-text search (`tsvector`) and trigram fuzzy matching (`pg_trgm`). Never invents concept IDs.
- **Validation**: `GET /api/v1/terminology/snomed/validate/{concept_id}`

### 2. Singapore Drug Dictionary (SDD) Search API
- **Endpoint**: `GET /api/v1/terminology/sdd/search?q={keyword}&page=1&page_size=20`
- **Description**: Ground-truth medication search across Singapore HSA-registered drugs by trade/brand name, generic substance, active ingredient, and strength.
- **Validation**: `GET /api/v1/terminology/sdd/validate/{medication_id}`

### 3. AI Diagnosis Suggestion API
- **Endpoint**: `POST /api/v1/ai/diagnoses/suggest`
- **Description**: Receives consultation context (chief complaint, history, symptoms, vitals, examination). Direct identifiers (NRIC, phone, name) are scrubbed by the privacy boundary before prompt rendering. Ollama generates differential candidates, which are immediately verified against the local SNOMED CT database.
- **Governance**: Every candidate requires doctor review (`requires_doctor_review: true`).

### 4. AI Medication Suggestion API
- **Endpoint**: `POST /api/v1/ai/medications/suggest`
- **Description**: Generates guideline-aligned treatment candidates for a doctor-selected diagnosis. Matches candidates to official SDD catalog IDs and runs an **independent deterministic safety engine** (allergy cross-reactions, high-risk drug-drug interactions, pregnancy/renal contraindications, and duplicate therapies).

---

## Directory Structure

```
gcms_ai_backend/
├── pyproject.toml              # Build & dependency specifications
├── requirements.txt            # Locked pip dependencies
├── docker-compose.yml          # PostgreSQL & Redis infrastructure
├── Dockerfile                  # Production container definition
├── .env.example                # Template configuration
├── docs/                       # Business & technical documentation PDFs
├── scripts/
│   ├── init_db.sql             # PostgreSQL extensions (pg_trgm, uuid-ossp)
│   ├── seed_dev_data.py        # Synthetic SNOMED & SDD seed data
│   ├── import_snomed_rf2.py    # Official SNOMED CT RF2 parser & importer
│   └── import_sdd.py           # Official SDD dataset importer
├── app/
│   ├── main.py                 # FastAPI application factory
│   ├── config.py               # Pydantic Settings
│   ├── models/                 # SQLAlchemy 2.0 database models
│   │   ├── snomed.py           # Concepts, descriptions, relationships
│   │   ├── sdd.py              # Medications, ingredients, catalogue
│   │   ├── audit.py            # Immutable governance event logs
│   │   └── ai_metadata.py      # AI request telemetry & prompt versions
│   ├── schemas/                # Pydantic v2 validation contracts
│   │   ├── common.py           # RequestID, Pagination, Error schemas
│   │   ├── consultation.py     # Consultation context payload
│   │   ├── snomed.py           # SNOMED query & response models
│   │   ├── sdd.py              # SDD query & response models
│   │   ├── diagnosis.py        # Differential diagnosis contracts
│   │   └── medication.py       # Medication recommendation contracts
│   ├── services/               # Terminology search engines
│   │   ├── snomed_service.py   # FTS + pg_trgm SNOMED search
│   │   └── sdd_service.py      # Multi-field SDD medication search
│   ├── ai/                     # Local Ollama integration layer
│   │   ├── base_provider.py    # Pluggable AI provider interface
│   │   ├── ollama/             # Async HTTP client, retries, error handling
│   │   ├── prompts/            # Versioned clinical system prompts
│   │   └── orchestrator/       # Diagnosis & medication reasoning engines
│   ├── clinical_safety/        # Independent Safety Engines
│   │   ├── allergy_checker.py  # Penicillin/Sulfa/NSAID cross-reactivity
│   │   ├── interaction_checker.py # Warfarin, Metformin, Statin interactions
│   │   ├── contraindication_checker.py # Pregnancy & renal organ risks
│   │   ├── duplicate_therapy_checker.py # Duplicate active substances
│   │   └── safety_orchestrator.py # Aggregated safety report
│   ├── privacy/                # Singapore Healthcare Privacy Boundary
│   │   ├── pii_filter.py       # NRIC/FIN, phone, email, name redaction
│   │   └── context_minimizer.py# Minimum-necessary data egress
│   ├── cms/                    # Upstream CMS REST adapter
│   ├── audit/                  # Audit logging service
│   ├── db/                     # Async session & engine management
│   └── api/
│       ├── middleware/         # Request ID, rate limiter, error handler, auth
│       └── v1/                 # REST endpoints
└── tests/                      # Unit & integration test suites
```

---

## Troubleshooting & FAQ

### 1. PostgreSQL Connection Refused (`connect: operation not permitted` or `Connection refused`)
- Verify that Docker is running: `docker compose ps`
- Start the containers: `docker compose up -d`
- Check PostgreSQL container logs: `docker compose logs postgres`

### 2. Ollama Connection Error (`Cannot reach Ollama at http://localhost:11434`)
- Ensure Ollama daemon is running: `ollama serve`
- Test connectivity: `curl http://localhost:11434/api/tags`
- Check if port 11434 is in use: `lsof -i :11434`

### 3. Model Not Found (`Model 'qwen3:8b' not found`)
- Pull the model manually: `ollama pull qwen3:8b`
- For semantic search embeddings: `ollama pull nomic-embed-text`
- Verify with: `ollama list`

### 4. Apple Silicon Metal GPU Acceleration
- Ollama automatically detects Apple Silicon and utilizes Metal acceleration.
- You can monitor GPU usage in macOS **Activity Monitor** under the **Window > GPU History** pane while running AI suggestions.

---

## Clinical Safety & Governance Principles

1. **No Autonomous Prescribing**: All outputs are flagged with `requires_doctor_review: true`.
2. **Ground-Truth Terminology**: LLMs are never permitted to hallucinate SNOMED or SDD codes. Mappings are resolved against the verified database; unverified candidates are explicitly marked `unresolved`.
3. **Independent Safety Engine**: Drug-drug interactions and allergy checks run in pure deterministic Python code, never delegated to generative AI.
4. **Data Sovereignty**: Zero consultation data leaves the local boundary. All inference runs through local Ollama.
