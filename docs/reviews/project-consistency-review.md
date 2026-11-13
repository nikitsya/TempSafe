# Project consistency review — 8 November 2026

Reviewed the repository at `06df99f` against source code, schema, tests and the recorded
EC2 deployment at `3578cfe`. This review updates documentation; it does not claim
that every functional requirement or physical integration test has passed.

## Scope and checks

- Checked Markdown guides, requirements, design targets and dated test reports;
  local document/image links and Markdown section anchors resolve.
- Read the three Word documents and two presentations. Historical proposals and
  dated results remain unchanged;
  the Alpha slides retain their dated status snapshot, as explained below.
- Compared API routes, payloads, database schema, device constants, frontend requests,
  Compose settings and deployment instructions with their source files.
- Ran all 150 backend tests against temporary MySQL 8.4. Migration 005 applied to
  the earlier schema; all tests passed with two dependency deprecation warnings.
  The temporary database was removed. Python and frontend JavaScript syntax checks passed.
- Reproduced the three frontend discrepancies below using isolated JavaScript execution
  and synthetic readings. This was not a browser, accessibility or real-device test.
- Reused the dated live checks in the [deployment record](../operations/deployment.md):
  HTTPS and health respond, anonymous data access is rejected, and the MQTT client connects.

The old and renamed GitHub Pages prototype URLs both returned 404; the prototype
guide now directs users to the local files.

The HTML prototype tests remain evidence for synthetic prototype screens, not for the
current FastAPI frontend. Research sources were checked selectively; this is not a new
clinical, legal, hardware-accuracy or full security certification.

## Confirmed implementation discrepancies

| Area                  | Reproduction and remaining work                                                                                                                                                                                                                      |
|-----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Historical thresholds | `history.js` uses the latest profile across all rows. A 26°C sample recorded as Normal under an upper limit of 30°C becomes Too high when the latest limit is 25°C. Use each row’s recorded profile/classification for the table, graph and periods. |
| Missing observations  | High samples with sequence numbers 1 and 3, 60 seconds apart, produce one excursion despite missing sample 2. Break continuity at missing observations; account for delayed arrivals when rebuilding periods.                                        |
| Lower-limit wording   | At 0°C with limits 0/24/25, the dashboard shows Alert but Details says Above the upper limit. The explanation must include equality in the low-alert branch.                                                                                         |
| Denied access         | The API hides unassigned box data, but the dashboard shows a generic loading error. Add the intended no-access explanation without exposing other boxes.                                                                                             |

These behaviours have not been changed by this documentation review. See the
[frontend guide](../../frontend/README.md#history-behaviour-and-limitations).

## Outstanding scope and evidence

- Device clock reliability is always set true by the logger; clock verification is missing.
- Phone notifications, sample-review actions, time-range filtering, device profile delivery
  and manual buzzer silencing remain unfinished.
- The new FastMQTT deployment needs a fresh Pi storage/acknowledgement trace. The 24-hour
  offline/restart recovery test and reference-thermometer validation remain unrecorded.
- Database runtime grants remain broad. Off-server backup and restore testing are unverified.
- The G-CA2 Word draft still contains hardware/frontend contributor prompts. Its deployment
  account predates the latest changes; complete the contributor sections before submission.

The MoSCoW priorities are unchanged. FR-13 remains Must Have; the updated review marks
four features complete, nine in progress and two planned. The Alpha slides retain their
explicit 6 November snapshot of three complete, ten in progress and two planned.
