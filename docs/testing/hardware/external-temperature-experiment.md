# Internal and External Temperature Experiment

**Status:** Planned; no results recorded yet.

## Purpose

Observe how temperature inside the prototype box changes when the surrounding
air warms and cools. Compare the two temperature curves and their delay before
deciding whether external temperature could support a useful prediction.
Existing internal-temperature Warning and Alert rules remain unchanged.

## Equipment and setup

- Raspberry Pi 5, SCD41 inside the small box, AM2302 outside it.
- Breadboard, wires and a 10 kohm pull-up resistor for the AM2302.
- A larger container around the small box and sealed bottles of warm water
  to warm the surrounding air. No medicines or boiling water.
- Keep both sensors away from bottle surfaces and box walls. Keep the Pi and
  exposed electrical connections outside the heated area, dry and protected
  from condensation. Connect or change wiring only with power disconnected.

Before testing, record the date, box material and dimensions, contents, lid
position, sensor positions and bottle arrangement. Photograph the setup.
Keep these conditions consistent between repeat runs.

## Procedure

1. Stop the main temperature logger. Run only
   `device/external_temperature_test.py` to read both sensors.
2. First place both sensors side by side in stable room conditions. Allow them
   to settle and record at least five minutes to check their difference.
   This is a comparison, not calibration against a reference thermometer.
3. Place the SCD41 inside the small box and the AM2302 in the surrounding air
   inside the larger container. Close the small box as recorded in the setup.
   Let readings settle and record a five-minute baseline.
4. Add sealed warm-water bottles beside the small box without touching it.
   Record the heating start time and both temperatures for about 20 minutes;
   extend if needed to observe the response. Reaching Alert is not required.
5. Remove the bottles and record the cooling start time. Continue recording
   for about 20 minutes, extending if temperatures are still changing markedly.
6. Return the setup to similar starting conditions and repeat. Aim for three
   heating/cooling runs, noting any differences in conditions.

## Measurement file

Use a separate CSV for the side-by-side comparison and for each experiment run.
Read both sensors approximately every five seconds; readings are sequential,
not exactly simultaneous. Preserve the timestamps and record errors explicitly.
Leave failed temperature values empty rather than substituting zero or an old value.

Planned CSV columns:

```text
timestamp_utc,inside_c,outside_c,inside_status,outside_status
```

Statuses: `valid`, `not_ready`, or `sensor_error`.
Use a unique filename for each run so earlier measurements are not overwritten.
Do not write experiment data to SQLite or publish it through MQTT.

**Before collecting evidence:** add CSV recording to the test script.
It currently prints readings to the terminal only.

## Results to complete after testing

Keep individual readings in the CSV files, not in a second manual table here.
Use this table to identify the files and record the experiment stages.

| Run | CSV file | Heating start (UTC) | Cooling start (UTC) | Observations / errors |
|-----|----------|---------------------|---------------------|-----------------------|
| 1   |          |                     |                     |                       |
| 2   |          |                     |                     |                       |
| 3   |          |                     |                     |                       |

Plot both temperatures against time, marking heating/cooling stages and missing
readings. Describe the observed delay, temperature difference and consistency
between runs. Any calculated delay must state how it was measured.

Conclude whether more experiments or a prediction model are justified.
These bench results do not establish prediction accuracy or performance in an ambulance.
