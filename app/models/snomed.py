"""SQLAlchemy models for SNOMED CT RF2 data."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SnomedConcept(Base):
    """SNOMED CT Concept — mirrors the RF2 Concept file."""

    __tablename__ = "snomed_concepts"

    concept_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    effective_time: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(20), nullable=False)
    definition_status_id: Mapped[str] = mapped_column(String(20), nullable=False)

    # -- relationships --
    descriptions: Mapped[list[SnomedDescription]] = relationship(
        "SnomedDescription",
        back_populates="concept",
        lazy="selectin",
    )
    source_relationships: Mapped[list[SnomedRelationship]] = relationship(
        "SnomedRelationship",
        foreign_keys="SnomedRelationship.source_id",
        back_populates="source_concept",
        lazy="selectin",
    )
    destination_relationships: Mapped[list[SnomedRelationship]] = relationship(
        "SnomedRelationship",
        foreign_keys="SnomedRelationship.destination_id",
        back_populates="destination_concept",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SnomedConcept {self.concept_id}>"


class SnomedDescription(Base):
    """SNOMED CT Description — mirrors the RF2 Description file."""

    __tablename__ = "snomed_descriptions"
    __table_args__ = (
        Index("ix_snomed_descriptions_concept_id", "concept_id"),
        Index(
            "ix_snomed_descriptions_term_trgm",
            "term",
            postgresql_using="gin",
            postgresql_ops={"term": "gin_trgm_ops"},
        ),
        Index(
            "ix_snomed_descriptions_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    description_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    effective_time: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    module_id: Mapped[str] = mapped_column(String(20), nullable=False)
    concept_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("snomed_concepts.concept_id"),
        nullable=False,
    )
    language_code: Mapped[str] = mapped_column(String(5), nullable=False)
    type_id: Mapped[str] = mapped_column(String(20), nullable=False)
    term: Mapped[str] = mapped_column(Text, nullable=False)
    case_significance_id: Mapped[str] = mapped_column(String(20), nullable=False)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        nullable=True,
    )

    # -- relationships --
    concept: Mapped[SnomedConcept] = relationship(
        "SnomedConcept",
        back_populates="descriptions",
    )

    # Well-known type_id constants
    FSN_TYPE_ID: str = "900000000000003001"
    SYNONYM_TYPE_ID: str = "900000000000013009"

    def __repr__(self) -> str:
        return f"<SnomedDescription {self.description_id} '{self.term[:40]}'>"


class SnomedRelationship(Base):
    """SNOMED CT Relationship — mirrors the RF2 Relationship file."""

    __tablename__ = "snomed_relationships"

    relationship_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    effective_time: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    module_id: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("snomed_concepts.concept_id"),
        nullable=False,
        index=True,
    )
    destination_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("snomed_concepts.concept_id"),
        nullable=False,
        index=True,
    )
    relationship_group: Mapped[int] = mapped_column(Integer, nullable=False)
    type_id: Mapped[str] = mapped_column(String(20), nullable=False)
    characteristic_type_id: Mapped[str] = mapped_column(String(20), nullable=False)
    modifier_id: Mapped[str] = mapped_column(String(20), nullable=False)

    # -- relationships --
    source_concept: Mapped[SnomedConcept] = relationship(
        "SnomedConcept",
        foreign_keys=[source_id],
        back_populates="source_relationships",
    )
    destination_concept: Mapped[SnomedConcept] = relationship(
        "SnomedConcept",
        foreign_keys=[destination_id],
        back_populates="destination_relationships",
    )

    # Well-known type_id for "Is a" relationship
    IS_A_TYPE_ID: str = "116680003"

    def __repr__(self) -> str:
        return f"<SnomedRelationship {self.relationship_id}>"


class SnomedReleaseMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks imported SNOMED CT releases."""

    __tablename__ = "snomed_release_metadata"

    edition: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    import_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<SnomedReleaseMetadata {self.edition} v{self.version}>"
