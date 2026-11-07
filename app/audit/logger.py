"""Audit logging for clinical governance and accountability."""

from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditEvent

logger = logging.getLogger("gcms.audit")


class AuditLogger:
    """Records audit trails for all AI and terminology queries without recording PHI."""

    @staticmethod
    async def log_event(
        db: AsyncSession | None,
        request_id: str,
        event_type: str,
        status: str,
        endpoint: str | None = None,
        model_used: str | None = None,
        prompt_version: str | None = None,
        clinician_id: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Structured log (safe - no PHI)
        logger.info(
            "AUDIT_EVENT",
            extra={
                "request_id": request_id,
                "event_type": event_type,
                "status": status,
                "endpoint": endpoint,
                "model_used": model_used,
                "clinician_id": clinician_id,
                "metadata": metadata or {},
            },
        )

        if db is not None:
            try:
                event = AuditEvent(
                    request_id=request_id,
                    event_type=event_type,
                    status=status,
                    endpoint=endpoint,
                    model_used=model_used,
                    prompt_version=prompt_version,
                    clinician_id=clinician_id,
                    tenant_id=tenant_id,
                    metadata_json=metadata,
                )
                db.add(event)
                await db.commit()
            except Exception as exc:
                logger.error(f"Failed to persist audit event to DB: {exc}")

