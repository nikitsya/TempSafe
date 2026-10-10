# UI wording guide

Author: Maryna Hordiienko

The paramedic must understand each message quickly, often under time pressure. Every message follows these rules:

- Say what happened in the heading and what it means for the user in the next line.
- Never present old or missing data as the current condition.
- Never use clinical words such as "safe" or "unsafe". The system compares readings with configured limits only.
- Use plain English, short sentences and no technical codes.

## Status messages

| State | Heading | Supporting text |
|---|---|---|
| Normal | NORMAL | Within configured limits (15–24°C) |
| Warning | WARNING | At or above early-warning threshold (24°C) |
| Alert (high) | ALERT | Above configured upper limit (25°C) |
| Alert (low) | ALERT | Below configured lower limit (15°C) |
| Stale | DATA STALE | Current conditions unknown. No new reading for {time} (limit 90 s). |
| Sensor failure | SENSOR ERROR | Latest reading failed at {time}. Temperature is unknown. |
| No contact | NOT REPORTING | No contact from the device for {time}. |
| Network failure | Unable to refresh | Check your internet connection. Information below is from {time}. |
| No data | No observations yet | This box has not sent any readings. Current conditions are unknown. |
| No access | No assigned box available | Your account is not assigned to a box. Ask your administrator to give you access. |

## Sign-in messages

| Situation | Message |
|---|---|
| Wrong username or password | Sign-in failed. The email/username or password is incorrect. Please try again. |
| Empty field | Enter your email or username. / Enter your password. |
| Session expired | Your session has ended. Please sign in again. |

## History messages

| Situation | Message |
|---|---|
| Empty range | No observations found for this period. |
| From after To | The start time must be before the end time. |
| Gap in data | No data (device offline) |

## Phone notifications (Web Push)

| Event | Notification text |
|---|---|
| Warning | TempSafe: Box TS-01 WARNING – 24.6°C at 14:17. Open the app to check. |
| Alert | TempSafe: Box TS-01 ALERT – above upper limit, 25.9°C at 14:31. |
| Not reporting | TempSafe: Box TS-01 has not reported for 3 min. |

Notification text contains no account details. Tapping it opens the signed-in dashboard.
