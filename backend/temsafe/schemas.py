"""Define the data returned by the API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


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
