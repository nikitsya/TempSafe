// Dashboard for TEMPSAFE.
// Get temperature data from the backend API.

const STATUS_VIEW = {
    normal: {
        cls: 'normal',
        icon: '✓',
        title: 'OK',
        role: 'status'
    },
    warning: {
        cls: 'warning',
        icon: '!',
        title: 'WARNING',
        role: 'status'
    },
    alert: {
        cls: 'alert',
        icon: '✕',
        title: 'TOO HOT',
        role: 'alert'
    },
    stale: {
        cls: 'unknown',
        icon: '⏱',
        title: 'NO DATA',
        role: 'status'
    },
    sensor_error: {
        cls: 'alert',
        icon: '⚠',
        title: 'SENSOR FAULT',
        role: 'alert'
    },
    not_reporting: {
        cls: 'unknown',
        icon: '⦸',
        title: 'OFFLINE',
        role: 'alert'
    },
    never_connected: {
        cls: 'unknown',
        icon: '⦸',
        title: 'NOT CONNECTED',
        role: 'status'
    },
    unknown: {
        cls: 'unknown',
        icon: '?',
        title: 'UNKNOWN',
        role: 'status'
    }
};

// Status words are short on purpose (usability: read at a glance).
// An alert says which way: TOO HOT or TOO COLD.
function viewFor(reading) {
    const view = STATUS_VIEW[reading.status] || STATUS_VIEW.unknown;
    if (reading.status === 'alert' && reading.tooCold) {
        return {...view, title: 'TOO COLD'};
    }
    return view;
}

