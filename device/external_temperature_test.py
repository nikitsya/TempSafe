"""Compare inside (SCD41) and outside (AM2302/DHT22) temperatures.

Planned DATA connection: BCM GPIO4 (physical pin 7).
Use 3.3 V power and a 10 kohm pull-up between DATA and 3.3 V.
Confirm wiring before running; connect hardware with the Pi powered off.

Requires adafruit-blinka, adafruit-circuitpython-scd4x and
adafruit-circuitpython-dht in the Pi's venv.
Stop temperature_readings.py and other SCD41 scripts before running this file.
Prints readings only: no CSV, SQLite, MQTT or alert control.
The sensors are read sequentially in each cycle, not at exactly the same instant.
Hardware operation on this Raspberry Pi still needs verification.
"""

from datetime import datetime, timezone
from time import sleep

import adafruit_dht
import adafruit_scd4x
import board

READ_INTERVAL_SECONDS = 5


def read_inside(sensor):
    try:
        if not sensor.data_ready:
            return "not ready"
        return f"{sensor.temperature:.1f} C"
    except (RuntimeError, OSError, ValueError) as error:
        return f"ERROR ({error})"


def read_outside(sensor):
    try:
        temperature = sensor.temperature
        if temperature is None:
            return "no reading"
        return f"{temperature:.1f} C"
    except (RuntimeError, OSError, ValueError) as error:
        return f"ERROR ({error})"


def main():
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
        print("Terminal output only; readings are not saved or sent.")
        sleep(READ_INTERVAL_SECONDS)  # Wait for the first SCD41 measurement.

        while True:
            observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            inside = read_inside(inside_sensor)
            outside = read_outside(outside_sensor)
            print(f"{observed_at} | Inside: {inside} | Outside: {outside}")

            sleep(READ_INTERVAL_SECONDS)
    finally:
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
