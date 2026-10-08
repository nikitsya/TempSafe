# Smart Box / TempSafe - MoSCoW Feature Prioritisation

**Date:** 8 October 2026

**Status:** Draft for group review

## Decision rules

- **Must Have:** without this feature, the core monitoring journey is incomplete or gives misleading information.
- **Should Have:** valuable for the user, but the core journey has an acceptable temporary alternative.
- **Could Have:** an enhancement to consider after the essential features are implemented and tested.
- **Won't Have This Time:** excluded from this release to keep the prototype achievable.

The priorities below reflect FR-01 to FR-15 in the [functional requirements](functional-requirements.md), including the
clarified single-colour LED, Must Have phone notifications and Should Have buzzer. They describe planned functionality,
not completed implementation.

## Universal Design justification

The selected principles are documented in [design principles](../design/design-principles.md):

- **P3 - Simple and Intuitive Use:** keep the main journey clear and reduce unnecessary interaction.
- **P4 - Perceptible Information:** communicate status through readable text, symbols and colour; distinguish current,
  stale and missing information.
- **P5 - Tolerance for Error:** make faults visible and prevent loss, duplication or misleading interpretation of
  records.

Accessibility is part of the essential interface, rather than an optional feature. Keyboard access, clear labels,
readable contrast, warnings that do not rely on colour alone and a table alternative to the graph apply to the Must Have
screens. Security and storage features also have technical justifications; their priority does not depend solely on
Universal Design.

## Must Have

| ID    | Feature                                        | Why it is essential                                                                                                                                                       | UX / Universal Design justification                                                                                                                                                                                  |
|-------|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-01 | Sign in and sign out                           | Establish an authorised user session before accessing box data.                                                                                                           | P3: clear login, failure and logout states support a predictable journey.                                                                                                                                            |
| FR-02 | Restrict access to the assigned prototype box  | Multiple assigned users share the single prototype box; unassigned users are denied through both the interface and API.                                                   | P3/P5: a clear shared-box identity reduces confusion; permission enforcement prevents inappropriate access.                                                                                                          |
| FR-03 | Measure and record internal temperature        | Temperature monitoring is the purpose of the prototype; readings need identity, time and quality information.                                                             | P5: a failed sensor read must not become a plausible temperature value.                                                                                                                                              |
| FR-04 | Show the latest temperature and its freshness  | A value without its age can mislead the user about the current condition.                                                                                                 | P3/P4: show value, units, observation time and explicit unknown, stale or sensor-error states.                                                                                                                       |
| FR-05 | Classify readings against a configured profile | Users need to distinguish Normal, early Warning and Alert against the configured profile.                                                                                 | P4/P5: use named states and symbols; an invalid reading must never be labelled normal.                                                                                                                               |
| FR-06 | Provide a local LED warning                    | Local feedback must continue when the network is unavailable.                                                                                                             | P4/P5: use a single-colour LED on for Warning/Alert and a distinct blink pattern for sensor failure; the dashboard also uses text and symbols. An unlit LED is not proof of working power or acceptable temperature. |
| FR-07 | Display temperature history                    | A current reading cannot explain what happened earlier.                                                                                                                   | P4/P5: provide a graph and readable table, with visible gaps and original observation times.                                                                                                                         |
| FR-08 | Identify loss of device contact                | The user must be able to distinguish missing communication from valid current monitoring.                                                                                 | P4/P5: explicitly show not-reporting and never-connected states and last contact time.                                                                                                                               |
| FR-09 | Buffer readings while offline                  | Intermittent connectivity must not immediately erase observation history.                                                                                                 | P5: retain at least 24 hours of sample attempts through a normal restart; show limitations rather than implying uninterrupted monitoring.                                                                            |
| FR-10 | Handle duplicate and delayed uploads           | Reconnection must not duplicate records or replace the current state with older data.                                                                                     | P5: preserve trustworthy history and avoid presenting a delayed historical warning as a current event.                                                                                                               |
| FR-14 | Send phone notifications                       | Staff away from the box need a remote Warning or Alert with connectivity and permission. Define and test the delivery channel, recipients and repeated-state suppression. | P4/P5: clear box identity, reading and time; avoid misleading delayed alerts and expose delivery failures.                                                                                                           |

Early Warning is part of FR-05 and FR-06, not an optional enhancement. The physical LED does not distinguish states by
colour; the application uses green, amber and red with labels and symbols.

## Should Have

| ID    | Feature                             | Why it is valuable                                                                     | Temporary alternative and UD justification                                                                                                                           |
|-------|-------------------------------------|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-11 | Refresh the dashboard automatically | Reduce repeated interaction while viewing status.                                      | A clearly labelled manual refresh can support the baseline journey. P3: automatic refresh reduces effort, with refresh failures visible.                             |
| FR-12 | Record review of a flagged sample   | Help users record that a flagged observation has been reviewed.                        | The user can inspect history without recording acknowledgement. P3/P5: distinguish reviewed from resolved; acknowledgement must not remove an ongoing warning.       |
| FR-13 | Estimate observed excursion periods | Summarise the timing and maximum temperature of consecutive out-of-range observations. | Users can inspect timestamped history first. P3/P5: summaries aid interpretation, but durations must be labelled estimated and broken by missing or invalid samples. |
| FR-15 | Provide an audible buzzer alert     | Add local audible feedback on Alert when available.                                    | P4: complement LED and application information. Visual feedback remains the temporary alternative; a silence control must not clear the warning.                     |

## Could Have

No separate Could Have feature is currently selected. Phone notifications are Must Have and the buzzer is Should Have;
optional features should not be invented just to fill this category.

## Won't Have This Time

| Feature                                                                              | Reason for exclusion                                                                            |
|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Automatic cooling or temperature regulation                                          | Monitoring is the core goal; active regulation introduces additional hardware and control work. |
| GPS tracking and box-opening detection                                               | These do not support the selected temperature-monitoring journey directly.                      |
| Humidity, weight measurement and a second sensor for external-temperature comparison | Separate research scope; one internal sensor is sufficient for the proposed baseline.           |
| Integration with ambulance-service systems or ePCR                                   | Requires external access and integration beyond the bench prototype.                            |
| Patient records, medication administration and controlled-drug accounting            | Outside the agreed monitoring scope.                                                            |
| Automated clinical decisions about medicine use or disposal                          | The prototype reports observations; staff follow their service's procedures.                    |
| Clinical deployment or testing with real medicines                                   | The assessed prototype is limited to demonstration and bench testing.                           |

## Confirmed direction and remaining implementation choices

- One internal temperature sensor and one single-colour LED; no RGB LED promise.
- Phone notifications are Must Have. Select and test the delivery channel and permission handling before implementation
  is considered complete.
- The buzzer is Should Have; select the part, sound pattern and silence control if implemented.
- Humidity and CO₂ reporting are outside this release, even though the SCD-41 can measure both.
- Demo upper-temperature settings use 24°C for Warning and above 25°C for Alert; the profile also needs a configured
  lower limit. These are prototype settings, not a universal medicine storage range.
- Record the clarified priorities and any subsequent group decisions in Scrumwise. This document does not claim that a
  group meeting or approval has occurred.

## Short version for the elevator pitch

> Our Must Have features provide internal temperature monitoring, a single-colour local warning LED, phone notifications
> with connectivity, authorised access and reliable history. The application combines Normal, Warning and Alert colours
> with text and symbols, following Perceptible Information. Fault and offline handling support Tolerance for Error. A
> buzzer, automatic refresh, review acknowledgement and estimated excursion summaries are Should Have improvements.
> Humidity, weight, tracking and cooling are outside this release.
