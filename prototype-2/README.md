# TempSafe Figma prototype

[Play the prototype](https://www.figma.com/proto/oPwORgZUE7djuQHnbzekz6/TempSafe?node-id=0-2&page-id=0%3A1&scaling=min-zoom) · [Edit the design in Figma](https://www.figma.com/design/oPwORgZUE7djuQHnbzekz6/TempSafe) · [Download the local Figma file](TempSafe.fig)

The four screens use synthetic readings from 5–11 November 2026 for medication box TS-01.

| Screen          | What to try                                                                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Overview        | Change the review date to see temperature excursions and gaps alongside the temperature trend.                                          |
| Alerts          | Review the five latest events and their Open or Resolved status.                                                                        |
| Reading history | Choose the end date and a one-, two- or seven-day period. Review the hourly summary and preview the CSV export for the selected period. |
| Settings        | Follow the example limit change through review, cancellation or confirmation.                                                           |

CSV export and settings changes are simulated in Figma. Text and controls are editable layers. Charts are images. To
open an independent copy, import `TempSafe.fig` into Figma Design.

## Design references

The location, date, 24-hour clock and current, minimum and maximum readings
follow the structure of the Irish cool-box temperature record. Appendix V
also leaves missed measurements
blank. [HSE National Immunisation Office, cool-box guidance](https://healthservice.hse.ie/documents/8424/Guidelines_for_maintaining_the_vaccine_cold-chain_in_vaccine_cool_boxes_SOP.pdf)

The yellow and green palette and the short chequered strip draw on Irish
ambulance vehicle markings. The screen uses lemon yellow for the active
section and temperature summary, deep green for navigation and the normal
temperature trace, and pale red bands for excursions above or below the limits. The **10 November**
trace includes a synthetic low-temperature excursion.
[NASRA history of emergency medical services in Ireland](https://www.nasra.ie/index.php/information/members/201-history-of-ems-in-ireland)

Alert states pair a colour with an icon and a written label.
[NHS status tag guidance](https://service-manual.nhs.uk/design-system/components/tag/)
