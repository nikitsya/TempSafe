from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, ForeignKeyConstraint, Numeric, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, CHAR, DATETIME, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from temsafe.database import Base


class Box(Base):
    """Represent the box to which measurements and profiles belong."""

    __tablename__ = "boxes"

    box_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    last_seen_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))


class ThresholdProfile(Base):
    """Represent the limits associated with a box's measurements."""

    __tablename__ = "threshold_profiles"

    profile_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    box_id: Mapped[str] = mapped_column(ForeignKey("boxes.box_id"))
    lower_c: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    upper_c: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    warning_c: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    source_note: Mapped[str] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), server_default=text("CURRENT_TIMESTAMP(6)")
    )


class TemperatureSample(Base):
    """Represent one sample attempt in the existing temperature_samples table."""

    __tablename__ = "temperature_samples"

    # The profile and measurement must belong to the same box.
    __table_args__ = (
        ForeignKeyConstraint(
            ["profile_id", "box_id"],
            ["threshold_profiles.profile_id", "threshold_profiles.box_id"],
        ),
    )

    sample_id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    box_id: Mapped[str] = mapped_column(ForeignKey("boxes.box_id"))
    sequence_no: Mapped[int] = mapped_column(BIGINT(unsigned=True))
    profile_id: Mapped[str] = mapped_column(CHAR(36))
    observed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
    clock_reliable: Mapped[bool] = mapped_column(Boolean)
    received_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), server_default=text("CURRENT_TIMESTAMP(6)")
    )
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    quality: Mapped[str] = mapped_column(ENUM("valid", "sensor_error"))


# Do not call Base.metadata.create_all() to initialise or migrate this schema.
