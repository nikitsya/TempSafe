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

## 4. Proposed system behaviour

1. The SCD-41 measures the temperature inside the controlled drug box at regular intervals.
2. The Raspberry Pi receives the sensor readings and stores them with a timestamp.
3. The web application displays the current temperature and temperature status.
4. When the temperature reaches the warning range, the system shows an early warning.
5. If the temperature exceeds 25°C or falls below the configured lower limit, the system records the out-of-range
   observation and displays Alert.
6. Timestamped readings support later review. Estimated excursion duration and maximum-temperature summaries are Should
   Have enhancements.

## 5. Short use-case summary

The controlled drug box will use an SCD-41 sensor connected to a Raspberry Pi to monitor its internal temperature. The
Raspberry Pi will collect and store temperature readings and make them available to a web application. The application
will show the current temperature, provide an early warning as the temperature approaches the configured limit, and
record an alert if the temperature exceeds 25°C.

The prototype is designed for monitoring and logging only; it will not cool the box automatically.

## 6. Prototype limitations

- The system does not automatically cool or regulate the controlled drug box.
- The prototype will not use real controlled drugs.
- The project will not integrate directly with NAS clinical or ePCR systems.
- The prototype is for demonstration and testing and is not intended for clinical deployment.

## 7. Research sources

- National Ambulance Service (NAS), *NASCG006 – Management and Requisition of Controlled Drugs*, Appendix 11:
  Practitioner Stock Limits.
- Health Products Regulatory Authority (HPRA), product information for Morphine Sulphate injection used in this
  research.
- Health Products Regulatory Authority (HPRA), product information for Fentanyl injection used in this research.

- [Adafruit SCD-41 product specifications](https://www.adafruit.com/product/5190).
- [Adafruit SCD-4x guide](https://learn.adafruit.com/adafruit-scd-40-and-scd-41).