// Convert API date to local date and time (used in Details).
function formatTime(date) {
    if (!date) {
        return 'Unknown';
    }

    const time = new Date(date);

    if (isNaN(time.getTime())) {
        return 'Unknown';
    }

    // e.g. "13 Nov 2026, 06:53"
    return time.toLocaleString('en-IE', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

// Convert API date to a short clock time (used on the main card).
function formatClock(date) {
    if (!date) {
        return null;
    }

    const time = new Date(date);

    if (isNaN(time.getTime())) {
        return null;
    }

    return time.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
}

// Short explanation of the status. Shown in Details, not on the main card.
function describe(reading, profile) {
    switch (reading.status) {
        case 'normal':
            return 'In range';

        case 'warning':
            return `Near the limit (${profile.upperC}°C)`;

        case 'alert':
            // The lower limit is inclusive: exactly 0°C is already an alert.
            return reading.temperatureC <= profile.lowerC
                ? `${profile.lowerC}°C or below`
                : `Above ${profile.upperC}°C`;

        case 'stale':
            return 'No reading for 90 s';

        case 'sensor_error':
            return 'Sensor cannot measure';

        case 'not_reporting':
            return 'Box not sending data';

        case 'never_connected':
            return 'Box never connected';

        default:
            return 'Clock not reliable';
    }
}

// Main card: only the status, the temperature and the time.
function statusCard(reading) {
    const view = viewFor(reading);

    let body = '';

    // Show a live temperature only when the time is reliable.
    if (
        reading.temperatureC !== null &&
        ['normal', 'warning', 'alert'].includes(reading.status) &&
        reading.ageSeconds !== null
    ) {
        body = `
            <div class="value">
                ${reading.temperatureC.toFixed(1)}<small>°C</small>
            </div>
            <div class="meta">
                ${reading.observedClock} · ${reading.ageSeconds} s ago
            </div>
        `;
    }

    // No current temperature: never show an old number here.
    else {
        body = `<p class="status-text">No temperature</p>`;

        if (reading.status === 'not_reporting' && reading.lastContact) {
            body += `<div class="meta">Last contact ${reading.lastContact}</div>`;
        }
    }

    return `
        <section class="status ${view.cls}">
            <div class="status-row">
                <span class="status-icon" aria-hidden="true">
                    ${view.icon}
                </span>
                <h2 class="status-title">${view.title}</h2>
            </div>

            ${body}
        </section>
    `;
}

// Everything else is behind the "Details" button.
function detailsCard(reading, profile) {
    const live = ['normal', 'warning', 'alert'].includes(reading.status) &&
        reading.ageSeconds !== null;

    const lastReading = !live && reading.temperatureC !== null
        ? `<dt>Last value</dt><dd>${reading.temperatureC.toFixed(1)}°C (old)</dd>`
        : '';

    return `
        <details class="details">
            <summary>Details</summary>
            <dl class="kv">
                <dt>Status</dt>
                <dd>${describe(reading, profile)}</dd>

                ${lastReading}

                <dt>Last measured</dt>
                <dd>${reading.observedAt}</dd>

                ${reading.lastContactFull
                    ? `<dt>Last contact</dt><dd>${reading.lastContactFull}</dd>`
                    : ''}

                <dt>Limits</dt>
                <dd>${profile.lowerC}–${profile.upperC}°C · warning ${profile.warningC}°C</dd>
            </dl>
        </details>
    `;
}

// Show a message when no readings exist.
function emptyState() {
    return `
        <section class="empty" role="status">
            <div class="empty-icon" aria-hidden="true">—</div>

            <h2>No readings yet</h2>

            <p class="muted">Check the box is on.</p>
        </section>
    `;
}

// The box does not exist or is not assigned to this user (API: 404 "Box not found").
function noAccessState() {
    return `
        <section class="empty" role="alert">
            <div class="empty-icon" aria-hidden="true">⦸</div>

            <h2>No access</h2>

            <p class="muted">Ask your admin for box TS-01.</p>
        </section>
    `;
}

// Show the dashboard and keep the Details panel open if the user opened it.
function renderDashboard(reading, profile) {
    const dashboard = document.getElementById('dashboard');
    const details = dashboard.querySelector('details');
    const detailsOpen = details ? details.open : false;

    dashboard.innerHTML =
        statusCard(reading) +
        detailsCard(reading, profile);

    if (detailsOpen) {
        dashboard.querySelector('details').open = true;
    }
}

// Device contact (FR-08). Uses GET /api/boxes/{box_id}.
// If the API sends contact_state, use it. Otherwise use last_seen_at:
// more than 3 minutes without contact means NOT REPORTING.
// No contact time means "unknown", not "offline", so nothing is shown.
const CONTACT_TIMEOUT_SECONDS = 180;

function contactState(box) {
    if (!box) {
        return null;
    }

    if (box.contact_state) {
        return String(box.contact_state).toLowerCase();
    }

    if (!box.last_seen_at) {
        return null;
    }

    const seen = new Date(box.last_seen_at);

    if (isNaN(seen.getTime())) {
        return null;
    }

    const seconds = (Date.now() - seen.getTime()) / 1000;
    return seconds > CONTACT_TIMEOUT_SECONDS ? 'not_reporting' : 'reporting';
}

// Convert API data into frontend data.
function convertReading(data, box = null) {

    // Check that the API returned a temperature profile.
    if (!data.profile) {
        throw new Error('Temperature profile is missing');
    }

    const profile = {
        lowerC: Number(data.profile.lower_c),
        warningC: Number(data.profile.warning_c),
        upperC: Number(data.profile.upper_c)
    };

    // Check that the profile contains valid limits.
    if (
        !Number.isFinite(profile.lowerC) ||
        !Number.isFinite(profile.warningC) ||
        !Number.isFinite(profile.upperC)
    ) {
        throw new Error('Invalid temperature profile');
    }

    // Read temperature from API.
    let temperature = null;

    if (
        data.temperature_c !== null &&
        data.temperature_c !== undefined &&
        data.temperature_c !== ''
    ) {
        temperature = Number(data.temperature_c);
    }

    if (temperature !== null && !Number.isFinite(temperature)) {
        temperature = null;
    }

    // Check observation time.
    let ageSeconds = null;

    if (data.clock_reliable && data.observed_at) {
        const observed = new Date(data.observed_at);

        if (!isNaN(observed.getTime())) {
            ageSeconds = Math.floor(
                (Date.now() - observed.getTime()) / 1000
            );

            // Allow a small clock difference between the device and this computer.
            if (ageSeconds < 0 && ageSeconds >= -30) {
                ageSeconds = 0;
            }
        }
    }

    // Read temperature status.
    let status = String(
        data.temperature_state || 'unknown'
    ).toLowerCase();

    if (!STATUS_VIEW[status]) {
        status = 'unknown';
    }

    // Check for sensor errors.
    if (
        data.quality === 'sensor_error' ||
        (temperature === null && data.quality !== 'valid')
    ) {
        status = 'sensor_error';
        temperature = null;
    }

    // Missing temperature cannot be normal.
    else if (temperature === null) {
        status = 'unknown';
    }

    // Unknown or unreliable observation time.
    else if (ageSeconds === null || ageSeconds < 0) {
        status = 'unknown';
    }

    // The API says the reading is older than 90 seconds.
    // The browser age is also checked, so that cached data becomes stale
    // when the refresh fails.
    else if (data.freshness === 'stale' || ageSeconds > 90) {
        status = 'stale';
    }

    // The API cannot tell how old the reading is.
    else if (data.freshness === 'unknown') {
        status = 'unknown';
    }

    // Device contact (FR-08) is more important than an old reading.
    const contact = contactState(box);

    if (contact === 'never_connected' || contact === 'not_reporting') {
        status = contact;
    }

    const reading = {
        status: status,
        temperatureC: temperature,
        observedAt: formatTime(data.observed_at),
        observedClock: formatClock(data.observed_at),
        receivedAt: formatTime(data.received_at),
        ageSeconds: ageSeconds,
        lastContact: box ? formatClock(box.last_seen_at) : null,
        lastContactFull: box && box.last_seen_at ? formatTime(box.last_seen_at) : null
    };

    return {reading, profile};
}

// Automatic refresh settings.
const REFRESH_SECONDS = 5;   // ask the API for new data
const TICK_SECONDS = 5;       // update "… s ago" and the stale check

let lastData = null;          // last successful API response
let lastBox = null;           // last box contact information
let lastStatus = null;        // last announced status
let loading = false;          // avoid overlapping requests

// Tell screen readers only when the status changes, not on every refresh.
function announceStatus(reading) {
    const view = viewFor(reading);
    const live = ['normal', 'warning', 'alert'].includes(reading.status) &&
        reading.ageSeconds !== null;
    const text = live
        ? `Status ${view.title}, ${reading.temperatureC.toFixed(1)} degrees Celsius`
        : `Status ${view.title}, temperature unknown`;

    if (reading.status === lastStatus) {
        return;
    }
    lastStatus = reading.status;

    const polite = document.getElementById('status-announcer');
    const urgent = document.getElementById('alert-announcer');
    polite.textContent = '';
    urgent.textContent = '';

    if (view.role === 'alert') {
        urgent.textContent = text;
    } else {
        polite.textContent = text;
    }
}

// Show the last saved data again, so the age and stale state stay correct.
function showLastData() {
    if (!lastData) {
        return;
    }
    const result = convertReading(lastData, lastBox);
    result.reading.tooCold = result.reading.temperatureC !== null &&
        result.reading.temperatureC <= result.profile.lowerC;
    renderDashboard(result.reading, result.profile);
    announceStatus(result.reading);
}

// Short message when a refresh fails but older data is still on screen.
function showRefreshError(show) {
    const banner = document.getElementById('refresh-error');
    if (!banner) {
        return;
    }
    banner.hidden = !show;
    if (show && lastData) {
        banner.textContent =
            `Can't refresh. Showing data from ${formatClock(lastData.received_at) || 'earlier'}.`;
    }
}

// Get the box contact information. Returns null if it is not available.
async function loadBox() {
    try {
        const response = await fetch(`${API_BASE}/boxes/TS-01`);
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        return null;
    }
}

// ---- Unread temperature alert (usability test finding 1) ----
// The status card shows only the current reading. If the box was too hot or too cold
// earlier and is now back within the limits, the user would miss it. So the dashboard
// shows a banner for the newest alert the user has not viewed yet, with a View button.
// "Viewed" is saved in this browser only (localStorage), per user and per box.
const SEEN_ALERT_KEY = 'tempsafe.seenAlert.TS-01';
const ALERT_CHECK_SECONDS = 30;
let shownAlertSeq = null;

function getSeenAlertSeq() {
    try {
        const value = Number(localStorage.getItem(SEEN_ALERT_KEY));
        return Number.isFinite(value) ? value : 0;
    } catch (error) {
        return 0;
    }
}

function setSeenAlertSeq(seq) {
    try {
        if (seq > getSeenAlertSeq()) localStorage.setItem(SEEN_ALERT_KEY, String(seq));
    } catch (error) {
        // Storage can be blocked (private mode). The banner then shows again next time.
    }
}

// Newest reading that the API classified as Alert, or null.
function newestAlert(readings) {
    for (const r of readings) {   // the API returns the newest first
        if (String(r.temperature_state || '').toLowerCase() !== 'alert') continue;
        const t = Number(r.temperature_c);
        const lower = Number(r.profile && r.profile.lower_c);
        if (!Number.isFinite(t) || !Number.isFinite(Number(r.sequence_no))) continue;
        return {
            seq: Number(r.sequence_no),
            kind: Number.isFinite(lower) && t <= lower ? 'low' : 'high',
            temperatureC: t,
            observedAt: r.observed_at ? new Date(r.observed_at) : null,
        };
    }
    return null;
}

function alertBannerHtml(alert) {
    const what = alert.kind === 'low' ? 'Low temperature detected' : 'High temperature detected';
    let when = '';
    if (alert.observedAt && !Number.isNaN(alert.observedAt.getTime())) {
        const day = alert.observedAt.toLocaleDateString('en-IE', {day: 'numeric', month: 'short'});
        const time = alert.observedAt.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
        when = `${day}, ${time} · `;
    }
    return `
        <section aria-labelledby="unread-alert-title" class="unread-alert">
            <span aria-hidden="true" class="unread-alert-icon">⚠</span>
            <div class="unread-alert-text">
                <h2 id="unread-alert-title">Alert: ${what}</h2>
                <p>${when}${alert.temperatureC.toFixed(1)}°C</p>
            </div>
            <a class="unread-alert-btn" data-alert-seq="${alert.seq}" href="history.html#alerts">
                View<span class="visually-hidden"> alert in history</span> <span aria-hidden="true">→</span>
            </a>
        </section>`;
}

async function checkUnreadAlert() {
    const box = document.getElementById('unread-alert');
    if (!box) return;
    try {
        const response = await fetch(`${API_BASE}/boxes/TS-01/readings?limit=100`);
        if (!response.ok) return;   // keep what is on screen
        const readings = await response.json();
        const alert = Array.isArray(readings) ? newestAlert(readings) : null;

        if (!alert || alert.seq <= getSeenAlertSeq()) {
            box.innerHTML = '';
            shownAlertSeq = null;
            return;
        }
        if (alert.seq === shownAlertSeq) return;   // already shown, do not announce again
        shownAlertSeq = alert.seq;
        box.innerHTML = alertBannerHtml(alert);
        const announcer = document.getElementById('alert-announcer');
        if (announcer) {
            announcer.textContent = alert.kind === 'low'
                ? 'Unread alert: low temperature detected.'
                : 'Unread alert: high temperature detected.';
        }
    } catch (error) {
        console.error('Unread alert error:', error);
    }
}

document.addEventListener('click', (event) => {
    const link = event.target.closest && event.target.closest('[data-alert-seq]');
    if (link) setSeenAlertSeq(Number(link.dataset.alertSeq));
});

// Get the latest reading from the API.
async function loadTemperature() {
    const dashboard = document.getElementById('dashboard');

    if (loading) {
        return;
    }
    loading = true;

    // Show the loading message only the first time.
    if (!lastData && !dashboard.innerHTML.trim()) {
        dashboard.innerHTML = `
            <section class="card" role="status">
                Loading…
            </section>
        `;
    }

    try {
        const response = await fetch(
            `${API_BASE}/boxes/TS-01/readings/latest`
        );

        // Not signed in or the session has ended.
        if (response.status === 401) {
            goToSignIn();
            return;
        }

        if (response.status === 404) {
            const errorData = await response.json();

            // No readings available.
            if (
                errorData.detail ===
                'No readings available for this box'
            ) {
                lastData = null;
                showRefreshError(false);
                dashboard.innerHTML = emptyState();
                return;
            }

            // The box does not exist or is not assigned to this user.
            if (errorData.detail === 'Box not found') {
                lastData = null;
                showRefreshError(false);
                dashboard.innerHTML = noAccessState();
                return;
            }
        }

        // Handle request errors.
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }

        // Read and check the JSON response before saving it.
        const data = await response.json();
        convertReading(data);

        // Device contact is optional: if it fails, the reading is still shown.
        lastBox = await loadBox();

        lastData = data;
        showRefreshError(false);
        showLastData();

    } catch (error) {
        console.error('Dashboard error:', error);

        // Keep the old data on screen if we have it.
        if (lastData) {
            showLastData();
            showRefreshError(true);
        } else {
            dashboard.innerHTML = `
                <section class="empty" role="alert">
                    <h2>Can't load</h2>

                    <p class="muted">Check your internet and refresh.</p>
                </section>
            `;
        }
    } finally {
        loading = false;
    }
}

// Start loading and refreshing when the page opens.
document.addEventListener('DOMContentLoaded', () => {
    loadTemperature();
    checkUnreadAlert();
    setInterval(checkUnreadAlert, ALERT_CHECK_SECONDS * 1000);

    // Ask the API for new data every five seconds.
    setInterval(loadTemperature, REFRESH_SECONDS * 1000);

    // Update the age every 5 seconds without a new request.
    setInterval(showLastData, TICK_SECONDS * 1000);

    // Refresh at once when the user comes back to the tab.
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            loadTemperature();
        }
    });
});
