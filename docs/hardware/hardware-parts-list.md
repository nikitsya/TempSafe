# IoT Controlled Drug Box – Development Parts List

This parts list reflects the current **TempSafe** project scope: continuous temperature monitoring inside a prototype
controlled drug box using a Raspberry Pi and SCD-41 sensor, with a single-colour warning LED. A buzzer is a Should Have
enhancement, partially implemented with a passive buzzer; manual silencing remains outstanding.

The project uses Raspberry Pi 5.
See the [wiring record](prototype-wiring.md) for the current connections.

## Parts List

| Part                        | Purpose / Notes                                                                                                                                                                                                            | Link / Source                                       | Cost           |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|----------------|
| Raspberry Pi 5              | Tested controller: reads temperature, controls the LED and passive buzzer, and saves readings to SQLite. Upload remains planned.                                                                                           | Raspberry Pi 5                                      | Already owned  |
| Adafruit SCD-41             | Already owned. I²C sensor with integrated temperature and humidity measurement; only temperature is used. Humidity and CO₂ reporting are outside this release.                                                             | https://www.adafruit.com/product/5190               | Already owned  |
| Single-colour LED           | Provides immediate visual feedback without requiring the Advanced Paramedic to open the web application. Lights for Warning or Alert; off for Normal; distinct blinking for sensor failure. No RGB capability is required. | Lecturer parts list / The Pi Hut                    | TBD            |
| Passive buzzer              | Should Have: tested on Alert at 500 Hz, one second on/two seconds off. Manual silence is not implemented; model and ratings remain unrecorded.                                                                             | Lecturer parts list / The Pi Hut                    | TBD            |
| LED resistor (tested 220 Ω) | Limits LED current in the tested GPIO18 assembly.                                                                                                                                                                          | Lecturer parts list / The Pi Hut                    | TBD            |
| Full-size breadboard        | Used to build and test the circuit without soldering.                                                                                                                                                                      | https://thepihut.com/products/full-sized-breadboard | £5.00          |
| Jumper wires                | Connect the SCD-41, LED indicator, buzzer and breadboard to the Raspberry Pi. Male/Male and Female/Male wires are useful for prototyping.                                                                                  | Lecturer parts list / The Pi Hut                    | Approx. €4–8   |
| microSD card                | Stores Raspberry Pi OS, project software and local log data.                                                                                                                                                               | Any compatible microSD card, e.g. 32 GB             | Existing / TBD |
| Raspberry Pi power supply   | Mains power for the bench prototype; the Pi communicates over Wi-Fi and does not need a direct connection to the laptop.                                                                                                   | Supply compatible with Raspberry Pi 5               | Existing / TBD |
| Plastic prototype box       | One simple plastic storage box for temperature monitoring and local feedback. No real controlled drugs will be used.                                                                                                       | To be purchased; final size to be confirmed         | TBD            |

The tested buzzer circuit also uses two 220 Ω resistors in series. See the
[buzzer test](../testing/hardware/buzzer-alert.md) for the recorded connections and limitations.

## Feedback logic

| Condition           | Single-colour LED                      | Passive buzzer                         | Application status                         |
|---------------------|----------------------------------------|----------------------------------------|--------------------------------------------|
| 0°C < T < 24°C      | Off                                    | Off                                    | Normal: text, symbol and green             |
| 24°C ≤ T ≤ 25°C     | Steadily lit                           | Off                                    | Warning: text, symbol and amber            |
| T ≤ 0°C or T > 25°C | Steadily lit                           | 500 Hz; one second on, two seconds off | Alert: text, symbol and red                |
| Sensor read error   | Two short flashes, then the loop pause | Repetition disabled                    | Explicit sensor error; temperature unknown |

These are demonstration thresholds. An unlit LED does not prove acceptable temperature or working power.
Manual buzzer silencing is still outstanding. Phone notifications remain planned and require connectivity
and permission; they are separate from the local hardware feedback.

## Behaviour and scope

The LED and buzzer are output devices; the SCD-41 is the sensor. See the
[device guide](../../device/README.md#main-temperature-logger) for implemented feedback and the
[project scope](../project-scope.md) for included and excluded features.
