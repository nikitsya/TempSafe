# Raspberry Pi device scripts

These scripts run on Raspberry Pi 5 with an SCD41 inside sensor, an AM2302
outside sensor, a single-colour LED and a passive buzzer. They are separate
from the FastAPI backend.

## Files

| File                      | Purpose                                                                                                                        | Run directly?                    |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `temperature_readings.py` | Reads temperature, controls the LED and buzzer, and saves readings or sensor read errors to SQLite through SQLAlchemy.         | Yes                              |
| `external_temperature_readings.py` | Reads the outside AM2302 and saves readings or sensor errors to the same SQLite queue. | Yes |
| `database.py`             | Configures the SQLite connection and SQLAlchemy sessions.                                                                      | No; imported by the other files. |
| `models.py`               | Defines the readings and device configuration tables.                                                                         | No; imported by other files. |
| `configuration.py`        | Validates and stores the active temperature profile.                                                                          | No; imported by other files. |
| `observation_clock.py`    | Checks clock synchronisation before recording an observation time.                                                             | No; imported by the sensor scripts. |
| `device_check.py`         | Inspects the queue and saved configuration; can back up and upgrade an existing queue.                                         | Yes |
| `scd41_basic_readings.py` | Original standalone sensor test: prints temperature and writes timestamped readings to CSV, approximately every five seconds.  | Yes                              |
| `led_test.py`             | Standalone LED pattern test; does not read temperature or use a database.                                                      | Yes                              |
| `mqtt_publisher.py`       | Sends pending readings from the local SQLite queue to the backend through MQTT over TLS and waits for server acknowledgements. | Yes                              |

Keep the production files `temperature_readings.py`, `external_temperature_readings.py`,
`mqtt_publisher.py`, `database.py`, `models.py`, `configuration.py`,
`observation_clock.py` and `device_check.py` in the same directory when copying
them to the Raspberry Pi.

## Before running

- Use the Raspberry Pi Python environment configured for the hardware tests.
- Enable I2C and connect the SCD41 to the Pi's I2C pins.
- Connect the AM2302 data line to BCM GPIO4 (physical pin 7), with a pull-up
  resistor to 3.3 V. See the [wiring record](../docs/hardware/prototype-wiring.md).
- The tested LED connection uses BCM GPIO18 (physical pin 12), a 220 ohm
  series resistor and GND (physical pin 14).
- The tested passive buzzer uses BCM GPIO17 (physical pin 11), two 220 ohm
  resistors in series (440 ohms total) and a shared ground connection.
- Required Python packages are `gpiozero`, `adafruit-blinka` (provides
  `board`), `adafruit-circuitpython-scd4x`, `adafruit-circuitpython-dht`,
  SQLAlchemy 2.x, aiosqlite and paho-mqtt. Python 3.11 or newer is required.
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

For the outside sensor:

```bash
python -m pip install adafruit-circuitpython-dht
```

Run the inside logger, outside logger and MQTT publisher in separate terminals.
Do not run a second copy of a logger or a standalone test that uses the same
hardware at the same time. Stop a running script with `Ctrl+C`.

## Main temperature logger

```bash
python temperature_readings.py
```

The script creates `temperature_readings.db` beside `database.py` if needed.
Existing records are retained. It waits for sensor data and pauses for
30 seconds after each reading or handled sensor read error; this is not
an exact fixed-rate scheduler.

| State             | Condition using the active profile                       | LED                                           |
|-------------------|----------------------------------------------------------|-----------------------------------------------|
| Normal            | Above lower and below warning                            | Off                                           |
| Warning           | At or above warning and at or below upper                | Steadily lit                                  |
| Alert             | At or below lower, or above upper                        | Steadily lit                                  |
| Sensor read error | An exception occurs while checking or reading the sensor | Two short flashes, followed by the loop pause |

