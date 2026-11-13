// Temperature history graph and table for the prototype box.
// Loads readings from GET /api/boxes/{box_id}/readings. The API returns them
// in descending measurement order (sequence_no). The table keeps this order;
// the graph shows them from oldest (left) to newest (right).
// Missing temperatures and sensor errors are never shown as 0°C.
// Each reading has its own recorded profile (limits) and temperature_state,
// so older readings keep the limits that applied when they were measured.

const HISTORY_BOX_ID = 'TS-01';
const HISTORY_LIMIT = 100;   // the API allows up to 100

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Limits recorded with one reading, or null if they are missing.
function readingProfile(reading) {
    const p = reading && reading.profile;
    if (!p) return null;
    const profile = {
        lowerC: Number(p.lower_c),
        warningC: Number(p.warning_c),
        upperC: Number(p.upper_c),
    };
    return Number.isFinite(profile.lowerC) && Number.isFinite(profile.upperC) ? profile : null;
}

// Alert kind of one reading: 'high', 'low' or null. Uses the API classification.
function alertKind(reading) {
    const v = readingValue(reading);
    const profile = readingProfile(reading);
    if (v === null || !profile) return null;
    const state = String(reading.temperature_state || '').toLowerCase();
    if (state !== 'alert') return null;
    return v <= profile.lowerC ? 'low' : 'high';
}

