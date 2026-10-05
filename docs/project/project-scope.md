# Project Scope

**TempSafe** is an IoT monitoring system for a Controlled Drug Box stored inside an ambulance. It continuously monitors temperature over time and alerts the Advanced Paramedic when storage conditions approach or exceed the configured temperature limit.

The project focuses on reducing unnecessary manual temperature checks by providing automatic monitoring, local visual and audible feedback, mobile/web alerts, and a record of temperature-excursion events.

## Included in the Project

- Continuous temperature monitoring inside the Controlled Drug Box using a DHT22 sensor.
- Use of a Raspberry Pi to collect, process and store temperature readings.
- Monitoring temperature over time, including the start time, maximum temperature and duration of a temperature excursion.
- Early warning when the temperature approaches 25°C and an alert when it exceeds 25°C.
- LED visual feedback: green for Normal, amber for Warning and red for Alert.
- Buzzer feedback when urgent attention is required.
- A web-based application for viewing current status, alerts and temperature history.
- Automatic logging of temperature readings and temperature-excursion events.
- Testing the system using a prototype Controlled Drug Box.

## Excluded from the Project

- Automatic cooling or temperature regulation of the Controlled Drug Box.
- Direct integration with National Ambulance Service systems or ePCR.
- GPS/location tracking or bag-opening detection.
- Tracking medication administration to individual patients.
- Replacing official controlled-drug records or clinical documentation.
- Automatically deciding whether a medication is clinically safe to use after a temperature excursion.
- Use of real controlled drugs during testing.
- Deployment of the prototype in a real ambulance or clinical environment.
