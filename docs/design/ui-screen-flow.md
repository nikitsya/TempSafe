# UI screen flow

Author: Maryna Hordiienko

This diagram shows how a user moves between TempSafe screens. Every box and history request is checked by the backend; hiding a button is not access control.

```mermaid
flowchart TD
    A[Open TempSafe over HTTPS] --> B[Sign in]
    B -->|Wrong username or password| B1[Generic error message]
    B1 --> B
    B -->|Signed in, no box assigned| K[No assigned box available]
    B -->|Signed in, box assigned| C[Current status]
    C --> S{Latest data}
    S -->|Fresh and valid| C1[Normal / Warning / Alert]
    S -->|Older than 90 s| F[Data stale]
    S -->|Failed reading| G[Sensor error]
    S -->|No contact for 180 s| H[Not reporting]
    S -->|API unreachable| I[Unable to refresh + Retry]
    S -->|No readings ever| J[No observations yet]
    C --> D[View temperature history]
    D -->|Valid range| D1[Graph + table]
    D -->|From after To| D2[Invalid range error]
    D -->|No rows| D3[No observations found]
    D --> C
    C --> P{Phone alerts}
    P -->|Permission granted| P1[Web Push on]
    P -->|Denied or unsupported| P2[Banner: phone notifications unavailable]
    C --> X[Sign out: server session invalidated]
    K --> X
```

## Screens

| Screen | Purpose | Mock-up |
|---|---|---|
| Sign in | Authenticate the user | `ui-signin.png` (A, B) |
| Current status | Show the latest temperature, status and freshness | `ui-dashboard.png` (C, D, E) |
| Error and empty states | Explain stale, failed, offline and missing data | `ui-states.png` (F–K) |
| History | Review earlier readings by date range | `ui-history.png` |