// Short local time: "14:20:05" for today, "3 Nov, 14:20" for other days.
function formatTime(value) {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    const today = new Date();
    const sameDay = date.toDateString() === today.toDateString();
    return sameDay
        ? date.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit', second: '2-digit'})
        : date.toLocaleString('en-IE', {day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'});
}

function observationCell(reading) {
    const observed = reading.clock_reliable ? formatTime(reading.observed_at) : null;
    if (observed) {
        return escapeHtml(observed);
    }
    // The box clock was not reliable, so the exact measurement time is unknown.
    // Show when the server received the reading instead, clearly marked.
    const received = formatTime(reading.received_at);
    if (!received) return '<span class="cell-warning">Unknown</span>';
    return `${escapeHtml(received)} <small class="muted">(received)</small>`;
}

function temperatureCell(reading) {
    if (reading.quality === 'sensor_error') {
        return '<span aria-label="Temperature unknown">—</span>';
    }
    if (reading.temperature_c === null || reading.temperature_c === undefined) {
        return '<span aria-label="Temperature missing">—</span>';
    }
    const value = Number(reading.temperature_c);
    if (Number.isNaN(value)) {
        return '<span aria-label="Temperature invalid">—</span> <small class="muted">Invalid</small>';
    }
    return value.toFixed(1);
}

// Status of one reading: never "Normal" for a failed or missing reading.
// Uses the temperature_state that the API calculated with the reading's own limits.
function statusCell(reading) {
    if (reading.quality === 'sensor_error') {
        return '<span class="tag alert">⚠ Sensor fault</span>';
    }
    if (readingValue(reading) === null) {
        return '<span class="tag unknown">? Unknown</span>';
    }
    const state = String(reading.temperature_state || '').toLowerCase();
    if (state === 'alert') {
        return alertKind(reading) === 'low'
            ? '<span class="tag alert">✕ Too cold</span>'
            : '<span class="tag alert">✕ Too hot</span>';
    }
    if (state === 'warning') return '<span class="tag warning">! Warning</span>';
    if (state === 'normal') return '<span class="tag normal">✓ OK</span>';
    return '<span class="tag unknown">? Unknown</span>';
}

function renderTable(readings, caption) {
    const rows = readings.map((reading) => `
        <tr>
            <td>${observationCell(reading)}</td>
            <td>${temperatureCell(reading)}</td>
            <td>${statusCell(reading)}</td>
        </tr>`).join('');

    return `
        <div aria-label="Temperature readings table" class="table-wrap" role="region" tabindex="0">
            <table class="history-table">
                <caption>${escapeHtml(caption)}</caption>
                <thead>
                <tr>
                    <th scope="col">Time</th>
                    <th scope="col">°C</th>
                    <th scope="col">Status</th>
                </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

// Read a temperature as a number, or null when it is missing or invalid.
function readingValue(reading) {
    if (reading.quality !== 'valid') return null;
    if (reading.temperature_c === null || reading.temperature_c === undefined) return null;
    const value = Number(reading.temperature_c);
    return Number.isFinite(value) ? value : null;
}

// Seconds between two readings, or null if a time is unknown.
function secondsBetween(earlier, later) {
    if (!earlier || !later || !earlier.clock_reliable || !later.clock_reliable) return null;
    const s = (new Date(later.observed_at) - new Date(earlier.observed_at)) / 1000;
    return Number.isFinite(s) ? s : null;
}

// No reading for longer than this means data is missing (same limit as NO NEW DATA).
const MAX_GAP_SECONDS = 90;

// True when readings are missing between two readings: the device numbers
// every sample, so a jump in sequence_no or a long time gap means a gap.
function hasGap(earlier, later) {
    if (!earlier || !later) return false;
    const a = Number(earlier.sequence_no);
    const b = Number(later.sequence_no);
    if (Number.isFinite(a) && Number.isFinite(b) && b - a > 1) return true;
    const seconds = secondsBetween(earlier, later);
    return seconds !== null && seconds > MAX_GAP_SECONDS;
}

// Short clock time for the graph, e.g. "14:20".
// Time label under the graph. Falls back to the receipt time when the device clock
// was not reliable, so the axis does not say "Oldest".
function graphLabel(reading) {
    const observed = graphTime(reading);
    if (observed || !reading || !reading.received_at) return observed;
    const date = new Date(reading.received_at);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
}

function graphTime(reading) {
    if (!reading || !reading.clock_reliable || !reading.observed_at) return null;
    const date = new Date(reading.observed_at);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
}

// Line graph of the readings with the warning and upper limit lines.
// Sensor errors and missing values break the line; they are never drawn as 0°C.
function renderGraph(readings) {
    const profile = readingProfile(readings[0]);   // limits of the newest reading
    const points = readings.slice().reverse();   // oldest first
    const values = points.map(readingValue);
    const known = values.filter((v) => v !== null);

    if (known.length < 2) {
        // A graph needs at least two measured temperatures. Sensor errors do not count.
        const word = known.length === 1 ? '1 temperature' : 'no temperatures';
        return `<div class="banner" role="status"><strong>Graph needs 2 or more readings</strong><br>` +
            `This period has ${word}.</div>` +
            `<button type="button" class="view-btn" data-goto-view="readings">See readings</button>`;
    }

    const W = 400, H = 220, L = 38, R = 10, T = 14, B = 30;
    const limits = [];
    if (profile && Number.isFinite(profile.warningC)) limits.push(profile.warningC);
    if (profile && Number.isFinite(profile.upperC)) limits.push(profile.upperC);

    let min = Math.floor(Math.min(...known, ...limits) - 1);
    let max = Math.ceil(Math.max(...known, ...limits) + 1);
    if (max - min < 4) max = min + 4;

    const n = points.length;
    const x = (i) => L + (n === 1 ? 0 : i * (W - L - R) / (n - 1));
    const y = (v) => T + (max - v) / (max - min) * (H - T - B);

    let svg = '';

    // Horizontal grid lines with temperature labels.
    const step = Math.max(1, Math.round((max - min) / 4));
    for (let v = min; v <= max; v += step) {
        svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="graph-grid"/>`;
        svg += `<text x="${L - 6}" y="${y(v) + 4}" text-anchor="end" class="graph-axis">${v}°</text>`;
    }

    // Limit lines with text labels.
    if (profile && Number.isFinite(profile.upperC)) {
        svg += `<line x1="${L}" x2="${W - R}" y1="${y(profile.upperC)}" y2="${y(profile.upperC)}" class="graph-upper"/>`;
    }
    if (profile && Number.isFinite(profile.warningC)) {
        svg += `<line x1="${L}" x2="${W - R}" y1="${y(profile.warningC)}" y2="${y(profile.warningC)}" class="graph-warning"/>`;
    }

    // Missing data: a thin grey dashed line joins the readings on both sides, so the graph
    // stays easy to follow but the gap is still clearly visible (FR-07, P5). It is never
    // drawn as a measured value.
    let prevKnown = null;
    let gapCount = 0;
    values.forEach((v, i) => {
        if (v === null) return;
        if (prevKnown !== null && (i - prevKnown > 1 || hasGap(points[prevKnown], points[i]))) {
            svg += `<line x1="${x(prevKnown).toFixed(1)}" y1="${y(values[prevKnown]).toFixed(1)}" ` +
                `x2="${x(i).toFixed(1)}" y2="${y(v).toFixed(1)}" class="graph-gap"/>`;
            gapCount++;
        }
        prevKnown = i;
    });

    // Temperature line, broken at sensor errors and missing values.
    let segment = [];
    const flush = () => {
        if (segment.length > 1) {
            svg += `<polyline points="${segment.join(' ')}" class="graph-line"/>`;
        }
        segment = [];
    };
    values.forEach((v, i) => {
        if (v === null || (i > 0 && hasGap(points[i - 1], points[i]))) {
            flush();
        }
        if (v === null) return;
        segment.push(`${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    });
    flush();

    // Points: red above the upper limit, blue otherwise.
    values.forEach((v, i) => {
        if (v === null) return;
        const high = alertKind(points[i]) !== null;
        svg += `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="${high ? 3.5 : 2.5}" class="${high ? 'graph-point-high' : 'graph-point'}"/>`;
    });

    // Time labels for the first and last reading.
    const first = graphLabel(points[0]) || 'Oldest';
    const last = graphLabel(points[n - 1]) || 'Latest';
    svg += `<text x="${L}" y="${H - 6}" class="graph-axis">${escapeHtml(first)}</text>`;
    svg += `<text x="${W - R}" y="${H - 6}" text-anchor="end" class="graph-axis">${escapeHtml(last)}</text>`;

    // Text summary for screen readers.
    const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;
    const gaps = values.length - known.length;
    let summary = `Temperature graph of the latest ${n} readings, oldest on the left. ` +
        `Lowest ${Math.min(...known).toFixed(1)}°C, highest ${Math.max(...known).toFixed(1)}°C. `;
    if (profile && Number.isFinite(profile.upperC)) {
        const outside = points.filter((r) => alertKind(r) !== null).length;
        summary += `${plural(outside, 'reading')} outside the limits. `;
    }
    summary += `${plural(gaps, 'gap')} for sensor errors or missing values. The same data is in Readings.`;

    // Legend with text labels for the limit lines.
    let legend = '<ul class="graph-legend">';
    if (profile && Number.isFinite(profile.upperC)) {
        legend += `<li><span class="legend-upper" aria-hidden="true"></span>Limit ${profile.upperC}°C</li>`;
    }
    if (profile && Number.isFinite(profile.warningC)) {
        legend += `<li><span class="legend-warning" aria-hidden="true"></span>Warning ${profile.warningC}°C</li>`;
    }
    legend += '<li><span class="legend-high" aria-hidden="true"></span>Alert</li>';
    if (gapCount > 0) {
        legend += '<li><span class="legend-gap" aria-hidden="true"></span>No data</li>';
    }
    legend += '</ul>';

    return `
        <figure class="graph">
            <svg aria-labelledby="graph-title graph-desc" role="img" viewBox="0 0 ${W} ${H}">
                <title id="graph-title">Temperature graph</title>
                <desc id="graph-desc">${escapeHtml(summary)}</desc>
                ${svg}
            </svg>
            <figcaption>
                ${legend}
            </figcaption>
        </figure>`;
}

// Find alert periods (FR-13): readings in a row that the API classified as Alert
// (above the upper limit or at/below the lower limit, using each reading's own limits).
// A sensor error, a missing reading (jump in sequence_no) or a long time gap breaks
// a period. The end is the first reading back within the limits, so the duration is estimated.
function findAlertPeriods(readings) {
    const points = readings.slice().reverse();   // oldest first
    const periods = [];
    let current = null;

    const close = (endReading, reason) => {
        current.end = endReading;
        current.reason = reason;
        periods.push(current);
        current = null;
    };

    let previous = null;
    points.forEach((reading) => {
        const v = readingValue(reading);
        if (v === null) {
            if (current) close(reading, 'gap');
            previous = reading;
            return;
        }
        // Missing readings: we do not know what happened, so the period stops here.
        if (current && hasGap(previous, reading)) {
            close(previous, 'nodata');
        }
        previous = reading;
        const kind = alertKind(reading);

        if (current && kind !== current.kind) {
            close(reading, 'back');
        }
        if (kind && !current) {
            current = {kind, start: reading, peak: v};
        } else if (kind && current) {
            current.peak = kind === 'high' ? Math.max(current.peak, v) : Math.min(current.peak, v);
        }
    });
    if (current) {
        current.end = null;
        current.reason = 'ongoing';
        periods.push(current);
    }
    return periods;
}

function periodTime(reading) {
    return graphTime(reading) || 'time unknown';
}

// Date of an alert, e.g. "5 Nov 2026". Shown for every alert (usability test finding 3).
function periodDate(reading) {
    if (!reading || !reading.clock_reliable || !reading.observed_at) return null;
    const date = new Date(reading.observed_at);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleDateString('en-IE', {day: 'numeric', month: 'short', year: 'numeric'});
}

// Opening History counts as viewing the alerts, so the dashboard banner goes away.
function markAlertsSeen(readings) {
    let newest = 0;
    readings.forEach((r) => {
        if (String(r.temperature_state || '').toLowerCase() === 'alert') {
            newest = Math.max(newest, Number(r.sequence_no) || 0);
        }
    });
    if (!newest) return;
    try {
        const key = `tempsafe.seenAlert.${HISTORY_BOX_ID}`;
        if (newest > (Number(localStorage.getItem(key)) || 0)) localStorage.setItem(key, String(newest));
    } catch (error) {
        // Storage can be blocked; nothing else depends on it.
    }
}

function periodMinutes(start, end) {
    if (!start || !end || !start.clock_reliable || !end.clock_reliable) return null;
    const ms = new Date(end.observed_at) - new Date(start.observed_at);
    if (!Number.isFinite(ms) || ms < 0) return null;
    return Math.max(1, Math.round(ms / 60000));
}

// Short list of alert periods above the graph.
function renderAlertPeriods(readings) {
    const periods = findAlertPeriods(readings);

    if (periods.length === 0) {
        return `<p class="period-none">✓ No alerts</p>`;
    }

    const rows = periods.slice().reverse().map((p) => {   // newest first
        const label = p.kind === 'high' ? '⚠ Too hot' : '⚠ Too cold';
        const peak = `${p.peak.toFixed(1)}°C`;   // highest for Too hot, lowest for Too cold
        const start = periodTime(p.start);
        let when;
        let length;

        if (p.reason === 'ongoing') {
            when = `since ${start}`;
            length = 'now';
        } else {
            const minutes = periodMinutes(p.start, p.end);
            const unsure = p.reason === 'gap' || p.reason === 'nodata';
            length = minutes === null ? 'unknown' : (unsure ? `${minutes}+ min` : `${minutes} min`);
            if (p.reason === 'gap') {
                when = `${start} – fault`;
            } else if (p.reason === 'nodata') {
                when = `${start} – no data`;
            } else {
                const end = periodTime(p.end);
                when = start === end ? start : `${start} – ${end}`;
            }
        }
        const day = periodDate(p.start);
        return `<tr>
            <th scope="row">${label}</th>
            <td class="period-date">${escapeHtml(day || 'unknown')}</td>
            <td>${escapeHtml(when)}</td>
            <td><strong>${escapeHtml(length)}</strong></td>
            <td>${peak}</td>
        </tr>`;
    }).join('');

    return `
        <section class="periods table-wrap" aria-label="Alerts table" role="region" tabindex="0">
            <table class="periods-table">
                <caption class="periods-title">Alerts</caption>
                <thead>
                <tr>
                    <th scope="col">Alert</th>
                    <th scope="col">Date</th>
                    <th scope="col">Time</th>
                    <th scope="col">Length (est.)</th>
                    <th scope="col">Peak</th>
                </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </section>`;
}

function showMessage(container, className, title, text) {
    container.innerHTML = `
        <div class="banner ${className}" role="${className === 'error' ? 'alert' : 'status'}">
            <strong>${escapeHtml(title)}</strong>${text ? '<br>' + escapeHtml(text) : ''}
        </div>`;
}

// Time filter (FR-07). "latest" shows the latest 100 readings.
// The other choices send from/to (UTC) to the API and also filter here,
// so the page only shows readings from the chosen period.
const RANGES = {
    latest: {label: 'Latest 100'},
    hour: {label: '1 hour'},
    today: {label: 'Today'},
    day: {label: '24 hours'},
};
let currentRange = {key: 'latest'};

function rangeTimes(range) {
    const now = new Date();
    if (range.key === 'hour') return {from: new Date(now - 3600 * 1000), to: now};
    if (range.key === 'day') return {from: new Date(now - 24 * 3600 * 1000), to: now};
    if (range.key === 'today') {
        const start = new Date(now);
        start.setHours(0, 0, 0, 0);
        return {from: start, to: now};
    }
    if (range.key === 'date' && range.date) {
        const start = new Date(`${range.date}T00:00:00`);
        const end = new Date(start);
        end.setDate(end.getDate() + 1);
        return {from: start, to: end};
    }
    return null;
}

function rangeLabel(range) {
    if (range.key === 'date' && range.date) {
        return new Date(`${range.date}T00:00:00`).toLocaleDateString('en-IE', {day: 'numeric', month: 'long', year: 'numeric'});
    }
    return RANGES[range.key] ? RANGES[range.key].label : 'Latest 100';
}

// Time used to place a reading in a period: observation time, or receipt time
// when the device clock was not reliable.
function readingTime(reading) {
    const value = reading.clock_reliable ? reading.observed_at : reading.received_at;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

function renderFilter() {
    const filter = document.getElementById('history-filter');
    if (!filter) return;
    const buttons = Object.entries(RANGES).map(([key, r]) =>
        `<button type="button" class="filter-btn" data-range="${key}" aria-pressed="${currentRange.key === key}">${r.label}</button>`
    ).join('');
    const today = new Date();
    const max = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    filter.innerHTML = `
        <div class="filter-row">
            <div class="filter-buttons" role="group" aria-label="Period">${buttons}</div>
            <label class="filter-date">Date
                <input type="date" id="history-date" max="${max}" value="${currentRange.key === 'date' ? currentRange.date : ''}">
            </label>
        </div>`;

    filter.querySelectorAll('[data-range]').forEach((button) => {
        button.addEventListener('click', () => {
            currentRange = {key: button.dataset.range};
            renderFilter();
            loadHistory();
        });
    });
    const dateInput = filter.querySelector('#history-date');
    dateInput.addEventListener('change', () => {
        if (!dateInput.value) return;
        currentRange = {key: 'date', date: dateInput.value};
        renderFilter();
        loadHistory();
    });
}

// Views (usability: one thing at a time, chosen with a clear button).
// The view is kept in the address (#alerts, #graph, #readings), so the dashboard
// buttons and the "View" button on the alert banner open the right one.
const VIEWS = {
    alerts: 'Alerts',
    graph: 'Graph',
    readings: 'Readings',
};
let currentView = VIEWS[location.hash.slice(1)] ? location.hash.slice(1) : 'graph';
let lastReadings = null;
let lastSummary = '';

function renderViews() {
    const box = document.getElementById('history-views');
    if (!box) return;
    box.innerHTML = `<div class="view-buttons" role="group" aria-label="Show">${
        Object.entries(VIEWS).map(([key, label]) =>
            `<button type="button" class="view-btn" data-view="${key}" aria-pressed="${currentView === key}">${label}</button>`
        ).join('')}</div>`;
    box.querySelectorAll('[data-view]').forEach((button) => {
        button.addEventListener('click', () => {
            currentView = button.dataset.view;
            history.replaceState(null, '', `#${currentView}`);
            renderViews();
            showView(false);
        });
    });
}

