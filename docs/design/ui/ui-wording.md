# UI wording guide

Use short, plain English. Status needs a word and symbol as well as colour. Describe readings against
configured limits; do not label medicines "safe" or "unsafe". All text is in sentence case; status words are not
written in capitals.

## Statuses and messages

| Situation                                  | Status word / heading      | Supporting text                                 |
|--------------------------------------------|----------------------------|-------------------------------------------------|
| Normal                                     | Normal                     | Temperature in °C                               |
| Warning                                    | Warning                    | Temperature in °C and `for {n} min`             |
| Alert (too high or too low)                | Alert                      | Temperature in °C and `for {n} min`             |
| Old reading (nothing new for 90 s)         | Last reading               | Last temperature in grey                        |
| Sensor cannot measure                      | Sensor fault               | No temperature                                  |
| Box not sending data                       | Offline                    | Last temperature in grey, or No temperature     |
| Box never connected                        | Not connected              | No temperature                                  |
| Time or status cannot be worked out        | Unknown                    | No temperature                                  |
| Alert starts (pop-up and web notification) | Alert                      | `{current}°C · {n} min`, updated while it lasts |
| Alert ends (pop-up and web notification)   | Back in range              | `{current}°C`                                   |
| Sensor fault (pop-up and web notification) | Sensor fault               | No temperature                                  |
| Box offline (pop-up and web notification)  | Offline                    | `No data for {n} min`, updated while it lasts   |
| Box back (pop-up and web notification)     | Back online                | `{current}°C`                                   |
| No access to the box                       | No access                  | Ask your admin for access.                      |
| Empty period                               | No readings in this period | Choose another period.                          |
| No readings at all                         | No readings yet            | Check the box is on.                            |
| Request failure                            | Can't load                 | Check your internet and refresh.                |
| Loading                                    | Loading…                   | No extra text                                   |

## Header and menu

The header shows **TempSafe** and **Sign out**. The menu has four pages: **Dashboard**, **History**, **Alerts** and
**Settings**. The box name is not shown (there is one box).

## Dashboard

While an alert is on, a red banner on top says **Alert: High temperature detected** (or **Low**) with a **View**
button under the text that opens Alerts. The banner disappears when the alert ends.

Below it are four tiles:

- **Status**: Normal, Warning or Alert with the temperature; Warning and Alert also show `for 4 min`.
- **Today's range**: two labelled values, `Min 20.4°C` and `Max 26.9°C` (a minus sign is shown as −).
- **Alerts today**: the number, and `last at 16:59` or `none today`.
- **Last measured**: `17:04` and `5 s ago`; when the last reading is not from today, the date comes first
  (`16 Nov 2026 · 1 day 23 h ago`).

Then a **Last hour** chart (line coloured by status, dashed limit lines, time marks every 15 minutes, grey band for no
data, violet band for sensor fault, legend) and three framed buttons: **Day graph**, **All readings** (the readings table) and
**Alerts and issues**.

## History

**Period**: Today (default), 1 hour or a date from the last 30 days; History and Alerts share the chosen period in the
browser tab, and **Today** goes back to today. With **1 hour** and no readings the page says `No readings in the last 60
minutes` with the exact times. The calendar does not allow older dates.
The **←** and **→** buttons next to the date open the previous or next day (**→** stops at today).
All readings of the period are loaded, with no limit, so the graph, Readings and Issues always cover the full period.
**Show**: Graph or Readings.

- **Graph**: in its own frame titled **Temperature readings**, with the date (`14 Nov 2026`) in a box above it. There
  is no text on the graph itself. The °C scale shows numbers only (`30`, `28`, …). The line is coloured by status (green
  Normal, amber Warning, red Alert); the colour changes exactly where the line crosses a limit. The dotted amber
  line is where Warning starts and the dashed red line is the Maximum (and Minimum when shown). Violet band = sensor
  fault, grey band = no data or offline. The legend explains them with the values: Normal, Warning, Alert,
  `Warning from 24°C`, `Maximum 25°C`, Sensor fault, No data. On a phone the whole day fits the screen width. Under the graph:
  hours `8` to `18` for Today or a date (the window grows if there are readings earlier or later), and marks such as
  `15:35` for 1 hour.
- **Readings**: table with Date (`14 Nov 2026`), Time (`16:41:16`), °C and Status.
- **Download CSV** (next to Graph and Readings): saves every reading of the period as `tempsafe-2026-11-17.csv`
  with Date, Time, Temperature (°C) and Status, oldest first. It opens in Excel.

