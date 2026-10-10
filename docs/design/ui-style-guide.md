# UI style guide

Author: Maryna Hordiienko

All mock-ups and the HTML prototype use the values below, so the screens look consistent.

## Colours

| Token | Hex | Use |
|---|---|---|
| `--navy` | `#16298A` | Brand, headings, primary buttons |
| `--ink` | `#1D2433` | Body text |
| `--muted` | `#5D6475` | Secondary text and labels |
| `--bg` | `#F5F5FA` | App background |
| `--green` / `--green-bg` | `#1E6B34` / `#E5F3E8` | Normal |
| `--amber` / `--amber-bg` | `#7A5600` / `#FFF3D1` | Warning |
| `--red` / `--red-bg` | `#A3222B` / `#FBE4E6` | Alert, sensor error, sign-in error |
| `--grey` / `--grey-bg` | `#4C5363` / `#ECEEF3` | Stale, not reporting, no data |

Colour is never the only signal: each status also has a symbol and a text label.

| Status | Symbol |
|---|---|
| Normal | ✓ |
| Warning | ! |
| Alert | ✕ |
| Sensor error | ⚠ |
| Stale | ⏱ |
| Not reporting | ⦸ |

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
