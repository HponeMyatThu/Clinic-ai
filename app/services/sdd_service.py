"""SDD medication search and validation service.

Provides multi-strategy search (exact, full-text, trigram, ingredient)
against the Singapore Drug Dictionary catalogue stored in PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import func, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.sdd import SDDActiveIngredient, SDDCatalogueMetadata, SDDMedication
from app.schemas.sdd import SDDIngredientResult, SDDMedicationResult, SDDMedicationValidation


class SDDService:
    """Service layer for SDD medication lookup and validation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SDDMedicationResult], int]:
        """Search SDD medications using a multi-strategy ranked approach.

        Strategy order (highest score wins per medication_id):
        1. Exact match on name / generic_name / brand_name → score 1.0
        2. Full-text search on search_vector → ts_rank * 0.8
        3. Trigram similarity on name / generic_name / brand_name → sim * 0.6
        4. Ingredient name trigram match → 0.7
        Results are deduplicated by medication_id keeping the best score.
        """
        query_lower = query.strip()
        if not query_lower:
            return [], 0

        ts_query_str = " & ".join(query_lower.split())

        # Active filter fragment
        active_filter = "AND m.active = true" if active_only else ""

        # Build a CTE that unions all match strategies and picks the best
        # score per medication_id.
        scoring_sql = text(f"""
            WITH exact_matches AS (
                SELECT m.medication_id, 1.0::float AS score, 'exact'::text AS match_type
                FROM sdd_medications m
                WHERE (
                    LOWER(m.name) = LOWER(:q)
                    OR LOWER(m.generic_name) = LOWER(:q)
                    OR LOWER(m.brand_name) = LOWER(:q)
                )
                {active_filter}
            ),
            fulltext_matches AS (
                SELECT m.medication_id,
                       (ts_rank(m.search_vector, plainto_tsquery('english', :q)) * 0.8)::float AS score,
                       'partial'::text AS match_type
                FROM sdd_medications m
                WHERE m.search_vector @@ plainto_tsquery('english', :q)
                {active_filter}
            ),
            trigram_matches AS (
                SELECT m.medication_id,
                       (GREATEST(
                           similarity(LOWER(m.name), LOWER(:q)),
                           COALESCE(similarity(LOWER(m.generic_name), LOWER(:q)), 0),
                           COALESCE(similarity(LOWER(m.brand_name), LOWER(:q)), 0)
                       ) * 0.6)::float AS score,
                       'fuzzy'::text AS match_type
                FROM sdd_medications m
                WHERE (
                    similarity(LOWER(m.name), LOWER(:q)) > 0.3
                    OR similarity(LOWER(m.generic_name), LOWER(:q)) > 0.3
                    OR similarity(LOWER(m.brand_name), LOWER(:q)) > 0.3
                )
                {active_filter}
            ),
            ingredient_matches AS (
                SELECT m.medication_id,
                       0.7::float AS score,
                       'ingredient'::text AS match_type
                FROM sdd_medications m
                INNER JOIN sdd_active_ingredients ai ON ai.medication_id = m.medication_id
                WHERE similarity(LOWER(ai.ingredient_name), LOWER(:q)) > 0.3
                {active_filter}
            ),
            all_matches AS (
                SELECT * FROM exact_matches
                UNION ALL
                SELECT * FROM fulltext_matches
                UNION ALL
                SELECT * FROM trigram_matches
                UNION ALL
                SELECT * FROM ingredient_matches
            ),
            best AS (
                SELECT DISTINCT ON (medication_id)
                    medication_id, score, match_type
                FROM all_matches
                ORDER BY medication_id, score DESC
            )
            SELECT medication_id, score, match_type
            FROM best
            ORDER BY score DESC, medication_id
        """)

        rows = (await self.db.execute(scoring_sql, {"q": query_lower})).all()
        total = len(rows)

        # Paginate the scored IDs
        offset = (page - 1) * page_size
        page_rows = rows[offset : offset + page_size]

        if not page_rows:
            return [], total

        # Fetch the full medication objects for the current page
        med_ids = [r.medication_id for r in page_rows]
        score_map: dict[str, tuple[float, str]] = {
            r.medication_id: (r.score, r.match_type) for r in page_rows
        }

        stmt = (
            select(SDDMedication)
            .options(selectinload(SDDMedication.active_ingredients))
            .where(SDDMedication.medication_id.in_(med_ids))
        )
        meds = (await self.db.execute(stmt)).scalars().all()

        # Build a lookup so we can order by score
        med_lookup = {m.medication_id: m for m in meds}
        results: list[SDDMedicationResult] = []
        for mid in med_ids:
            med = med_lookup.get(mid)
            if med is None:
                continue
            score, match_type = score_map[mid]
            results.append(self._to_result(med, match_type=match_type, score=score))

        return results, total

    async def validate_medication(self, medication_id: str) -> SDDMedicationValidation:
        """Look up a medication by its SDD identifier."""
        stmt = select(SDDMedication).where(
            SDDMedication.medication_id == medication_id
        )
        med = (await self.db.execute(stmt)).scalar_one_or_none()

        if med is None:
            return SDDMedicationValidation(
                medication_id=medication_id,
                valid=False,
            )

        return SDDMedicationValidation(
            medication_id=med.medication_id,
            valid=True,
            active=med.active,
            name=med.name,
        )

    async def get_catalogue_version(self) -> str:
        """Return the latest catalogue version from metadata, falling back to config."""
        stmt = (
            select(SDDCatalogueMetadata.catalogue_version)
            .order_by(SDDCatalogueMetadata.import_date.desc())
            .limit(1)
        )
        version = (await self.db.execute(stmt)).scalar_one_or_none()
        if version:
            return version
        return get_settings().sdd_catalogue_version

    async def find_by_ingredient(self, ingredient_name: str) -> list[SDDMedicationResult]:
        """Find all medications containing a specific active ingredient.

        Uses trigram similarity (threshold > 0.3) on ingredient_name to allow
        for minor spelling variations.
        """
        ingredient_lower = ingredient_name.strip().lower()

        sql = text("""
            SELECT DISTINCT m.medication_id
            FROM sdd_medications m
            INNER JOIN sdd_active_ingredients ai ON ai.medication_id = m.medication_id
            WHERE similarity(LOWER(ai.ingredient_name), :ing) > 0.3
            ORDER BY m.medication_id
        """)

        rows = (await self.db.execute(sql, {"ing": ingredient_lower})).all()
        if not rows:
            return []

        med_ids = [r.medication_id for r in rows]

        stmt = (
            select(SDDMedication)
            .options(selectinload(SDDMedication.active_ingredients))
            .where(SDDMedication.medication_id.in_(med_ids))
            .order_by(SDDMedication.name)
        )
        meds = (await self.db.execute(stmt)).scalars().all()

        return [
            self._to_result(med, match_type="ingredient", score=0.7)
            for med in meds
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_result(
        med: SDDMedication,
        *,
        match_type: str,
        score: float,
    ) -> SDDMedicationResult:
        """Convert an ORM model instance to a Pydantic response."""
        return SDDMedicationResult(
            medication_id=med.medication_id,
            name=med.name,
            generic_name=med.generic_name,
            brand_name=med.brand_name,
            active_ingredients=[
                SDDIngredientResult(
                    ingredient_name=ai.ingredient_name,
                    strength_value=ai.strength_value,
                    strength_unit=ai.strength_unit,
                )
                for ai in med.active_ingredients
            ],
            strength=med.strength,
            dosage_form=med.dosage_form,
            route=med.route,
            manufacturer=med.manufacturer,
            atc_code=med.atc_code,
            active=med.active,
            match_type=match_type,
            relevance_score=min(score, 1.0),
        )
