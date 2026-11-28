# Raspberry Pi device scripts

These scripts run on Raspberry Pi 5 with an inside SCD41, an outside AM2302 (DHT22), a single-colour LED and a passive
buzzer. They are separate from the FastAPI backend.

## Files

| File                               | Purpose                                                                                                                        | Run directly?                    |
|------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `temperature_readings.py`          | Reads temperature, controls the LED and buzzer, and saves readings or sensor read errors to SQLite through SQLAlchemy.         | Yes                              |
| `database.py`                      | Configures the SQLite connection and SQLAlchemy sessions.                                                                      | No; imported by the other files. |
| `models.py`                        | Defines the `readings` queue and `device_configuration` tables.                                                                | No; imported by the main script. |
| `scd41_basic_readings.py`          | Original standalone sensor test: prints temperature and writes timestamped readings to CSV, approximately every five seconds.  | Yes                              |
| `led_test.py`                      | Standalone LED pattern test; does not read temperature or use a database.                                                      | Yes                              |
| `mqtt_publisher.py`                | Sends pending readings from the local SQLite queue to the backend through MQTT over TLS and waits for server acknowledgements. | Yes                              |
| `external_temperature_readings.py` | Records outside temperature in the shared queue.                                                                               | Yes                              |
| `configuration.py`                 | Validates threshold messages and stores the active profile in SQLite.                                                          | Imported                         |
| `observation_clock.py`             | Checks system clock synchronisation before timestamping a reading.                                                             | Imported                         |
| `device_check.py`                  | Inspects an existing queue. The optional `--upgrade` backs it up and migrates it.                                              | Yes                              |

Copy the device scripts together so both loggers and the publisher import the
same modules and open the same queue. For an existing Pi, stop those processes
before running `python device_check.py --upgrade`. Run `python device_check.py`
to inspect counts, pending samples and the saved configuration.

## Before running

- Use Python 3.11 or later in the Raspberry Pi environment.
- Enable I2C and connect the SCD41 to the Pi's I2C pins.
- The tested LED connection uses BCM GPIO18 (physical pin 12), a 220 ohm
  series resistor and GND (physical pin 14).
- The tested passive buzzer uses BCM GPIO17 (physical pin 11), two 220 ohm
  resistors in series (440 ohms total) and a shared ground connection.
- Required Python packages are `gpiozero`, `adafruit-blinka` (provides
  `board`), `adafruit-circuitpython-scd4x`, SQLAlchemy 2.x, aiosqlite and paho-mqtt.
  The outside logger also needs `adafruit-circuitpython-dht` and uses BCM GPIO4.
  The hardware libraries also require the appropriate Raspberry Pi system
  configuration; installing Python packages on Windows does not provide
  access to the Pi's GPIO or I2C hardware.

The commands below use the current Pi directory. If using a repository
checkout on the Pi, change to its `device` directory instead and activate
the appropriate virtual environment.

```bash
cd /home/user/scd41
source .venv/bin/activate
```

Install the asynchronous SQLite dependencies in the device environment:

```bash
python -m pip install "SQLAlchemy[asyncio]>=2,<3" "aiosqlite>=0.20,<1"
```

For MQTT support:

```bash
python -m pip install "paho-mqtt>=2,<3"
```

The inside logger, outside logger and publisher can run in separate terminals
at the same time. Stop any script using a sensor or GPIO output before running
a standalone test that uses the same hardware.

## Main temperature logger

```bash
python temperature_readings.py
```

The script creates `temperature_readings.db` beside `database.py` if needed.
Existing records are retained. It waits for sensor data and pauses for
30 seconds after each reading or handled sensor read error; this is not
an exact fixed-rate scheduler.

| State             | Current code condition                                   | LED                                           |
|-------------------|----------------------------------------------------------|-----------------------------------------------|
| Normal            | Above the lower limit and below the warning threshold    | Off                                           |
| Warning           | From the warning threshold through the upper limit       | Steadily lit                                  |
| Alert             | At or below the lower limit, or above the upper limit    | Steadily lit                                  |
| Sensor read error | An exception occurs while checking or reading the sensor | Two short flashes, followed by the loop pause |

