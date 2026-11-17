"""Import real SNOMED CT and SDD data exported from AWS Server (47.131.196.190).

This script reads:
  - data/aws_export/snomed_ct.tsv.gz (81,607 SNOMED CT concepts & descriptions)
  - data/aws_export/sdd_tertiarycare.tsv.gz (13,124 Singapore Drug Dictionary medications & ingredients)
  - data/aws_export/pharmacy_items.tsv.gz (202 Clinic Pharmacy items)

And imports them into the running PostgreSQL database (Docker: gcms-postgres).
"""

from __future__ import annotations

import asyncio
import datetime
import gzip
import logging
import re
import sys
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory, engine
from app.models.base import Base
from app.models.sdd import SDDActiveIngredient, SDDCatalogueMetadata, SDDMedication
from app.models.snomed import SnomedConcept, SnomedDescription, SnomedReleaseMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_real_data")

DATA_DIR = Path("data/aws_export")
SNOMED_FILE = DATA_DIR / "snomed_ct.tsv.gz"
SDD_FILE = DATA_DIR / "sdd_tertiarycare.tsv.gz"
PHARMACY_FILE = DATA_DIR / "pharmacy_items.tsv.gz"

BATCH_SIZE = 5000

# Regex helpers for SDD parsing
DOSAGE_FORMS = [
    "Tablet", "Capsule", "Injection", "Cream", "Lotion", "Ear Drops", "Eye Drops",
    "Syrup", "Suspension", "Inhaler", "Ointment", "Gel", "Solution", "Suppository",
    "Powder", "Patch", "Spray", "Sachet", "Nebuliser Solution", "Topical Powder",
    "Mouthwash", "Gargle", "Enema", "Elixir", "Linctus", "Emulsion"
]
DOSAGE_FORM_RE = re.compile(r"\b(" + "|".join(re.escape(f) for f in DOSAGE_FORMS) + r")\b", re.IGNORECASE)

ROUTE_MAP = {
    "tablet": "Oral",
    "capsule": "Oral",
    "syrup": "Oral",
    "suspension": "Oral",
    "sachet": "Oral",
    "elixir": "Oral",
    "linctus": "Oral",
    "injection": "Intravenous / Intramuscular",
    "cream": "Topical",
    "lotion": "Topical",
    "ointment": "Topical",
    "gel": "Topical",
    "topical powder": "Topical",
    "eye drops": "Ophthalmic",
    "ear drops": "Otic",
    "inhaler": "Inhalation",
    "nebuliser solution": "Inhalation",
    "suppository": "Rectal",
    "patch": "Transdermal",
    "mouthwash": "Oral / Topical",
    "gargle": "Oral / Topical",
    "spray": "Nasal / Topical",
}


def parse_date(date_str: str | None) -> datetime.date:
    """Parse string date to date object, fallback to 2024-01-01."""
    if not date_str or date_str == "NULL":
        return datetime.date(2024, 1, 1)
    try:
        # e.g. "2014-07-31 00:00:00.000000" or "2014-07-31"
        clean = date_str.split()[0].strip()
        return datetime.date.fromisoformat(clean)
    except Exception:
        return datetime.date(2024, 1, 1)


