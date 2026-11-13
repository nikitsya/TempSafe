# UI wording guide

Use short, plain English. Status needs a word and symbol as well as colour. Describe readings against
configured limits; do not label medicines “safe” or “unsafe”.

## Current application

Status words are short so they can be read at a glance. The main card shows the status word, temperature and time.
Explanations and limits sit behind **Details**. Missing or unreliable current values show **No temperature**; older
recorded values may appear in Details as **Last value**. See the [frontend guide](../../../frontend/README.md) for
implementation limits.

| Situation                 | Status word / heading  | Supporting text (Details unless stated)                |
|---------------------------|------------------------|--------------------------------------------------------|
| Normal                    | OK                     | In range                                               |
| Warning                   | WARNING                | Near the limit ({upper}°C)                             |
| High alert                | TOO HOT                | Above {upper}°C                                        |
| Low alert                 | TOO COLD               | {lower}°C or below                                     |
| Unread alert (dashboard)  | Alert: High temperature detected / Alert: Low temperature detected | {date}, {time} · {temperature}°C and a **View** button |
| Stale reading             | NO DATA                | No temperature (card); No reading for 90 s             |
| Sensor failure            | SENSOR FAULT           | No temperature (card); Sensor cannot measure           |
| Unreliable time           | UNKNOWN                | No temperature (card); Clock not reliable              |
| Device contact lost       | OFFLINE                | No temperature; Last contact {time} (card); Box not sending data |
| Device never connected    | NOT CONNECTED          | No temperature (card); Box never connected             |
| No access to the box      | No access              | Ask your admin for box TS-01.                          |
| Empty history period      | No readings in this period | Choose another period.                             |
| No readings               | No readings yet        | Check the box is on.                                   |
| Request failure           | Can't load             | Check your internet and refresh.                       |
| Loading                   | Loading…               | No extra explanation needed                            |
| Box clock not reliable    | {received time} (received) | Unknown when no receipt time exists                |

Details rows: **Status**, **Last measured**, **Last contact** (when the box reports contact) and **Limits**
(`0–25°C · warning 24°C`). Dates use the format **13 Nov 2026, 06:53**.

The dashboard has three framed buttons: **Graph**, **Last 100** and **Alerts**. They open History in that view.

History has two framed choosers. **Period**: Latest 100, 1 hour, Today, 24 hours or a date. **Show**: Alerts, Graph
or Readings, one view at a time. Reading statuses are **OK**, **Warning**, **Too hot**, **Too cold**, **Sensor fault**
and **Unknown**. The Alerts table has the columns Alert, Date (**5 Nov 2026**), Time, Length and Peak. The Length (est.)
column header marks every duration as an estimate (FR-13); **1+ min** means readings are missing, so it was at least that long. Opening the Alerts view or pressing **View** marks
the alert as viewed in this browser, and the dashboard banner disappears.

Sign-in validates empty fields and submits credentials to the backend. Current messages are:

| Situation                  | Message                                                                        |
|----------------------------|--------------------------------------------------------------------------------|
| Invalid credentials        | Sign-in failed. The email/username or password is incorrect. Please try again. |
| Missing or expired session | Please sign in to continue.                                                    |
| Confirmed sign-out         | You have signed out.                                                           |
| Sign-out failure           | We couldn’t confirm that you’ve signed out. Please try again.                  |

Sign out revokes the session. The confirmation is shown only after a 204 response;
a failed request leaves the user on the page with an error and a retry opportunity.

## Planned features

These messages are design targets for remaining interface features:

| Situation             | Proposed wording                                                      |
|-----------------------|-----------------------------------------------------------------------|
| Invalid history range | The start time must be before the end time.                           |
| Phone warning         | TempSafe: Box TS-01 WARNING — 24.6°C at 14:17. Open the app to check. |
| Phone alert           | TempSafe: Box TS-01 ALERT — above upper limit, 25.9°C at 14:31.       |

Phone notifications contain no account details and should open the authorised dashboard.
See the [planned Web Push flow](web-push-permission-flow.md).
