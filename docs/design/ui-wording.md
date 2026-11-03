# UI wording guide

Use short, plain English. Status needs a word and symbol as well as colour. Describe readings against
configured limits; do not label medicines “safe” or “unsafe”.

## Current application

The main card shows status, temperature and observation time. Explanations and limits sit behind **Details**. Missing or
unreliable current values show **Temperature unknown**; older recorded values
may appear in Details. See the [frontend guide](../../frontend/README.md) for implementation limits.

| Situation                 | Heading or label       | Supporting text                                                 |
|---------------------------|------------------------|-----------------------------------------------------------------|
| Normal                    | NORMAL                 | Within limits (Details)                                         |
| Warning                   | WARNING                | Close to the upper limit ({upper}°C) (Details)                  |
| High alert                | ALERT                  | Above the upper limit ({upper}°C) (Details)                     |
| Stale reading             | NO NEW DATA            | Temperature unknown; No new reading for over 90 s (Details)     |
| Sensor failure            | SENSOR ERROR           | Temperature unknown; The sensor could not measure (Details)     |
| Unreliable time           | UNKNOWN                | Temperature unknown; Measurement time is not reliable (Details) |
| No readings               | No readings yet        | Check that the box is on and connected.                         |
| Dashboard request failure | Can't load temperature | Check your internet and refresh.                                |
| History request failure   | Can't load history     | Check your internet and refresh.                                |
| Unknown history box       | Box not found          | Ask your administrator to check the box.                        |
| Loading                   | Loading…               | No extra explanation needed                                     |
| Missing history timestamp | Time unknown           | Show receipt time separately when available                     |

The low-alert explanation should be **At or below the lower limit ({lower}°C)** to match the API's
inclusive lower boundary. The current dashboard wording at equality remains a known defect.

Sign-in currently checks empty fields and explains that authentication is not available. The Sign out
link only returns to the sign-in page.

## Planned features

These messages are design targets, not working authentication, contact detection or notification features:

| Situation             | Proposed wording                                                      |
|-----------------------|-----------------------------------------------------------------------|
| Device contact lost   | NO CONNECTION — The box is not sending data.                          |
| No access             | No assigned box available. Ask your administrator for access.         |
| Invalid credentials   | Sign-in failed. The email/username or password is incorrect.          |
| Session expired       | Your session has ended. Please sign in again.                         |
| Invalid history range | The start time must be before the end time.                           |
| Empty history range   | No observations found for this period.                                |
| Phone warning         | TempSafe: Box TS-01 WARNING — 24.6°C at 14:17. Open the app to check. |
| Phone alert           | TempSafe: Box TS-01 ALERT — above upper limit, 25.9°C at 14:31.       |

Phone notifications contain no account details and should open the authorised dashboard.
See the [planned Web Push flow](web-push-permission-flow.md).
