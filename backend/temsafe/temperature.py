"""Classify temperatures using the profile applied to a measurement."""

from decimal import Decimal
from temsafe.models import ThresholdProfile
from typing import Literal


def classify_temperature(
        temperature_c: Decimal | None,
        quality: str,
        profile: ThresholdProfile,
) -> Literal["Normal", "Warning", "Alert", "Unknown"]:
    """Return the temperature state without reading or changing the database."""
    # A failed or missing measurement must never be treated as a normal temperature.
    if quality != "valid" or temperature_c is None:
        return "Unknown"

    # The lower boundary is inclusive; the upper boundary itself is still Warning.
    if temperature_c <= profile.lower_c or temperature_c > profile.upper_c:
        return "Alert"
    if temperature_c >= profile.warning_c:
        return "Warning"
    return "Normal"
