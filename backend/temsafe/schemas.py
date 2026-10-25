"""Define the data returned by the API."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import Literal


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
