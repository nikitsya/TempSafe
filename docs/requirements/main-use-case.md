# Main Use Case — Reviewing a Temperature Excursion After Patient Care

## User persona

[Shannon Rice — Advanced Paramedic](user-persona.md).

## Goal

Check the current temperature inside the Controlled Drug Box and review a completed high-temperature excursion,
including its start and end times, estimated duration and maximum recorded temperature.

## Environment / context

The Controlled Drug Box is fixed inside an ambulance parked outdoors on a hot day. Shannon is treating a patient
away from the ambulance and cannot immediately respond to a temperature notification. By the time she opens the
application, the temperature has returned to Normal, but the completed excursion remains available for review.

The values and times below are synthetic demonstration data for the Figma prototype and user testing. All displayed
times refer to the same day and use local time.

## Preconditions

- The system records valid temperature readings every 30 seconds, with no missing samples during this scenario.
- The upper alert threshold is 25°C; the early-warning threshold is 24°C.
- Shannon is signed in and authorised to view the Controlled Drug Box.
- The application on Shannon's phone has connectivity and permission to receive notifications.
- This demonstration uses the single-colour LED and phone notification; the optional buzzer is outside this walkthrough.

## Trigger

At 14:00, the first recorded temperature above 25°C is 26.2°C, triggering a high-temperature Alert.

## Main flow

1. At 14:00, the system records 26.2°C and changes the temperature status to Alert. The single-colour LED is lit.
2. Shannon's phone receives the notification: "TempSafe — High temperature alert. Controlled Drug Box: 26.2°C. Recorded
   at 14:00."
3. Shannon continues treating the patient. The system continues recording readings above 25°C through 14:19:30,
   reaching a maximum of 28.1°C at 14:10.
4. At 14:20, the system records 23.8°C, the first reading back below the upper limit. The excursion is marked Ended,
   the current status becomes Normal, and the LED turns off. The event remains in history.
5. At 14:25, Shannon opens the earlier notification. The application opens the Controlled Drug Box dashboard with
   current data.
6. The dashboard displays 23.5°C, Normal, and "Latest reading: 14:25". A visible card says
   "High-temperature event recorded" and provides a "View event" button.
7. Shannon selects "View event". The details screen shows Ended, start time 14:00, end time 14:20,
   "Estimated time above 25°C: 20 minutes", maximum temperature 28.1°C, and upper threshold 25°C.
   A temperature graph includes the 25°C threshold line.
8. Shannon uses these details to take further action in accordance with the service's medicine-handling procedures.

## Expected outcome

Shannon sees that the current temperature is 23.5°C and Normal, while recognising that an earlier high-temperature
excursion occurred. She identifies the recorded event interval as 14:00–14:20, its estimated duration as 20 minutes,
and its maximum temperature as 28.1°C. The completed event remains accessible even though the current status is Normal.

The demonstration estimates duration from the first above-limit observation to the first subsequent observation back
within the upper limit. Actual threshold-crossing times fall between samples, so the duration is explicitly labelled
as estimated. These are measurements of the temperature inside the box, not of the medicines themselves. The system
retains the records and does not automatically determine whether medicines remain suitable for use.
