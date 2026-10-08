# Persona – TempSafe

**Name:** Shannon Rice  
**Age:** 32  
**Occupation:** Advanced Paramedic  
**Experience:** 7 years in pre-hospital emergency care  
**Location:** Ireland

**User type:** Confident smartphone and workplace digital-system user, but not a technical expert.

## About

Shannon works as an Advanced Paramedic and regularly responds to emergency calls.

During her shift, controlled drugs are stored in a secure **Controlled Drug Box** inside a **Vehicle Security Safe** in
the ambulance.

Shannon often works in stressful and time-critical situations. While she is treating a patient, she may not be able to
return to the parked ambulance to check the drug box or change the vehicle conditions.

TempSafe is designed to monitor the temperature inside the Controlled Drug Box automatically over time and provide clear
feedback only when attention is required.

## Goals

Shannon wants to:

- make sure temperature-sensitive controlled drugs remain within suitable storage conditions;
- avoid spending time on regular manual temperature checks;
- receive an early warning if the temperature is approaching the configured limit;
- know how long the medication has been exposed to an elevated temperature;
- quickly understand whether a temperature excursion has occurred;
- receive clear feedback without needing to open the phone application every time;
- receive only important notifications that do not distract her from emergency care.

## User Needs

The Advanced Paramedic needs a system that:

- works automatically in the background;
- continuously monitors temperature over time;
- does not require regular user interaction while conditions are normal;
- records the duration and maximum temperature of a temperature excursion;
- provides clear visual feedback directly on the box;
- provides an audible warning when urgent attention is required;
- sends a phone notification when the temperature approaches or exceeds the configured limit;
- uses clear text as well as colour so that the status is not communicated by colour alone;
- is simple and reliable to use under pressure.

## Frustrations

Shannon may experience the following problems:

- she cannot leave a patient during emergency care simply to check the temperature of a box in the ambulance;
- the temperature inside a parked ambulance can rise significantly even when the outside temperature is moderate;
- the outside air temperature does not show the actual conditions inside a closed vehicle safe;
- without continuous monitoring, she may not know how long the medicines were exposed to a high temperature;
- regular manual checks take additional time;
- too many unnecessary notifications may be distracting;
- a status shown only by colour may be unclear or inaccessible;
- complicated interfaces are difficult to use in emergency situations.

## Technology Use

Shannon regularly uses a smartphone and digital systems at work, but TempSafe should require minimal interaction.

If the storage conditions remain normal, Shannon should not need to check or enter anything manually. The system should
monitor the box continuously and provide local feedback through an LED indicator.

The web application is mainly used when Shannon receives a warning or alert, or when she needs to review the temperature
history and duration of an excursion.

## Typical Scenario

During an emergency call, Shannon is treating a patient away from the ambulance. The ambulance is parked outside in
direct sunlight. The outside temperature may be moderate, for example around **18°C**, but the temperature inside the
vehicle and the enclosed storage area can rise much higher.

Shannon cannot leave the patient to return to the ambulance and manually check the Controlled Drug Box or turn on the
air conditioning.

TempSafe continuously monitors the temperature inside the box and records how the temperature changes over time.

While the temperature remains normal, the system requires no action. A **green LED** provides a simple local indication
that the monitored conditions are normal.

If the temperature reaches the early-warning range, the LED changes to **amber** and TempSafe sends a phone notification
with a clear message, for example:

> **Warning: Controlled Drug Box temperature has reached 24°C.**

If the temperature exceeds **25°C**, the LED changes to **red**, the buzzer provides an audible alert, and the system
records the temperature excursion. A higher-priority phone alert is also sent:

> **Alert: Controlled Drug Box temperature has exceeded 25°C.**
>
When the temperature exceeds **25°C**, the database records the start time of the excursion. The web application shows
how long the drugs have been above the safe limit, for example:

> **EXCURSION – 12 min – max 27.4°C**

TempSafe records the start time, maximum temperature and duration of the excursion so Shannon can review what happened
after the immediate emergency situation.

## Environment

TempSafe is designed specifically for use in an ambulance.

The Controlled Drug Box is kept inside a Vehicle Security Safe in the vehicle. Because this is an enclosed storage area,
its temperature can differ significantly from the outside air temperature.

Research on medication storage in emergency vehicles has shown that medication storage areas can become considerably
hotter than the outdoor environment. In one study, the temperature inside an insulated drug pouch reached more than
**40°C**.

For this reason, TempSafe measures the temperature directly inside the Controlled Drug Box rather than relying on the
outside temperature.

## Tasks

The Advanced Paramedic should not need to perform regular manual temperature checks. TempSafe should automatically:

- measure the temperature inside the Controlled Drug Box;
- record temperature readings over time;
- operate without user input while conditions are normal;
- provide green, amber and red LED feedback for quick local status recognition;
- send an early phone warning when the temperature approaches the configured limit;
- use the buzzer and a higher-priority alert when the configured upper limit is exceeded;
- record the start time, maximum temperature and duration of a temperature excursion;
- allow the user to review the recorded event later.

## Main Use Case

TempSafe continuously monitors temperature over time inside the Controlled Drug Box located in the ambulance security
safe.

While conditions are normal, the system works in the background and requires no action from Shannon.

If the temperature approaches the configured limit, TempSafe provides an early warning through the LED indicator and a
phone notification. If the temperature exceeds the limit, it provides stronger visual and audible feedback and records
how long the excursion lasts.

The aim is to give the Advanced Paramedic useful information at the right time without adding unnecessary manual checks
during patient care.

## System

The TempSafe system includes:

- **Controlled Drug Box** – secure container used to store controlled drugs;
- **Vehicle Security Safe** – secure safe inside the ambulance where the Controlled Drug Box is kept;
- **Raspberry Pi** – collects and processes sensor data;
- **SCD-41 temperature sensor** – measures the temperature inside the Controlled Drug Box;
- **LED indicator** – provides immediate visual feedback about the temperature status;
- **Buzzer** – provides audible feedback when urgent attention is required;
- **Database / Data Storage** – stores temperature readings and temperature excursion events, and tracks each excursion:
  start time, end time, maximum temperature and duration;
- **Web Application** – displays current status, temperature history, alerts and excursion duration;
- **Notification System** – sends warnings and alerts to the user;
- **Internet Connection** – allows data to be transferred from the Raspberry Pi to the application.

## Temperature and Feedback Logic

The prototype uses the following temperature and feedback logic:

- **Below 24°C – Normal:** green LED, no alert;
- **24°C to 25°C – Warning:** amber LED and early phone warning;
- **Above 25°C – Temperature excursion:** red LED, buzzer and high-priority phone alert.

The **24°C threshold** is a project-defined early warning. The **25°C threshold** is used in the prototype as the upper
storage limit for Morphine Sulphate and Fentanyl.

Colour is not used as the only form of communication. The web interface also displays a clear text status and the
measured temperature, and the buzzer provides an additional form of feedback for urgent events.

## Main Project Value

The main purpose of TempSafe is not to give the Advanced Paramedic more data to check. It is designed to reduce manual
checking and provide useful feedback only when the storage conditions require attention.

The key information is not only the current temperature, but also **temperature over time**: whether an excursion
occurred, how high the temperature became, and how long it lasted.

TempSafe supports the existing work of the Advanced Paramedic instead of requiring the user to constantly adapt to the
technology.

> **TempSafe is an automatic IoT monitoring system for a Controlled Drug Box that tracks temperature over time and gives
clear visual, audible and mobile feedback when storage conditions require attention.**
