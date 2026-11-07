"""Unit tests for Clinical Safety engine."""

from __future__ import annotations

import pytest
from app.clinical_safety.allergy_checker import AllergyChecker
from app.clinical_safety.interaction_checker import InteractionChecker
from app.clinical_safety.contraindication_checker import ContraindicationChecker
from app.clinical_safety.duplicate_therapy_checker import DuplicateTherapyChecker
from app.clinical_safety.safety_orchestrator import SafetyOrchestrator
from app.schemas.common import SafetyStatus
from app.schemas.consultation import ConsultationContext


def test_allergy_checker_penicillin_cross_reactivity():
    checker = AllergyChecker()
    result = checker.check(
        medication_name="Augmentin 625mg Tablet",
        generic_name="Amoxicillin and Clavulanate Potassium",
        active_ingredients=["Amoxicillin", "Clavulanic Acid"],
        patient_allergies=["Penicillin"],
    )
    assert result.has_conflict is True
    assert any("ALLERGY" in w or "CROSS-REACTIVITY" in w for w in result.warnings)


def test_interaction_checker_warfarin_aspirin():
    checker = InteractionChecker()
    result = checker.check(
        proposed_medication="Aspirin 100mg Tablet",
        generic_name="Aspirin",
        current_medications=["Warfarin 5mg daily"],
    )
    assert result.has_warnings is True
    assert any("bleeding risk" in w.description.lower() for w in result.warnings)


def test_contraindication_pregnancy():
    checker = ContraindicationChecker()
    result = checker.check(
        medication_name="Losartan 50mg",
        generic_name="Losartan",
        patient_conditions=["Hypertension"],
        pregnancy_status="pregnant_trimester_2",
        renal_function="normal",
        hepatic_function="normal",
    )
    assert result.has_contraindication is True
    assert any("CRITICAL CONTRAINDICATION" in w for w in result.warnings)


def test_duplicate_therapy_detection():
    checker = DuplicateTherapyChecker()
    result = checker.check(
        proposed_medication="Panadol 500mg",
        generic_name="Paracetamol",
        active_ingredients=["Paracetamol"],
        current_medications=["Paracetamol 500mg QDS"],
    )
    assert result.is_duplicate is True
    assert any("DUPLICATE" in w for w in result.warnings)


def test_safety_orchestrator_blocks_allergic_drug():
    orchestrator = SafetyOrchestrator()
    context = ConsultationContext(
        chief_complaint="Throat infection",
        allergies=["Penicillin"],
        current_medications=[],
    )
    report = orchestrator.evaluate_medication(
        medication_name="Amoxicillin 500mg",
        generic_name="Amoxicillin",
        active_ingredients=["Amoxicillin"],
        context=context,
    )
    assert report.overall_status == SafetyStatus.BLOCKED

