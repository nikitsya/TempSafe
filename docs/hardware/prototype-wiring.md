# TempSafe prototype wiring — Raspberry Pi 5

[Editable Fritzing diagram](fritzing/prototype_wiring.fzz) — open with **File → Open** in Fritzing.

## Tested assembly

The project uses Raspberry Pi 5: LED on GPIO18 with 220 Ω, passive buzzer on GPIO17 with 440 Ω.
See the [device guide](../../device/README.md) for connections and limitations.
The linked Fritzing diagram is outdated and does not represent the current assembly.

## Sensor connections

| Raspberry Pi 5 physical pin | Function     | Adafruit SCD-41 breakout connection |
|-----------------------------|--------------|-------------------------------------|
| 1                           | 3.3 V power  | VIN                                 |
| 6                           | Ground       | GND                                 |
| 3                           | GPIO2 / SDA1 | SDA                                 |
| 5                           | GPIO3 / SCL1 | SCL                                 |

## LED and buzzer connections

Physical pin 12 (BCM GPIO18) → 220 Ω series resistor → LED anode; LED cathode → physical pin 14 (GND).
The passive buzzer uses GPIO17 (physical pin 11), two 220 Ω resistors in series and shared ground.
See the [buzzer test](../testing/buzzer-alert.md) for component limitations.

## What each part does

| Part                     | Role                                                                                                                   |
|--------------------------|------------------------------------------------------------------------------------------------------------------------|
| Plastic prototype box    | Holds the sensor; the container itself has no electrical connection.                                                   |
| Adafruit SCD-41 breakout | Measures temperature inside the box; humidity and CO₂ reporting are outside this release.                              |
| Raspberry Pi 5           | Reads the sensor, runs the monitoring software and controls the warning LED.                                           |
| Solderless breadboard    | Provides temporary electrical connections without soldering; it has no processor or Wi-Fi.                             |
| Jumper wires             | Carry power, ground and signals between components. Colours in the diagram are labels, not a required colour standard. |
| Resistor                 | Limits current through the warning LED.                                                                                |
| Single-colour LED        | Provides local visual feedback. It is an output device, not a sensor.                                                  |
| USB-C power supply       | Powers the Raspberry Pi 5 from mains; use a compatible supply.                                                         |
| Laptop                   | Provides remote access via SSH; no direct laptop-to-Pi cable is required.                                              |

## Sources

- [Adafruit SCD-4x Raspberry Pi wiring](https://learn.adafruit.com/adafruit-scd-40-and-scd-41/python-circuitpython)
- [Adafruit SCD-4x pinouts](https://learn.adafruit.com/adafruit-scd-40-and-scd-41/pinouts)
- [Raspberry Pi GPIO documentation and pinout](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)
