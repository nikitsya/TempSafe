# Project Scope

**TempSafe** is an IoT monitoring system for a Controlled Drug Box stored inside an ambulance. It continuously monitors
temperature over time and alerts the Advanced Paramedic when storage conditions approach or exceed the configured
temperature limit.

The current prototype is tested on a bench without medicines; ambulance use is a future context.

The project focuses on reducing unnecessary manual temperature checks by providing automatic monitoring, local LED
feedback, planned phone notifications and a record of temperature observations. Estimated excursion
summaries (FR-13) are Must Have; audible buzzer feedback remains Should Have.
This document defines the target scope; see the [implementation review](requirements/moscow-prioritisation.md)
for completed and outstanding work.

## Application platform

TempSafe will be a responsive web application with a Python/FastAPI backend and an HTML, CSS and JavaScript frontend.
Planned Progressive Web App (PWA) support would let users add a home-screen icon and open the same web application
in a standalone window on supported phones. PWA installation and Web Push require browser/platform testing.
A separate native mobile application is a Could Have follow-up, subject to a team decision.

## Included in the Project

- Continuous temperature monitoring inside the Controlled Drug Box using an SCD-41 sensor.
- Use of a Raspberry Pi to collect, process and store temperature readings.
- Monitoring temperature over time through timestamped readings and accessible history. Estimated excursion timing and
  maximum-temperature summaries are Must Have (FR-13).
- Classification against versioned lower/upper limits: demonstration Warning begins at 24°C; Alert is above 25°C or
  at or below the agreed 0.00°C lower threshold.
- A single-colour LED lights for Warning or Alert and uses a distinct blink pattern for sensor failure. Normal leaves it
  off; an unlit LED does not prove acceptable temperature or working power.
- The application shows Normal, Warning and Alert using green, amber and red, together with text and symbols.
- Phone notifications for Warning and Alert with connectivity and permission. Web Push is the proposed delivery channel;
  browser support and delivery still need testing.
- Buzzer feedback on Alert is Should Have, rather than a guaranteed baseline component.
- A responsive web application with a FastAPI backend for viewing current status, alerts and temperature history.
- Automatic logging of sample attempts, including errors, quality and original observation times.
- Device publishing through MQTT over TLS, a cloud FastMQTT subscriber and MySQL; HTTPS for the web API.
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
