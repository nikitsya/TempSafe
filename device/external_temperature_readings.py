"""Queue AM2302 readings independently of the inside sensor and its alarms."""

import asyncio
from math import isfinite
from uuid import uuid4

from configuration import ensure_active_configuration, get_active_configuration
from database import AsyncSessionLocal, engine, initialise_database
from models import Reading
from observation_clock import observation_time


def read_temperature(sensor):
    """Treat a missing or invalid AM2302 result as a failed sample attempt."""
    temperature = sensor.temperature
    if temperature is None or not isfinite(temperature) or not -40 <= temperature <= 80:
        raise ValueError("Outside temperature is missing or outside the sensor range")
    return round(temperature, 2)


async def record_sample(sensor, configuration):
    try:
        temperature = await asyncio.to_thread(read_temperature, sensor)
        quality = "valid"
    except (RuntimeError, OSError, ValueError) as error:
        print("Outside sensor error:", error)
        temperature, quality = None, "sensor_error"

    observed_at = await observation_time()
    if observed_at is None:
        print("Clock is not synchronised; saving this attempt without an observation time")
    async with AsyncSessionLocal.begin() as session:
        session.add(Reading(
            sample_id=str(uuid4()),
            sensor_location="outside",
            observed_at=observed_at,
            temperature_c=temperature,
            quality=quality,
            clock_reliable=int(observed_at is not None),
            box_id=configuration.box_id,
            profile_id=configuration.profile_id,
        ))
    print(f"Outside: {temperature} C | Quality: {quality}")


async def monitor_temperature(sensor, configuration):
    while True:
        try:
            configuration = await get_active_configuration()
        except Exception as error:
            print("Configuration error; using the last active profile:", error)
        try:
            await record_sample(sensor, configuration)
        except Exception as error:
            print("Database error: outside reading was not saved:", error)
        await asyncio.sleep(30)


async def main():
    import adafruit_dht
    import board

    sensor = None
    try:
        await initialise_database()
        configuration = await ensure_active_configuration()
        sensor = adafruit_dht.DHT22(board.D4, use_pulseio=False)
        await monitor_temperature(sensor, configuration)
    finally:
        try:
            if sensor is not None:
                sensor.exit()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Outside logger stopped.")
