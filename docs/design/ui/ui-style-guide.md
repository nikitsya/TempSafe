# UI style guide

These values apply to the original UI mock-ups and HTML prototype. The later
[core scenario mock-ups](core-scenario-mockups.md) document their own visual style.

## Web application (from Sprint 9)

Clinical and calm, easy to read at a glance in an ambulance. A navy frame, white cards on a cool grey page, one
accent blue for actions; green, amber and red are used only for status. All text pairs meet WCAG AA.

| Token        | Hex       | Use                                              |
|--------------|-----------|--------------------------------------------------|
| `--navy`     | `#14233F` | Header and menu, main text                       |
| `--accent`   | `#1E5AA8` | Buttons, links, selected tab and focus outline   |
| `--page`     | `#F4F6F9` | Page background                                  |
| `--line`     | `#DDE3EB` | Card borders and table lines                     |
| `--muted`    | `#56647B` | Labels and secondary text                        |
| `--normal`   | `#1B7A43` | Normal                                           |
| `--warning`  | `#8A5800` | Warning (lines `#C48A12`)                        |
| `--alert`    | `#B42318` | Alert                                            |
| `--grey`     | `#536074` | No data, offline, last reading                   |
| `--fault`    | `#7C2D12` | Sensor fault                                     |

- Typeface: IBM Plex Sans 400–700, self-hosted in `frontend/css/fonts` (SIL Open Font Licence), tabular numbers.
- Sentence case for all labels, buttons, tabs and status words.
- Radius 14 px for cards, 8 px for controls, round pills for status tags. No shadows except pop-ups.
- The status tile is the strongest element: a coloured band on the left, the status word and a large temperature.
- Period and view choosers are segmented controls; the selected option is white with blue text.
- Touch targets are at least 44 px high.

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
