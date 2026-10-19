import csv
from datetime import datetime
import time
import board
import adafruit_scd4x

i2c = board.I2C()
sensor = adafruit_scd4x.SCD4X(i2c)

sensor.start_periodic_measurement()

log_file = open("temperature_readings.csv", "w", newline="")
writer = csv.writer(log_file)
writer.writerow(["timestamp", "temperature_c"])
while True:
    if sensor.data_ready:
        print(f"Temperature: {sensor.temperature:.1f} C")
        writer.writerow([datetime.now().astimezone().isoformat(timespec="seconds"), f"{sensor.temperature:.1f}"])
        log_file.flush()

    time.sleep(5)
