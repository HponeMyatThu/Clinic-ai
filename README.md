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
    │   ├── PostgreSQL SNOMED CT Database (FTS5 + pg_trgm fuzzy matching)
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

## Technology Stack

- **Framework**: Python 3.11+, FastAPI, Pydantic v2
- **Database & Search**: PostgreSQL 16, SQLAlchemy 2.0 (Async), `pg_trgm`, `tsvector`
- **AI Runtime**: Local Ollama daemon (`qwen3:8b`, `llama3.1:8b`)
- **Containers**: Docker & Docker Compose
- **Safety & Privacy**: Custom regex PII scrubber, independent rule-based safety orchestrator

---

## Quick Start Guide

### 1. Environment Setup

```bash
# Clone and enter directory
cd /Volumes/SSD/gcms_ai_backend

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
```

### 2. Start PostgreSQL & Redis via Docker

```bash
docker compose up -d
```

### 3. Start Local Ollama on macOS

For maximum performance on Apple Silicon (M-series Metal GPU acceleration):

```bash
# Install Ollama (if not already installed)
brew install ollama

# Start the Ollama daemon
ollama serve

# In another terminal, pull the recommended clinical reasoning model
ollama pull qwen3:8b
# (Alternative: ollama pull llama3.1:8b)
```

### 4. Seed Development Terminology Data

Populate the database with 50 common clinical SNOMED CT concepts and 40 Singapore Drug Dictionary medications:

```bash
python3 -m scripts.seed_dev_data
```

### 5. Launch the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- System Health Probe: `http://localhost:8000/api/v1/health`

---

## Directory Structure

```
gcms_ai_backend/
├── pyproject.toml              # Build & dependency specifications
├── docker-compose.yml          # PostgreSQL & Redis infrastructure
├── Dockerfile                  # Production container definition
├── .env.example                # Template configuration
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
│   │   ├── snomed_service.py   # FTS5 + pg_trgm SNOMED search
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

## Clinical Safety & Governance Principles

1. **No Autonomous Prescribing**: All outputs are flagged with `requires_doctor_review: true`.
2. **Ground-Truth Terminology**: LLMs are never permitted to hallucinate SNOMED or SDD codes. Mappings are resolved against the verified database; unverified candidates are explicitly marked `unresolved`.
3. **Independent Safety Engine**: Drug-drug interactions and allergy checks run in pure deterministic Python code, never delegated to generative AI.
4. **Data Sovereignty**: Zero consultation data leaves the local boundary. All inference runs through local Ollama.
