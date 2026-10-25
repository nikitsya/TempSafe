"""Define the data returned by the API."""

from datetime import datetime
from decimal import Decimal
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator
from typing import Literal
from uuid import UUID


class ReadingCreate(BaseModel):
    """Validate an incoming sample before it can be stored in MySQL."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    sample_id: UUID
    box_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    sequence_no: int = Field(strict=True, ge=0, le=18446744073709551615)
    profile_id: UUID
    observed_at: AwareDatetime | None
    clock_reliable: StrictBool
    temperature_c: Decimal | None = Field(ge=-40, le=80, max_digits=5, decimal_places=2)
    quality: Literal["valid", "sensor_error"]

    @model_validator(mode="after")
    def check_sample_consistency(self):
        """Match the quality and clock rules enforced by the existing SQL schema."""
        if self.quality == "valid" and self.temperature_c is None:
            raise ValueError("A valid sample requires a temperature")
        if self.quality == "sensor_error" and self.temperature_c is not None:
            raise ValueError("A sensor error must not contain a temperature")
        if self.clock_reliable != (self.observed_at is not None):
            raise ValueError("A reliable clock requires an observation time; an unreliable clock requires null")
        return self


class BoxResponse(BaseModel):
    """Return a box's identity and last recorded contact time."""

    model_config = ConfigDict(from_attributes=True)

    box_id: str
    name: str
    # A box may not have contacted the server yet.
    last_seen_at: datetime | None


class ReadingResponse(BaseModel):
    """Return a stored sample, including missing values after a sensor error."""

    # Read fields from a SQLAlchemy model
    model_config = ConfigDict(from_attributes=True)

    sample_id: str
    box_id: str
    sequence_no: int
    profile_id: str
    observed_at: datetime | None
    clock_reliable: bool
    received_at: datetime
    temperature_c: Decimal | None
    quality: Literal["valid", "sensor_error"]


class LatestReadingResponse(ReadingResponse):
    """Include the calculated temperature state alongside all reading fields."""

    temperature_state: Literal["Normal", "Warning", "Alert", "Unknown"]
