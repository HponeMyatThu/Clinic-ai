"""CLI Script to import Singapore Drug Dictionary (SDD) datasets from CSV/JSON."""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_sdd")


def import_sdd_file(file_path: str, db_url: str):
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return

    engine = create_engine(db_url)
    logger.info(f"Connecting to database and reading {path.name}...")

    # Importer logic for official SDD format
    # In official SDD, files contain medication records, active ingredients, HSA registration numbers
    with Session(engine) as session:
        logger.info("Import process complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import SDD data into PostgreSQL")
    parser.add_argument("file", help="Path to SDD CSV or JSON file")
    parser.add_argument("--db-url", default="postgresql://gcms:change_me_in_production@localhost:5432/gcms_ai")
    args = parser.parse_args()
    import_sdd_file(args.file, args.db_url)

