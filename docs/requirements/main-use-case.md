# Main Use Case — Reviewing a Temperature Excursion After Patient Care

## User persona

[Shannon Rice — Advanced Paramedic](user-persona.md).

## Goal

Check the current temperature inside the Controlled Drug Box and identify when the temperature crossed a configured
threshold, the highest or lowest temperature recorded, and how long the excursion lasted.

## Environment / context

The Controlled Drug Box is fixed inside an ambulance. The Advanced Paramedic is treating a patient and cannot
immediately respond to a temperature notification.

## Preconditions

- The system measures and records the temperature inside the box with timestamps.
- Temperature thresholds are configured.
- The application on the paramedic's phone has connectivity and permission to receive notifications.

## Trigger

The temperature inside the box rises above 25°C or reaches 0°C or below, according to the proposed prototype settings.
The low-temperature threshold is a project-defined freezing-risk alert, not a verified minimum storage temperature
for every medicine. Its adoption across the project is pending team agreement.

## Main flow

1. The system detects that the temperature has crossed a configured alert threshold.
2. The single-colour LED lights up and a notification is delivered to the application on the paramedic's phone.
   The buzzer sounds if implemented.
3. The paramedic continues treating the patient while the system continues recording temperature readings.
4. When available, the paramedic opens the application.
5. The paramedic checks the current temperature, status and timestamp of the latest reading.
6. The paramedic opens the temperature excursion details.
7. The application shows the start time, end time or an "Ongoing" label, the estimated duration, and the maximum
   temperature for a high-temperature excursion or minimum temperature for a low-temperature excursion.
8. The paramedic uses this information to take further action in accordance with the service's medicine-handling
   procedures.

## Expected outcome

The paramedic understands when the temperature inside the box crossed the configured threshold, how long the excursion
lasted, and how high or low the recorded temperature reached. Current readings, their freshness and the event history
are available in the application.

Duration is labelled as estimated. For an ongoing event, it is calculated up to the latest available observation.
Data gaps are clearly identified and are not treated as evidence of uninterrupted exposure. The system retains the
records and does not automatically determine whether medicines remain suitable for use.
