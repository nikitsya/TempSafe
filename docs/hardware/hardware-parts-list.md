# IoT Controlled Drug Box – Development Parts List

This parts list reflects the current **TempSafe** project scope: continuous temperature monitoring inside a prototype controlled drug box using a Raspberry Pi and DHT22 sensor, with local visual and audible feedback using an LED indicator and buzzer.

## Parts List

| Part | Purpose / Notes | Link / Source | Cost |
| --- | --- | --- | --- |
| Raspberry Pi | Main controller. Collects temperature readings, processes the temperature status, stores data and sends it to the web application. It also controls the LED indicator and buzzer. | Use existing Raspberry Pi if available | Existing / TBD |
| DHT22 temperature & humidity sensor | Measures the temperature inside the controlled drug box. Temperature is the main value used by the project. | https://thepihut.com/collections/the-pi-hut/products/dht22-temperature-humidity-sensor-extras | £8.70 |
| RGB LED or three LEDs (green / amber / red) | Provides immediate visual feedback without requiring the Advanced Paramedic to open the web application. Green = Normal, amber = Warning, red = Alert. | Lecturer parts list / The Pi Hut | TBD |
| Active buzzer | Provides an audible alert when the temperature exceeds the configured upper limit and urgent attention is required. | Lecturer parts list / The Pi Hut | TBD |
| LED resistor(s) (approx. 220–330 Ω) | Protect the LED(s) by limiting current. The exact number depends on whether an RGB LED or separate LEDs are used. | Lecturer parts list / The Pi Hut | TBD |
| Full-size breadboard | Used to build and test the circuit without soldering. | https://thepihut.com/products/full-sized-breadboard | £5.00 |
| Jumper wires | Connect the DHT22, LED indicator, buzzer and breadboard to the Raspberry Pi. Male/Male and Female/Male wires are useful for prototyping. | Lecturer parts list / The Pi Hut | Approx. €4–8 |
| Pull-up resistor (4.7–10 kΩ) | May be required for the DHT22 data line, depending on the sensor module used. | May already be included with the DHT22 module | €0–6 |
| microSD card | Stores Raspberry Pi OS, project software and local log data. | Any compatible microSD card, e.g. 32 GB | Existing / TBD |
| Power supply / power bank | Powers the Raspberry Pi, sensor and feedback devices during testing. The exact option depends on the Raspberry Pi model. | To be selected after the Raspberry Pi model is confirmed | TBD |
| Controlled drug box / prototype case | Physical enclosure used to demonstrate sensor installation, temperature monitoring and local feedback. No real controlled drugs will be used. | Use an existing suitable lockable case/box | Existing / TBD |

## Feedback Logic

- **Below 24°C – Normal:** green LED, no buzzer.
- **24°C to 25°C – Warning:** amber LED and early warning in the application.
- **Above 25°C – Alert:** red LED, buzzer and high-priority alert in the application.

The LED and buzzer are **output / feedback devices**, not sensors. The DHT22 remains the main sensor used to collect environmental data.

## Scope Notes

- **Scope note:** The reed switch/opening sensor and GNSS/GPS module are not included in the current version of the project.
- **Project focus:** The prototype focuses on temperature monitoring over time, logging, mobile/web alerts, and clear local feedback through light and sound.
- **Temperature threshold:** The prototype uses **25°C** as the upper temperature limit for alerting, with an early warning before the limit is exceeded.
- **User interaction:** The Advanced Paramedic should not need to check the application while the temperature is normal. The system provides feedback automatically when attention is required.
