"""Pytest configuration and shared test fixtures."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.schemas.consultation import ConsultationContext


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def async_client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def sample_consultation_context() -> ConsultationContext:
    """Realistic consultation context for an acute respiratory presentation."""
    return ConsultationContext(
        consultation_id="enc-test-101",
        chief_complaint="Productive cough and fever for 3 days",
        history_of_present_illness="Patient reports runny nose and low-grade fever starting 3 days ago.",
        symptoms=["Cough", "Fever", "Rhinorrhea", "Throat discomfort"],
        symptom_duration="3 days",
        medical_history=["Hypertension"],
        current_medications=["Amlodipine 5mg daily"],
        allergies=["Penicillin"],
        patient_age=45,
        patient_gender="M",
    )

