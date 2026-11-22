"""Local storage and validation for the active temperature configuration."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from math import isfinite
from uuid import UUID

from sqlalchemy.dialects.sqlite import insert

from database import AsyncSessionLocal
from models import DeviceConfiguration


BOX_ID = "TS-01"
DEFAULT_PROFILE_ID = "e93a4368-e11a-4f27-8b31-d55d61392548"


@dataclass(frozen=True)
class TemperatureConfiguration:
    box_id: str
    profile_id: str
    lower_c: float
    warning_c: float
    upper_c: float


DEFAULT_CONFIGURATION = TemperatureConfiguration(
    box_id=BOX_ID,
    profile_id=DEFAULT_PROFILE_ID,
    lower_c=0.0,
    warning_c=24.0,
    upper_c=25.0,
)


def get_temperature_state(temperature, configuration):
    """Classify a valid temperature using the active local profile."""
    if temperature <= configuration.lower_c or temperature > configuration.upper_c:
        return "Alert"
    if temperature >= configuration.warning_c:
        return "Warning"
    return "Normal"


def configuration_from_payload(payload):
    """Validate a version 1 configuration payload received through MQTT."""
    try:
        values = json.loads(payload)
        if not isinstance(values, dict):
            raise ValueError("Configuration payload must be an object")
        if type(values.get("schema_version")) is not int or values["schema_version"] != 1:
            raise ValueError("Unsupported configuration schema")
        if values.get("box_id") != BOX_ID:
            raise ValueError("Configuration is for a different box")

        profile_id = str(UUID(values["profile_id"]))
        limits = []
        for name in ("lower_c", "warning_c", "upper_c"):
            value = values[name]
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError("A limit must be a decimal number")
            limit = Decimal(str(value))
            if not limit.is_finite() or not Decimal("-40") <= limit <= Decimal("80"):
                raise ValueError("A limit must be between -40 and 80 degrees Celsius")
            if limit != limit.quantize(Decimal("0.01")):
                raise ValueError("A limit must have at most two decimal places")
            limits.append(float(limit))
        lower_c, warning_c, upper_c = limits
    except (KeyError, TypeError, ValueError, InvalidOperation) as error:
        raise ValueError("Invalid configuration payload") from error

    if not all(isfinite(value) for value in (lower_c, warning_c, upper_c)):
        raise ValueError("Configuration limits must be finite")
    if not lower_c < warning_c < upper_c:
        raise ValueError("Configuration limits are not ordered")

    return TemperatureConfiguration(
        box_id=BOX_ID,
        profile_id=profile_id,
        lower_c=lower_c,
        warning_c=warning_c,
        upper_c=upper_c,
    )


def configuration_from_record(record):
    return TemperatureConfiguration(
        box_id=record.box_id,
        profile_id=record.profile_id,
        lower_c=record.lower_c,
        warning_c=record.warning_c,
        upper_c=record.upper_c,
    )


async def ensure_active_configuration():
    """Create the original prototype profile when the device has no local one."""
    async with AsyncSessionLocal.begin() as session:
        await session.execute(
            insert(DeviceConfiguration).values(**DEFAULT_CONFIGURATION.__dict__)
            .on_conflict_do_nothing(index_elements=["box_id"])
        )
        record = await session.get(DeviceConfiguration, BOX_ID)
        return configuration_from_record(record)


async def get_active_configuration():
    async with AsyncSessionLocal() as session:
        record = await session.get(DeviceConfiguration, BOX_ID)

        if record is not None:
            return configuration_from_record(record)

    return await ensure_active_configuration()


async def save_active_configuration(configuration):
    """Atomically replace the active profile after MQTT validation succeeds."""
    async with AsyncSessionLocal.begin() as session:
        record = await session.get(DeviceConfiguration, configuration.box_id)
        if record is None:
            session.add(DeviceConfiguration(**configuration.__dict__))
            return

        record.profile_id = configuration.profile_id
        record.lower_c = configuration.lower_c
        record.warning_c = configuration.warning_c
        record.upper_c = configuration.upper_c
