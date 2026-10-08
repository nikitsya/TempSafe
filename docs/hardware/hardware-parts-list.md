# IoT Controlled Drug Box – Development Parts List

This parts list reflects the current **TempSafe** project scope: continuous temperature monitoring inside a prototype
controlled drug box using a Raspberry Pi and SCD-41 sensor, with a single-colour warning LED. A buzzer is a Should Have
enhancement, subject to component availability and testing.

## Parts List

| Part                                | Purpose / Notes                                                                                                                                                                                                            | Link / Source                                       | Cost           |
|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|----------------|
| Raspberry Pi 400                    | Main controller. Collects temperature readings, processes the temperature status, stores data and sends it to the web application. It controls the LED indicator and, if implemented, the buzzer.                          | Already owned Raspberry Pi 400                      | Already owned  |
| Adafruit SCD-41                     | Already owned. I²C sensor with integrated temperature and humidity measurement; only temperature is used. Humidity and CO₂ reporting are outside this release.                                                             | https://www.adafruit.com/product/5190               | Already owned  |
| Single-colour LED                   | Provides immediate visual feedback without requiring the Advanced Paramedic to open the web application. Lights for Warning or Alert; off for Normal; distinct blinking for sensor failure. No RGB capability is required. | Lecturer parts list / The Pi Hut                    | TBD            |
| Active buzzer                       | Should Have: provides an audible alert on Alert, with a silence control; not a guaranteed baseline component.                                                                                                              | Lecturer parts list / The Pi Hut                    | TBD            |
| LED resistor(s) (approx. 220–330 Ω) | Protect the LED(s) by limiting current. Select the resistor value for the actual LED and supply voltage.                                                                                                                   | Lecturer parts list / The Pi Hut                    | TBD            |
| Full-size breadboard                | Used to build and test the circuit without soldering.                                                                                                                                                                      | https://thepihut.com/products/full-sized-breadboard | £5.00          |
| Jumper wires                        | Connect the SCD-41, LED indicator, buzzer and breadboard to the Raspberry Pi. Male/Male and Female/Male wires are useful for prototyping.                                                                                  | Lecturer parts list / The Pi Hut                    | Approx. €4–8   |
| microSD card                        | Stores Raspberry Pi OS, project software and local log data.                                                                                                                                                               | Any compatible microSD card, e.g. 32 GB             | Existing / TBD |
| Raspberry Pi 400 power supply       | Mains power for the bench prototype; the Pi communicates over Wi-Fi and does not need a direct connection to the laptop.                                                                                                   | Compatible Raspberry Pi 400 supply                  | Existing / TBD |
| Plastic prototype box               | One simple plastic storage box for temperature monitoring and local feedback. No real controlled drugs will be used.                                                                                                       | To be purchased; final size to be confirmed         | TBD            |

## Feedback Logic

- **Normal:** physical LED off; application shows green with a text label and symbol.
- **Warning:** physical LED on; application shows amber with text and a symbol; send a phone notification when
  connected.
- **Alert:** physical LED on; application shows red with text and a symbol; send a phone notification when connected.
  Sound the buzzer if implemented.
- **Sensor failure:** distinct LED blinking and an explicit application error, never Normal.

For the existing demo example, Warning starts at 24°C and high-temperature Alert starts above 25°C. Configured
lower-limit violations also produce Alert.

The LED and buzzer are **output / feedback devices**, not sensors. The SCD-41 remains the main sensor used to collect
environmental data.

## Scope Notes

- **Scope note:** The reed switch/opening sensor and GNSS/GPS module are not included in the current version of the
  project.
- **Project focus:** The prototype focuses on temperature monitoring over time, logging, mobile/web alerts, and clear
  local feedback through light and sound.
- **Temperature threshold:** The prototype uses **25°C** as the upper temperature limit for alerting, with an early
  warning before the limit is exceeded.
- **User interaction:** The Advanced Paramedic should not need to check the application while the temperature is normal.
  The system provides feedback automatically when attention is required.
