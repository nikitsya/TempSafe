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
// "5 s ago", "4 min ago", "3 h ago", "1 day 16 h ago" (test 18 Nov, T1-04: no "1 days ago").
function ageText(seconds) {
    if (seconds < 60) return `${seconds} s ago`;
    return `${readableDuration(seconds / 60)} ago`;
}

// ---- How long the current status has lasted, and the alert banner ----
// Uses the latest 100 readings: counts back while the status stays the same.
let stateSince = null;     // time the current Warning or Alert started (ms)
let recentReadings = [];   // latest 100 readings, newest first (for the Last hour chart)
let todayStats = null;     // {min, max, alerts, lastAlert} for today
let alertBanner = null;    // {low: true/false} while an alert is on
let recentOutside = [];   // outside sensor, last hour, newest first (comparison only)

// "4 min", "1 h 20 min", "1 day 16 h", "1 month 3 days" (main.js).
function shortDuration(ms) {
    return readableDuration(ms / 60000);
}

// The last hour of one sensor, newest first. 100 readings at 30 s are only 50 minutes,
// so more pages are loaded until the whole hour is covered. Paging keeps the sensor.
async function lastHourReadings(sensor) {
    const outside = sensor === 'outside';
    const where = outside ? '&sensor_location=outside' : '';
    const response = await fetch(`${API_BASE}/boxes/TS-01/readings?limit=100${where}`);
    if (!response.ok) return outside ? [] : null;
    let readings = await response.json();
    if (!Array.isArray(readings)) return outside ? [] : null;
    // An older backend ignores sensor_location: keep only rows that say they are outside.
    if (outside) readings = readings.filter((r) => r.sensor_location === 'outside');
    const hourAgo = Date.now() - 3600 * 1000;
    for (let page = 0; page < 5 && readings.length && readings.length % 100 === 0; page++) {
        const oldest = readings[readings.length - 1];
        if (new Date(oldest.observed_at).getTime() < hourAgo) break;
        const more = await fetch(`${API_BASE}/boxes/TS-01/readings?limit=100${where}&before_sequence=${oldest.sequence_no}`);
        if (!more.ok) break;
        const rows = await more.json();
        if (!Array.isArray(rows) || rows.length === 0) break;
        readings.push(...rows);
    }
    return readings;
}

