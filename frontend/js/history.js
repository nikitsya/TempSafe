// Temperature history graph and table for the prototype box.
// Loads readings from GET /api/boxes/{box_id}/readings. The API returns them
// in descending measurement order (sequence_no). The table keeps this order;
// the graph shows them from oldest (left) to newest (right).
// Missing temperatures and sensor errors are never shown as 0°C.

const HISTORY_BOX_ID = 'TS-01';
const HISTORY_LIMIT = 100;   // the API allows up to 100

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
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
    // The device clock was not reliable: show when the server received it.
    const received = formatTime(reading.received_at);
    return `<span class="cell-warning">Unknown</span>` +
        (received ? `<br><small class="muted">got ${escapeHtml(received)}</small>` : '');
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
    return `${value.toFixed(1)}°C`;
}

// Status of one reading: never "Normal" for a failed or missing reading.
function statusCell(reading, profile) {
    if (reading.quality === 'sensor_error') {
        return '<span class="tag alert">⚠ Sensor error</span>';
    }
    const v = readingValue(reading);
    if (v === null) {
        return '<span class="tag unknown">? Unknown</span>';
    }
    if (!profile || !Number.isFinite(profile.upperC)) {
        return '<span class="tag normal">✓ Valid</span>';
    }
    if (v > profile.upperC) return '<span class="tag alert">✕ Too high</span>';
    if (Number.isFinite(profile.lowerC) && v <= profile.lowerC) return '<span class="tag alert">✕ Too low</span>';
    if (Number.isFinite(profile.warningC) && v >= profile.warningC) return '<span class="tag warning">! Warning</span>';
    return '<span class="tag normal">✓ Normal</span>';
}

function renderTable(readings, profile) {
    const rows = readings.map((reading) => `
        <tr>
            <td>${observationCell(reading)}</td>
            <td>${temperatureCell(reading)}</td>
            <td>${statusCell(reading, profile)}</td>
        </tr>`).join('');

    return `
        <div aria-label="Temperature readings table" class="table-wrap" role="region" tabindex="0">
            <table class="history-table">
                <caption>Last ${readings.length} readings</caption>
                <thead>
                <tr>
                    <th scope="col">Time</th>
                    <th scope="col">Temperature</th>
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

// Short clock time for the graph, e.g. "14:20".
function graphTime(reading) {
    if (!reading || !reading.clock_reliable || !reading.observed_at) return null;
    const date = new Date(reading.observed_at);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
}

// Line graph of the readings with the warning and upper limit lines.
// Sensor errors and missing values break the line; they are never drawn as 0°C.
function renderGraph(readings, profile) {
    const points = readings.slice().reverse();   // oldest first
    const values = points.map(readingValue);
    const known = values.filter((v) => v !== null);

    if (known.length < 2) {
        return '<p class="muted">Not enough readings for a graph yet.</p>';
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

    // Temperature line, broken at sensor errors and missing values.
    let segment = [];
    const flush = () => {
        if (segment.length > 1) {
            svg += `<polyline points="${segment.join(' ')}" class="graph-line"/>`;
        }
        segment = [];
    };
    values.forEach((v, i) => {
        const gap = i > 0 ? secondsBetween(points[i - 1], points[i]) : null;
        if (v === null || (gap !== null && gap > MAX_GAP_SECONDS)) {
            flush();
        }
        if (v === null) return;
        segment.push(`${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    });
    flush();

    // Points: red above the upper limit, blue otherwise.
    values.forEach((v, i) => {
        if (v === null) return;
        const high = profile && Number.isFinite(profile.upperC) && v > profile.upperC;
        svg += `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="${high ? 3.5 : 2.5}" class="${high ? 'graph-point-high' : 'graph-point'}"/>`;
    });

    // Time labels for the first and last reading.
    const first = graphTime(points[0]) || 'Oldest';
    const last = graphTime(points[n - 1]) || 'Latest';
    svg += `<text x="${L}" y="${H - 6}" class="graph-axis">${escapeHtml(first)}</text>`;
    svg += `<text x="${W - R}" y="${H - 6}" text-anchor="end" class="graph-axis">${escapeHtml(last)}</text>`;

    // Text summary for screen readers.
    const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;
    const gaps = values.length - known.length;
    let summary = `Temperature graph of the latest ${n} readings, oldest on the left. ` +
        `Lowest ${Math.min(...known).toFixed(1)}°C, highest ${Math.max(...known).toFixed(1)}°C. `;
    if (profile && Number.isFinite(profile.upperC)) {
        const above = known.filter((v) => v > profile.upperC).length;
        summary += `${plural(above, 'reading')} above the upper limit. `;
    }
    summary += `${plural(gaps, 'gap')} for sensor errors or missing values. The same data is in the table below.`;

    // Legend with text labels for the limit lines.
    let legend = '<ul class="graph-legend">';
    if (profile && Number.isFinite(profile.upperC)) {
        legend += `<li><span class="legend-upper" aria-hidden="true"></span>Limit ${profile.upperC}°C</li>`;
    }
    if (profile && Number.isFinite(profile.warningC)) {
        legend += `<li><span class="legend-warning" aria-hidden="true"></span>Warning ${profile.warningC}°C</li>`;
    }
    legend += '<li><span class="legend-high" aria-hidden="true"></span>Too high</li></ul>';

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