## Alerts

**Period**: Today (default), 1 hour or a date. **Show**: Status or Issues.

- **Status** (notification history, newest first): one row per change of status. Columns: **Status** (Alert,
  Warning, Normal, Sensor fault or No data, as a coloured dot and word), **Peak** (a dash for Sensor fault and No
  data), **How long** (or **Now**) and **Time** (`14:05 – 14:23`, or `since 14:05`). The date is shown once, in a box
  next to the table title (`17 Nov 2026`); a time on another day starts with the day (`16 Nov, 23:50`). **Now** appears
  only for today: a past day's last status ends at its last reading. When the box is offline or the sensor fails, only
  the No data or Sensor fault row shows **Now**. When readings stopped before the status changed, How long says
  `at least 1 h 45 min` (tooltip: Exact end unknown: readings stopped). Rows are lightly tinted with the status colour;
  Sensor fault is violet, so it is not confused with a red temperature Alert.
- **Issues**: **Sensor fault** (the box was online but the sensor could not measure) and **No data** (nothing was
  received: the box was offline, had no connection or readings were missing). Columns: **Problem**, **How long** and
  **Time**, newest first; the date is shown once next to the title, and a time on another day starts with the day
  (`16 Nov, 23:50 – 00:10`). An ongoing issue shows `since {time}` and **Now**. With no issues the page
  shows **✓ No issues**.

Durations: `at least …` means a sensor error or missing readings ended the row. Long durations show hours or days (up to 24
h: `3 h 20 min`; then `1 day 16 h`, `8 days`, `1 month 3 days`). Pop-ups, the Dashboard and Alerts use the same format.
A period that crosses midnight shows a date range (`4 – 6 Nov 2026`). If the
box clock was not set, the time is when the server received the reading. On phones each row becomes a card with
labels.

## Pop-ups and web notifications

When an alert starts and when it ends, every signed-in page shows a pop-up (bottom right, with a close button).
Alert or not is decided with the limits set in Settings. The alert pop-up keeps the current temperature and minutes
up to date. If the **Notifications** switch in Settings is on, the browser also shows a web notification with the
same text. Each start and end is announced once.

## Settings

| Situation          | Heading / text                                                                      | Notes                                                                                     |
|--------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| Notifications      | Notifications [On/Off switch]                                                       | Off: *Get a message from this browser when the box goes into Alert or back in range, even on another tab. Your browser will ask for permission when you turn this on.* On: *This browser shows a message when the box goes into Alert or back in range.* Blocked or unsupported: the switch is off and explains how to allow the site |
| Limits form        | Temperature limits: **Minimum**, **Warning from**, **Maximum**                      | No hints; current values are filled in                                                    |
| Rules              | Alert at or below Minimum or above Maximum; Warning from Warning from up to Maximum | FR-05                                                                                     |
| Confirm            | Change the limits?                                                                  | Now / New, with **Confirm** and **Cancel**                                                |
| Saved              | Saved                                                                               | The website uses these limits for new readings once the box updates.                      |
| Wrong order        | Must be higher than the minimum. / Must be higher than warning from.                | Shown under the field                                                                     |
| No limits selected | The form is filled in with the limits recorded with the latest reading              | If there are none: **No limits set yet.** and an empty form                               |

## Outside the box (outside sensor)

Shown only when the box sends outside readings. It is information, never a status, and is shown in blue.

| Place                 | Text                                                                                                               |
|-----------------------|--------------------------------------------------------------------------------------------------------------------|
| Dashboard tile        | **Outside the box** · `25.5°C` (only the temperature) |
| Tile, outside fault   | **Sensor fault** · No outside temperature                                                                          |
| Tile, old data        | Value in grey · `Last reading 20:46`                                                                               |
| Blue card (outside warm) | **Outside has reached 24°C and is rising** · The inside may warm up soon. Check where the box is kept. (inside already at Warning: Check where the box is kept.) |
| Forecast card         | **Warning in about 2 minutes** · Inside is warming fast. Check where the box is kept. · Estimate from the last 2 minutes. (`in about 1 minute`, `in less than a minute`) |
| Graph legend          | Outside the box (dashed blue line)                                                                                 |
| Readings column       | **Outside °C** (`25.5`, `Sensor fault` or `—`)                                                                     |
| CSV columns           | `Inside temperature (°C)`, `Outside temperature (°C)`                                                              |

See [outside-temperature-display.md](outside-temperature-display.md) for when the blue card shows and how the time is calculated.
