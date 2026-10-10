# Accessibility acceptance criteria

Author: Maryna Hordiienko

These criteria turn Principle 4 (Perceptible Information) from [design-principles.md](design-principles.md) and WCAG 2.2 level AA into checks for each screen. A screen is accepted only when all its criteria pass. BT IDs refer to the automated browser test plan (`docs/testing/browser-test-plan.md`); UX IDs refer to the manual tests in `docs/testing/initial-test-plan.md`.

| ID | Criterion | How it is checked | Test |
|---|---|---|---|
| AC-01 | Every status uses text and a symbol as well as colour. | Inspect each state in greyscale. | BT-05 |
| AC-02 | Text contrast is at least 4.5:1; large text and icons at least 3:1. | Contrast checker on each colour pair. | BT-12, UX-02 |
| AC-03 | All features work with the keyboard only (Tab, Shift+Tab, Enter, Space). | Complete sign-in and history filter without a mouse. | BT-08, UX-04 |
| AC-04 | The focused element always has a visible outline. | Tab through every screen. | BT-08, UX-04 |
| AC-05 | Every form field has a visible label linked to the input. | Check `label for` / `id` pairs. | BT-01 |
| AC-06 | Status changes are announced to screen readers. | The status card uses `role="status"`; Alert and errors use `role="alert"`. | BT-05 |
| AC-07 | The graph has an equivalent data table. | The history table lists the same readings as the graph. | BT-10, UX-04 |
| AC-08 | Touch targets are at least 44 × 44 px. | Measure buttons in the browser tools. | BT-12, UX-02 |
| AC-09 | Pages work at 200% zoom and 320 px width without horizontal scrolling. | Resize the browser window. | BT-12, UX-02 |
| AC-10 | Error messages say what went wrong and how to fix it. | Review against `ui-wording.md`. | BT-02, BT-09 |
| AC-11 | Old or missing data is never shown as the current Normal state. | Stale, sensor error and offline states. | BT-06 |
| AC-12 | Time is shown with a clock time and an age (for example "14:17:30 · 12 s ago"). | Inspect the status card. | BT-04 |
