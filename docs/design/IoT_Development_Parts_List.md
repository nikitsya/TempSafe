# IoT Controlled Drug Box – Development Parts List

This parts list reflects the current project scope: temperature monitoring inside a prototype controlled drug box using a Raspberry Pi and DHT22 sensor.

## Parts List

| Part | Purpose / Notes | Link / Source | Cost |
| --- | --- | --- | --- |
| Raspberry Pi | Main controller. Collects temperature readings, stores data and sends it to the web application. | Use existing Raspberry Pi if available | Existing / TBD |
| DHT22 temperature & humidity sensor | Measures the temperature inside the controlled drug box. Temperature is the main value used by the project. | https://thepihut.com/collections/the-pi-hut/products/dht22-temperature-humidity-sensor-extras | £8.70 |
| Full-size breadboard | Used to build and test the circuit without soldering. | https://thepihut.com/products/full-sized-breadboard | £5.00 |
| Jumper wires | Connect the DHT22 and breadboard to the Raspberry Pi. Male/Male and Female/Male wires are useful for prototyping. | Lecturer parts list / The Pi Hut | Approx. €4–8 |
| Pull-up resistor (4.7–10 kΩ) | May be required for the DHT22 data line, depending on the sensor module used. | May already be included with the DHT22 module | €0–6 |
| microSD card | Stores Raspberry Pi OS, project software and local log data. | Any compatible microSD card, e.g. 32 GB | Existing / TBD |
| Power supply / power bank | Powers the Raspberry Pi and sensor during testing. The exact option depends on the Raspberry Pi model. | To be selected after the Raspberry Pi model is confirmed | TBD |
| Controlled drug box / prototype case | Physical enclosure used to demonstrate sensor installation and temperature monitoring. No real controlled drugs will be used. | Use an existing suitable lockable case/box | Existing / TBD |

## Scope Notes

- **Scope note:** The reed switch/opening sensor and GNSS/GPS module are not included in the current version of the project. The prototype focuses on temperature monitoring, logging and alerts.
- **Temperature threshold:** The prototype uses **25°C** as the upper temperature limit for alerting, with an early warning before the limit is exceeded.
