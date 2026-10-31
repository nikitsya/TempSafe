from gpiozero import LED
import sqlite3
from datetime import datetime, timezone
import time
import board
from pathlib import Path
import adafruit_scd4x
from uuid import uuid4

BOX_ID = "TS-01"
PROFILE_ID = "e93a4368-e11a-4f27-8b31-d55d61392548"
led = LED(18)
def get_temperature_state(temperature):
    if temperature <= 0 or temperature > 25:
        return "Alert"

    if 24 <= temperature <= 25:
        return "Warning"

    return "Normal"

def update_led(state):
    if state == "Normal":
        led.off()
    else:
        led.on()

i2c = board.I2C()
sensor = adafruit_scd4x.SCD4X(i2c)

sensor.start_periodic_measurement()

connection = sqlite3.connect(Path(__file__).resolve().parent / "temperature_readings.db")

connection.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        sequence_no INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id TEXT NOT NULL UNIQUE,
        observed_at TEXT,
        temperature_c REAL,
        quality TEXT NOT NULL,
        clock_reliable INTEGER NOT NULL,
        box_id TEXT NOT NULL,
        profile_id TEXT NOT NULL,
        uploaded INTEGER NOT NULL DEFAULT 0
    )
""")
connection.commit()

def sensor_error_flash():
    led.off()

    for _ in range(2):
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(0.2)

while True:
    try:

        if sensor.data_ready:
            temperature = round(sensor.temperature, 2)

            state = get_temperature_state(temperature)
            update_led(state)

            observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

            connection.execute(
                """INSERT INTO readings
                (sample_id, observed_at, temperature_c, quality, clock_reliable, box_id, profile_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid4()), observed_at, temperature, "valid", 1, BOX_ID, PROFILE_ID) 
            )

            connection.commit()
            print(f"Saved: {observed_at} | {temperature:.2f} C | State: {state}")

    except Exception as error:
        print("Sensor error:", error)
        sensor_error_flash()

    time.sleep(30)
