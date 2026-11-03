# Usability test script (end users)

`initial-test-plan.md` lists UX-03 with the precondition "Task script ready". This file is that task script: the
step-by-step guide for the end-user tests UX-01, UX-03 and UX-05. Results are copied into the Execution record of
`initial-test-plan.md`. Only synthetic data is used.

## Prototype used

The tests use the clickable UI prototype, because it can show every status screen and the history page on request:

- Prototype: open `prototype/ui/login.html` locally or use the link in
  the [prototype guide](../../prototype/ui/README.md).
- Test account: `paramedic` / `demo`
- Box TS-01, legacy Demo v1: Lower 15°C · Warning 24°C · Upper 25°C (synthetic data).
  This differs from the application's 0/24/25°C profile; these tasks apply only to the HTML prototype.

The facilitator switches the dashboard state by opening `dashboard.html?state=...` before a task. The participant does
not use the "Prototype states" links. These links and the "synthetic data" note on the history page label the
prototype as a demonstration.

| Task | Screen prepared by the facilitator   |
|------|--------------------------------------|
| T1   | `login.html`                         |
| T2   | `dashboard.html?state=normal`        |
| T3   | `dashboard.html?state=normal`        |
| T4   | `history.html` (default 14:00–14:40) |
| T5   | `dashboard.html?state=stale`         |
| T6   | `dashboard.html?state=sensor`        |
| T7   | Any page while signed in             |

## Participants

Participants are paramedics where available. Otherwise, classmates act as proxy users and are recorded as proxies on
the observation sheet. Team members who built the prototype do not take part as participants.

## Before the session (5 min)

1. Read the consent wording and tick the consent box on the observation sheet:

   > We are testing the TempSafe prototype, not you. There are no wrong answers. The session takes about 15 minutes.
   > We will take written notes about what you do and say. We will not record audio or video and will not store your
   > name or any personal data. The notes are only used for this college project. You can skip a task or stop at any
   > time without giving a reason. Are you happy to take part?

2. Ask the participant to think aloud.
3. Read the core scenario:

   > You are a paramedic. You have just finished treating a patient away from the ambulance. You want to check the
   > medicine box: what its condition is now, and whether anything happened while you were away.

4. Give the participant a phone or laptop with the prototype open on the sign-in page.

## Tasks

Read each instruction exactly as written. Do not use screen names, button labels or status words in the instruction.
Do not help the participant during a task. If they are stuck for 2 minutes, mark the task as failed and move on.

| Task | Instruction to the participant                                                                                       | Success when the participant…                                                                                                                                                                                 | Target time | Plan ID      |
|------|----------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|--------------|
| T1   | Sign in with the test account.                                                                                       | Reaches the current status screen.                                                                                                                                                                            | 60 s        | UX-03        |
| T2   | Tell me the condition of the medicine box right now.                                                                 | Says the current status and value (Normal, 21.8°C, observed 14:20).                                                                                                                                           | 15 s        | UX-01, UX-03 |
| T3   | Did the temperature go above its upper limit at any time earlier today? If it did, tell me when and how high it got. | Finds the earlier period above 25°C (about 14:10–14:16) and the highest value (26.0°C), **and** says that the excursion is over and the box is no longer above 25°C. Does not mix up past and current status. | 90 s        | UX-03        |
| T4   | Find a time when there was no data.                                                                                  | Points to the gap (14:26:30–14:29).                                                                                                                                                                           | 60 s        | UX-05        |
| T5   | Is the temperature shown here the current temperature?                                                               | Says the data is stale and current conditions are unknown; the 22.8°C reading is from 14:12:05 and is historical.                                                                                             | 20 s        | UX-05        |
| T6   | What is the temperature in the box now?                                                                              | Says it is unknown because the sensor failed. Does not read it as 0°C or Normal.                                                                                                                              | 20 s        | UX-01, UX-05 |
| T7   | Sign out.                                                                                                            | Returns to the sign-in page.                                                                                                                                                                                  | 15 s        | UX-03        |

After each task, record completion, assistance, time, difficulties and quotes on the observation sheet.

Note: signing in and the "Back to current status" link open the dashboard in its default WARNING state. If the
participant returns to the dashboard during T3, accept WARNING as the current status; the key point is that the
earlier excursion above 25°C has ended.

## After the tasks (5 min)

1. What was the easiest part? What was the hardest part?
2. Was any message confusing?
3. Was it clear what the condition is now and what happened earlier?
4. Rate from 1 (very hard) to 5 (very easy): "It was easy to understand the box status."

## Success criteria

- Every participant distinguishes the current status from the earlier excursion (T3).
- Every participant distinguishes stale data and sensor errors from current Normal (T5, T6).
- At least 80% of participants complete T1, T2, T4 and T7 without help.
- Average ease rating of at least 4 out of 5.

## Team walkthrough (before the first session)

One team member runs every task on the prepared prototype and confirms it can be completed.

| Task | Screen opens as listed above | Task can be completed | Notes                                                                                         |
|------|------------------------------|-----------------------|-----------------------------------------------------------------------------------------------|
| T1   | ✅                           | ✅                    | Sign-in opens the dashboard in the default WARNING state                                      |
| T2   | ✅                           | ✅                    | NORMAL, 21.8°C, observed 14:20:00                                                             |
| T3   | ✅                           | ✅                    | "View temperature history": Alert rows 14:10:00–14:16:00, max 26.0°C; back link opens WARNING |
| T4   | ✅                           | ✅                    | Missing (device offline) 14:26:30–14:29:00 in graph and table                                 |
| T5   | ✅                           | ✅                    | DATA STALE, 22.8°C recorded 14:12:05 labelled historical                                      |
| T6   | ✅                           | ✅                    | SENSOR ERROR, "Temperature is unknown", not shown as 0°C or Normal                            |
| T7   | ✅                           | ✅                    | "Sign out" on the dashboard returns to the sign-in page (history page has no sign-out)        |

**Walkthrough done by:** Maryna Hordiienko **Date:** 2 November 2026
