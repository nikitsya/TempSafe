# Design principles

This document explains which Universal Design principle guides the Smart Box interface and how it affects our design
decisions.

## What is Universal Design?

Universal Design means designing a product so it can be used by as many people as possible, in as many situations as
possible, without special adaptation. The 7 Principles of Universal Design were developed in 1997 at North Carolina
State University and are promoted in Ireland by the National Disability Authority (NDA).

## Key principle: Principle 4 – Perceptible Information

> *The design communicates necessary information effectively to the user, regardless of ambient conditions or the user's
sensory abilities.*

### Why we chose it

Paramedics use Smart Box in changing and difficult conditions: bright sunlight, darkness, noise, rain and high stress.
Their hands and attention are often busy with a patient. A temperature warning is only useful if it is noticed
immediately and understood at a glance. For this reason, Principle 4 is the most important principle for our project.

### How it affects our design decisions

| Guideline                                                | Design decision in Smart Box                                                                                                                           |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| 4a. Use different modes for essential information        | Every alert is shown in more than one way: colour, icon, text and sound or vibration.                                                                  |
| 4b. Provide adequate contrast                            | Text and key values meet WCAG AA contrast (at least 4.5:1). The dashboard works in bright light and in a dark vehicle.                                 |
| 4c. Maximise legibility                                  | The current temperature is shown in large, clear numbers. Labels are short and use plain words.                                                        |
| 4d. Differentiate elements in ways that can be described | Each status has its own name and icon: **Normal**, **Warning**, **Out of range**. Staff can say "the box is out of range" instead of "the box is red". |
| 4e. Compatibility with assistive technology              | We use semantic HTML, text alternatives for icons and correct labels, so screen readers can read the status.                                           |

**Rule:** colour is never the only way to show a problem.

### Example use case: temperature alert during a call

|               |                                                                                                                                                                             |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Actor**     | Paramedic                                                                                                                                                                   |
| **Goal**      | Notice quickly that the medicine box is outside its safe temperature range.                                                                                                 |
| **Situation** | The paramedic is treating a patient outdoors on a hot day. The box has been in direct sunlight. The paramedic is busy, under stress and cannot look at the screen for long. |
| **Trigger**   | The temperature inside the box rises above the configured upper limit.                                                                                                      |

**Main flow**

1. The sensor records a reading above the limit.
2. The system changes the box status to **Out of range**.
3. The dashboard shows the alert in several ways at the same time: red colour, warning icon, the text "Out of range",
   and a sound or vibration on the device.
4. The paramedic notices the alert without reading long text.
5. When there is time, the paramedic opens the dashboard and sees the current temperature in large numbers and the time
   the problem started.
6. The paramedic checks the box and follows the service's procedures.
7. The reading history keeps the record for later review.

**How Principle 4 supports this use case**

- If the alert used colour only, the paramedic could miss it in bright sunlight or if they have a colour vision
  deficiency. Icon, text and sound make sure the message gets through (4a).
- High contrast and large numbers make the temperature readable outdoors and in a dark vehicle (4b, 4c).
- A clear status name, "Out of range", lets the paramedic tell a colleague exactly what is wrong (4d).

## Supporting principles

### Principle 3 – Simple and Intuitive Use

The main screen shows only what staff need first: the current temperature, the status and the time of the last reading.
The temperature history and settings are on separate screens. This keeps the interface easy to use when the user is
tired or under pressure.

### Principle 5 – Tolerance for Error

The system warns clearly when the temperature moves outside the configured range. Changing the allowed temperature range
needs a confirmation step, so it cannot be changed by accident. The reading history cannot be deleted from the
interface, so the record remains available for review.

## Summary

Smart Box is designed so that a paramedic can understand the condition of the medicine box in a few seconds, in any
environment. Principle 4 (Perceptible Information) is our key principle, supported by Principle 3 (Simple and Intuitive
Use) and Principle 5 (Tolerance for Error).

## Reference

National Disability Authority – The 7 Principles of Universal
Design: https://universaldesign.ie/about-universal-design/the-7-principles-of-universal-design
