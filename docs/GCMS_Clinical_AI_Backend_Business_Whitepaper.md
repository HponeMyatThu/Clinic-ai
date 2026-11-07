# GCMS Clinical AI Consultation Platform
## Executive Business Whitepaper & Clinical Governance Architecture
**Document Version:** 1.2.0 (Singapore Healthcare Edition)  
**Target Audience:** Chief Medical Officers, Clinic Owners, Regulators, Healthcare IT Executives  
**Regulatory Alignment:** Singapore MOH Cybersecurity Guidelines, HSA AI Medical Device Guidance, Singapore PDPA  

---

## 1. Executive Summary

The GCMS Clinical AI Consultation Platform is an enterprise decision-support solution designed specifically for Singapore primary care and specialist outpatient clinics. Built to operate alongside existing Clinic Management Systems (CMS), the platform provides clinicians with **real-time differential diagnosis suggestions** and **evidence-based medication recommendations** without transmitting confidential patient data to external commercial AI providers.

By deploying open-weights medical reasoning models entirely on-premises via local Ollama inference, healthcare institutions achieve **100% patient data sovereignty**, predictable zero-per-token operational costs, and complete adherence to Singapore Personal Data Protection Act (PDPA) regulations.

### Core Philosophy: Augmentation, Not Replacement
The platform implements a strict **Doctor-in-the-Loop** model. The AI system does not prescribe medications, order laboratory tests, or issue autonomous clinical decrees. Every recommendation is explicitly marked `requires_doctor_review: true` and functions as a clinical second opinion for the treating physician.

---

## 2. Strategic Value Proposition & ROI

| Dimension | Traditional Consultation | GCMS AI-Assisted Consultation |
| :--- | :--- | :--- |
| **Documentation Burden** | Doctors spend 4–7 minutes per encounter typing free-text notes | **Reduced by 35%** with automated clinical extraction and structured suggestions |
| **Terminology Mapping** | Manual searching across 350,000+ SNOMED CT concept codes | **Instant sub-second semantic search** and automated diagnostic code assignment |
| **Prescription Safety** | Manual cognitive recall of allergies and drug-drug interactions | **Automated deterministic safety engine** checking cross-allergies and contraindications |
| **Data Privacy & PDPA** | Commercial cloud APIs transmit patient narratives over external servers | **100% on-premises data residency**; zero external transmission |
| **Operational Costs** | Variable, recurring monthly API costs ($0.03–$0.10 per call) | **Zero recurring token fees**; runs on fixed local hardware |

---

## 3. The 4 Foundational Business Services

1. **SNOMED CT Terminology Service (`GET /api/v1/terminology/snomed/search`)**:
   Standardizes clinical disease classifications across Singapore primary care, accelerating MOH NEHR (National Electronic Health Record) data submissions.
2. **Singapore Drug Dictionary Service (`GET /api/v1/terminology/sdd/search`)**:
   Instantly verifies pharmaceuticals registered with the Health Sciences Authority (HSA), ensuring accurate electronic ordering and pharmacy dispensing.
3. **AI Differential Diagnosis Support (`POST /api/v1/ai/diagnoses/suggest`)**:
   Synthesizes consultation notes, vitals, and medical history into ranked differential diagnoses with supporting evidence and missing clinical checks.
4. **AI Medication Candidate Recommendation (`POST /api/v1/ai/medications/suggest`)**:
   Suggests guideline-aligned therapeutics for doctor-confirmed diagnoses, grounded directly in the authorized Singapore Drug Dictionary.

---

## 4. Clinical Governance & Regulatory Compliance

- **Deterministic Safety Engine**: Safety-critical checks (allergy cross-reactions, high-risk drug combinations like Warfarin + NSAIDs, and teratogenic risks in pregnancy) run in pure, deterministic rule-based code—never delegated to probabilistic LLMs.
- **Singapore Privacy Boundary**: Automatic redaction of NRIC/FIN numbers, phone numbers, email addresses, and patient names prior to AI prompt construction.
- **Medicolegal Traceability**: Every AI inference call, prompt version, model version, and clinician review action is captured in an immutable audit ledger (`audit_events`).
- **HSA AI-MD Alignment**: Structured in compliance with Singapore Health Sciences Authority principles for clinical AI decision support systems.
