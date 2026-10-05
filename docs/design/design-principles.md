Design principles

This document explains which Universal Design principle guides the Smart Box interface and how it affects our design decisions.

What is Universal Design?

Universal Design means designing a product so it can be used by as many people as possible, in as many situations as possible, without special adaptation. The 7 Principles of Universal Design were developed in 1997 at North Carolina State University and are promoted in Ireland by the National Disability Authority (NDA).

Key principle: Principle 4 – Perceptible Information

The design communicates necessary information effectively to the user, regardless of ambient conditions or the user's sensory abilities.

Why we chose it

Paramedics use Smart Box in changing and difficult conditions: bright sunlight, darkness, noise, rain and high stress. Their hands and attention are often busy with a patient. A temperature warning is only useful if it is noticed immediately and understood at a glance. For this reason, Principle 4 is the most important principle for our project.

How it affects our design decisions
Guideline	Design decision in Smart Box
4a. Use different modes for essential information	Every alert is shown in more than one way: colour, icon, text and sound or vibration.
4b. Provide adequate contrast	Text and key values meet WCAG AA contrast (at least 4.5:1). The dashboard works in bright light and in a dark vehicle.
4c. Maximise legibility	The current temperature is shown in large, clear numbers. Labels are short and use plain words.
4d. Differentiate elements in ways that can be described	Each status has its own name and icon: Normal, Warning, Out of range. Staff can say "the box is out of range" instead of "the box is red".
4e. Compatibility with assistive technology	We use semantic HTML, text alternatives for icons and correct labels, so screen readers can read the status.

Rule: colour is never the only way to show a problem.

Supporting principles
Principle 3 – Simple and Intuitive Use

The main screen shows only what staff need first: the current temperature, the status and the time of the last reading. The temperature history and settings are on separate screens. This keeps the interface easy to use when the user is tired or under pressure.

Principle 5 – Tolerance for Error

The system warns clearly when the temperature moves outside the configured range. Changing the allowed temperature range needs a confirmation step, so it cannot be changed by accident. The reading history cannot be deleted from the interface, so the record remains available for review.

Summary

Smart Box is designed so that a paramedic can understand the condition of the medicine box in a few seconds, in any environment. Principle 4 (Perceptible Information) is our key principle, supported by Principle 3 (Simple and Intuitive Use) and Principle 5 (Tolerance for Error).

Reference

National Disability Authority – The 7 Principles of Universal Design: https://universaldesign.ie/about-universal-design/the-7-principles-of-universal-design
