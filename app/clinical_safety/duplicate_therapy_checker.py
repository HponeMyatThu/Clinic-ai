"""Duplicate medication and duplicate therapy detection."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DuplicateTherapyResult(BaseModel):
    is_duplicate: bool = False
    warnings: list[str] = Field(default_factory=list)


class DuplicateTherapyChecker:
    """Detects duplicate active ingredients or therapeutic duplication."""

    def check(
        self,
        proposed_medication: str,
        generic_name: str | None,
        active_ingredients: list[str],
        current_medications: list[str],
    ) -> DuplicateTherapyResult:
        if not current_medications:
            return DuplicateTherapyResult(is_duplicate=False)

        warnings: list[str] = []
        tokens = [proposed_medication.lower()]
        if generic_name:
            tokens.append(generic_name.lower())
        for ing in active_ingredients:
            tokens.append(ing.lower())

        for curr_med in current_medications:
            curr_lower = curr_med.lower()
            for token in tokens:
                if len(token) > 3 and token in curr_lower:
                    warnings.append(
                        f"DUPLICATE THERAPY ALERT: Patient is already taking '{curr_med}', which matches proposed '{proposed_medication}'."
                    )
                    break

        return DuplicateTherapyResult(
            is_duplicate=len(warnings) > 0,
            warnings=warnings,
        )

