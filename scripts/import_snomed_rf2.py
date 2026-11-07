#!/usr/bin/env python
"""Import SNOMED CT RF2 Snapshot files into PostgreSQL.

Usage::

    python -m scripts.import_snomed_rf2 /path/to/RF2/Snapshot

Expects the standard RF2 naming convention:
    - sct2_Concept_Snapshot_*.txt
    - sct2_Description_Snapshot_*.txt
    - sct2_Relationship_Snapshot_*.txt
"""

from __future__ import annotations

import argparse
import csv
import glob
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.snomed import (
    SnomedConcept,
    SnomedDescription,
    SnomedRelationship,
    SnomedReleaseMetadata,
)

BATCH_SIZE = 5_000


def _find_rf2_file(directory: Path, pattern: str) -> Path | None:
    """Locate an RF2 file in *directory* matching *pattern*."""
    matches = list(directory.glob(pattern))
    if not matches:
        return None
    return matches[0]


def _parse_date(date_str: str) -> date:
    """Parse an RF2 effectiveTime string (yyyyMMdd) into a ``date``."""
    return datetime.strptime(date_str, "%Y%m%d").date()


def _bool(val: str) -> bool:
    return val.strip() == "1"


def _import_concepts(session: Session, filepath: Path) -> int:
    """Import concepts from an RF2 Concept Snapshot file."""
    count = 0
    batch: list[dict] = []

    print(f"  Reading {filepath.name} ...")
    with open(filepath, "r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            batch.append(
                {
                    "concept_id": row["id"],
                    "effective_time": _parse_date(row["effectiveTime"]),
                    "active": _bool(row["active"]),
                    "module_id": row["moduleId"],
                    "definition_status_id": row["definitionStatusId"],
                }
            )
            if len(batch) >= BATCH_SIZE:
                _upsert_concepts(session, batch)
                count += len(batch)
                print(f"    Concepts imported: {count}", end="\r")
                batch.clear()

    if batch:
        _upsert_concepts(session, batch)
        count += len(batch)

    print(f"    Concepts imported: {count}")
    return count


def _upsert_concepts(session: Session, rows: list[dict]) -> None:
    """Bulk upsert concepts using INSERT … ON CONFLICT DO UPDATE."""
    stmt = text("""
        INSERT INTO snomed_concepts
            (concept_id, effective_time, active, module_id, definition_status_id)
        VALUES
            (:concept_id, :effective_time, :active, :module_id, :definition_status_id)
        ON CONFLICT (concept_id) DO UPDATE SET
            effective_time = EXCLUDED.effective_time,
            active = EXCLUDED.active,
            module_id = EXCLUDED.module_id,
            definition_status_id = EXCLUDED.definition_status_id
    """)
    session.execute(stmt, rows)
    session.flush()


def _import_descriptions(session: Session, filepath: Path) -> int:
    """Import descriptions from an RF2 Description Snapshot file."""
    count = 0
    batch: list[dict] = []

    print(f"  Reading {filepath.name} ...")
    with open(filepath, "r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            batch.append(
                {
                    "description_id": row["id"],
                    "effective_time": _parse_date(row["effectiveTime"]),
                    "active": _bool(row["active"]),
                    "module_id": row["moduleId"],
                    "concept_id": row["conceptId"],
                    "language_code": row["languageCode"],
                    "type_id": row["typeId"],
                    "term": row["term"],
                    "case_significance_id": row["caseSignificanceId"],
                }
            )
            if len(batch) >= BATCH_SIZE:
                _upsert_descriptions(session, batch)
                count += len(batch)
                print(f"    Descriptions imported: {count}", end="\r")
                batch.clear()

    if batch:
        _upsert_descriptions(session, batch)
        count += len(batch)

    print(f"    Descriptions imported: {count}")
    return count


def _upsert_descriptions(session: Session, rows: list[dict]) -> None:
    """Bulk upsert descriptions using INSERT … ON CONFLICT DO UPDATE."""
    stmt = text("""
        INSERT INTO snomed_descriptions
            (description_id, effective_time, active, module_id, concept_id,
             language_code, type_id, term, case_significance_id)
        VALUES
            (:description_id, :effective_time, :active, :module_id, :concept_id,
             :language_code, :type_id, :term, :case_significance_id)
        ON CONFLICT (description_id) DO UPDATE SET
            effective_time = EXCLUDED.effective_time,
            active = EXCLUDED.active,
            module_id = EXCLUDED.module_id,
            concept_id = EXCLUDED.concept_id,
            language_code = EXCLUDED.language_code,
            type_id = EXCLUDED.type_id,
            term = EXCLUDED.term,
            case_significance_id = EXCLUDED.case_significance_id
    """)
    session.execute(stmt, rows)
    session.flush()


