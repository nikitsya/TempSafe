"""Record an inside/outside temperature experiment to a CSV file.

Inside: SCD41 over I2C.
Outside: AM2302/DHT22 on BCM GPIO4 (physical pin 7).

This is an experiment-only script. It does not use SQLite, MQTT, LEDs,
the buzzer, or the production temperature logger. Run it from the Raspberry
Pi project directory so that the CSV file is saved there.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

import adafruit_dht
import adafruit_scd4x
import board

READ_INTERVAL_SECONDS = 5


def read_inside(sensor):
    """Return the SCD41 temperature and its reading status."""
    try:
        if not sensor.data_ready:
            return None, "not_ready"
        return round(sensor.temperature, 2), "valid"
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Inside sensor error: {error}")
        return None, "sensor_error"


def read_outside(sensor):
    """Return the AM2302 temperature and its reading status."""
    try:
        temperature = sensor.temperature
        if temperature is None:
            return None, "not_ready"
        return round(temperature, 2), "valid"
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Outside sensor error: {error}")
        return None, "sensor_error"


def display_temperature(value, status):
    if value is None:
        return status
    return f"{value:.1f} C"


def create_csv_file():
    started_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = Path.cwd() / f"external_temperature_experiment_{started_at}.csv"
    csv_file = csv_path.open("w", newline="", encoding="utf-8")
    writer = csv.writer(csv_file)
    writer.writerow(
        [
            "timestamp_utc",
            "inside_temperature_c",
            "inside_status",
            "outside_temperature_c",
            "outside_status",
        ]
    )
    csv_file.flush()
    return csv_path, csv_file, writer


def main():
    csv_path, csv_file, writer = create_csv_file()
    i2c = board.I2C()
    inside_sensor = None
    outside_sensor = None
    measurement_started = False

    try:
        inside_sensor = adafruit_scd4x.SCD4X(i2c)
        outside_sensor = adafruit_dht.DHT22(board.D4, use_pulseio=False)
        inside_sensor.start_periodic_measurement()
        measurement_started = True

        print("Inside: SCD41 | Outside: AM2302 on GPIO4. Ctrl+C to stop.")
        print(f"Saving experiment readings to: {csv_path.name}")
        sleep(READ_INTERVAL_SECONDS)

        while True:
            observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            inside_temperature, inside_status = read_inside(inside_sensor)
            outside_temperature, outside_status = read_outside(outside_sensor)

            writer.writerow(
                [
                    observed_at,
                    inside_temperature,
                    inside_status,
                    outside_temperature,
                    outside_status,
                ]
            )
            csv_file.flush()

            print(
                f"{observed_at} | "
                f"Inside: {display_temperature(inside_temperature, inside_status)} | "
                f"Outside: {display_temperature(outside_temperature, outside_status)}"
            )
            sleep(READ_INTERVAL_SECONDS)
    finally:
        csv_file.close()
        try:
            if outside_sensor is not None:
                outside_sensor.exit()
        finally:
            try:
                if measurement_started:
                    inside_sensor.stop_periodic_measurement()
            finally:
                i2c.deinit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by user.")
