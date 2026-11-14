// Dashboard for TEMPSAFE.
// Get temperature data from the backend API.

const STATUS_VIEW = {
    normal: {
        cls: 'normal',
        icon: '✓',
        title: 'Normal',
        role: 'status'
    },
    warning: {
        cls: 'warning',
        icon: '!',
        title: 'Warning',
        role: 'status'
    },
    alert: {
        cls: 'alert',
        icon: '✕',
        title: 'Alert',
        role: 'alert'
    },
    stale: {
        cls: 'unknown',
        icon: '⏱',
        title: 'Last reading',
        role: 'status'
    },
    sensor_error: {
        cls: 'alert',
        icon: '⚠',
        title: 'Sensor fault',
        role: 'alert'
    },
    not_reporting: {
        cls: 'unknown',
        icon: '⦸',
        title: 'Offline',
        role: 'alert'
    },
    never_connected: {
        cls: 'unknown',
        icon: '⦸',
        title: 'Not connected',
        role: 'status'
    },
    unknown: {
        cls: 'unknown',
        icon: '?',
        title: 'Unknown',
        role: 'status'
    }
};

// Status words follow FR-05: Normal, Warning and Alert. Details say which limit
// an alert crossed ("Above 25°C" or "0°C or below").
function viewFor(reading) {
    return STATUS_VIEW[reading.status] || STATUS_VIEW.unknown;
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




// Age of the last reading for Details (FR-04): "5 s ago", "3 min ago", "2 h ago".
function ageText(seconds) {
    if (seconds < 60) return `${seconds} s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
}

// ---- How long the current status has lasted, and the alert banner ----
// Uses the latest 100 readings: counts back while the status stays the same.
let stateSince = null;     // time the current Warning or Alert started (ms)
let recentReadings = [];   // latest 100 readings, newest first (for the Last hour chart)
let todayStats = null;     // {min, max, alerts, lastAlert} for today
let alertBanner = null;    // {low: true/false} while an alert is on

// "4 min", "1 h", "1 h 20 min", "2 days" – as short as possible.
function shortDuration(ms) {
    const minutes = Math.max(1, Math.round(ms / 60000));
    if (minutes < 60) return `${minutes} min`;
    if (minutes < 1440) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return m ? `${h} h ${m} min` : `${h} h`;
    }
    const days = Math.round(minutes / 1440);
    return `${days} day${days === 1 ? '' : 's'}`;
}

async function loadRecentState() {
    try {
        const response = await fetch(`${API_BASE}/boxes/TS-01/readings?limit=100`);
        if (!response.ok) return;
        const readings = await response.json();
        if (!Array.isArray(readings) || readings.length === 0) return;
        recentReadings = readings;
        const stateOf = (r) => r.quality === 'valid' ? String(r.temperature_state || '').toLowerCase() : null;
        const current = stateOf(readings[0]);
        stateSince = null;
        alertBanner = null;
        if (current === 'warning' || current === 'alert') {
            let first = readings[0];
            for (let i = 1; i < readings.length; i++) {
                const gap = Number(readings[i - 1].sequence_no) - Number(readings[i].sequence_no) > 1;
                if (gap || stateOf(readings[i]) !== current) break;
                first = readings[i];
            }
            stateSince = new Date(first.observed_at).getTime();
        }
        if (current === 'alert') {
            const lower = Number(readings[0].profile && readings[0].profile.lower_c);
            alertBanner = {low: Number.isFinite(lower) && Number(readings[0].temperature_c) <= lower};
        }
    } catch (error) {
        console.error('Recent state error:', error);
    }
}

// "Alert: High temperature detected" with a View button (usability test finding 1).
function renderAlertBanner() {
    const box = document.getElementById('alert-banner');
    if (!box) return;
    if (!alertBanner) {
        box.innerHTML = '';
        return;
    }
    const text = alertBanner.low ? 'Alert: Low temperature detected' : 'Alert: High temperature detected';
    if (box.dataset.text === text && box.innerHTML) return;   // already shown
    box.dataset.text = text;
    box.innerHTML = `
        <section aria-labelledby="alert-banner-title" class="unread-alert alert-banner-stacked">
            <span aria-hidden="true" class="unread-alert-icon">⚠</span>
            <div class="unread-alert-text">
                <h2 id="alert-banner-title">${text}</h2>
            </div>
            <a class="unread-alert-btn" href="alerts.html">
                View<span class="visually-hidden"> alerts</span> <span aria-hidden="true">→</span>
            </a>
        </section>`;
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

            <p class="muted">Ask your admin for access.</p>
        </section>
    `;
}

// Show the status card and the details.
// ---- Dashboard panel ----
// Row of four tiles (status and temperature, today's range, alerts today, last measured),
// then a "Last hour" chart. The red alert banner stays on top.
function tile(label, value, sub, extraClass = '') {
    return `
        <section class="tile ${extraClass}">
            <h2 class="tile-label">${label}</h2>
            <div class="tile-value">${value}</div>
            ${sub ? `<p class="tile-sub">${sub}</p>` : ''}
        </section>`;
}

function mainTile(reading) {
    const view = viewFor(reading);
    const live = ['normal', 'warning', 'alert'].includes(reading.status) && reading.ageSeconds !== null;
    const value = reading.temperatureC === null
        ? '<span class="tile-none">No temperature</span>'
        : `${reading.temperatureC.toFixed(1)}<small>°C</small>`;
    const forChip = live && ['warning', 'alert'].includes(reading.status) && stateSince
        ? `<span class="status-for">for ${shortDuration(Date.now() - stateSince)}</span>` : '';
    return `
        <section class="tile tile-main status ${view.cls}">
            <div class="status-row">
                <span aria-hidden="true" class="status-icon">${view.icon}</span>
                <h2 class="status-title">${view.title}</h2>
            </div>
            <div class="value ${live ? '' : 'value-old'}">${value}</div>
            ${forChip}
        </section>`;
}

function todayTiles(reading) {
    const range = todayStats && todayStats.min !== null
        ? `${todayStats.min.toFixed(1)} – ${todayStats.max.toFixed(1)}<small>°C</small>` : '—';
    const alerts = todayStats ? String(todayStats.alerts) : '—';
    const alertSub = todayStats && todayStats.lastAlert ? `last at ${formatClock(todayStats.lastAlert)}` : 'none today';
    const measured = reading.observedClock || '—';
    const ago = reading.ageSeconds !== null ? ageText(reading.ageSeconds) : '';
    return tile("Today's range", range, '') +
        tile('Alerts today', alerts, alertSub, todayStats && todayStats.alerts ? 'tile-alert' : '') +
        tile('Last measured', measured, ago);
}

// Small "Last hour" chart: line coloured by status, dashed limit lines, a few time marks.
function lastHourChart(profile) {
    const now = Date.now();
    const from = now - 3600 * 1000;
    const points = recentReadings.slice().reverse().filter((r) => {
        const t = new Date(r.observed_at).getTime();
        return r.clock_reliable && t >= from && t <= now + 30000;
    });
    const valid = points.filter((r) => r.quality === 'valid' && Number.isFinite(Number(r.temperature_c)));
    let body;
    if (valid.length < 2) {
        body = '<p class="muted chart-empty">No readings in the last hour.</p>';
    } else {
        const W = 900, H = 260, L = 44, R = 10, T = 12, B = 34;
        const values = valid.map((r) => Number(r.temperature_c));
        let min = Math.min(...values, profile.warningC) - 1;
        let max = Math.max(...values, profile.upperC) + 1;
        min = Math.floor(min);
        max = Math.ceil(max);
        const x = (t) => L + (t - from) / (now - from) * (W - L - R);
        const y = (v) => T + (max - v) / (max - min) * (H - T - B);
        const color = (r) => {
            const st = String(r.temperature_state || '').toLowerCase();
            return st === 'alert' ? 'line-alert' : st === 'warning' ? 'line-warning' : 'line-normal';
        };
        let svg = '';
        const step = max - min > 8 ? 4 : 2;
        for (let v = Math.ceil(min / step) * step; v <= max; v += step) {
            svg += `<line class="graph-grid" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>` +
                `<text class="graph-axis" x="${L - 8}" y="${y(v) + 5}" text-anchor="end">${v}</text>`;
        }
        [profile.upperC, profile.warningC].forEach((v, i) => {
            svg += `<line class="${i === 0 ? 'graph-upper' : 'graph-warning'}" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>`;
        });
        for (let k = 0; k <= 4; k++) {
            const t = from + k * 15 * 60000;
            svg += `<text class="graph-axis" x="${x(t)}" y="${H - 8}" text-anchor="${k === 0 ? 'start' : k === 4 ? 'end' : 'middle'}">${formatClock(new Date(t))}</text>`;
        }
        // Grey band: no data (more than 90 s without a reading). Red band: sensor fault.
        const band = (t1, t2, cls) => {
            const x1 = Math.max(L, x(t1));
            const x2 = Math.min(W - R, x(t2));
            if (x2 - x1 > 1) svg += `<rect class="${cls}" x="${x1.toFixed(1)}" y="${T}" width="${(x2 - x1).toFixed(1)}" height="${H - T - B}"/>`;
        };
        const times = points.map((r) => new Date(r.observed_at).getTime());
        if (times.length && times[0] - from > 90000) band(from, times[0], 'band-nodata');
        for (let i = 1; i < points.length; i++) {
            const seqGap = Number(points[i].sequence_no) - Number(points[i - 1].sequence_no) > 1;
            if (seqGap || times[i] - times[i - 1] > 90000) band(times[i - 1], times[i], 'band-nodata');
            if (points[i - 1].quality === 'sensor_error') band(times[i - 1], times[i], 'band-fault');
        }
        if (times.length && now - times[times.length - 1] > 90000) band(times[times.length - 1], now, 'band-nodata');
        if (!times.length) band(from, now, 'band-nodata');

        for (let i = 1; i < points.length; i++) {
            const a = points[i - 1];
            const b = points[i];
            const gap = Number(b.sequence_no) - Number(a.sequence_no) > 1 ||
                new Date(b.observed_at) - new Date(a.observed_at) > 90000;
            if (gap || a.quality !== 'valid' || b.quality !== 'valid') continue;
            svg += `<line class="graph-seg ${color(b)}" x1="${x(new Date(a.observed_at).getTime()).toFixed(1)}" ` +
                `y1="${y(Number(a.temperature_c)).toFixed(1)}" x2="${x(new Date(b.observed_at).getTime()).toFixed(1)}" ` +
                `y2="${y(Number(b.temperature_c)).toFixed(1)}"/>`;
        }
        const last = valid[valid.length - 1];
        body = `<svg class="mini-chart" role="img" viewBox="0 0 ${W} ${H}"
                    aria-label="Temperature in the last hour: lowest ${Math.min(...values).toFixed(1)}°C, highest ${Math.max(...values).toFixed(1)}°C, now ${Number(last.temperature_c).toFixed(1)}°C.">${svg}</svg>`;
        body += `<ul class="graph-legend mini-legend">
            <li><span aria-hidden="true" class="legend-line line-normal"></span>Normal</li>
            <li><span aria-hidden="true" class="legend-line line-warning"></span>Warning</li>
            <li><span aria-hidden="true" class="legend-line line-alert"></span>Alert</li>
            <li><span aria-hidden="true" class="legend-upper"></span>Limit</li>
            <li><span aria-hidden="true" class="legend-band legend-fault"></span>Sensor fault</li>
            <li><span aria-hidden="true" class="legend-band legend-nodata"></span>No data</li>
        </ul>`;
    }
    return `
        <section aria-labelledby="chart-title" class="tile tile-chart">
            <h2 class="tile-label" id="chart-title">Last hour</h2>
            ${body}
        </section>`;
}

function renderDashboard(reading, profile) {
    const dashboard = document.getElementById('dashboard');
    dashboard.innerHTML = `
        <div class="tiles">
            ${mainTile(reading)}
            ${todayTiles(reading)}
        </div>
        ${lastHourChart(profile)}`;
    renderAlertBanner();
}

// Today's lowest and highest temperature and number of alerts (refreshed every minute).
async function loadToday() {
    try {
        const today = new Intl.DateTimeFormat('en-CA', {
            timeZone: 'Europe/Dublin', year: 'numeric', month: '2-digit', day: '2-digit'
        }).format(new Date());
        const all = [];
        let before = null;
        for (let page = 0; page < 10; page++) {
            let url = `${API_BASE}/boxes/TS-01/readings?limit=100&start_date=${today}&end_date=${today}`;
            if (before !== null) url += `&before_sequence=${before}`;
            const response = await fetch(url);
            if (!response.ok) return;
            const rows = await response.json();
            all.push(...rows);
            if (rows.length < 100) break;
            before = rows[rows.length - 1].sequence_no;
        }
        const values = all.filter((r) => r.quality === 'valid').map((r) => Number(r.temperature_c)).filter(Number.isFinite);
        let alerts = 0;
        let lastAlert = null;
        const oldestFirst = all.slice().reverse();
        oldestFirst.forEach((r, i) => {
            const isAlert = String(r.temperature_state || '').toLowerCase() === 'alert';
            const prev = oldestFirst[i - 1];
            const prevAlert = prev && String(prev.temperature_state || '').toLowerCase() === 'alert' &&
                Number(r.sequence_no) - Number(prev.sequence_no) === 1;
            if (isAlert && !prevAlert) {
                alerts++;
                lastAlert = r.observed_at;
            }
        });
        todayStats = {
            min: values.length ? Math.min(...values) : null,
            max: values.length ? Math.max(...values) : null,
            alerts,
            lastAlert,
        };
    } catch (error) {
        console.error('Today error:', error);
    }
}

// Device contact (FR-08). Uses GET /api/boxes/{box_id}/status.
// The server says "reporting" while it received anything (even a sensor error)
// in the last 90 seconds, "not_reporting" after that and "never_reported"
// before the first sample. If the request fails, contact is unknown and
// nothing extra is shown.
const CONTACT_STATES = {
    reporting: 'reporting',
    not_reporting: 'not_reporting',
    never_reported: 'never_connected'
};

function contactState(boxStatus) {
    if (!boxStatus) {
        return null;
    }
    return CONTACT_STATES[boxStatus.contact_status] || null;
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
        lastContact: box ? formatClock(box.last_received_at) : null,
        lastContactFull: box && box.last_received_at ? formatTime(box.last_received_at) : null
    };

    return {reading, profile};
}