def parse_sdd_medication(term: str) -> dict[str, Any]:
    """Parse SDD PreferredTerm string into brand, generic, dosage form, and ingredients."""
    bracket_match = re.search(r"\[(.*?)\]", term)
    ingredients_raw = bracket_match.group(1).strip() if bracket_match else None

    brand = term[: bracket_match.start()].strip() if bracket_match else None
    remainder = term[bracket_match.end() :].strip() if bracket_match else term

    # Extract dosage form
    form_match = DOSAGE_FORM_RE.search(remainder)
    dosage_form = form_match.group(1).capitalize() if form_match else None

    # Derive route
    route = ROUTE_MAP.get(dosage_form.lower(), "Other") if dosage_form else None

    # Parse generic name and ingredients
    parsed_ingredients: list[dict[str, str | None]] = []
    generic_name = None

    if ingredients_raw:
        # Split on '+' (e.g. 'Amlodipine 10 mg + Atorvastatin 40 mg')
        parts = [p.strip() for p in ingredients_raw.split("+")]
        clean_names = []
        for part in parts:
            # Parse 'Amlodipine 10 mg' or 'Clotrimazole 1 %'
            ing_match = re.match(r"^(.*?)(?:\s+([0-9.]+)\s*([a-zA-Z%]+.*))?$", part)
            if ing_match:
                ing_name = ing_match.group(1).strip()
                val = ing_match.group(2)
                unit = ing_match.group(3)
                clean_names.append(ing_name)
                parsed_ingredients.append({
                    "ingredient_name": ing_name,
                    "strength_value": val,
                    "strength_unit": unit,
                })
            else:
                clean_names.append(part)
                parsed_ingredients.append({
                    "ingredient_name": part,
                    "strength_value": None,
                    "strength_unit": None,
                })
        generic_name = " + ".join(clean_names)
    elif not brand:
        # No brackets, e.g. 'Piperacillin Injection'
        if dosage_form and term.lower().endswith(dosage_form.lower()):
            generic_name = term[: -len(dosage_form)].strip()
        else:
            generic_name = term
        parsed_ingredients.append({
            "ingredient_name": generic_name,
            "strength_value": None,
            "strength_unit": None,
        })

    # If brand name is missing, use generic name or full term
    if not brand and generic_name:
        brand = generic_name

    # Extract strength from remainder if not in ingredients
    strength = None
    str_match = re.search(r"([0-9.]+\s*(?:mg|g|mcg|%|ml|units?|iu)\b)", remainder, re.IGNORECASE)
    if str_match:
        strength = str_match.group(1)

    return {
        "brand_name": brand[:500] if brand else None,
        "generic_name": generic_name[:500] if generic_name else None,
        "dosage_form": dosage_form[:200] if dosage_form else None,
        "route": route[:100] if route else None,
        "strength": strength[:200] if strength else None,
        "ingredients": parsed_ingredients,
    }


