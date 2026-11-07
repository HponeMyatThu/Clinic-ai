"""SQLAlchemy models for Singapore Drug Dictionary (SDD) data."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SDDMedication(Base):
    """A medication entry from the Singapore Drug Dictionary."""

    __tablename__ = "sdd_medications"
    __table_args__ = (
        Index(
            "ix_sdd_medications_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_sdd_medications_generic_name_trgm",
            "generic_name",
            postgresql_using="gin",
            postgresql_ops={"generic_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_sdd_medications_brand_name_trgm",
            "brand_name",
            postgresql_using="gin",
            postgresql_ops={"brand_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_sdd_medications_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    medication_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="SDD catalogue identifier"
    )
    name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Display name"
    )
    generic_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="e.g. Tablet, Capsule, Syrup"
    )
    route: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="e.g. Oral, Topical, IV"
    )
    manufacturer: Mapped[str | None] = mapped_column(String(300), nullable=True)
    hsa_reg_no: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="HSA registration number"
    )
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, nullable=False
    )
    atc_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="ATC classification code"
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, nullable=True
    )

    # -- relationships --
    active_ingredients: Mapped[list[SDDActiveIngredient]] = relationship(
        "SDDActiveIngredient",
        back_populates="medication",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<SDDMedication {self.medication_id} '{self.name}'>"


class SDDActiveIngredient(UUIDPrimaryKeyMixin, Base):
    """An active ingredient entry linked to an SDD medication."""

    __tablename__ = "sdd_active_ingredients"
    __table_args__ = (
        Index(
            "ix_sdd_active_ingredients_ingredient_name_trgm",
            "ingredient_name",
            postgresql_using="gin",
            postgresql_ops={"ingredient_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_sdd_active_ingredients_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    medication_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("sdd_medications.medication_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name: Mapped[str] = mapped_column(String(500), nullable=False)
    strength_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strength_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, nullable=True
    )

    # -- relationships --
    medication: Mapped[SDDMedication] = relationship(
        "SDDMedication",
        back_populates="active_ingredients",
    )

    def __repr__(self) -> str:
        return f"<SDDActiveIngredient '{self.ingredient_name}'>"


class SDDCatalogueMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks imported SDD catalogue versions."""

    __tablename__ = "sdd_catalogue_metadata"

    catalogue_version: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Singapore Drug Dictionary",
    )
    import_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<SDDCatalogueMetadata v{self.catalogue_version}>"