// Automatic refresh settings.
const REFRESH_SECONDS = 5;   // ask the API for new data
const TICK_SECONDS = 5;       // update "… s ago" and the stale check

let lastData = null;          // last successful API response
let lastBox = null;           // last box status (contact) from the API
let lastStateCheck = 0;       // when loadRecentState last ran
let lastTodayCheck = 0;       // when loadToday last ran
let lastStatus = null;        // last announced status
let loading = false;          // avoid overlapping requests

// Tell screen readers only when the status changes, not on every refresh.
function announceStatus(reading) {
    const view = viewFor(reading);
    const live = ['normal', 'warning', 'alert'].includes(reading.status) &&
        reading.ageSeconds !== null;
    let text = `Status ${view.title}, temperature unknown`;
    if (live) {
        text = `Status ${view.title}, ${reading.temperatureC.toFixed(1)} degrees Celsius`;
    } else if (reading.temperatureC !== null && ['stale', 'not_reporting'].includes(reading.status)) {
        text = `Status ${view.title}, last measured ${reading.temperatureC.toFixed(1)} degrees Celsius, not live`;
    }

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
        const response = await fetch(`${API_BASE}/boxes/TS-01/status`);
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        return null;
    }
}

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
        if (Date.now() - lastStateCheck > 15000) {
            lastStateCheck = Date.now();
            await loadRecentState();
        }
        if (Date.now() - lastTodayCheck > 60000) {
            lastTodayCheck = Date.now();
            await loadToday();
        }

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