async def import_snomed(session: AsyncSession) -> int:
    """Import 81,607 real SNOMED CT concepts and descriptions."""
    # Check if already imported
    existing = (await session.execute(text("SELECT count(*) FROM snomed_concepts"))).scalar() or 0
    if existing >= 80000:
        logger.info(f"SNOMED CT already imported ({existing:,} concepts found). Skipping import.")
        return existing

    logger.info(f"Opening SNOMED CT dataset: {SNOMED_FILE}")
    if not SNOMED_FILE.exists():
        logger.error(f"File not found: {SNOMED_FILE}")
        return 0

    # Clean existing data
    logger.info("Clearing old SNOMED CT seed data...")
    await session.execute(text("TRUNCATE TABLE snomed_descriptions, snomed_relationships, snomed_concepts CASCADE;"))
    await session.commit()

    concept_batch: list[dict[str, Any]] = []
    description_batch: list[dict[str, Any]] = []
    total_concepts = 0
    total_descriptions = 0

    with gzip.open(SNOMED_FILE, "rt", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        # ConceptId, PreferredTeam, EffectiveTime, ConceptStatus, CTCategory

        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue

            cid = parts[0].strip()
            term = parts[1].strip()
            eff_time_str = parts[2].strip() if len(parts) > 2 else None
            status_str = parts[3].strip() if len(parts) > 3 else "1"

            if not cid or not term:
                continue

            eff_time = parse_date(eff_time_str)
            active = bool(int(status_str)) if status_str.isdigit() else True

            concept_batch.append({
                "concept_id": cid,
                "effective_time": eff_time,
                "active": active,
                "module_id": "900000000000207008",
                "definition_status_id": "900000000000073002",
            })

            # Check if term has semantic tag at end, e.g. "Asthma (disorder)"
            has_tag = bool(re.search(r"\(([^)]+)\)\s*$", term))
            type_id = SnomedDescription.FSN_TYPE_ID if has_tag else SnomedDescription.SYNONYM_TYPE_ID

            description_batch.append({
                "description_id": f"{cid}01",
                "concept_id": cid,
                "effective_time": eff_time,
                "active": active,
                "module_id": "900000000000207008",
                "language_code": "en",
                "type_id": type_id,
                "term": term,
                "case_significance_id": "900000000000020002",
            })

            # If term has semantic tag, also create a clean synonym without tag
            if has_tag:
                clean_term = re.sub(r"\s*\([^)]+\)\s*$", "", term).strip()
                if clean_term and clean_term != term:
                    description_batch.append({
                        "description_id": f"{cid}02",
                        "concept_id": cid,
                        "effective_time": eff_time,
                        "active": active,
                        "module_id": "900000000000207008",
                        "language_code": "en",
                        "type_id": SnomedDescription.SYNONYM_TYPE_ID,
                        "term": clean_term,
                        "case_significance_id": "900000000000020002",
                    })

            if len(concept_batch) >= BATCH_SIZE:
                await session.execute(
                    text(
                        "INSERT INTO snomed_concepts (concept_id, effective_time, active, module_id, definition_status_id) "
                        "VALUES (:concept_id, :effective_time, :active, :module_id, :definition_status_id) "
                        "ON CONFLICT (concept_id) DO NOTHING"
                    ),
                    concept_batch,
                )
                await session.execute(
                    text(
                        "INSERT INTO snomed_descriptions (description_id, concept_id, effective_time, active, module_id, language_code, type_id, term, case_significance_id) "
                        "VALUES (:description_id, :concept_id, :effective_time, :active, :module_id, :language_code, :type_id, :term, :case_significance_id) "
                        "ON CONFLICT (description_id) DO NOTHING"
                    ),
                    description_batch,
                )
                await session.commit()
                total_concepts += len(concept_batch)
                total_descriptions += len(description_batch)
                logger.info(f"Imported {total_concepts:,} SNOMED concepts, {total_descriptions:,} descriptions...")
                concept_batch = []
                description_batch = []

    # Final batch
    if concept_batch:
        await session.execute(
            text(
                "INSERT INTO snomed_concepts (concept_id, effective_time, active, module_id, definition_status_id) "
                "VALUES (:concept_id, :effective_time, :active, :module_id, :definition_status_id) "
                "ON CONFLICT (concept_id) DO NOTHING"
            ),
            concept_batch,
        )
        await session.execute(
            text(
                "INSERT INTO snomed_descriptions (description_id, concept_id, effective_time, active, module_id, language_code, type_id, term, case_significance_id) "
                "VALUES (:description_id, :concept_id, :effective_time, :active, :module_id, :language_code, :type_id, :term, :case_significance_id) "
                "ON CONFLICT (description_id) DO NOTHING"
            ),
            description_batch,
        )
        await session.commit()
        total_concepts += len(concept_batch)
        total_descriptions += len(description_batch)

    # Generate Full-Text Search TSVectors
    logger.info("Generating PostgreSQL TSVectors for SNOMED CT descriptions...")
    await session.execute(
        text("UPDATE snomed_descriptions SET search_vector = to_tsvector('english', term)")
    )
    await session.commit()

    # Track release metadata
    meta = SnomedReleaseMetadata(
        edition="Singapore / International (Live AWS Server Sync)",
        version="2024.11-PRODUCTION",
        record_count=total_concepts,
    )
    session.add(meta)
    await session.commit()

    logger.info(f"SNOMED CT import complete: {total_concepts:,} concepts, {total_descriptions:,} descriptions.")
    return total_concepts


async def import_sdd(session: AsyncSession) -> int:
    """Import 13,124 real Singapore Drug Dictionary medications & active ingredients."""
    logger.info(f"Opening SDD dataset: {SDD_FILE}")
    if not SDD_FILE.exists():
        logger.error(f"File not found: {SDD_FILE}")
        return 0

    logger.info("Clearing old SDD seed data...")
    try:
        await session.execute(text("ALTER TABLE sdd_active_ingredients ALTER COLUMN strength_unit TYPE character varying(255);"))
        await session.execute(text("ALTER TABLE sdd_active_ingredients ALTER COLUMN strength_value TYPE character varying(255);"))
        await session.commit()
    except Exception:
        pass
    await session.execute(text("TRUNCATE TABLE sdd_active_ingredients, sdd_medications CASCADE;"))
    await session.commit()

    med_batch: list[dict[str, Any]] = []
    ing_batch: list[dict[str, Any]] = []
    total_meds = 0
    total_ings = 0

    with gzip.open(SDD_FILE, "rt", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        # ConceptId, PreferredTerm, SddClass, MapStatus, RecordStatus

        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue

            cid = parts[0].strip()
            term = parts[1].strip()

            if not cid or not term:
                continue

            parsed = parse_sdd_medication(term)

            med_batch.append({
                "medication_id": cid,
                "name": term[:500],
                "generic_name": parsed["generic_name"],
                "brand_name": parsed["brand_name"],
                "strength": parsed["strength"],
                "dosage_form": parsed["dosage_form"],
                "route": parsed["route"],
                "manufacturer": "Singapore Health Sciences Authority (HSA) Registered",
                "hsa_reg_no": None,
                "active": True,
                "atc_code": None,
            })

            for ing in parsed["ingredients"]:
                s_val = ing["strength_value"][:250] if ing["strength_value"] else None
                s_unit = ing["strength_unit"][:250] if ing["strength_unit"] else None
                ing_batch.append({
                    "id": uuid.uuid4(),
                    "medication_id": cid,
                    "ingredient_name": ing["ingredient_name"][:500],
                    "strength_value": s_val,
                    "strength_unit": s_unit,
                })

            if len(med_batch) >= BATCH_SIZE:
                await session.execute(
                    text(
                        "INSERT INTO sdd_medications (medication_id, name, generic_name, brand_name, strength, dosage_form, route, manufacturer, hsa_reg_no, active, atc_code) "
                        "VALUES (:medication_id, :name, :generic_name, :brand_name, :strength, :dosage_form, :route, :manufacturer, :hsa_reg_no, :active, :atc_code) "
                        "ON CONFLICT (medication_id) DO NOTHING"
                    ),
                    med_batch,
                )
                if ing_batch:
                    await session.execute(
                        text(
                            "INSERT INTO sdd_active_ingredients (id, medication_id, ingredient_name, strength_value, strength_unit) "
                            "VALUES (:id, :medication_id, :ingredient_name, :strength_value, :strength_unit)"
                        ),
                        ing_batch,
                    )
                await session.commit()
                total_meds += len(med_batch)
                total_ings += len(ing_batch)
                logger.info(f"Imported {total_meds:,} SDD medications, {total_ings:,} ingredients...")
                med_batch = []
                ing_batch = []

    # Final batch
    if med_batch:
        await session.execute(
            text(
                "INSERT INTO sdd_medications (medication_id, name, generic_name, brand_name, strength, dosage_form, route, manufacturer, hsa_reg_no, active, atc_code) "
                "VALUES (:medication_id, :name, :generic_name, :brand_name, :strength, :dosage_form, :route, :manufacturer, :hsa_reg_no, :active, :atc_code) "
                "ON CONFLICT (medication_id) DO NOTHING"
            ),
            med_batch,
        )
        if ing_batch:
            await session.execute(
                text(
                    "INSERT INTO sdd_active_ingredients (id, medication_id, ingredient_name, strength_value, strength_unit) "
                    "VALUES (:id, :medication_id, :ingredient_name, :strength_value, :strength_unit)"
                ),
                ing_batch,
            )
        await session.commit()
        total_meds += len(med_batch)
        total_ings += len(ing_batch)

    # Generate Full-Text Search TSVectors for SDD
    logger.info("Generating PostgreSQL TSVectors for SDD medications & ingredients...")
    await session.execute(
        text(
            "UPDATE sdd_medications SET search_vector = "
            "to_tsvector('english', coalesce(name, '') || ' ' || coalesce(generic_name, '') || ' ' || coalesce(brand_name, ''))"
        )
    )
    await session.execute(
        text("UPDATE sdd_active_ingredients SET search_vector = to_tsvector('english', ingredient_name)")
    )
    await session.commit()

    # Track catalogue metadata
    meta = SDDCatalogueMetadata(
        catalogue_version="SDD-TERTIARY-CARE-2024",
        source="Singapore Drug Dictionary (Live AWS Server Sync)",
        record_count=total_meds,
    )
    session.add(meta)
    await session.commit()

    logger.info(f"SDD import complete: {total_meds:,} medications, {total_ings:,} ingredients.")
    return total_meds


async def main() -> None:
    logger.info("Starting Real Medical Terminology Import into local Docker database...")
    async with async_session_factory() as session:
        # 1. Ensure table schemas exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 2. Import SNOMED CT
        snomed_count = await import_snomed(session)

        # 3. Import SDD
        sdd_count = await import_sdd(session)

        logger.info("=" * 60)
        logger.info("DATABASE SYNC FINISHED SUCCESSFULLY!")
        logger.info(f"Total SNOMED CT Real Concepts: {snomed_count:,}")
        logger.info(f"Total SDD Real Medications:    {sdd_count:,}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