async function loadRecentState() {
    try {
        const [readings, outside] = await Promise.all([
            lastHourReadings('inside'),
            lastHourReadings('outside').catch(() => []),
        ]);
        recentOutside = outside || [];
        if (!Array.isArray(readings) || readings.length === 0) return;
        recentReadings = readings;
        const stateOf = (r) => r.quality === 'valid' ? String(r.temperature_state || '').toLowerCase() : null;
        const current = stateOf(readings[0]);
        stateSince = null;
        alertBanner = null;
        if (current === 'warning' || current === 'alert') {
            let first = readings[0];
            for (let i = 1; i < readings.length; i++) {
                if (readingGap(readings[i], readings[i - 1]) || stateOf(readings[i]) !== current) break;
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
// "16 Nov 2026" in Irish time.
function dayLabel(date) {
    return date.toLocaleDateString('en-IE', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Europe/Dublin'});
}

function todayLabel() {
    return dayLabel(new Date());
}

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
    // Two labelled values, so "-3.4 – 30.9" is not read as two minus numbers (test 18 Nov, T2-01).
    const num = (v) => {
        const r = Number(v.toFixed(1));   // same rounding as the main tile; -0.04 shows as 0.0, not −0.0
        return `${r < 0 ? '−' : ''}${Math.abs(r).toFixed(1)}`;
    };
    // Today's range is reloaded every minute, so the readings since then are added here.
    // Otherwise Max could stay below the temperature shown now.
    let low = todayStats ? todayStats.min : null;
    let high = todayStats ? todayStats.max : null;
    const today = todayLabel();
    recentReadings.forEach((r) => {
        if (r.quality !== 'valid' || r.temperature_c == null) return;
        const v = Number(r.temperature_c);
        if (!Number.isFinite(v) || dayLabel(new Date(r.observed_at)) !== today) return;
        low = low === null ? v : Math.min(low, v);
        high = high === null ? v : Math.max(high, v);
    });
    if (reading.temperatureC !== null && reading.observedDay === today) {
        low = low === null ? reading.temperatureC : Math.min(low, reading.temperatureC);
        high = high === null ? reading.temperatureC : Math.max(high, reading.temperatureC);
    }
    const range = low !== null
        ? `<span class="range-pair"><span><small>Min</small> ${num(low)}<small>°C</small></span>` +
          `<span><small>Max</small> ${num(high)}<small>°C</small></span></span>` : '—';
    const alerts = todayStats ? String(todayStats.alerts) : '—';
    const alertSub = todayStats && todayStats.lastAlert ? `last at ${formatClock(todayStats.lastAlert)}` : 'none today';
    // Not today: show the date as well, so "19:18" is not read as today or yesterday (T1-04).
    const measured = reading.observedClock || '—';
    const day = reading.observedDay && reading.observedDay !== todayLabel() ? `${reading.observedDay} · ` : '';
    const ago = reading.ageSeconds !== null ? `${day}${ageText(reading.ageSeconds)}` : day.replace(' · ', '');
    return tile("Today's range", range, '') +
        tile('Alerts today', alerts, alertSub, todayStats && todayStats.alerts ? 'tile-alert' : '') +
        tile('Last measured', measured, ago);
}


// ---- Outside the box (AM2302, comparison only) ----
// Statuses, alerts, pop-ups and the LED/buzzer stay tied to the inside sensor (dual-sensor handover).
function outsideOf(r) {
    if (!r || r.quality !== 'valid' || r.temperature_c == null) return null;
    const v = Number(r.temperature_c);
    return Number.isFinite(v) ? v : null;
}

// Latest outside reading and its change over about 2 minutes.
function outsideTrend() {
    const latest = recentOutside[0];
    if (!latest) return null;
    const time = new Date(latest.observed_at).getTime();
    const stale = !latest.clock_reliable || Date.now() - time > READING_GAP_MS;
    const now = outsideOf(latest);
    let change = null;
    if (now !== null) {
        const older = recentOutside.find((r) => time - new Date(r.observed_at).getTime() >= 120000 && outsideOf(r) !== null);
        if (older && time - new Date(older.observed_at).getTime() <= 240000) change = now - outsideOf(older);
    }
    return {latest, now, change, stale, time};
}

// ---- Forecast: when may the inside reach Warning? ----
// Requested by the lecturer (22 Nov) and based on Hanna's heating run of 20 Nov
// (docs/testing/hardware/external-temperature-experiment.md, "Proposed follow-up").
const FORECAST_WINDOW_MS = 2 * 60 * 1000;   // inside readings of the last 2 minutes
const FORECAST_MIN_READINGS = 4;            // fewer readings: the rise is not confirmed
const FORECAST_MIN_RATE = 0.2;              // °C per minute; slower is not a confirmed rise
const FORECAST_MARGIN = 0.85;               // heating speeds up, so a straight line is late:
                                            // in the run, 85% of it was never later than reality

// How fast the inside temperature is rising, in °C per minute: a straight line fitted to the
// inside readings of the last 2 minutes. null when there are too few readings, or a gap,
// sensor error or unreliable time inside that window.
function insideRate() {
    const latest = recentReadings[0];
    if (!latest || latest.quality !== 'valid' || !latest.clock_reliable) return null;
    const end = new Date(latest.observed_at).getTime();
    const points = [];
    for (let i = 0; i < recentReadings.length; i++) {
        const r = recentReadings[i];
        const t = new Date(r.observed_at).getTime();
        if (end - t > FORECAST_WINDOW_MS) break;
        if (r.quality !== 'valid' || !r.clock_reliable) return null;
        if (i > 0 && readingGap(r, recentReadings[i - 1])) return null;
        points.push({t: (t - end) / 60000, v: Number(r.temperature_c)});
    }
    if (points.length < FORECAST_MIN_READINGS) return null;
    const n = points.length;
    const mt = points.reduce((a, p) => a + p.t, 0) / n;
    const mv = points.reduce((a, p) => a + p.v, 0) / n;
    const den = points.reduce((a, p) => a + (p.t - mt) ** 2, 0);
    if (den === 0) return null;
    return points.reduce((a, p) => a + (p.t - mt) * (p.v - mv), 0) / den;
}

// The blue card (Hanna, 22 Nov): shown as soon as the OUTSIDE reading is fresh, has reached
// "Warning from" of the active profile and is rising (at least
// +0.3°C in 2 minutes). It does not wait for the inside to rise, so it also shows when
// only the outside AM2302 is heated in a demo. null when the card is not needed.
function outsideWarm(profile) {
    const trend = outsideTrend();
    const warning = profile ? Number(profile.warningC) : NaN;
    if (!trend || trend.stale || trend.now === null || trend.change === null || !Number.isFinite(warning)) return null;
    if (!(trend.now >= warning && trend.change >= 0.3)) return null;
    const inside = recentReadings[0];
    const insideWarm = !!inside && inside.quality === 'valid' && Number(inside.temperature_c) >= warning;
    return {outside: trend.now, warning, insideWarm, forecast: warningForecast(warning)};
}

// The time in the card (lecturer, 22 Nov) is added only when the inside rise is confirmed:
// the inside reading is fresh, valid and still below "Warning from", and rising by at least
// 0.2°C per minute over the last 2 minutes (4+ readings).
// The time comes from the INSIDE readings only: (Warning from − inside now) ÷ inside rate.
function warningForecast(warning) {
    const inside = recentReadings[0];
    if (!inside || inside.quality !== 'valid' || readingGap(inside, {observed_at: new Date().toISOString()})) return null;
    const insideC = Number(inside.temperature_c);
    if (!(insideC < warning)) return null;
    const rate = insideRate();
    if (rate === null || rate < FORECAST_MIN_RATE) return null;
    return {inside: insideC, rate, minutes: ((warning - insideC) / rate) * FORECAST_MARGIN};
}

// "less than a minute", "about 1 minute", "about 3 minutes" (rounded down, never later than measured).
function forecastText(minutes) {
    if (minutes < 1) return 'in less than a minute';
    const n = Math.floor(minutes);
    return `in about ${n} minute${n === 1 ? '' : 's'}`;
}

function renderOutsideBanner(profile) {
    const box = document.getElementById('outside-banner');
    if (!box) return;
    const warm = alertBanner ? null : outsideWarm(profile);
    if (!warm) {
        box.innerHTML = '';
        return;
    }
    const limit = Number.isInteger(warm.warning) ? String(warm.warning) : warm.warning.toFixed(1);
    // With a confirmed inside rise the card says when; before that it says why.
    const text = warm.forecast
        ? `<h2 id="outside-banner-title">Warning ${forecastText(warm.forecast.minutes)}</h2>
                <p>Inside is warming fast. Check where the box is kept.</p>
                <p class="forecast-note">Estimate from the last 2 minutes.</p>`
        : `<h2 id="outside-banner-title">Outside has reached ${limit}°C and is rising</h2>
                <p>${warm.insideWarm ? '' : 'The inside may warm up soon. '}Check where the box is kept.</p>`;
    box.innerHTML = `
        <section aria-labelledby="outside-banner-title" class="info-banner" role="status">
            <span aria-hidden="true" class="info-banner-icon">i</span>
            <div>
                ${text}
            </div>
        </section>`;
}

// Dashboard tile for the outside sensor. Faults and old data are shown as such, never hidden.
function outsideTile() {
    const trend = outsideTrend();
    if (!trend) return '';
    if (trend.latest.quality === 'sensor_error') {
        return tile('Outside the box', '<span class="outside-fault">Sensor fault</span>', 'No outside temperature', 'tile-outside');
    }
    if (trend.now === null) return '';
    const value = `${trend.now.toFixed(1)}<small>°C</small>`;
    if (trend.stale) {
        return tile('Outside the box', `<span class="value-old">${value}</span>`,
            `Last reading ${formatClock(trend.latest.observed_at)}`, 'tile-outside');
    }
    // Only the temperature (Hanna, 22 Nov: too many numbers). Rising or not is used by the blue card.
    return tile('Outside the box', value, '', 'tile-outside');
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
        // Outside the box (comparison only), oldest first, in the same hour.
        const outsidePts = recentOutside.slice().reverse().filter((r) => {
            const t = new Date(r.observed_at).getTime();
            return r.clock_reliable && t >= from && t <= now + 30000;
        });
        const outsideVals = outsidePts.map(outsideOf).filter((v) => v !== null);
        let min = Math.min(...values, ...outsideVals, profile.warningC) - 1;
        let max = Math.max(...values, ...outsideVals, profile.upperC) + 1;
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
            if (readingGap(points[i - 1], points[i])) band(times[i - 1], times[i], 'band-nodata');
            if (points[i - 1].quality === 'sensor_error') band(times[i - 1], times[i], 'band-fault');
        }
        if (times.length && now - times[times.length - 1] > 90000) band(times[times.length - 1], now, 'band-nodata');
        if (!times.length) band(from, now, 'band-nodata');

        for (let i = 1; i < points.length; i++) {
            const a = points[i - 1];
            const b = points[i];
            const gap = readingGap(a, b);
            if (gap || a.quality !== 'valid' || b.quality !== 'valid') continue;
            // The colour changes where the line crosses a limit.
            limitPieces(new Date(a.observed_at).getTime(), Number(a.temperature_c),
                new Date(b.observed_at).getTime(), Number(b.temperature_c), profile, color(b)).forEach((s) => {
                svg += `<line class="graph-seg ${s.cls}" x1="${x(s.t1).toFixed(1)}" y1="${y(s.v1).toFixed(1)}" ` +
                    `x2="${x(s.t2).toFixed(1)}" y2="${y(s.v2).toFixed(1)}"/>`;
            });
        }
        // Outside line: dashed blue, breaks at gaps and outside sensor faults.
        let outsidePath = '';
        outsidePts.forEach((r, i) => {
            const v = outsideOf(r);
            if (v === null) return;
            const prev = outsidePts[i - 1];
            const continues = prev && outsideOf(prev) !== null && !readingGap(prev, r);
            outsidePath += `${continues ? 'L' : 'M'}${x(new Date(r.observed_at).getTime()).toFixed(1)} ${y(v).toFixed(1)}`;
        });
        if (outsidePath) svg += `<path class="graph-outside" d="${outsidePath}"/>`;
        const last = valid[valid.length - 1];
        body = `<svg class="mini-chart" role="img" viewBox="0 0 ${W} ${H}"
                    aria-label="Temperature in the last hour: lowest ${Math.min(...values).toFixed(1)}°C, highest ${Math.max(...values).toFixed(1)}°C, now ${Number(last.temperature_c).toFixed(1)}°C.">${svg}</svg>`;
        body += `<ul class="graph-legend mini-legend">
            <li><span aria-hidden="true" class="legend-line line-normal"></span>Normal</li>
            <li><span aria-hidden="true" class="legend-line line-warning"></span>Warning</li>
            <li><span aria-hidden="true" class="legend-line line-alert"></span>Alert</li>
            ${limitLegend(profile, false)}
            ${outsidePath ? '<li><span aria-hidden="true" class="legend-outside"></span>Outside the box</li>' : ''}
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
    const outside = outsideTile();
    dashboard.innerHTML = `
        <div class="tiles ${outside ? 'tiles-5' : ''}">
            ${mainTile(reading)}
            ${todayTiles(reading)}
            ${outside}
        </div>
        ${lastHourChart(profile)}`;
    renderAlertBanner();
    renderOutsideBanner(profile);
}

// Today's lowest and highest temperature and number of alerts (refreshed every minute).
async function loadToday() {
    try {
        const today = new Intl.DateTimeFormat('en-CA', {
            timeZone: 'Europe/Dublin', year: 'numeric', month: '2-digit', day: '2-digit'
        }).format(new Date());
        const all = [];
        let before = null;
        // Every reading of today, page by page: no limit.
        while (true) {
            let url = `${API_BASE}/boxes/TS-01/readings?limit=100&start_date=${today}&end_date=${today}`;
            if (before !== null) url += `&before_sequence=${before}`;
            const response = await fetch(url);
            if (!response.ok) return;
            const rows = await response.json();
            all.push(...rows);
            if (rows.length < 100) break;
            const next = rows[rows.length - 1].sequence_no;
            if (before !== null && next >= before) break;   // safety: the API did not move back
            before = next;
        }
        const values = all.filter((r) => r.quality === 'valid').map((r) => Number(r.temperature_c)).filter(Number.isFinite);
        let alerts = 0;
        let lastAlert = null;
        const oldestFirst = all.slice().reverse();
        oldestFirst.forEach((r, i) => {
            const isAlert = String(r.temperature_state || '').toLowerCase() === 'alert';
            const prev = oldestFirst[i - 1];
            const prevAlert = prev && String(prev.temperature_state || '').toLowerCase() === 'alert' &&
                !readingGap(prev, r);
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
        observedDay: data.observed_at ? dayLabel(new Date(data.observed_at)) : null,
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
