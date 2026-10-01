# Research Sensor Use Case – Smart Paramedic Bag

## 1. Data the sensors need to collect

The smart paramedic bag needs to collect three main types of data:

- **Bag open/closed status** – to detect when the bag is opened or closed.
- **Temperature inside the bag** – to make sure medical supplies are stored in suitable conditions.
- **Location data** – to help the user find and track the paramedic bag.

The system can also record the time when the bag is opened and send an alert if the temperature becomes too high or too low.

## 2. Sensor comparison

### Opening detection

For detecting when the bag is opened:

| Sensor | Advantages | Limitations |
|---|---|---|
| Reed switch + magnet | Cheap, simple, small, low power | Magnet must be positioned correctly |
| Hall effect sensor | Reliable, no physical contact | Needs power and is slightly more complex |
| Microswitch | Simple and reliable | Requires physical contact with the lid |

**Chosen option:** Reed switch, because it is simple, inexpensive and easy to connect to a Raspberry Pi.

### Temperature monitoring

| Sensor | Advantages | Limitations |
|---|---|---|
| DHT22 | Measures temperature and humidity, inexpensive | Slower readings |
| DS18B20 | Good temperature accuracy, simple | Only measures temperature |
| BME280 | Measures temperature, humidity and air pressure | More expensive and slightly more complex |

**Chosen option:** DHT22, because it can measure both temperature and humidity and is already suitable for Raspberry Pi projects.

### Location Tracking

The Smart Paramedic Bag also needs to collect location data so the user can see where the bag is.

Possible options:

| Option | Advantages | Limitations |
|---|---|---|
| L76K Multi-GNSS Module | Compatible with Raspberry Pi, supports several GNSS systems, compact and suitable for prototyping | More expensive than some basic GPS modules and requires wiring |
| NEO-7M GPS module | Low cost, small, suitable for prototyping | Requires additional wiring and may need to be ordered from another supplier |
| USB GPS receiver | Easy USB connection | Larger and less convenient for a portable bag |

**Chosen option:** L76K Multi-GNSS Module, because it is compatible with Raspberry Pi, compact, supports multiple satellite navigation systems, and is available from the same supplier as the other project components.

**Limitation:** The GNSS module provides location coordinates but does not send the data to the mobile app by itself. The Raspberry Pi will need an Internet connection, such as Wi-Fi or a mobile hotspot, to send the location data.

## 3. Short use-case summary

The smart paramedic bag will use a reed switch to detect when the bag is opened, a DHT22 sensor to monitor temperature and humidity, and a GPS module to determine the location of the bag. The Raspberry Pi will collect the sensor data and send it to the application. The app can show the bag location and current temperature, record when the bag was opened, and send alerts when necessary.
