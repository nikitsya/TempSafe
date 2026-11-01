# Prototype wiring — Raspberry Pi 5, SCD-41, LED and passive buzzer

[Editable Fritzing diagram](fritzing/prototype_wiring.fzz) — open with **File → Open** in Fritzing.

Keep the Raspberry Pi outside the monitored box to reduce heat affecting the sensor readings.

## Sensor connections

| Raspberry Pi 5 physical pin | Function     | Adafruit SCD-41 breakout connection |
|-----------------------------|--------------|-------------------------------------|
| 1                           | 3.3 V power  | VIN                                 |
| 6                           | Ground       | GND                                 |
| 3                           | GPIO2 / SDA1 | SDA                                 |
| 5                           | GPIO3 / SCL1 | SCL                                 |

## Tested LED connections

Physical pin 12 (BCM GPIO18) → 220 Ω series resistor → LED anode;
LED cathode → physical pin 14 (GND).

| Component or wire           | Breadboard connection |
|-----------------------------|-----------------------|
| GPIO18 / physical pin 12    | A5                    |
| 220 Ω resistor              | B5 → B10              |
| LED long leg / anode (+)    | C10                   |
| LED short leg / cathode (−) | C11                   |
| GND / physical pin 14       | A11                   |

## Tested passive buzzer connections

Physical pin 11 (BCM GPIO17) → two 220 Ω resistors in series (440 Ω total)
→ passive buzzer → shared ground at physical pin 14.

| Component or wire        | Breadboard connection |
|--------------------------|-----------------------|
| GPIO17 / physical pin 11 | A20                   |
| First 220 Ω resistor     | B20 → B25             |
| Second 220 Ω resistor    | C25 → C30             |
| First buzzer leg         | E30                   |
| Second buzzer leg        | E32                   |
| Shared ground jumper     | E32 → E11             |

The buzzer uses 500 Hz PWM with 50% duty cycle on Alert: one second on,
two seconds off. Manual silencing is not implemented. The buzzer model and
electrical ratings were not recorded; this describes the tested assembly.

## What each part does

| Part                     | Role                                                                                                                   |
|--------------------------|------------------------------------------------------------------------------------------------------------------------|
| Plastic prototype box    | Holds the sensor; the container itself has no electrical connection.                                                   |
| Adafruit SCD-41 breakout | Measures temperature inside the box; humidity and CO₂ reporting are outside this release.                              |
| Raspberry Pi 5           | Reads the sensor, runs the monitoring software and controls the LED and buzzer.                                        |
| Solderless breadboard    | Provides temporary electrical connections without soldering; it has no processor or Wi-Fi.                             |
| Jumper wires             | Carry power, ground and signals between components. Colours in the diagram are labels, not a required colour standard. |
| Resistor                 | Limits current through the warning LED.                                                                                |
| Single-colour LED        | Provides local visual feedback. It is an output device, not a sensor.                                                  |
| Passive buzzer           | Provides an audible warning on Alert.                                                                                  |
| USB-C power supply       | Powers the Raspberry Pi 5 from mains; use a compatible power supply.                                                   |
| Laptop                   | Provides remote access through Raspberry Pi Connect; no direct laptop-to-Pi cable is required.                         |

## Sources

- [Adafruit SCD-4x Raspberry Pi wiring](https://learn.adafruit.com/adafruit-scd-40-and-scd-41/python-circuitpython)
- [Adafruit SCD-4x pinouts](https://learn.adafruit.com/adafruit-scd-40-and-scd-41/pinouts)
- [Raspberry Pi GPIO documentation and pinout](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)

## Current assembly — 1 November 2026

Hanna updated the [Fritzing file](fritzing/prototype_wiring.fzz) to reflect the
LED and buzzer assembly. The confirmed connections above supersede the
earlier LED design using GPIO17, a 1 kΩ resistor and ground pin 9.

The sensor pin mapping is listed above; its breadboard coordinates have not been confirmed.

Each numbered row connects A–E internally; F–J is a separate group across
the centre gap. Row 11 provides the shared LED/buzzer ground through A11
to physical pin 14. Sensor wiring must use separate junctions from the
output circuits except for intentional shared ground connections.

See the [LED test](../testing/led-patterns.md) and
[buzzer test](../testing/buzzer-alert.md) for the recorded results.
