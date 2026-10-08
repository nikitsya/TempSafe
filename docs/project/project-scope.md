# Project Scope

**TempSafe** is an IoT monitoring system for a Controlled Drug Box stored inside an ambulance. It continuously monitors
temperature over time and alerts the Advanced Paramedic when storage conditions approach or exceed the configured
temperature limit.

The project focuses on reducing unnecessary manual temperature checks by providing automatic monitoring, local LED
feedback, phone notifications and a record of temperature observations. Audible buzzer feedback and estimated excursion
summaries are Should Have enhancements.

## Included in the Project

- Continuous temperature monitoring inside the Controlled Drug Box using a DHT22 sensor.
- Use of a Raspberry Pi to collect, process and store temperature readings.
- Monitoring temperature over time through timestamped readings and accessible history. Estimated excursion timing and
  maximum-temperature summaries are Should Have.
- Early warning when the temperature approaches 25°C and an alert when it exceeds 25°C.
- A single-colour LED lights for Warning or Alert and uses a distinct blink pattern for sensor failure. Normal leaves it
  off; an unlit LED does not prove acceptable temperature or working power.
- The application shows Normal, Warning and Alert using green, amber and red, together with text and symbols.
- Phone notifications for Warning and Alert with connectivity and permission. The delivery channel is still to be
  selected and tested.
- Buzzer feedback on Alert is Should Have, rather than a guaranteed baseline component.
- A web-based application for viewing current status, alerts and temperature history.
- Automatic logging of temperature readings, including quality and original observation times.
- Testing the system using a prototype Controlled Drug Box.

## Excluded from the Project

- Automatic cooling or temperature regulation of the Controlled Drug Box.
- Direct integration with National Ambulance Service systems or ePCR.
- GPS/location tracking, bag-opening detection, weight measurement, humidity reporting and a second external temperature
  sensor.
- Tracking medication administration to individual patients.
- Replacing official controlled-drug records or clinical documentation.
- Automatically deciding whether a medication is clinically safe to use after a temperature excursion.
- Use of real controlled drugs during testing.
- Deployment of the prototype in a real ambulance or clinical environment.