On first start the prototype uses 0°C, 24°C and 25°C. Each logger reads the
active SQLite profile before sampling. Both record its ID, and the inside logger
uses its limits for the LED and buzzer.

On Alert, an asynchronous task drives the passive buzzer at 500 Hz with
50% PWM duty cycle: one second of sound followed by two seconds of silence.
Normal, Warning and handled sensor read errors clear the alert and switch off
the buzzer.
Temperature changes are acted on when the next reading is processed.
The buzzer runs locally without a network dependency. `Ctrl+C` during the
measurement loop stops the task and switches off and releases both outputs.

Successful readings have `quality="valid"`. Handled sensor read errors are
stored with `quality="sensor_error"` and a NULL temperature. Database errors
are reported separately in the terminal. A `Saved:` message appears only
after the transaction commits.

## Outside temperature logger

Run `python external_temperature_readings.py` in the same device environment.
An attempt is recorded with `sensor_location="outside"` and the loop waits 30
seconds before the next attempt. Both loggers share the SQLite sequence counter.
Only the inside logger controls the LED and buzzer.

## MQTT publisher

```bash
python mqtt_publisher.py
```

The MQTT publisher runs separately from the temperature measurement script. Set `MQTT_PASSWORD`
in its terminal before starting it, as shown below. It sends readings that have not yet been
confirmed as stored by the backend.

The publisher:

- Selects the oldest pending record where `uploaded = 0`.
- Connects over TLS with certificate and server-name verification.
- Subscribes to the box's `acks` and `configuration` topics before publishing to `tempsafe/boxes/TS-01/readings`.
- Validates the latest configuration and commits it to SQLite. Sending the
  [applied-profile confirmation](../docs/operations/mqtt.md#device-threshold-configuration-contract)
  remains outstanding in this publisher.
- Sets `uploaded = 1` only after a matching `stored` acknowledgement.
- Retains unconfirmed records and retries with unchanged identifiers.
- Waits for new readings when the queue is empty.

The local SQLite database therefore acts as an offline queue between the sensor process and MQTT transmission.

## Running the logger and publisher together

Open two SSH terminals.

In the first terminal, start temperature collection:

```bash
cd /home/user/scd41
source .venv/bin/activate
python temperature_readings.py
```

In the second terminal, activate the same environment and provide the MQTT password:

```bash
cd /home/user/scd41
source .venv/bin/activate
read -s -p "MQTT password: " MQTT_PASSWORD
echo
export MQTT_PASSWORD
python mqtt_publisher.py
```

The MQTT password is entered without being displayed on the screen. It is not stored in the source code and is available
only in the current terminal session.

A message similar to:

```bash
Server confirmed storage: ...
```

means that the backend has confirmed that the reading was stored.

Stop either process with Ctrl+C in its corresponding terminal.

## Current limitations

- Sensor initialisation failures occur before the loop and are not recorded
  by its error handler.
- If `timedatectl` cannot confirm synchronisation within two seconds, the
  loggers store a null observation time and `clock_reliable=0`.
- The scripts target `TS-01`. Its initial demo profile ID must exist on the
  backend before the first samples are uploaded.
- MQTT publishing is implemented, but automatic startup after Raspberry Pi reboot is not yet configured.
- Manual buzzer silencing is not implemented, so FR-15 is only partially
  implemented. Stopping the whole script is not a substitute for a silence control.

Do not commit the generated database or backup database files to Git.

## Standalone sensor test

```bash
python scd41_basic_readings.py
```

This is the earlier CSV test, not the main SQLite logger. It writes
`temperature_readings.csv` in the terminal's current directory and **overwrites that CSV when started**. Preserve any
required test evidence
before running it again.

## Standalone LED test

```bash
python led_test.py
```

The test shows five seconds off, five seconds steadily lit, then five
repetitions of two short flashes and a pause. It switches the LED off
and releases it when the test finishes.

## Test evidence

- [SCD41 readings, SQLite storage and simulated sensor error test](../docs/testing/hardware/scd41-basic-readings.md)
- [LED tests](../docs/testing/hardware/led-patterns.md)
- [Temperature-triggered buzzer test](../docs/testing/hardware/buzzer-alert.md)

The sensor error test used a temporary software exception. Normal readings
were verified after removing that exception and restarting the script.
