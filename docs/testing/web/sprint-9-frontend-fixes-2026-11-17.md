# TempSafe · Front-end fixes after testing · 17 November 2026

This report answers the [manual front-end test of 14 November](sprint-9-frontend-test-2026-11-14.md). For each
finding it says what I changed and how I checked it. I retested on the `feature/sprint-9-frontend-musts` branch
locally with box TS-01, using the test reading sender (`send_test_readings.py --backfill 1500`, then `--fast`).

## Fixed

| Finding (14 November)                                                                                    | What I changed                                                                                                                                                                                                         | How I checked it                                                                                                      |
|----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| The graph and Issues used only the latest 1,000 readings, so the morning was shaded grey as **No data**. | History, Issues, Readings and the Dashboard tiles (**Today's range**, **Alerts today**) now load every reading of the chosen day, page by page, with no limit. The message *Showing the latest 1000 readings* is gone. | Sent 1,500 readings over about 12.5 hours. The graph showed all of them; grey appeared only before the first reading. |
| When the box was offline, two rows said **Now** (**Normal · Now** and **No data · Now**).                | Only the ongoing **No data** or **Sensor fault** row shows **Now**, and it is listed first. The last temperature row ends at the last reading, for example **Normal 3+ min**.                                          | Stopped the sender for two minutes and opened **Alerts → Status**.                                                    |
| The line turned red at about 20 °C, at the peak reading, not at the limit.                               | The line now changes colour exactly where it crosses a limit: amber at **Warning from**, red above **Maximum** or at **Minimum**. Same on History and on the Dashboard **Last hour** chart.                            | Checked the History graph for today: colours change on the dashed limit lines.                                        |
| The date picker allowed dates back to 1968.                                                              | The calendar allows only the last 30 days. A typed older date shows a message and is not loaded.                                                                                                                       | Opened **History → Date** and tried an older date.                                                                    |
| Settings showed **No limits set yet** although the readings had limits.                                  | When no configuration is selected for the box, the form is filled in with the limits from the latest reading. Saving still creates the configuration.                                                                  | Opened **Settings** and saved new limits.                                                                             |
| Long durations were shown in minutes only (for example **2422 min** in the alert pop-up).                | One readable format everywhere: minutes, hours up to 24 h, then days and months (**1 day 16 h**, **8 days**, **1 month 3 days**). Used in pop-ups, the Dashboard and Alerts.                                           | Checked the alert pop-up and **How long** in **Alerts → Status**.                                                     |
| The same date was repeated in every row of **Notification history**.                                     | The date is shown once, in a box next to the table title, as on the graph. A row that started on an earlier day shows **from 16 Nov**. The same in **Issues**, which keeps its Time column.                            | Opened **Alerts → Status** and **Issues** for today and for an earlier date.                                          |
| Moving between days meant opening the calendar each time.                                                | **←** and **→** buttons next to the date open the previous or next day. **→** stops at today and **←** at 30 days ago.                                                                                                 | Pressed **←** and **→** on History and Alerts.                                                                        |
| No way to look at all the original readings of a day outside the site.                                   | **Download CSV** on History saves every reading of the chosen period (Date, Time, Temperature, Status), which opens in Excel.                                                                                          | Downloaded the file for today and opened it in Excel.                                                                 |

I also updated [ui-wording.md](../../design/ui/ui-wording.md) to match these changes.

## Not changed, and why

| Suggestion                                  | Decision                                                                                             |
|---------------------------------------------|------------------------------------------------------------------------------------------------------|
| Rename **Issues** to **Data issues**        | Kept **Issues** for now; open to the team's opinion.                                                 |
| Show Warning and Alert as background bands  | Kept the coloured line; it now changes colour exactly at the limits, which answers the main concern. |
| Browser (system) notification not confirmed | Needs a check with the browser's notification permission allowed.                                    |

## For the backend

- **TS-01** has no row selected in `box_configuration`, so `GET /configuration` returns 404. The front end now works
  around it, but the box should have its configuration set.
- The readings API returns at most 100 readings per request (`le=100`). With no limit on the front end, a busy day
  needs many requests; a higher maximum would make History load faster.
