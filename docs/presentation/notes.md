# TempSafe Presentation

Presentation files for the TempSafe application, developed by team Smart Box.

## Agreed hardware and feature direction

- Must Have: one internal SCD-41 temperature sensor, one single-colour warning LED, phone notifications with
  connectivity
  and permission, and the web application with accessible status and history.
- The physical LED lights for Warning or Alert; it does not change colour. A distinct blink pattern indicates sensor
  failure.
- Green, amber and red refer to application states, supported by text and symbols.
- Should Have: a buzzer and estimated excursion summaries; these are planned enhancements rather than guaranteed
  baseline features.
- Humidity reporting and additional sensors are outside this release.
- The phone notification channel and configured lower temperature limit still need to be selected and tested.

Slide mock-ups are illustrative sample data. If a mock-up shows an exposure timer or start/end/maximum summary, it
depicts a Should Have enhancement. A phone image does not imply a separate native mobile application; the planned user
interface is web-based.

## Physical prototype scope

This release contains one physical prototype box with one box ID. Multiple authorised users may be assigned to that same
box. Permission tests use assigned and unassigned users against it; no second physical box is required. Box IDs and
plural database tables allow future expansion without promising additional hardware for this release.