def _import_relationships(session: Session, filepath: Path) -> int:
    """Import relationships from an RF2 Relationship Snapshot file."""
    count = 0
    batch: list[dict] = []

    print(f"  Reading {filepath.name} ...")
    with open(filepath, "r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            batch.append(
                {
                    "relationship_id": row["id"],
                    "effective_time": _parse_date(row["effectiveTime"]),
                    "active": _bool(row["active"]),
                    "module_id": row["moduleId"],
                    "source_id": row["sourceId"],
                    "destination_id": row["destinationId"],
                    "relationship_group": int(row["relationshipGroup"]),
                    "type_id": row["typeId"],
                    "characteristic_type_id": row["characteristicTypeId"],
                    "modifier_id": row["modifierId"],
                }
            )
            if len(batch) >= BATCH_SIZE:
                _upsert_relationships(session, batch)
                count += len(batch)
                print(f"    Relationships imported: {count}", end="\r")
                batch.clear()

    if batch:
        _upsert_relationships(session, batch)
        count += len(batch)

    print(f"    Relationships imported: {count}")
    return count


def _upsert_relationships(session: Session, rows: list[dict]) -> None:
    """Bulk upsert relationships using INSERT … ON CONFLICT DO UPDATE."""
    stmt = text("""
        INSERT INTO snomed_relationships
            (relationship_id, effective_time, active, module_id,
             source_id, destination_id, relationship_group,
             type_id, characteristic_type_id, modifier_id)
        VALUES
            (:relationship_id, :effective_time, :active, :module_id,
             :source_id, :destination_id, :relationship_group,
             :type_id, :characteristic_type_id, :modifier_id)
        ON CONFLICT (relationship_id) DO UPDATE SET
            effective_time = EXCLUDED.effective_time,
            active = EXCLUDED.active,
            module_id = EXCLUDED.module_id,
            source_id = EXCLUDED.source_id,
            destination_id = EXCLUDED.destination_id,
            relationship_group = EXCLUDED.relationship_group,
            type_id = EXCLUDED.type_id,
            characteristic_type_id = EXCLUDED.characteristic_type_id,
            modifier_id = EXCLUDED.modifier_id
    """)
    session.execute(stmt, rows)
    session.flush()


def _update_search_vectors(session: Session) -> None:
    """Populate the tsvector column on all description rows."""
    print("  Updating search_vector column ...")
    session.execute(
        text(
            "UPDATE snomed_descriptions "
            "SET search_vector = to_tsvector('english', term)"
        )
    )
    session.flush()
    print("  search_vector updated.")


def _record_metadata(
    session: Session,
    edition: str,
    version: str,
    record_count: int,
) -> None:
    """Write a release-metadata row."""
    session.execute(
        text("""
            INSERT INTO snomed_release_metadata
                (id, edition, version, import_date, record_count, created_at, updated_at)
            VALUES
                (gen_random_uuid(), :edition, :version, now(), :record_count, now(), now())
        """),
        {"edition": edition, "version": version, "record_count": record_count},
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import SNOMED CT RF2 Snapshot files into PostgreSQL.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Path to the directory containing RF2 Snapshot .txt files",
    )
    parser.add_argument(
        "--edition",
        default="International",
        help="SNOMED CT edition label (default: International)",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Release version (default: derived from Concept filename date)",
    )
    args = parser.parse_args()

    rf2_dir: Path = args.directory
    if not rf2_dir.is_dir():
        print(f"ERROR: {rf2_dir} is not a directory.", file=sys.stderr)
        sys.exit(1)

    concept_file = _find_rf2_file(rf2_dir, "sct2_Concept_Snapshot_*.txt")
    description_file = _find_rf2_file(rf2_dir, "sct2_Description_Snapshot_*.txt")
    relationship_file = _find_rf2_file(rf2_dir, "sct2_Relationship_Snapshot_*.txt")

    if not concept_file:
        print("ERROR: No sct2_Concept_Snapshot_*.txt found.", file=sys.stderr)
        sys.exit(1)
    if not description_file:
        print("ERROR: No sct2_Description_Snapshot_*.txt found.", file=sys.stderr)
        sys.exit(1)

    # Derive version from filename if not provided
    version = args.version
    if version is None:
        # e.g. sct2_Concept_Snapshot_INT_20240101.txt → 20240101
        stem = concept_file.stem
        parts = stem.split("_")
        version = parts[-1] if parts else "unknown"

    settings = get_settings()
    sync_url = settings.sync_database_url
    engine = create_engine(sync_url, echo=False)

    t0 = time.perf_counter()
    total_records = 0

    print(f"SNOMED CT RF2 Import — edition={args.edition}, version={version}")
    print(f"  Database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print()

    with Session(engine) as session:
        with session.begin():
            # 1. Concepts
            n = _import_concepts(session, concept_file)
            total_records += n

            # 2. Descriptions
            n = _import_descriptions(session, description_file)
            total_records += n

            # 3. Relationships (optional — file may not be present)
            if relationship_file:
                n = _import_relationships(session, relationship_file)
                total_records += n
            else:
                print("  WARNING: No Relationship file found — skipping.")

            # 4. Search vectors
            _update_search_vectors(session)

            # 5. Metadata
            _record_metadata(session, args.edition, version, total_records)

    elapsed = time.perf_counter() - t0
    print()
    print(f"Import complete: {total_records:,} records in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
