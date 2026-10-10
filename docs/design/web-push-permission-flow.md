# Web Push permission flow

Author: Maryna Hordiienko (frontend and Web Push integration)

[ui-design.md](ui-design.md) states that TempSafe plans Web Push with a service worker and explicit permission. This document shows the detailed flow. The browser asks for permission only after the user chooses to turn alerts on, never on first page load.

## Flow

```mermaid
sequenceDiagram
    actor U as User
    participant P as TempSafe page
    participant SW as Service worker
    participant B as Browser push service
    participant S as TempSafe server
    U->>P: Tap "Turn on phone alerts"
    P->>P: Check Notification and PushManager support
    alt Not supported (or iOS without home-screen install)
        P-->>U: Banner: phone notifications unavailable
    else Supported
        P->>U: Browser permission prompt
        alt Permission denied
            P-->>U: Banner: permission blocked, monitoring on screen still works
        else Permission granted
            P->>SW: Register service worker
            P->>B: Subscribe with VAPID public key
            B-->>P: Subscription endpoint and keys
            P->>S: POST /api/push-subscriptions (signed-in session)
            S-->>P: Saved for the user's assigned box
            P-->>U: Phone alerts: On
        end
    end
    Note over S,B: On a Warning or Alert transition the server sends a push to authorised subscriptions only
    S->>B: Push message
    B->>SW: Push event
    SW->>U: Show notification, tap opens the dashboard
```

## UI states

| State | What the user sees |
|---|---|
| Not asked yet | Button "Turn on phone alerts" |
| Granted | "Phone alerts: On (Web Push)" |
| Denied | Info banner with a link "How to enable" |
| Unsupported | Info banner explaining that this browser cannot show phone alerts |
| iOS / iPadOS | Instruction to add TempSafe to the home screen first |

## Server rules (from design document Section 6)

- A notification is created only when the current state changes to Warning or Alert. Unchanged repeated states are suppressed.
- Delayed historical uploads do not trigger current warnings.
- Failed deliveries are retried and marked; duplicates are prevented.
- Target: receipt within 60 seconds of an online Warning/Alert transition. This is measured on supported phones, not guaranteed.
- Notification text contains no account details and links to the signed-in dashboard.

## Planned browser checks

Chrome on Android, Safari on iOS 16.4+ (home-screen web app), Chrome and Edge on Windows.