The initial default profile uses 0, 24 and 25 degrees C for lower, warning and
upper respectively. The backend can update the active profile via MQTT; the
last accepted profile is saved locally and used without a network connection.
These thresholds do not determine whether medicines are suitable for use.

On Alert, an asynchronous task drives the passive buzzer at 500 Hz with
50% PWM duty cycle: one second of sound followed by two seconds of silence.
Normal, Warning and handled sensor read errors disable the buzzer.
Temperature changes are acted on when the next reading is processed.
The buzzer runs locally without a network dependency. `Ctrl+C` during the
measurement loop stops the task and switches off and releases both outputs.

Successful readings have `quality="valid"`. Handled sensor read errors are
stored with `quality="sensor_error"` and a NULL temperature. Database errors
are reported separately in the terminal. A `Saved:` message appears only
after the transaction commits.

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
- Publishes to `tempsafe/boxes/TS-01/readings` after subscribing to `tempsafe/boxes/TS-01/acks`.
- Sets `uploaded = 1` only after a matching `stored` acknowledgement.
- Retains unconfirmed records and retries with unchanged identifiers.
- Waits for new readings when the queue is empty.

The local SQLite database therefore acts as an offline queue between the sensor process and MQTT transmission.

The publisher also subscribes to `tempsafe/boxes/TS-01/configuration`.
It validates the box ID, profile ID and ordered finite limits before saving the
profile in the local `device_configuration` table. Invalid messages are ignored.
`Active configuration updated: ...` confirms a profile was saved locally. The
publisher then sends the saved profile ID to
`tempsafe/boxes/TS-01/configuration/applied` with QoS 1. If the MQTT client
cannot queue that message, the device retries; queueing alone does not confirm
that the backend received it. Deployment requires backend support and permission
to publish to this topic. The
inside logger reads the saved profile for subsequent measurements and LED/buzzer
decisions; the outside logger also uses its profile ID for new samples. During
an outage the last saved profile remains available. See the
[MQTT configuration contract](../docs/operations/mqtt.md#device-threshold-configuration-contract).

Both sensors write separate rows to `readings`, identified by `sensor_location`
(`inside` or `outside`) and sharing the sequence counter. Only inside readings
control the LED and buzzer. Unconfirmed records remain in the queue until the
server confirms storage.

## Running both loggers and the publisher

Open three SSH terminals. Start the publisher first so it can receive the active
configuration. Each terminal needs its own activated environment.

In the first terminal, provide the MQTT password and start the publisher:

```bash
cd /home/user/scd41
source .venv/bin/activate
read -s -p "MQTT password: " MQTT_PASSWORD
echo
export MQTT_PASSWORD
python mqtt_publisher.py
```

In the second terminal, start the inside logger:

```bash
cd /home/user/scd41
source .venv/bin/activate
python temperature_readings.py
```

In the third terminal, start the outside logger:

```bash
cd /home/user/scd41
source .venv/bin/activate
python external_temperature_readings.py
```

The MQTT password is entered without being displayed on the screen. It is not stored in the source code and is available
only in the current terminal session.

A message similar to:

```bash
Server confirmed storage: ...
```

means that the backend has confirmed that the reading was stored.

Stop each process with Ctrl+C in its corresponding terminal.

To inspect an existing queue and its saved profile in another Pi terminal:

```bash
cd /home/user/scd41
source .venv/bin/activate
python device_check.py
```

The output includes per-sensor counts, pending readings and `Saved configuration`.
For an older queue, stop all device processes before using
`python device_check.py --upgrade`; this creates a backup before migration.

## Current limitations

- Sensor initialisation failures occur before the loop and are not recorded
  by its error handler.
- Observation times use the Pi's UTC clock only when `timedatectl` reports it
  synchronised; otherwise the attempt is saved without an observation time.
- The device box ID and initial default profile must match the intended backend
  records. Later valid profiles can be received through MQTT.
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

The SCD41 test record includes a simulated error and a physical disconnection check.