// Find alert periods (FR-13): readings in a row above the upper limit
// or at/below the lower limit. A sensor error or missing value breaks a period.
// The end is the first reading back within the limits, so the duration is estimated.
function findAlertPeriods(readings, profile) {
    if (!profile || !Number.isFinite(profile.upperC) || !Number.isFinite(profile.lowerC)) {
        return null;
    }
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
        // A long time without readings also breaks a period: we do not know what happened.
        const gap = secondsBetween(previous, reading);
        if (current && gap !== null && gap > MAX_GAP_SECONDS) {
            close(previous, 'nodata');
        }
        previous = reading;
        const kind = v > profile.upperC ? 'high' : (v <= profile.lowerC ? 'low' : null);

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

function periodMinutes(start, end) {
    if (!start || !end || !start.clock_reliable || !end.clock_reliable) return null;
    const ms = new Date(end.observed_at) - new Date(start.observed_at);
    if (!Number.isFinite(ms) || ms < 0) return null;
    return Math.max(1, Math.round(ms / 60000));
}

// Short list of alert periods above the graph.
function renderAlertPeriods(readings, profile) {
    const periods = findAlertPeriods(readings, profile);
    if (periods === null) return '';

    if (periods.length === 0) {
        return `<p class="period-none">✓ No alerts in these readings</p>`;
    }

    const rows = periods.slice().reverse().map((p) => {   // newest first
        const label = p.kind === 'high' ? '⚠ Too hot' : '⚠ Too cold';
        const peak = `${p.peak.toFixed(1)}°C`;   // highest for Too hot, lowest for Too cold
        const start = periodTime(p.start);
        let when;
        let length;

        if (p.reason === 'ongoing') {
            when = `since ${start}`;
            length = 'still going';
        } else {
            const minutes = periodMinutes(p.start, p.end);
            const unsure = p.reason === 'gap' || p.reason === 'nodata';
            length = minutes === null ? 'unknown' : `${unsure ? 'at least' : 'about'} ${minutes} min`;
            if (p.reason === 'gap') {
                when = `${start} – sensor error`;
            } else if (p.reason === 'nodata') {
                when = `${start} – no data`;
            } else {
                const end = periodTime(p.end);
                when = start === end ? start : `${start} – ${end}`;
            }
        }
        return `<tr>
            <th scope="row">${label}</th>
            <td>${escapeHtml(when)}</td>
            <td><strong>${escapeHtml(length)}</strong></td>
            <td>${peak}</td>
        </tr>`;
    }).join('');

    return `
        <section class="periods">
            <table class="periods-table">
                <caption class="periods-title">Alerts</caption>
                <thead>
                <tr>
                    <th scope="col">Alert</th>
                    <th scope="col">Time</th>
                    <th scope="col">How long</th>
                    <th scope="col">Peak</th>
                </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </section>`;
}

// Get the box temperature limits from the latest reading. Returns null if not available.
async function loadProfile() {
    try {
        const response = await fetch(
            `${API_BASE}/boxes/${HISTORY_BOX_ID}/readings/latest`,
            {headers: {Accept: 'application/json'}}
        );
        if (!response.ok) return null;
        const data = await response.json();
        if (!data.profile) return null;
        return {
            lowerC: Number(data.profile.lower_c),
            warningC: Number(data.profile.warning_c),
            upperC: Number(data.profile.upper_c),
        };
    } catch (error) {
        return null;
    }
}

function showMessage(container, className, title, text) {
    container.innerHTML = `
        <div class="banner ${className}" role="${className === 'error' ? 'alert' : 'status'}">
            <strong>${escapeHtml(title)}</strong>${text ? '<br>' + escapeHtml(text) : ''}
        </div>`;
}

async function loadHistory() {
    const container = document.getElementById('history');
    if (!container) return;

    container.setAttribute('aria-busy', 'true');
    showMessage(container, '', 'Loading…', '');

    try {
        const response = await fetch(
            `${API_BASE}/boxes/${HISTORY_BOX_ID}/readings?limit=${HISTORY_LIMIT}`,
            {headers: {Accept: 'application/json'}}
        );

        // Not signed in or the session has ended.
        if (response.status === 401) {
            goToSignIn();
            return;
        }
        if (response.status === 404) {
            showMessage(container, 'error', 'Box not found',
                'Ask your administrator to check the box.');
            return;
        }
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }

        const readings = await response.json();

        if (!Array.isArray(readings) || readings.length === 0) {
            showMessage(container, '', 'No readings yet',
                'Check that the box is on and connected.');
            return;
        }

        const profile = await loadProfile();
        container.innerHTML = renderAlertPeriods(readings, profile) + renderGraph(readings, profile) + renderTable(readings, profile);
    } catch (error) {
        console.error('History error:', error);
        showMessage(container, 'error', "Can't load history",
            'Check your internet and refresh.');
    } finally {
        container.setAttribute('aria-busy', 'false');
    }
}

document.addEventListener('DOMContentLoaded', loadHistory);