# UI style guide

These values apply to the original UI mock-ups and HTML prototype. The later
[core scenario mock-ups](core-scenario-mockups.md) document their own visual style.

## Web application (from Sprint 9)

The web application uses a teal medical palette. Status colours below are unchanged. White text is only placed on
`--teal` or darker (4.9:1). `--teal-bright` is decoration only (top stripes and frames), never text.

| Token           | Hex       | Use                                                  |
|-----------------|-----------|------------------------------------------------------|
| `--teal`        | `#0E7F77` | Brand, navigation bar, buttons, button borders       |
| `--teal-dark`   | `#0A625C` | Active tab, headings and labels on light backgrounds |
| `--teal-bright` | `#13B0A5` | Decorative stripes only                              |
| `--mint`        | `#E8F6F4` | Table headers, light panels                          |
| `--bg`          | `#F3F4F4` | Page background                                      |
| `--focus`       | `#1D2433` | 3 px focus outline (white inside the navigation bar) |

- Status word 32 px and temperature 64 px, weight 800. Buttons and section titles in upper case, weight 800.
- Content is grouped in framed panels: Period and Show on History; Graph, Last 100 and Alerts on the dashboard.
- Touch targets are at least 44 px high; main buttons and tabs are 52 px.
- Status symbols: OK ✓, Warning !, Too hot / Too cold ✕, Sensor fault ⚠, No data ⏱, Offline and Not connected ⦸.

## Original prototype colours

| Token                    | Hex                   | Use                                |
|--------------------------|-----------------------|------------------------------------|
| `--navy`                 | `#16298A`             | Brand, headings, primary buttons   |
| `--ink`                  | `#1D2433`             | Body text                          |
| `--muted`                | `#5D6475`             | Secondary text and labels          |
| `--bg`                   | `#F5F5FA`             | App background                     |
| `--green` / `--green-bg` | `#1E6B34` / `#E5F3E8` | Normal                             |
| `--amber` / `--amber-bg` | `#7A5600` / `#FFF3D1` | Warning                            |
| `--red` / `--red-bg`     | `#A3222B` / `#FBE4E6` | Alert, sensor error, sign-in error |
| `--grey` / `--grey-bg`   | `#4C5363` / `#ECEEF3` | Stale, not reporting, no data      |

Colour is never the only signal: each status also has a symbol and a text label.

| Status        | Symbol |
|---------------|--------|
| Normal        | ✓     |
| Warning       | !      |
| Alert         | ✕     |
| Sensor error  | ⚠     |
| Stale         | ⏱      |
| Not reporting | ⦸      |

## Typography

- Font: Inter, with the system sans-serif font as fallback.
- Temperature value: 56 px, weight 800.
- Status heading: 26 px, weight 800, upper case.
- Body text: 14–16 px; text is never smaller than 12 px.

## Layout and controls

- Mobile first: one column, maximum width 420 px; history uses a wider layout on desktop.
- Primary buttons span the full width and are at least 48 px high.
- Cards have 18 px rounded corners and a light border.
- The focused element has a 3 px visible outline.
