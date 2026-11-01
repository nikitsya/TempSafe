# Raspberry Pi device scripts

These scripts run on the Raspberry Pi connected to the SCD41 sensor and
single-colour LED and passive buzzer. They are separate from the FastAPI backend.

## Files

| File | Purpose | Run directly? |
| --- | --- | --- |
| `temperature_readings.py` | Reads temperature, controls the LED and buzzer, and saves readings or sensor read errors to SQLite through SQLAlchemy. | Yes |
| `database.py` | Configures the SQLite connection and SQLAlchemy sessions. | No; imported by the other files. |
| `models.py` | Defines the `readings` table for SQLAlchemy. | No; imported by the main script. |
| `scd41_basic_readings.py` | Original standalone sensor test: prints temperature and writes timestamped readings to CSV, approximately every five seconds. | Yes |
| `led_test.py` | Standalone LED pattern test; does not read temperature or use a database. | Yes |

Keep `temperature_readings.py`, `database.py` and `models.py` in the same
directory when copying them to the Raspberry Pi.

## Before running

- Use the Raspberry Pi Python environment configured for the hardware tests.
- Enable I2C and connect the SCD41 to the Pi's I2C pins.
- The tested LED connection uses BCM GPIO18 (physical pin 12), a 220 ohm
  series resistor and GND (physical pin 14).
- The tested passive buzzer uses BCM GPIO17 (physical pin 11), two 220 ohm
  resistors in series (440 ohms total) and a shared ground connection.
- Required Python packages are `gpiozero`, `adafruit-blinka` (provides
  `board`), `adafruit-circuitpython-scd4x` and SQLAlchemy 2.x.
  The hardware libraries also require the appropriate Raspberry Pi system
  configuration; installing Python packages on Windows does not provide
  access to the Pi's GPIO or I2C hardware.

The commands below use Hanna's current Pi directory. If using a repository
checkout on the Pi, change to its `device` directory instead and activate
the appropriate virtual environment.

```bash
cd /home/user/scd41
source .venv/bin/activate
```

For an existing hardware environment that does not yet have SQLAlchemy:

```bash
python -m pip install "SQLAlchemy>=2,<3"
```

Run only one hardware script at a time. Stop a running script with `Ctrl+C`
before starting another.

## Main temperature logger

```bash
python temperature_readings.py
```

The script creates `temperature_readings.db` beside `database.py` if needed.
Existing records are retained. It waits for sensor data and pauses for
30 seconds after each reading or handled sensor read error; this is not
an exact fixed-rate scheduler.

| State | Current code condition | LED |
| --- | --- | --- |
| Normal | Above 0 and below 24 degrees C | Off |
| Warning | 24 through 25 degrees C, inclusive | Steadily lit |
| Alert | At or below 0, or above 25 degrees C | Steadily lit |
| Sensor read error | An exception occurs while checking or reading the sensor | Two short flashes, followed by the loop pause |

These are the prototype's configured thresholds, not a determination that
medicines are suitable for use.

On Alert, a background thread drives the passive buzzer at 500 Hz with
50% PWM duty cycle: one second of sound followed by two seconds of silence.
Normal, Warning and handled sensor read errors disable repetition; a tone
already in progress can finish its remaining fraction of a second.
Temperature changes are acted on when the next reading is processed.
The buzzer runs locally without a network dependency. `Ctrl+C` during the
measurement loop stops the thread and switches off and releases both outputs.

Successful readings have `quality="valid"`. Handled sensor read errors are
stored with `quality="sensor_error"` and a NULL temperature. Database errors
are reported separately in the terminal. A `Saved:` message appears only
after the transaction commits.

Current limitations:

- Sensor initialisation failures occur before the loop and are not recorded
  by its error handler.
- Timestamps use the Pi's system clock in UTC. `clock_reliable` is currently
  set to 1 without an independent clock synchronisation check.
- `BOX_ID` and `PROFILE_ID` are configured in the script and must match the
  intended backend records before integration.
- MQTT transmission is not implemented. Records remain `uploaded=0`;
  they are not yet sent to the backend MySQL database.
- Manual buzzer silencing is not implemented, so FR-15 is only partially
  implemented. Stopping the whole script is not a substitute for a silence control.

Do not commit the generated database or backup database files to Git.

## Standalone sensor test

```bash
python scd41_basic_readings.py
```

This is the earlier CSV test, not the main SQLite logger. It writes
`temperature_readings.csv` in the terminal's current directory and
**overwrites that CSV when started**. Preserve any required test evidence
before running it again.

## Standalone LED test

```bash
python led_test.py
```

The test shows five seconds off, five seconds steadily lit, then five
repetitions of two short flashes and a pause. It switches the LED off
and releases it when the test finishes.

## Test evidence

- [SCD41 readings, SQLite storage and simulated sensor error test](../docs/testing/scd41-basic-readings.md)
- [LED tests](../docs/testing/led-patterns.md)
- [Temperature-triggered buzzer test](../docs/testing/buzzer-alert.md)

The sensor error test used a temporary software exception. Normal readings
were verified after removing that exception and restarting the script.
