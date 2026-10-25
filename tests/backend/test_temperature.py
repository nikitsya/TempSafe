"""Check temperature classification without connecting to MySQL."""

import pytest
from decimal import Decimal
from temsafe.models import ThresholdProfile
from temsafe.temperature import classify_temperature


@pytest.fixture
def prototype_profile():
    """Build the agreed profile in memory without saving test data."""
    return ThresholdProfile(
        lower_c=Decimal("0.00"),
        warning_c=Decimal("24.00"),
        upper_c=Decimal("25.00"),
    )


@pytest.mark.parametrize("temperature, expected", [
    ("-0.01", "Alert"),
    ("0.00", "Alert"),
    ("0.01", "Normal"),
    ("23.99", "Normal"),
    ("24.00", "Warning"),
    ("24.01", "Warning"),
    ("24.99", "Warning"),
    ("25.00", "Warning"),
    ("25.01", "Alert"),
])
def test_prototype_boundaries(prototype_profile, temperature, expected):
    """Check temperatures just below, at and just above each agreed boundary."""
    assert classify_temperature(Decimal(temperature), "valid", prototype_profile) == expected


@pytest.mark.parametrize("temperature, quality", [
    (None, "sensor_error"),
    (Decimal("20.00"), "sensor_error"),
    (None, "valid"),
])
def test_unusable_reading_is_unknown(prototype_profile, temperature, quality):
    """Keep failed readings unknown even if a temperature value is present."""
    assert classify_temperature(temperature, quality, prototype_profile) == "Unknown"


@pytest.mark.parametrize("temperature, expected", [
    ("5.00", "Alert"),
    ("15.00", "Normal"),
    ("25.00", "Warning"),
    ("31.00", "Alert"),
])
def test_classification_uses_supplied_profile(temperature, expected):
    """Use different test limits to ensure the prototype values are not hard-coded."""
    profile = ThresholdProfile(
        lower_c=Decimal("10.00"),
        warning_c=Decimal("20.00"),
        upper_c=Decimal("30.00"),
    )

    assert classify_temperature(Decimal(temperature), "valid", profile) == expected
