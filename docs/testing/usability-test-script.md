# Usability test script (end users)

Author: Maryna Hordiienko

`initial-test-plan.md` lists UX-03 with the precondition "Task script ready". This file is that task script: the step-by-step guide for the end-user tests UX-01, UX-03 and UX-05. Results are copied into the Execution record of `initial-test-plan.md`. Participants are paramedics where available; otherwise classmates act as proxy users and are recorded as proxies. Only synthetic data is used.

## Before the session (5 min)

1. Explain the purpose: "We are testing the app, not you. There are no wrong answers."
2. Ask for consent to take notes (see the observation sheet).
3. Ask the participant to think aloud.
4. Give the participant a phone or laptop with the prototype open on the sign-in page.

## Tasks

Do not help the participant during a task. If they are stuck for 2 minutes, mark the task as failed and move on.

| Task | Instruction to the participant | Success when the participant… | Target time | Plan ID |
|---|---|---|---|---|
| T1 | Sign in with the test account. | Reaches the current status screen. | 60 s | UX-03 |
| T2 | Tell me if the medicine box is OK right now. | Says the status (for example "Warning, 24.6°C"). | 15 s | UX-01, UX-03 |
| T3 | (Stale state shown) Is this temperature current? | Says the data is old / current conditions unknown. | 20 s | UX-05 |
| T4 | (Sensor error shown) What is the temperature now? | Says it is unknown because the sensor failed. | 20 s | UX-01, UX-05 |
| T5 | Find the highest temperature between 14:00 and 14:40 today. | Uses the filter and reads the value from the graph or table. | 90 s | UX-03 |
| T6 | Find a time when there was no data. | Points to the gap (14:26:30–14:29). | 60 s | UX-05 |
| T7 | Sign out. | Returns to the sign-in page. | 15 s | UX-03 |

## After the tasks (5 min)

1. What was the easiest part? What was the hardest part?
2. Was any message confusing?
3. Rate from 1 (very hard) to 5 (very easy): "It was easy to know if the box is OK."

## Success criteria

- Every participant distinguishes stale data from current Normal (T3).
- At least 80% of participants complete T1, T2, T5 and T7 without help.
- Average ease rating of at least 4 out of 5.
