# Core Scenario Usability Test Results

## Test information

| Item | Details |
| --- | --- |
| Date | 5 November 2026 |
| Participants | Two proxy users, not paramedics |
| Device | Laptop |
| Interface | Working TempSafe website |
| Scenario | Review the current box status and an earlier temperature excursion after patient care |
| Script | [Usability Test Script](usability-test-script.md) |
| Observation template | [Usability Observation Sheet](usability-observation-sheet.md) |

Before the sessions, the facilitator warmed and cooled the SCD41 sensor to
prepare one event using real recorded readings. Both participants reviewed
the same event after the temperature returned to Normal. They did not see
the sensor being warmed or cooled.

The scenario described a notification arriving during patient care; the
test did not establish that a real phone notification was delivered.
Participants consented to written notes.

## Rating results

Participants rated each question from 1 to 5, where 1 was very difficult or
unclear and 5 was very easy or clear.

| Question | Participant 1 | Participant 2 |
| --- | ---: | ---: |
| 1. Understand current temperature status | 5 | 5 |
| 2. Understand current temperature display | 5 | 5 |
| 3. Identify an excursion while away | 1 | 1 |
| 4. Find previous temperature alerts | 5 | 5 |
| 5. Use the History page | 4 | 5 |
| 6. Understand event duration | 5 | 5 |
| 7. Identify the date and time of an excursion | 2 | 3 |
| 8. Understand peak temperature | 5 | 5 |
| 9. Navigate between Current Status and History | 5 | 5 |
| 10. Overall interface clarity | 5 | 4 |
| 11. Confidence completing the task | 5 | 5 |

## Findings and proposed changes

### Previous event on Current Status

Both participants understood the current temperature and Normal status.
However, the Current Status screen did not clearly communicate that an
earlier temperature excursion had occurred while the paramedic was away.
Both rated identifying an excursion while away 1 out of 5.

**Proposed change:** Show a visible recent or unreviewed alert and provide
a direct action to view the event.

### Date in History

Participants found the earlier event in History and understood its duration
and peak temperature. In the version tested, the event displayed a time but
not a date. Participants rated identifying the date and time 2 and 3 out of
5, respectively.

**Proposed change:** Display the date for each temperature event.

### Details section

Neither participant opened Details independently during the main tasks.
Afterwards, the facilitator asked about the section and the participants
opened it. Both said that information repeated the main screen and did not
find the section useful.

Participants understood the difference between **Measured** and
**Received**, but did not find both timestamps useful in the case shown,
where the times were almost the same.

**Proposed change:** Review the contents of Details and remove unnecessary
repetition. Consider where and when to show both timestamps: the difference
can matter when transmission is delayed.

## Scope

These findings describe two proxy-user sessions, not all paramedics. They
relate to the website version used on the test date; proposed changes are not
claims that the changes have been implemented. The test focused on the core
scenario rather than every application feature.
