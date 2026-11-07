"""Define the data returned by the API."""

from datetime import UTC, datetime
from decimal import Decimal
from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, StrictBool, model_validator
from typing import Annotated, Literal
from uuid import UUID


def as_utc(value: datetime) -> datetime:
    """Interpret timezone-free database values as UTC and normalise aware values."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


UTCTimestamp = Annotated[datetime, AfterValidator(as_utc)]


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
    last_seen_at: UTCTimestamp | None


class ReadingResponse(BaseModel):
    """Return a stored sample, including missing values after a sensor error."""

    # Read fields from a SQLAlchemy model
    model_config = ConfigDict(from_attributes=True)

    sample_id: str
    box_id: str
    sequence_no: int
    profile_id: str
    observed_at: UTCTimestamp | None
    clock_reliable: bool
    received_at: UTCTimestamp
    temperature_c: Decimal | None
    quality: Literal["valid", "sensor_error"]


class ReadingProfileResponse(BaseModel):
    """Return the limits recorded for a sample."""

    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    lower_c: Decimal
    warning_c: Decimal
    upper_c: Decimal


class HistoryReadingResponse(ReadingResponse):
    """Include the recorded profile and calculated temperature state."""

    temperature_state: Literal["Normal", "Warning", "Alert", "Unknown"]
    profile: ReadingProfileResponse


class LatestReadingResponse(HistoryReadingResponse):
    """Include the freshness of the latest observation."""

    freshness: Literal["fresh", "stale", "unknown"]


class HeartbeatSettings(BaseModel):
    """Represent the desired interval between device heartbeats."""

    model_config = ConfigDict(extra="forbid")
    heartbeat_interval_seconds: int = Field(strict=True, ge=1, le=65535)


class ThresholdSettingsCreate(BaseModel):
    """Validate prototype limits before creating an immutable profile."""

    model_config = ConfigDict(extra="forbid")

    lower_c: Decimal = Field(ge=-40, le=80, max_digits=5, decimal_places=2)
    warning_c: Decimal = Field(ge=-40, le=80, max_digits=5, decimal_places=2)
    upper_c: Decimal = Field(ge=-40, le=80, max_digits=5, decimal_places=2)
    source_note: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def check_limits(self):
        """Require ordered limits and a meaningful explanation."""
        if not self.lower_c < self.warning_c < self.upper_c:
            raise ValueError("Require lower_c < warning_c < upper_c")
        self.source_note = self.source_note.strip()
        if not self.source_note:
            raise ValueError("A source note is required")
        return self


class ThresholdSettingsResponse(ReadingProfileResponse):
    """Describe the desired profile, not confirmation of device adoption."""

    box_id: str
    source_note: str
    is_demo: bool
    created_at: UTCTimestamp
