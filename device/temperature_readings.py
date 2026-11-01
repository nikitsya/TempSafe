from gpiozero import LED, PWMOutputDevice
from datetime import datetime, timezone
import time
import board
from database import Base, engine, SessionLocal
from models import Reading
import adafruit_scd4x
from uuid import uuid4
from threading import Event, Thread

BOX_ID = "TS-01"
PROFILE_ID = "e93a4368-e11a-4f27-8b31-d55d61392548"
led = LED(18)
buzzer = PWMOutputDevice(17, frequency=500, initial_value=0)

buzzer_alert = Event()
buzzer_shutdown = Event()


def buzzer_worker():
    try:
        while not buzzer_shutdown.is_set():
            if not buzzer_alert.wait(timeout=0.1):
                continue

            if buzzer_shutdown.is_set():
                break

            buzzer.value = 0.5
            buzzer_shutdown.wait(1)
            buzzer.off()
            buzzer_shutdown.wait(2)
    finally:
        buzzer.off()


buzzer_thread = Thread(target=buzzer_worker, daemon=True)
buzzer_thread.start()


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

Base.metadata.create_all(engine)

def sensor_error_flash():
    led.off()

    for _ in range(2):
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(0.2)

def save_reading(temperature, quality):
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with SessionLocal.begin() as session:
        session.add(Reading(
            sample_id=str(uuid4()),
            observed_at=observed_at,
            temperature_c=temperature,
            quality=quality,
            clock_reliable=1,
            box_id=BOX_ID,
            profile_id=PROFILE_ID,
        ))

    print(f"Saved: {observed_at} | {temperature} C | Quality: {quality}")

try:

    while True:
        try:
            if not sensor.data_ready:
                time.sleep(1)
                continue

            temperature = round(sensor.temperature, 2)
            quality = "valid"

        except Exception as error:
            print("Sensor error:", error)
            temperature = None
            quality = "sensor_error"

        if quality == "sensor_error":
            buzzer_alert.clear()
            sensor_error_flash()
        else:
            state = get_temperature_state(temperature)
            update_led(state)
            
            if state == "Alert":
                buzzer_alert.set()
            else:
                buzzer_alert.clear()

            print(f"State: {state}")

        try:
            save_reading(temperature, quality)
        except Exception as error:
            print("Database error: reading was not saved:", error)

        time.sleep(30)

except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    buzzer_shutdown.set()
    buzzer_thread.join()
    buzzer.off()
    buzzer.close()
    led.off()
    led.close()