function showView(focus) {
    const container = document.getElementById('history');
    if (!container || !lastReadings) return;
    let body;
    if (currentView === 'alerts') {
        body = renderAlertPeriods(lastReadings);
        markAlertsSeen(lastReadings);   // the user has now seen the alerts
    } else if (currentView === 'readings') {
        body = renderTable(lastReadings, 'Readings');
    } else {
        body = renderGraph(lastReadings);
    }
    container.innerHTML = `<p class="history-summary">${escapeHtml(lastSummary)}</p>${body}`;
    const goto = container.querySelector('[data-goto-view]');
    if (goto) {
        goto.addEventListener('click', () => {
            currentView = goto.dataset.gotoView;
            history.replaceState(null, '', `#${currentView}`);
            renderViews();
            showView(true);
        });
    }
    if (focus) container.focus();
}

async function loadHistory() {
    const container = document.getElementById('history');
    if (!container) return;

    container.setAttribute('aria-busy', 'true');
    showMessage(container, '', 'Loading…', '');

    const times = rangeTimes(currentRange);
    let query = `limit=${HISTORY_LIMIT}`;
    if (times) {
        query += `&from=${encodeURIComponent(times.from.toISOString())}&to=${encodeURIComponent(times.to.toISOString())}`;
    }

    try {
        const response = await fetch(
            `${API_BASE}/boxes/${HISTORY_BOX_ID}/readings?${query}`,
            {headers: {Accept: 'application/json'}}
        );

        // Not signed in or the session has ended.
        if (response.status === 401) {
            goToSignIn();
            return;
        }
        // The box does not exist or is not assigned to this user.
        if (response.status === 404) {
            showMessage(container, 'error', 'No access', 'Ask your admin for box TS-01.');
            return;
        }
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }

        let readings = await response.json();
        if (!Array.isArray(readings)) readings = [];

        if (times) {
            readings = readings.filter((r) => {
                const t = readingTime(r);
                return t !== null && t >= times.from && t < times.to;
            });
        }

        if (readings.length === 0) {
            lastReadings = null;
            if (times) {
                showMessage(container, '', 'No readings in this period', 'Choose another period.');
            } else {
                showMessage(container, '', 'No readings yet', 'Check the box is on.');
            }
            return;
        }

        lastReadings = readings;
        lastSummary = `${readings.length} readings · ${rangeLabel(currentRange)}` +
            (times && readings.length >= HISTORY_LIMIT ? ` (latest ${HISTORY_LIMIT})` : '');
        showView(false);

    } catch (error) {
        console.error('History error:', error);
        showMessage(container, 'error', "Can't load", 'Check your internet and refresh.');
    } finally {
        container.setAttribute('aria-busy', 'false');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    renderFilter();
    renderViews();
    await loadHistory();
    // Opened from a dashboard button: move keyboard and screen reader focus to the view.
    if (location.hash) {
        const container = document.getElementById('history');
        if (container) container.focus();
    }
});
