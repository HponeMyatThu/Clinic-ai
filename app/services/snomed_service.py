"""SNOMED CT search and validation service."""

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import Select, func, literal, literal_column, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.snomed import SnomedConcept, SnomedDescription, SnomedReleaseMetadata
from app.schemas.snomed import SnomedConceptResult, SnomedConceptValidation

# Pre-compiled regex for extracting semantic tags from FSN
_SEMANTIC_TAG_RE = re.compile(r"\(([^)]+)\)\s*$")


class SnomedService:
    """Provides SNOMED CT lookup, search, and validation against PostgreSQL."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._settings = get_settings()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SnomedConceptResult], int]:
        """Search SNOMED CT descriptions using a three-tier scoring strategy.

        1. Exact match on term (score = 1.0)
        2. Full-text search via ``search_vector`` (score = ts_rank * 0.8)
        3. Trigram similarity where ``similarity > 0.3`` (score = similarity * 0.6)

        Results are deduplicated by concept_id (keeping the highest score),
        grouped so each concept carries its preferred term + synonyms, then
        paginated with OFFSET / LIMIT.

        Returns:
            A tuple of ``(results, total_count)``.
        """
        query_normalised = query.strip()
        offset = (page - 1) * page_size

        # ----- Tier 1: Exact match -----
        exact_q = (
            select(
                SnomedDescription.concept_id,
                SnomedDescription.description_id,
                SnomedDescription.term,
                SnomedDescription.type_id,
                SnomedDescription.active.label("desc_active"),
                SnomedConcept.active.label("concept_active"),
                literal(1.0).label("score"),
                literal("exact").label("match_type"),
            )
            .join(SnomedConcept, SnomedDescription.concept_id == SnomedConcept.concept_id)
            .where(func.lower(SnomedDescription.term) == func.lower(query_normalised))
        )

        # ----- Tier 2: Full-text search -----
        ts_query = func.plainto_tsquery("english", query_normalised)
        fts_q = (
            select(
                SnomedDescription.concept_id,
                SnomedDescription.description_id,
                SnomedDescription.term,
                SnomedDescription.type_id,
                SnomedDescription.active.label("desc_active"),
                SnomedConcept.active.label("concept_active"),
                (func.ts_rank(SnomedDescription.search_vector, ts_query) * 0.8).label("score"),
                literal("partial").label("match_type"),
            )
            .join(SnomedConcept, SnomedDescription.concept_id == SnomedConcept.concept_id)
            .where(SnomedDescription.search_vector.op("@@")(ts_query))
        )

        # ----- Tier 3: Trigram similarity -----
        similarity_fn = func.similarity(SnomedDescription.term, query_normalised)
        trgm_q = (
            select(
                SnomedDescription.concept_id,
                SnomedDescription.description_id,
                SnomedDescription.term,
                SnomedDescription.type_id,
                SnomedDescription.active.label("desc_active"),
                SnomedConcept.active.label("concept_active"),
                (similarity_fn * 0.6).label("score"),
                literal("fuzzy").label("match_type"),
            )
            .join(SnomedConcept, SnomedDescription.concept_id == SnomedConcept.concept_id)
            .where(similarity_fn > 0.25)
        )

        # Apply active_only filter to all three tiers
        if active_only:
            exact_q = exact_q.where(SnomedConcept.active.is_(True))
            fts_q = fts_q.where(SnomedConcept.active.is_(True))
            trgm_q = trgm_q.where(SnomedConcept.active.is_(True))

        # ----- Combine -----
        combined = union_all(exact_q, fts_q, trgm_q).subquery("combined")

        # Deduplicate: pick the row with the highest score per (concept_id, description_id)
        deduped = (
            select(
                combined.c.concept_id,
                combined.c.description_id,
                combined.c.term,
                combined.c.type_id,
                combined.c.desc_active,
                combined.c.concept_active,
                func.max(combined.c.score).label("score"),
                # Keep the match_type of the highest-scoring tier
                func.min(combined.c.match_type).label("match_type"),
            )
            .group_by(
                combined.c.concept_id,
                combined.c.description_id,
                combined.c.term,
                combined.c.type_id,
                combined.c.desc_active,
                combined.c.concept_active,
            )
        ).subquery("deduped")

        # ----- Execute the full query (no pagination yet — we need all rows
        #       to group descriptions by concept) -----
        ordered = (
            select(
                deduped.c.concept_id,
                deduped.c.description_id,
                deduped.c.term,
                deduped.c.type_id,
                deduped.c.desc_active,
                deduped.c.concept_active,
                deduped.c.score,
                deduped.c.match_type,
            )
            .order_by(deduped.c.score.desc())
        )

        result = await self.db.execute(ordered)
        rows = result.all()

        # ----- Group by concept_id -----
        concept_map: dict[str, dict] = {}
        concept_order: list[str] = []  # preserve score order

        for row in rows:
            cid = row.concept_id
            if cid not in concept_map:
                concept_map[cid] = {
                    "concept_id": cid,
                    "active": row.concept_active,
                    "score": float(row.score),
                    "match_type": row.match_type,
                    "fsn": None,
                    "preferred_term": None,
                    "synonyms": [],
                }
                concept_order.append(cid)
            entry = concept_map[cid]

            # Update score if this row is higher (shouldn't happen given
            # ordering, but be defensive)
            if float(row.score) > entry["score"]:
                entry["score"] = float(row.score)
                entry["match_type"] = row.match_type

            # Classify description
            if row.type_id == SnomedDescription.FSN_TYPE_ID:
                entry["fsn"] = row.term
            elif row.type_id == SnomedDescription.SYNONYM_TYPE_ID:
                if entry["preferred_term"] is None:
                    entry["preferred_term"] = row.term
                else:
                    if row.term not in entry["synonyms"] and row.term != entry["preferred_term"]:
                        entry["synonyms"].append(row.term)

        total = len(concept_order)

        # ----- Paginate -----
        page_ids = concept_order[offset : offset + page_size]

        results: list[SnomedConceptResult] = []
        for cid in page_ids:
            entry = concept_map[cid]
            preferred = entry["preferred_term"] or entry["fsn"] or ""
            display = preferred
            semantic_tag = self._extract_semantic_tag(entry["fsn"]) if entry["fsn"] else None

            results.append(
                SnomedConceptResult(
                    concept_id=entry["concept_id"],
                    display=display,
                    preferred_term=preferred,
                    synonyms=entry["synonyms"],
                    active=entry["active"],
                    semantic_tag=semantic_tag,
                    match_type=entry["match_type"],
                    relevance_score=round(entry["score"], 4),
                )
            )

        return results, total

    async def validate_concept(self, concept_id: str) -> SnomedConceptValidation:
        """Check whether a SNOMED CT concept ID exists and is active."""
        stmt = (
            select(SnomedConcept)
            .where(SnomedConcept.concept_id == concept_id)
        )
        result = await self.db.execute(stmt)
        concept = result.scalar_one_or_none()

        if concept is None:
            return SnomedConceptValidation(concept_id=concept_id, valid=False)

        # Fetch preferred term (first synonym description)
        desc_stmt = (
            select(SnomedDescription.term)
            .where(
                SnomedDescription.concept_id == concept_id,
                SnomedDescription.type_id == SnomedDescription.SYNONYM_TYPE_ID,
                SnomedDescription.active.is_(True),
            )
            .limit(1)
        )
        desc_result = await self.db.execute(desc_stmt)
        preferred = desc_result.scalar_one_or_none()

        # Fallback to FSN if no synonym
        if preferred is None:
            fsn_stmt = (
                select(SnomedDescription.term)
                .where(
                    SnomedDescription.concept_id == concept_id,
                    SnomedDescription.type_id == SnomedDescription.FSN_TYPE_ID,
                    SnomedDescription.active.is_(True),
                )
                .limit(1)
            )
            fsn_result = await self.db.execute(fsn_stmt)
            preferred = fsn_result.scalar_one_or_none()

        return SnomedConceptValidation(
            concept_id=concept_id,
            valid=True,
            active=concept.active,
            display=preferred,
        )

    async def get_release_version(self) -> str:
        """Return the most recent SNOMED CT release version from metadata.

        Falls back to the configured ``snomed_release_version`` setting.
        """
        stmt = (
            select(SnomedReleaseMetadata.version)
            .order_by(SnomedReleaseMetadata.import_date.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        return version or self._settings.snomed_release_version

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_semantic_tag(fsn: str | None) -> str | None:
        """Extract the semantic tag from a Fully Specified Name.

        Example::

            >>> SnomedService._extract_semantic_tag("Diabetes mellitus (disorder)")
            'disorder'
        """
        if not fsn:
            return None
        match = _SEMANTIC_TAG_RE.search(fsn)
        return match.group(1) if match else None
