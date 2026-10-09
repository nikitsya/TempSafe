# Research Sensor Use Case – Controlled Drug Box

## 1. Data the sensor needs to collect

The project focuses on temperature monitoring inside a controlled drug box used in an ambulance. The sensor system needs
to collect the following data:

- Current temperature inside the controlled drug box (°C).
- Date and time of each temperature reading.
- Temperature status, for example `Normal`, `Warning` or `Alert`.
- Timestamped out-of-range observations; estimated excursion duration is a Should Have summary.

**Current project scope:** GPS/location tracking and bag-opening detection are not included in this version of the
project.

## 2. Why temperature monitoring is needed

The National Ambulance Service (NAS) controlled-drug policy identifies four practitioner stock positions: Morphine
Sulphate 10 mg/1 ml, Fentanyl 100 mcg/2 ml, Ketamine 200 mg/20 ml and Ketamine 500 mg/5 ml.

For the product information reviewed for this project, morphine and fentanyl have an upper storage limit of 25°C. The
table below includes only the medications for which this temperature limit is relevant to the prototype. Because these
medicines may be stored in the same controlled drug box, the prototype will use 25°C as its main upper temperature
threshold.

| Medication                   | Storage Conditions                                           |
|------------------------------|--------------------------------------------------------------|
| Morphine Sulphate 10 mg/1 ml | Store at a temperature not above 25°C                        |
| Fentanyl 100 mcg/2 ml        | Store at a temperature not above 25°C and protect from light |

**Prototype threshold logic:**

- For valid readings within the configured lower limit: below 24°C = `Normal`
- 24–25°C = `Warning`
- Above 25°C = `Alert`

The 24°C warning level is a project-defined early warning, not a clinical storage requirement.

## 3. Temperature sensor comparison

| Sensor  | Advantages                                                                              | Limitations                                                                       |
|---------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| SCD-41  | Already owned; integrated temperature and humidity measurement; I²C interface           | Primarily a CO₂ sensor; temperature validation and offset assessment are required |
| DHT22   | Measures temperature and humidity; inexpensive; easy to use with Raspberry Pi           | Slower readings; humidity is not essential for the current scope                  |
| DS18B20 | Good temperature accuracy; simple digital interface; suitable for continuous monitoring | Measures temperature only                                                         |
| BME280  | Measures temperature, humidity and air pressure; compact digital sensor                 | More expensive and provides data not required by the current scope                |

**Chosen option: Adafruit SCD-41 (already owned by the team).** This is primarily a CO₂ sensor with integrated
temperature and humidity measurement and an I²C interface. The prototype uses its temperature readings only; humidity
and CO₂ reporting are outside this release. DHT22, DS18B20 and BME280 are comparison alternatives, not installed
sensors.
Validate temperature readings against a reference thermometer in the assembled box, including the effect of sensor
self-heating and placement; agree any temperature offset and acceptance tolerance from the manufacturer guidance
and measured results before evaluating temperature alerts.

The physical single-colour LED is off for Normal and on for Warning or Alert, with a distinct blink pattern for sensor
failure. The application uses green, amber and red with text and symbols. Phone notifications are Must Have with
connectivity and permission; the buzzer is Should Have.

## 4. User feedback devices

LED and buzzer are not sensors. They are output devices that give the Advanced Paramedic immediate feedback without requiring the user to open the web application.

| Output device | Purpose | Advantages | Limitations |
| --- | --- | --- | --- |
| RGB LED / three LEDs | Provides immediate visual status: green = Normal, amber = Warning, red = Alert | Very quick to understand; visible without opening the app | Colour should not be the only form of communication |
| Buzzer | Provides an audible alert when urgent attention is required | Can attract attention even when the user is not looking at the box | Should only be used for important alerts to avoid unnecessary distraction |

The system will combine colour with clear text in the web application. This supports usability and avoids relying on colour alone.

## 5. Proposed system behaviour

## 1. The DHT22 measures the temperature inside the Controlled Drug Box at regular intervals.

## 2. The Raspberry Pi receives the readings and stores them with a timestamp.

## 3. The system calculates the current status and tracks temperature over time.

## 4. Below 24°C, the LED shows green and no alert is sent.

## 5. Between 24°C and 25°C, the LED changes to amber and the system sends an early warning.

## 6. Above 25°C, the LED changes to red, the buzzer sounds, and the system sends a high-priority alert.

## 7. The system records the start time, maximum temperature and duration of the temperature excursion.

## 8. The web application allows the user to review the current status and historical excursion data.

## 6. Short use-case summary

TempSafe uses a SCD-41 sensor connected to a Raspberry Pi to monitor the temperature inside a Controlled Drug Box over time. The Advanced Paramedic does not need to perform regular manual checks while conditions are normal. A green LED shows that conditions are normal. If the temperature approaches the configured limit, the LED changes to amber and the user receives an early warning. If the temperature exceeds 25°C, the LED changes to red, the buzzer sounds, and the system records the temperature excursion and sends an alert. The prototype is designed for monitoring, feedback and logging only; it does not cool the box automatically.

## 7. Prototype limitations

The system does not automatically cool or regulate the Controlled Drug Box.

The prototype will not use real controlled drugs.

The project will not integrate directly with NAS clinical or ePCR systems.

The prototype is for demonstration and testing and is not intended for clinical deployment.

The LED and buzzer provide local feedback but do not replace official clinical or medication-storage procedures.
## 7. Research sources

- National Ambulance Service (NAS), *NASCG006 – Management and Requisition of Controlled Drugs*, Appendix 11:
  Practitioner Stock Limits.
- Health Products Regulatory Authority (HPRA), product information for Morphine Sulphate injection used in this
  research.
- Health Products Regulatory Authority (HPRA), product information for Fentanyl injection used in this research.

- [Adafruit SCD-41 product specifications](https://www.adafruit.com/product/5190).
- [Adafruit SCD-4x guide](https://learn.adafruit.com/adafruit-scd-40-and-scd-41).
