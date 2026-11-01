# Temperature-Triggered Buzzer — Integration Test

## Test information

| Item | Details |
| --- | --- |
| Date | 1 November 2026 |
| Tested by | Hanna |
| Project | TempSafe |
| Related requirements | FR-15 — audible buzzer alert; FR-06 — local LED warning |
| Result | PASS for the observed high-temperature activation and recovery checks |
| Script | `device/temperature_readings.py` |

## Objective

Verify that real SCD41 temperature readings activate the LED and passive
buzzer on Alert, that readings continue to be saved, and that both outputs
switch off when the measured temperature returns to Normal.

## Equipment and connections

- Raspberry Pi 5 and SCD41 sensor.
- White single-colour LED controlled by BCM GPIO18 (physical pin 12).
- Passive buzzer controlled by BCM GPIO17 (physical pin 11).
- Two 220 ohm resistors in series in the buzzer circuit (440 ohms total).
- Buzzer return connected to the shared ground circuit.

The buzzer model and electrical ratings were not recorded. These connections
describe the tested assembly, not a wiring recommendation for other buzzers.

## Configuration

- Buzzer frequency: 500 Hz, selected after a standalone frequency test.
- PWM duty cycle: 50%.
- Alert sound pattern: one second on, two seconds off, repeated in a background thread.
- Alert thresholds in the code: at or below 0 degrees C, or above 25 degrees C.
- Measurement loop pause: 30 seconds after each processed reading.
- Storage: local SQLite through SQLAlchemy.
- Manual silence control: not implemented.

## Procedure

1. Ran `python temperature_readings.py` on the Raspberry Pi.
2. Observed an initial Normal reading.
3. Warmed the sensor until readings exceeded 25 degrees C.
4. Observed the LED and listened to the buzzer while readings were recorded.
5. Allowed the measured temperature to return to Normal and checked both outputs.
6. Stopped the script with `Ctrl+C`.

## Recorded results

The following readings are transcribed from the terminal output supplied
by the tester. Timestamps are UTC on 1 November 2026.

| Time | Temperature (degrees C) | State |
| --- | --- | --- |
| 18:30:53 | 23.65 | Normal |
| 18:31:23 | 29.03 | Alert |
| 18:31:53 | 34.18 | Alert |
| 18:32:23 | 32.48 | Alert |
| 18:32:53 | 25.23 | Alert |
| 18:33:23 | 17.41 | Normal |

Each reading produced a `Saved:` message with `Quality: valid` after the
database transaction committed. Consecutive timestamps were 30 seconds apart.
The script printed `Stopped by user.` after `Ctrl+C`.

Hanna confirmed that:

- During Alert, the LED was steadily lit and the buzzer repeated the
  one-second sound / two-second pause pattern.
- On return to Normal, the LED switched off and the buzzer became silent.

## Limitations and remaining work

- This run tested high-temperature Alert and return to Normal. It did not
  exercise the low-temperature threshold, Warning, or sensor-error behaviour
  with the buzzer integrated.
- The sound pattern was confirmed by observation, not instrumented timing.
- No deliberate Wi-Fi disconnection test was recorded. The buzzer logic
  runs locally, but network-loss behaviour was not separately tested here.
- No reference thermometer was used to assess measurement accuracy.
- The results are transcribed terminal output and tester observations;
  no photograph or video is attached to this report.
- Manual silencing without clearing the LED or stopping measurement is
  still required to complete FR-15.
- MQTT transmission, backend integration and medicine suitability were
  outside this test.
