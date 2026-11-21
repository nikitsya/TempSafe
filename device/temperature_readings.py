import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import adafruit_scd4x
import board
from gpiozero import LED, PWMOutputDevice

from configuration import (
    ensure_active_configuration,
    get_active_configuration,
    get_temperature_state,
)
from database import Base, engine, AsyncSessionLocal
from models import Reading


BOX_ID = "TS-01"


def update_led(led, state):
    if state == "Normal":
        led.off()
    else:
        led.on()


async def buzzer_worker(buzzer, buzzer_alert):
    try:
        while True:
            await buzzer_alert.wait()

            buzzer.value = 0.5
            await asyncio.sleep(1)

            buzzer.off()
            await asyncio.sleep(2)
    finally:
        buzzer.off()


async def sensor_error_flash(led):
    led.off()

    for _ in range(2):
        led.on()
        await asyncio.sleep(0.2)
        led.off()
        await asyncio.sleep(0.2)


def read_temperature(sensor):
    if not sensor.data_ready:
        return None

    return round(sensor.temperature, 2)


async def save_reading(temperature, quality, observed_at, configuration):
    async with AsyncSessionLocal.begin() as session:
        session.add(Reading(
            sample_id=str(uuid4()),
            observed_at=observed_at,
            temperature_c=temperature,
            quality=quality,
            clock_reliable=1,
            box_id=BOX_ID,
            profile_id=configuration.profile_id,
        ))

    print(
        f"Saved: {observed_at} | "
        f"{temperature} C | Quality: {quality}"
    )


async def monitor_temperature(sensor, led, buzzer, buzzer_alert, configuration):
    while True:
        try:
            configuration = await get_active_configuration()
        except Exception as error:
            print("Configuration error; using the last active profile:", error)

        try:
            temperature = await asyncio.to_thread(
                read_temperature, sensor
            )

            if temperature is None:
                await asyncio.sleep(1)
                continue

            quality = "valid"

        except Exception as error:
            print("Sensor error:", error)
            temperature = None
            quality = "sensor_error"

        observed_at = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        if quality == "sensor_error":
            buzzer_alert.clear()
            buzzer.off()
            await sensor_error_flash(led)

        else:
            state = get_temperature_state(temperature, configuration)
            update_led(led, state)

            if state == "Alert":
                buzzer_alert.set()
            else:
                buzzer_alert.clear()
                buzzer.off()

            print(f"State: {state}")

        try:
            await save_reading(
                temperature, quality, observed_at, configuration
            )
        except Exception as error:
            print("Database error: reading was not saved:", error)

        await asyncio.sleep(30)


async def main():
    with LED(18) as led, PWMOutputDevice(
        17, frequency=500, initial_value=0
    ) as buzzer:
        i2c = board.I2C()
        sensor = adafruit_scd4x.SCD4X(i2c)
        sensor.start_periodic_measurement()

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        configuration = await ensure_active_configuration()
        buzzer_alert = asyncio.Event()

        try:
            async with asyncio.TaskGroup() as tasks:
                tasks.create_task(
                    buzzer_worker(buzzer, buzzer_alert)
                )
                tasks.create_task(
                    monitor_temperature(
                        sensor, led, buzzer, buzzer_alert, configuration
                    )
                )
        finally:
            buzzer.off()
            led.off()
            await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user.")
