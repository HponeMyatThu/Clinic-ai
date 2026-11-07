# GCMS Clinical AI Backend — Technical Architecture & REST API Specification
**Version:** 1.2.0 (FastAPI + Ollama Production Reference)  
**Target Audience:** Software Architects, Backend Engineers, DevOps, Clinical Safety Officers  
**Core Technologies:** Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Ollama, Docker  

---

## 1. System Architecture

The GCMS Clinical AI Backend is structured as an asynchronous Backend-for-Frontend (BFF) connecting the doctor-facing React UI, the core Clinic Management System (CMS), local Ollama LLMs, and high-performance PostgreSQL terminology datasets.

```
React Frontend (Doctor UI)
         │
         ▼
FastAPI Backend-for-Frontend (BFF)
 ├── Authentication & RBAC (OIDC / JWT)
 ├── Singapore Privacy Boundary (PII Regex Scrubber)
 │
 ├── Layer 1: Terminology Search Services
 │    ├── PostgreSQL SNOMED CT Database (Full-text tsvector + pg_trgm fuzzy matching)
 │    └── PostgreSQL SDD Database (Brand, Generic, Ingredient, Strength matching)
 │
 ├── Layer 2: Local AI Reasoning Layer (Ollama)
 │    ├── Ollama Connection Pooling & Retry (tenacity)
 │    ├── Structured Pydantic JSON Mode
 │    └── Prompt Templates (v1.2.0)
 │
 ├── Layer 3: Independent Deterministic Safety Engine
 │    ├── AllergyChecker (Penicillins, NSAIDs, Sulfas, Statins)
 │    ├── InteractionChecker (Warfarin, Metformin, CYP3A4 inhibitors)
 │    ├── ContraindicationChecker (Pregnancy, Renal / eGFR caution)
 │    └── DuplicateTherapyChecker
 │
 ├── Upstream CMS Integration (REST Client & Adapter)
 └── Immutable Audit Logger (audit_events, ai_request_logs)
```

---

## 2. The 4 Core REST API Contracts

### API 1: SNOMED CT Search
- **Endpoint**: `GET /api/v1/terminology/snomed/search`
- **Query Params**: `q` (string, min 2 chars), `active_only` (bool, default true), `page` (int), `page_size` (int)
- **Response**: Paginated `SnomedConceptResult` objects with `concept_id`, `preferred_term`, `synonyms`, `semantic_tag`, `match_type`, and `relevance_score`.

### API 2: Singapore Drug Dictionary (SDD) Search
- **Endpoint**: `GET /api/v1/terminology/sdd/search`
- **Query Params**: `q` (brand, generic, or ingredient), `active_only` (bool), `page` (int), `page_size` (int)
- **Response**: Paginated `SDDMedicationResult` objects with `medication_id`, `name`, `generic_name`, `brand_name`, `strength`, `dosage_form`, and active ingredients.

### API 3: AI Diagnosis Suggestion
- **Endpoint**: `POST /api/v1/ai/diagnoses/suggest`
- **Request Body**:
  ```json
  {
    "consultation_context": {
      "chief_complaint": "Cough and fever for 3 days",
      "symptoms": ["Cough", "Fever", "Sore throat"],
      "symptom_duration": "3 days",
      "medical_history": ["Hypertension"],
      "current_medications": ["Amlodipine 5mg daily"],
      "allergies": ["Penicillin"]
    },
    "max_suggestions": 5
  }
  ```
- **Response**: `suggestions` array with `candidate_id`, `display`, `snomed_concept_id`, `mapping_status` (`verified`/`unresolved`/`ambiguous`), `supporting_factors`, `contradicting_factors`, `missing_information`, and `requires_doctor_review: true`.

### API 4: AI Medication Suggestion
- **Endpoint**: `POST /api/v1/ai/medications/suggest`
- **Request Body**:
  ```json
  {
    "selected_diagnosis": {
      "display": "Acute upper respiratory tract infection",
      "snomed_concept_id": "386661006"
    },
    "consultation_context": {
      "chief_complaint": "Fever and sore throat",
      "allergies": ["Penicillin"],
      "current_medications": []
    }
  }
  ```
- **Response**: `suggestions` array with `medication_id` (matched from SDD), `sdd_match_status`, `safety_status` (`safe`/`requires_review`/`blocked`), `allergy_warnings`, `interaction_warnings`, `contraindication_warnings`, and `requires_doctor_review: true`.

---

## 3. Database Schema Reference

| Table | Primary Key | Indexes | Description |
| :--- | :--- | :--- | :--- |
| `snomed_concepts` | `concept_id` (VARCHAR 20) | B-Tree (`active`) | Core SNOMED CT concept registry |
| `snomed_descriptions` | `description_id` (VARCHAR 20) | GIN (`search_vector`), GIN (`term` trgm) | Concept terms, FSN, and synonyms |
| `snomed_relationships`| `relationship_id` (VARCHAR 20) | B-Tree (`source_id`, `destination_id`) | Concept hierarchy |
| `sdd_medications` | `medication_id` (VARCHAR 50) | GIN (`search_vector`), GIN (`name`/`generic`) | Singapore HSA-registered medications |
| `sdd_active_ingredients`| `id` (UUID) | GIN (`ingredient_name` trgm) | Active chemical ingredients |
| `audit_events` | `id` (UUID) | B-Tree (`request_id`, `event_type`, `created_at`)| Immutable clinical audit log (No PHI) |
| `ai_request_logs` | `id` (UUID) | B-Tree (`request_id`, `created_at`) | AI latency, tokens, prompt telemetry |

---

## 4. Privacy & Healthcare Regulatory Safeguards

1. **Deterministic PII Redaction (`app/privacy/pii_filter.py`)**:
   - Regex patterns match Singapore NRIC/FIN (`[STFGM]\d{7}[A-Z]`), Singapore phone numbers, email addresses, and patient name labels, replacing them with `[REDACTED]` tokens prior to model inference.
2. **Context Minimization (`app/privacy/context_minimizer.py`)**:
   - Strips administrative identifiers (patient name, NRIC, full address, phone) leaving only minimum-necessary clinical findings.
3. **Deterministic Safety Validation (`app/clinical_safety/`)**:
   - Independent Python algorithms verify contraindications and interactions. The LLM is never trusted as the sole safety checker.

