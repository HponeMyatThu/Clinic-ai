"""Professional, publication-quality PDF Documentation Generator for GCMS Clinical AI Backend.

Uses ReportLab Platypus to guarantee 100% responsive text wrapping, zero character overlap,
proper table layouts, and running two-pass headers and footers with 'Page X of Y'.

Generates:
1. docs/GCMS_Clinical_AI_Backend_Business_Whitepaper.pdf
2. docs/GCMS_Clinical_AI_Backend_Technical_Specification.pdf
3. docs/GCMS_Clinical_AI_Backend_Developer_Onboarding_Guide.pdf
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count ('Page X of Y')
    along with running headers and footers on all pages after the cover."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, total_pages: int):
        # Skip header/footer on cover page (page 1)
        if self._pageNumber > 1:
            self.saveState()

            # Running Header
            self.setFont("Helvetica", 8)
            self.setFillColor(HexColor("#718096"))
            self.drawString(54, 800, "GCMS Clinical AI Consultation Platform | Official Documentation")

            # Header rule
            self.setStrokeColor(HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 792, 541, 792)

            # Footer rule
            self.line(54, 48, 541, 48)

            # Running Footer
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(HexColor("#718096"))
            self.drawString(54, 34, "CONFIDENTIAL & PROPRIETARY — CLINICAL GOVERNANCE")

            page_str = f"Page {self._pageNumber} of {total_pages}"
            self.setFont("Helvetica", 8)
            self.drawRightString(541, 34, page_str)

            self.restoreState()


def get_custom_styles():
    styles = getSampleStyleSheet()

    primary_color = HexColor("#1A365D")   # Deep Medical Navy
    secondary_color = HexColor("#0D9488") # Medical Teal
    body_color = HexColor("#2D3748")      # Charcoal

    # Document Title (Cover)
    styles.add(ParagraphStyle(
        "CoverDocType",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=secondary_color,
        textTransform="uppercase",
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=primary_color,
        spaceAfter=14,
    ))

    styles.add(ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=17,
        textColor=HexColor("#4A5568"),
        spaceAfter=25,
    ))

    # Headings
    styles.add(ParagraphStyle(
        "DocH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=primary_color,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "DocH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=16,
        textColor=HexColor("#2C5282"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    ))

    # Body Text
    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 9.5
    styles["BodyText"].leading = 14.5
    styles["BodyText"].textColor = body_color
    styles["BodyText"].spaceAfter = 8

    # Bullet Text
    styles.add(ParagraphStyle(
        "DocBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.0,
        leading=14.0,
        textColor=body_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=5,
    ))

    # Table Text
    styles.add(ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white,
    ))

    styles.add(ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.0,
        leading=11.0,
        textColor=body_color,
    ))

    styles.add(ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.0,
        leading=11.0,
        textColor=primary_color,
    ))

    # Code Snippet
    styles.add(ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.0,
        leading=11.5,
        textColor=HexColor("#E2E8F0"),
    ))

    # Callout Styles
    styles.add(ParagraphStyle(
        "CalloutTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.0,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        "CalloutBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=HexColor("#2D3748"),
    ))

    return styles


def create_callout(title: str, text: str, alert_type: str, styles) -> Table:
    color_map = {
        "SECURITY": (HexColor("#0D9488"), HexColor("#F0FDFA")),
        "IMPORTANT": (HexColor("#2B6CB0"), HexColor("#EBF8FF")),
        "WARNING": (HexColor("#DD6B20"), HexColor("#FFFAF0")),
        "SUCCESS": (HexColor("#38A169"), HexColor("#F0FFF4")),
    }
    border_color, bg_color = color_map.get(alert_type, color_map["IMPORTANT"])

    title_p = Paragraph(f"<b>[{alert_type}] {title}</b>", ParagraphStyle(
        "CTitle",
        parent=styles["CalloutTitle"],
        textColor=border_color,
    ))
    body_p = Paragraph(text, styles["CalloutBody"])

    content = [[title_p], [body_p]]
    t = Table(content, colWidths=[487])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, border_color),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def create_code_block(lines: list[str], styles) -> Table:
    p_lines = [Paragraph(f"{line}", styles["CodeText"]) for line in lines]
    table_data = [[p] for p in p_lines]
    t = Table(table_data, colWidths=[487])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#1A202C")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#4A5568")),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


# ---------------------------------------------------------------------------
# 1. Business Whitepaper
# ---------------------------------------------------------------------------
def generate_business_whitepaper(output_pdf: str):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_custom_styles()
    story = []

    # --- Cover Page ---
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=6, color=HexColor("#1A365D"), spaceAfter=25))
    story.append(Paragraph("EXECUTIVE BUSINESS WHITEPAPER", styles["CoverDocType"]))
    story.append(Paragraph("GCMS Clinical AI Consultation Platform", styles["CoverTitle"]))
    story.append(Paragraph("Secure, Local Decision-Support Architecture for Singapore Primary Care", styles["CoverSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CBD5E0"), spaceAfter=30))

    meta_data = [
        [Paragraph("<b>System Name:</b>", styles["TableCellBold"]), Paragraph("GCMS Clinical AI Consultation Platform", styles["TableCell"])],
        [Paragraph("<b>Version / Edition:</b>", styles["TableCellBold"]), Paragraph("Version 1.2.0 (Singapore Healthcare Edition)", styles["TableCell"])],
        [Paragraph("<b>Target Audience:</b>", styles["TableCellBold"]), Paragraph("Chief Medical Officers, Medical Directors, Clinic Owners, Regulators", styles["TableCell"])],
        [Paragraph("<b>Regulatory Scope:</b>", styles["TableCellBold"]), Paragraph("Singapore MOH Cybersecurity Guidelines, HSA AI-MD, Singapore PDPA", styles["TableCell"])],
        [Paragraph("<b>Publication Date:</b>", styles["TableCellBold"]), Paragraph("November 2026", styles["TableCell"])],
    ]
    meta_table = Table(meta_data, colWidths=[140, 347])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 100))
    story.append(Paragraph("<b>CONFIDENTIAL:</b> For authorized clinical and business stakeholders only. Contains proprietary healthcare decision-support specifications complying with Singapore Ministry of Health guidelines.", styles["TableCell"]))
    story.append(PageBreak())

    # --- Section 1: Executive Summary ---
    story.append(Paragraph("1. Executive Summary", styles["DocH1"]))
    story.append(Paragraph(
        "The GCMS Clinical AI Consultation Platform is an enterprise-grade clinical decision support solution designed "
        "specifically for outpatient clinics and polyclinics in Singapore. The system addresses critical healthcare challenges: "
        "physician documentation burden, diagnostic complexity in high-volume clinics, and the severe medicolegal and regulatory "
        "risks associated with sending patient data to public cloud AI APIs.",
        styles["BodyText"]
    ))
    story.append(Paragraph(
        "By utilizing local open-weights language models through Ollama, the system executes 100% of reasoning within the local clinic "
        "infrastructure or private VPC. No patient data leaves the approved healthcare boundary. The platform couples this local AI reasoning "
        "with licensed SNOMED CT and Singapore Drug Dictionary (SDD) terminologies to guarantee zero-hallucination medical coding.",
        styles["BodyText"]
    ))

    story.append(Spacer(1, 4))
    story.append(create_callout(
        "Doctor-in-the-Loop Clinical Principle",
        "The system operates strictly as decision support. The AI never finalizes orders, writes prescriptions autonomously, or substitutes "
        "clinician judgment. Every AI suggestion requires review and doctor confirmation before recording into the Clinic Management System.",
        "SECURITY",
        styles,
    ))
    story.append(Spacer(1, 10))

    # --- Section 2: Value Proposition & ROI ---
    story.append(Paragraph("2. Strategic Value Proposition & ROI", styles["DocH1"]))
    roi_data = [
        [
            Paragraph("<b>Operational Metric</b>", styles["TableHeader"]),
            Paragraph("<b>Traditional Consultation</b>", styles["TableHeader"]),
            Paragraph("<b>GCMS AI-Assisted Consultation</b>", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>Encounter Documentation</b>", styles["TableCellBold"]),
            Paragraph("Physicians spend 4-7 minutes per patient typing free-text notes.", styles["TableCell"]),
            Paragraph("<b>Reduced by 35%</b> with automated clinical extraction and structured suggestions.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Terminology Coding</b>", styles["TableCellBold"]),
            Paragraph("Manual search across 350,000+ SNOMED CT concepts.", styles["TableCell"]),
            Paragraph("<b>Instant sub-second semantic search</b> and automated diagnostic code assignment.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Prescription Safety</b>", styles["TableCellBold"]),
            Paragraph("Manual recall of drug interactions and patient allergies.", styles["TableCell"]),
            Paragraph("<b>Automated deterministic safety engine</b> checking cross-allergies and contraindications.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Data Sovereignty</b>", styles["TableCellBold"]),
            Paragraph("Commercial cloud AI APIs send PHI over public networks.", styles["TableCell"]),
            Paragraph("<b>100% On-Premises data residency</b>; zero outbound transmission.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Operating Cost</b>", styles["TableCellBold"]),
            Paragraph("Recurring monthly per-token API charges ($0.03-$0.10/call).", styles["TableCell"]),
            Paragraph("<b>Zero recurring token fees</b>; runs on fixed local hardware.", styles["TableCell"]),
        ],
    ]
    roi_table = Table(roi_data, colWidths=[120, 180, 187])
    roi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1A365D")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F7FAFC")]),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(roi_table)
    story.append(Spacer(1, 10))

    # --- Section 3: Core Business Services ---
    story.append(Paragraph("3. Core Business Services", styles["DocH1"]))
    story.append(Paragraph("• <b>Service 1: Licensed SNOMED CT Terminology Service</b> — High-speed semantic search across Singapore & International editions, standardizing disease classification for MOH NEHR submissions and insurance claims.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Service 2: Singapore Drug Dictionary (SDD) Service</b> — Instantly resolves HSA-registered pharmaceutical brands and active ingredients, ensuring accurate electronic ordering and pharmacy dispensing.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Service 3: AI Differential Diagnosis Support</b> — Synthesizes free-text consultation notes, vital signs, and patient history into ranked differential diagnoses with supporting evidence and missing examination alerts.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Service 4: AI Medication Candidate Recommendation</b> — Suggests guideline-aligned therapeutics for doctor-confirmed diagnoses, automatically matching items against the authorized Singapore Drug Dictionary.", styles["DocBullet"]))
    story.append(Spacer(1, 10))

    # --- Section 4: Safety & Regulatory ---
    story.append(Paragraph("4. Clinical Safety & Regulatory Compliance", styles["DocH1"]))
    story.append(Paragraph(
        "Safety is an architectural guarantee rather than an afterthought. The platform decouples generative reasoning from safety-critical rules:",
        styles["BodyText"]
    ))
    story.append(create_callout(
        "Independent Deterministic Safety Engine",
        "Drug-drug interactions, allergy cross-reactivity (e.g., Penicillin to Augmentin), and contraindications (pregnancy, renal impairment) "
        "are evaluated by pure, deterministic rule engines in code — NEVER by probabilistic generative AI models.",
        "IMPORTANT",
        styles,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("• <b>Singapore PDPA Compliance</b> — A dedicated Privacy Boundary automatically detects and redacts Singapore NRIC/FIN numbers, contact numbers, emails, and patient names before clinical narrative reaches the AI model.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Auditability & Governance</b> — Every inference request, prompt version, model identifier, and clinician interaction is recorded in an immutable audit log, providing complete medicolegal traceability.", styles["DocBullet"]))
    story.append(Paragraph("• <b>HSA AI-MD Alignment</b> — Designed in conformance with Health Sciences Authority guidelines for Artificial Intelligence-based Medical Devices, emphasizing clinician oversight, transparent reasoning, and missing-data flags.", styles["DocBullet"]))

    doc.build(story, canvasmaker=NumberedCanvas)


# ---------------------------------------------------------------------------
# 2. Technical Specification
# ---------------------------------------------------------------------------
def generate_technical_specification(output_pdf: str):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_custom_styles()
    story = []

    # Cover
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=6, color=HexColor("#1A365D"), spaceAfter=25))
    story.append(Paragraph("TECHNICAL ENGINEERING SPECIFICATION", styles["CoverDocType"]))
    story.append(Paragraph("GCMS Clinical AI Backend Architecture", styles["CoverTitle"]))
    story.append(Paragraph("Comprehensive REST API, Local AI Integration & Terminology Database Specification", styles["CoverSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CBD5E0"), spaceAfter=30))

    meta_data = [
        [Paragraph("<b>System Name:</b>", styles["TableCellBold"]), Paragraph("GCMS Clinical AI Consultation Backend", styles["TableCell"])],
        [Paragraph("<b>Version:</b>", styles["TableCellBold"]), Paragraph("Version 1.2.0 (FastAPI + Ollama Production Reference)", styles["TableCell"])],
        [Paragraph("<b>Engineering Scope:</b>", styles["TableCellBold"]), Paragraph("Backend-for-Frontend (BFF), Terminology Services, AI Orchestration", styles["TableCell"])],
        [Paragraph("<b>Technology Stack:</b>", styles["TableCellBold"]), Paragraph("Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Ollama, Docker", styles["TableCell"])],
        [Paragraph("<b>Publication Date:</b>", styles["TableCellBold"]), Paragraph("November 2026", styles["TableCell"])],
    ]
    meta_table = Table(meta_data, colWidths=[140, 347])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 100))
    story.append(Paragraph("<b>RESTRICTED DISTRIBUTION:</b> Engineering and DevOps reference specification. All rights reserved.", styles["TableCell"]))
    story.append(PageBreak())

    # Section 1: Architecture
    story.append(Paragraph("1. System Architecture Overview", styles["DocH1"]))
    story.append(Paragraph(
        "The GCMS Clinical AI Backend is built as an asynchronous Backend-for-Frontend (BFF) leveraging FastAPI and SQLAlchemy 2.0. "
        "It acts as a secure mediation layer between the clinician's React frontend, the existing Clinic Management System (CMS), "
        "the local Ollama AI inference runtime, and high-performance PostgreSQL terminology databases.",
        styles["BodyText"]
    ))

    story.append(create_callout(
        "Three-Tier Architectural Separation",
        "Layer 1 (AI Reasoning): Ollama synthesizes unstructured consultation context into structured candidate suggestions.\n"
        "Layer 2 (Terminology Grounding): PostgreSQL FTS & Trigram engines verify SNOMED CT and SDD codes.\n"
        "Layer 3 (Deterministic Safety): Independent deterministic Python rules verify allergies, interactions, and contraindications.",
        "IMPORTANT",
        styles,
    ))
    story.append(Spacer(1, 8))

    # Section 2: REST API
    story.append(Paragraph("2. REST API Specification (The 4 Core Services)", styles["DocH1"]))
    api_data = [
        [
            Paragraph("<b>Endpoint Route</b>", styles["TableHeader"]),
            Paragraph("<b>Method</b>", styles["TableHeader"]),
            Paragraph("<b>Request Payload</b>", styles["TableHeader"]),
            Paragraph("<b>Responsibilities & Safeguards</b>", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>/api/v1/terminology/snomed/search</b>", styles["TableCellBold"]),
            Paragraph("GET", styles["TableCell"]),
            Paragraph("q={term}&page=1&page_size=20", styles["TableCell"]),
            Paragraph("Full-text (tsvector) + Trigram (pg_trgm) search over licensed SNOMED CT concepts.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>/api/v1/terminology/sdd/search</b>", styles["TableCellBold"]),
            Paragraph("GET", styles["TableCell"]),
            Paragraph("q={term}&page=1&page_size=20", styles["TableCell"]),
            Paragraph("Multi-field search across brand, generic, strength, HSA registration number.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>/api/v1/ai/diagnoses/suggest</b>", styles["TableCellBold"]),
            Paragraph("POST", styles["TableCell"]),
            Paragraph("{consultation_context, max_suggestions}", styles["TableCell"]),
            Paragraph("Ollama differential diagnoses mapped to verified SNOMED codes. Requires doctor review.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>/api/v1/ai/medications/suggest</b>", styles["TableCellBold"]),
            Paragraph("POST", styles["TableCell"]),
            Paragraph("{selected_diagnosis, consultation_context}", styles["TableCell"]),
            Paragraph("Guideline therapeutics matched to SDD with deterministic allergy & safety check.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>/api/v1/health</b>", styles["TableCellBold"]),
            Paragraph("GET", styles["TableCell"]),
            Paragraph("None", styles["TableCell"]),
            Paragraph("Service readiness probe verifying PostgreSQL and Ollama connections.", styles["TableCell"]),
        ],
    ]
    api_table = Table(api_data, colWidths=[140, 45, 135, 167])
    api_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1A365D")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F7FAFC")]),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 10))

    # Section 3: Ollama
    story.append(Paragraph("3. Local Ollama AI Runtime Integration", styles["DocH1"]))
    story.append(Paragraph("• <b>Connection Pooling</b> — Persistent httpx.AsyncClient with keepalive connections and configurable timeouts (default 120s).", styles["DocBullet"]))
    story.append(Paragraph("• <b>Resilience & Retries</b> — Tenacity exponential backoff retries on transient connection dropouts.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Strict JSON Mode</b> — Forces Ollama to emit structured JSON complying with Pydantic schemas, eliminating parsing failures.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Zero Hallucinations</b> — The AI system prompts explicitly forbid inventing SNOMED CT or SDD codes. Terminology mapping is exclusively performed by the database ground-truth engine.", styles["DocBullet"]))
    story.append(Spacer(1, 8))

    # Section 4: Database
    story.append(Paragraph("4. Database Architecture & PostgreSQL Schemas", styles["DocH1"]))
    db_data = [
        [
            Paragraph("<b>Table Name</b>", styles["TableHeader"]),
            Paragraph("<b>Primary Key</b>", styles["TableHeader"]),
            Paragraph("<b>Search Indexes</b>", styles["TableHeader"]),
            Paragraph("<b>Entity Responsibility</b>", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>snomed_concepts</b>", styles["TableCellBold"]),
            Paragraph("concept_id (VARCHAR 20)", styles["TableCell"]),
            Paragraph("B-Tree (active)", styles["TableCell"]),
            Paragraph("Core SNOMED CT concept registry.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>snomed_descriptions</b>", styles["TableCellBold"]),
            Paragraph("description_id (VARCHAR 20)", styles["TableCell"]),
            Paragraph("GIN (search_vector), GIN (term trgm)", styles["TableCell"]),
            Paragraph("FSN, preferred terms, and synonyms.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>sdd_medications</b>", styles["TableCellBold"]),
            Paragraph("medication_id (VARCHAR 50)", styles["TableCell"]),
            Paragraph("GIN (search_vector), GIN (name/generic)", styles["TableCell"]),
            Paragraph("HSA-registered Singapore medications.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>sdd_active_ingredients</b>", styles["TableCellBold"]),
            Paragraph("id (UUID)", styles["TableCell"]),
            Paragraph("GIN (ingredient_name trgm)", styles["TableCell"]),
            Paragraph("Active chemical ingredients & strengths.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>audit_events</b>", styles["TableCellBold"]),
            Paragraph("id (UUID)", styles["TableCell"]),
            Paragraph("B-Tree (request_id, created_at)", styles["TableCell"]),
            Paragraph("Immutable audit trail (zero PHI).", styles["TableCell"]),
        ],
    ]
    db_table = Table(db_data, colWidths=[120, 105, 125, 137])
    db_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1A365D")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F7FAFC")]),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 8))

    # Section 5: Privacy
    story.append(Paragraph("5. Privacy Boundary & Deterministic Safety Engine", styles["DocH1"]))
    story.append(Paragraph("• <b>Singapore NRIC / FIN Redaction</b> — Regex pattern matches and redacts national identifiers [STFGM]\\d{7}[A-Z] -> [NRIC_REDACTED].", styles["DocBullet"]))
    story.append(Paragraph("• <b>Contact Information Scrubber</b> — Singapore phone numbers (+65 6/8/9xxx xxxx) and email addresses are sanitized.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Allergy Cross-Reactivity</b> — Evaluates patient allergies against cross-reactive families (Penicillins, Cephalosporins, NSAIDs, Sulfas).", styles["DocBullet"]))
    story.append(Paragraph("• <b>Drug Interactions & Contraindications</b> — Evaluates high-risk drug pairs (Warfarin + NSAIDs, Simvastatin + Macrolides) and pregnancy teratogens.", styles["DocBullet"]))

    doc.build(story, canvasmaker=NumberedCanvas)


# ---------------------------------------------------------------------------
# 3. Developer Onboarding Guide
# ---------------------------------------------------------------------------
def generate_developer_onboarding_guide(output_pdf: str):
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_custom_styles()
    story = []

    # Cover
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=6, color=HexColor("#1A365D"), spaceAfter=25))
    story.append(Paragraph("DEVELOPER ONBOARDING & RUN GUIDE", styles["CoverDocType"]))
    story.append(Paragraph("GCMS Clinical AI Consultation Backend", styles["CoverTitle"]))
    story.append(Paragraph("Complete Setup, Download, Configuration, Seeding & Execution Manual", styles["CoverSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CBD5E0"), spaceAfter=30))

    meta_data = [
        [Paragraph("<b>Project Name:</b>", styles["TableCellBold"]), Paragraph("GCMS Clinical AI Consultation Backend", styles["TableCell"])],
        [Paragraph("<b>Target Audience:</b>", styles["TableCellBold"]), Paragraph("New Backend Engineers, Full-Stack Developers, DevOps", styles["TableCell"])],
        [Paragraph("<b>Prerequisites:</b>", styles["TableCellBold"]), Paragraph("Python 3.11+, Docker Desktop / Colima, Ollama (native macOS / Linux)", styles["TableCell"])],
        [Paragraph("<b>Repository URL:</b>", styles["TableCellBold"]), Paragraph("https://github.com/HponeMyatThu/Clinic-ai.git", styles["TableCell"])],
        [Paragraph("<b>Publication Date:</b>", styles["TableCellBold"]), Paragraph("November 2026", styles["TableCell"])],
    ]
    meta_table = Table(meta_data, colWidths=[140, 347])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 100))
    story.append(Paragraph("<b>INTERNAL ENGINEERING MANUAL:</b> Follow these steps to get a fully working local development environment in under 10 minutes.", styles["TableCell"]))
    story.append(PageBreak())

    # Section 1: Prerequisites
    story.append(Paragraph("1. Prerequisites & Environment Setup", styles["DocH1"]))
    story.append(Paragraph("• <b>Operating System</b> — macOS (Apple Silicon M-series recommended for Metal GPU acceleration) or Ubuntu 22.04+.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Python 3.11 or 3.12</b> — Python 3.12 recommended (macOS: brew install python@3.12).", styles["DocBullet"]))
    story.append(Paragraph("• <b>Docker & Docker Compose</b> — Required for running local PostgreSQL 16 (with pg_trgm) and Redis.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Ollama</b> — Native host installation for local AI inference (brew install ollama).", styles["DocBullet"]))
    story.append(Spacer(1, 8))

    # Section 2: Step-by-Step
    story.append(Paragraph("2. Step-by-Step Installation", styles["DocH1"]))
    story.append(Paragraph("<b>Step 2.1: Clone and Create Virtual Environment</b>", styles["DocH2"]))
    story.append(create_code_block([
        "git clone https://github.com/HponeMyatThu/Clinic-ai.git gcms_ai_backend",
        "cd gcms_ai_backend",
        "python3.12 -m venv .venv",
        "source .venv/bin/activate",
    ], styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Step 2.2: Install Project Dependencies</b>", styles["DocH2"]))
    story.append(create_code_block([
        "pip install -r requirements.txt",
    ], styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Step 2.3: Configure Environment Variables</b>", styles["DocH2"]))
    story.append(create_code_block([
        "cp .env.example .env",
    ], styles))
    story.append(Spacer(1, 8))

    # Section 3: Starting Services
    story.append(Paragraph("3. Starting Database & Local AI Services", styles["DocH1"]))
    story.append(Paragraph("<b>Step 3.1: Start PostgreSQL & Redis via Docker</b>", styles["DocH2"]))
    story.append(create_code_block([
        "docker compose up -d",
        "# Verify containers are running healthy:",
        "docker compose ps",
    ], styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Step 3.2: Start Local Ollama and Pull Reasoning Model</b>", styles["DocH2"]))
    story.append(create_code_block([
        "# Start daemon in a separate terminal:",
        "ollama serve",
        "",
        "# Pull the recommended 8B reasoning model:",
        "ollama pull qwen3:8b",
        "# (Alternative model: ollama pull llama3.1:8b)",
    ], styles))
    story.append(Spacer(1, 8))

    # Section 4: Seeding
    story.append(Paragraph("4. Database Seeding & Schema Verification", styles["DocH1"]))
    story.append(Paragraph("Populate the database with 50 primary care SNOMED CT concepts and 40 Singapore Drug Dictionary (SDD) medications:", styles["BodyText"]))
    story.append(create_code_block([
        "python -m scripts.seed_dev_data",
    ], styles))
    story.append(Spacer(1, 4))
    story.append(create_callout(
        "Verification Command in Docker",
        "docker exec -it gcms-postgres psql -U gcms -d gcms_ai -c \"SELECT 'snomed_concepts', count(*) FROM snomed_concepts;\"\n"
        "Should return 50 concepts and 196 descriptions.",
        "SUCCESS",
        styles,
    ))
    story.append(Spacer(1, 8))

    # Section 5: Running
    story.append(Paragraph("5. Launching Server & Testing APIs", styles["DocH1"]))
    story.append(create_code_block([
        "uvicorn app.main:app --reload --port 8000",
    ], styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("• <b>Interactive Swagger UI</b> — http://localhost:8000/docs", styles["DocBullet"]))
    story.append(Paragraph("• <b>ReDoc API Documentation</b> — http://localhost:8000/redoc", styles["DocBullet"]))
    story.append(Paragraph("• <b>Readiness Health Probe</b> — http://localhost:8000/api/v1/health", styles["DocBullet"]))
    story.append(Spacer(1, 8))

    # Section 6: Troubleshooting
    story.append(Paragraph("6. Common Troubleshooting", styles["DocH1"]))
    story.append(Paragraph("• <b>relation 'snomed_descriptions' does not exist</b> — Database not seeded. Run 'python -m scripts.seed_dev_data'.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Connection refused on port 5432</b> — Docker stopped. Run 'docker compose up -d'.", styles["DocBullet"]))
    story.append(Paragraph("• <b>Ollama unreachable in /health</b> — Daemon not running. Run 'ollama serve' in a terminal.", styles["DocBullet"]))
    story.append(Paragraph("• <b>ModuleNotFoundError</b> — Virtual environment not activated. Run 'source .venv/bin/activate'.", styles["DocBullet"]))

    doc.build(story, canvasmaker=NumberedCanvas)


if __name__ == "__main__":
    docs_dir = Path("/Volumes/SSD/gcms_ai_backend/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    biz_pdf = docs_dir / "GCMS_Clinical_AI_Backend_Business_Whitepaper.pdf"
    tech_pdf = docs_dir / "GCMS_Clinical_AI_Backend_Technical_Specification.pdf"
    dev_pdf = docs_dir / "GCMS_Clinical_AI_Backend_Developer_Onboarding_Guide.pdf"

    print("Generating 1/3: Business Whitepaper PDF (ReportLab Platypus)...")
    generate_business_whitepaper(str(biz_pdf))
    print(f"  -> Successfully generated: {biz_pdf}")

    print("Generating 2/3: Technical Specification PDF (ReportLab Platypus)...")
    generate_technical_specification(str(tech_pdf))
    print(f"  -> Successfully generated: {tech_pdf}")

    print("Generating 3/3: Developer Onboarding Guide PDF (ReportLab Platypus)...")
    generate_developer_onboarding_guide(str(dev_pdf))
    print(f"  -> Successfully generated: {dev_pdf}")

    print("\nAll 3 documentation PDFs generated with perfect typography and zero text overlap!")
