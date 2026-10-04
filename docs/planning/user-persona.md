# User Persona

## Persona

**Name:** Shannon Rice  
**Age:** 32  
**Occupation:** Advanced Paramedic  
**Experience:** 7 years in pre-hospital emergency care  
**Location:** Ireland

**User type:** Confident smartphone and workplace digital-system user, but not a technical expert.

## About

Shannon works as an Advanced Paramedic and regularly responds to emergency calls.

During her shift, she works with controlled drugs that are stored in a secure **Controlled Drug Box**. The Controlled
Drug Box is placed inside a **Vehicle Security Safe** in the ambulance.

Shannon works in stressful and fast-moving situations, so the monitoring system should not require constant attention or
regular manual checks.

The main purpose of the system is to monitor the temperature inside the Controlled Drug Box automatically and notify
Shannon only when the temperature is approaching the allowed limit or exceeds it.

## Goals

Shannon wants to:

- make sure controlled drugs are stored within suitable temperature conditions;
- avoid spending time on regular manual temperature checks;
- receive an early warning if the temperature approaches the allowed limit;
- receive an alert if the temperature exceeds the configured limit;
- review temperature history after a temperature excursion;
- quickly understand whether any action is required;
- receive only important notifications that do not distract her from emergency work.

## User Needs

The Advanced Paramedic needs a system that:

- works automatically;
- does not require regular interaction;
- is reliable;
- is easy to understand;
- runs continuously in the background;
- constantly monitors the temperature inside the Controlled Drug Box;
- sends warnings only when attention is required;
- automatically stores temperature data;
- records temperature excursions;
- shows how long the temperature remained above the configured limit;
- avoids unnecessary notifications.

## Frustrations

Shannon may experience the following problems:

- she has limited time for additional manual checks during emergency calls;
- the temperature inside the ambulance can change significantly during a shift;
- the outside air temperature does not show the actual conditions inside a closed vehicle safe;
- a parked ambulance may heat up, especially if it remains in direct sunlight;
- without automatic monitoring, a temperature problem may only be noticed after the medicines have already been exposed;
- regular manual temperature checks take additional time;
- too many unnecessary notifications may be distracting;
- complicated interfaces are difficult to use in emergency situations.

## Technology Use

Shannon regularly uses a smartphone and digital systems at work.

The system should require minimal interaction.

If the temperature inside the Controlled Drug Box remains within the normal range, Shannon should not need to check or
enter anything manually.

The system should operate automatically in the background.

The application is mainly used when:

- the user receives a warning;
- the temperature exceeds the configured limit;
- the current status needs to be reviewed;
- the user needs to review the history of a temperature event.

## Typical Scenario

During a shift, the ambulance is parked for a period of time.

The Controlled Drug Box is stored inside the Vehicle Security Safe in the ambulance.

Shannon does not check the temperature manually because the IoT system continuously monitors it.

As long as the temperature remains within the normal range, the system works in the background and requires no action
from the user.

If the temperature begins to approach the configured limit, Shannon receives an early warning:

> **Warning: Controlled Drug Box temperature has reached 24°C.**

This gives her an opportunity to take action before the upper storage limit is exceeded.

If the temperature rises above **25°C**, the system sends a higher-priority notification:

> **Alert: Controlled Drug Box temperature has exceeded 25°C.**

At the same time, the system automatically records:

- the date and time of the excursion;
- the maximum recorded temperature;
- the amount of time the temperature remained above the configured limit.

After receiving the alert, Shannon can open the application and review the details.

## Environment

The system is designed for use **inside an ambulance**.

Controlled drugs are stored in a secure **Controlled Drug Box**, which is placed inside a **Vehicle Security Safe** in
the ambulance.

This is a closed storage area, so the temperature inside it may differ from the outside temperature.

Even when the outdoor temperature is moderate, the inside of the ambulance and the enclosed storage area may become
significantly warmer, especially if the vehicle is parked in direct sunlight for a period of time.

Research on medication storage in emergency vehicles has shown that temperatures inside vehicles and medication storage
areas can rise significantly above outside temperatures. In one study, the temperature inside an insulated drug pouch
reached more than 40°C, despite substantially lower outdoor temperatures.

For this reason, the outside temperature is not a reliable indicator of the storage conditions for controlled drugs.

In this project, the temperature is measured **directly inside the Controlled Drug Box**, close to the medicines.

The system should operate continuously and automatically while the ambulance is in use.

## Tasks

The Advanced Paramedic should not need to check the temperature manually on a regular basis.

The system should automatically:

- measure the temperature inside the Controlled Drug Box;
- store temperature readings;
- operate without user input while the temperature is normal;
- send an early warning when the temperature approaches the configured limit;
- send an alert when the temperature exceeds 25°C;
- record a temperature excursion;
- store the maximum recorded temperature;
- store the duration of the temperature excursion.

The user should interact with the system only when attention is required.

## Main Use Case

**The IoT system continuously monitors the temperature inside the Controlled Drug Box located in the ambulance security
safe.**

If the temperature remains within the normal range, the system operates in the background and requires no action from
the Advanced Paramedic.

If the temperature approaches the configured limit, the system automatically sends an early warning.

If the temperature exceeds **25°C**, the system sends an alert and automatically records the temperature excursion.

The Advanced Paramedic receives a notification only when the storage conditions require attention.

## System

The system includes:

- **Controlled Drug Box** – secure container used to store controlled drugs;
- **Vehicle Security Safe** – secure safe inside the ambulance where the Controlled Drug Box is kept;
- **Raspberry Pi** – collects and processes sensor data;
- **DHT22 sensor** – measures the temperature inside the Controlled Drug Box;
- **Database / Data Storage** – stores temperature readings and temperature excursion events;
- **Web Application** – displays current status, alerts and historical data;
- **Notification System** – sends warnings and alerts to the user;
- **Internet Connection** – allows data to be transferred from the Raspberry Pi to the application.

## Temperature Logic

The prototype uses the following temperature logic:

- **Below 24°C – Normal**
- **24°C to 25°C – Warning**
- **Above 25°C – Alert**

The **24°C threshold** is an early-warning level created for the project.

It allows the user to be notified before the maximum storage temperature is exceeded.

The **25°C threshold** is used in the project as the upper storage limit for **Morphine Sulphate** and **Fentanyl**.

## Main Project Value

The main purpose of the system is not to make the Advanced Paramedic check the medicines more often.

Instead, the system is designed to **reduce manual checks and save time**.

The temperature is monitored automatically.

If the storage conditions are normal, the user receives no notification and does not need to take any action.

The system attracts the Advanced Paramedic’s attention only when the temperature begins to approach a potentially unsafe
level or exceeds it.

> **An automatic IoT temperature-monitoring system for a Controlled Drug Box inside an ambulance, designed to work in
the background and notify the Advanced Paramedic only when the temperature approaches or exceeds the configured storage
limit.**
