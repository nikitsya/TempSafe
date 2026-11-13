# Temperature sample volume per medication box

At the nominal 30-second sampling interval, one continuously running TempSafe box produces **2,880 sample records per 24
hours** and **86,400 per 30 days**. These figures count both successful measurements and recorded sensor errors.

## What the Raspberry Pi actually does

The logger reads the SCD-41, attempts to save one record to SQLite, then waits 30 seconds. Reading the sensor, handling
an error and writing to disk also take time, so two consecutive timestamps can be more than 30 seconds apart. If the
sensor has no fresh value yet, the logger waits one second and checks again without creating a row. A handled sensor
exception produces a record with no temperature and the quality `sensor_error`, provided the SQLite write
succeeds. [Logger implementation](../../device/temperature_readings.py) · [Device guide](../../device/README.md)

## Expected record counts

For one box, divide the elapsed time in seconds by 30. One hour contains 3,600 seconds, giving 120 records. A 24-hour
day therefore gives 120 × 24 = 2,880. The table assumes an exact cadence, continuous operation and successful writes.
Each period includes its start and excludes the first instant of the next period, so midnight is counted once.

| Elapsed period | Calculation | Expected records |
|----------------|-------------|-----------------:|
| 1 minute       | 60 ÷ 30     |                2 |
| 1 hour         | 3,600 ÷ 30  |              120 |
| 24 hours       | 2,880 × 1   |            2,880 |
| 7 days         | 2,880 × 7   |           20,160 |
| 28-day month   | 2,880 × 28  |           80,640 |
| 29-day month   | 2,880 × 29  |           83,520 |
| 30-day month   | 2,880 × 30  |           86,400 |
| 31-day month   | 2,880 × 31  |           89,280 |
| 365-day year   | 2,880 × 365 |        1,051,200 |
| 366-day year   | 2,880 × 366 |        1,054,080 |

These calculations use elapsed 24-hour days. An Irish calendar day spanning a clock change can contain 23 or 25 hours,
giving 2,760 or 3,000 nominal records respectively. For several boxes operating over the same period, multiply the
expected count by the number of boxes.

## Where the records go and how long they stay

| Situation                                     | Effect on the count                                                                                                                                                                           |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Wi-Fi is unavailable while the Pi is running  | The Pi continues saving locally. Once connectivity returns, the publisher retries pending records with their original IDs. MySQL can therefore receive earlier observations in a later batch. |
| MySQL confirms storage                        | The publisher marks the local row as uploaded. An identical retry returns the existing server record, so one observation counts once in MySQL even if it was transmitted twice.               |
| The Pi is switched off or a local write fails | There is no saved record for that attempt or interval. A gap can therefore reduce the actual count below the estimate.                                                                        |

SQLite must have capacity for **at least 24 hours of offline sampling**. The project has no agreed one-month retention
period for MySQL readings. The database design leaves the retention period for the team to agree and proposes deleting
expired records only after a successful backup. The hourly summary in the Figma prototype groups readings for display
and does not change how the backend stores
them. [Offline buffering requirement](../requirements/functional-requirements.md) · [MQTT publisher](../../device/mqtt_publisher.py) · [Server storage and retries](../../backend/tempsafe/monitoring/readings.py) · [Retention proposal](database-research.md) · [Dashboard example](../../ui-example/README.md)

## Estimating disk space

A row in MySQL includes identifiers, timestamps, quality and a profile reference as well as the temperature. Indexes
also take space. To estimate the monthly footprint, measure the growth of the sample table **including its indexes**
over a representative batch, divide by the number of rows added, then multiply by 86,400 for a 30-day month. Measure the
Pi's SQLite file and backup copies separately if budgeting total storage. No production disk measurement is assumed
here. [MySQL sample schema](../../database/schema.sql)
