// Temperature history graph and table for the prototype box.
// Loads readings from GET /api/boxes/{box_id}/readings. The API returns them
// in descending measurement order (sequence_no, shared by both sensors). The table keeps this order;
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

// Time of a reading with seconds, e.g. "16:41:16" (observation time, or the time the
// server received it when the box clock was not set).
function observationCell(reading) {
    const t = readingTime(reading);
    if (!t) return '<span class="cell-warning">Unknown</span>';
    return escapeHtml(t.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit', second: '2-digit'}));
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
        return '<span class="tag fault">⚠ Sensor fault</span>';
    }
    if (readingValue(reading) === null) {
        return '<span class="tag unknown">? Unknown</span>';
    }
    const state = String(reading.temperature_state || '').toLowerCase();
    if (state === 'alert') {
        return '<span class="tag alert">✕ Alert</span>';
    }
    if (state === 'warning') return '<span class="tag warning">! Warning</span>';
    if (state === 'normal') return '<span class="tag normal">✓ Normal</span>';
    return '<span class="tag unknown">? Unknown</span>';
}

// ---- Outside sensor (comparison only; never a status) ----

function outsideValue(reading) {
    if (!reading || reading.quality !== 'valid' || reading.temperature_c == null) return null;
    const v = Number(reading.temperature_c);
    return Number.isFinite(v) ? v : null;
}

// The outside reading taken closest to an inside reading (within 45 s), or null.
function outsideNear(reading) {
    const t = readingTime(reading);
    if (!t || !lastOutside.length) return null;
    let best = null;
    let bestMs = 45 * 1000;
    for (const o of lastOutside) {
        const ot = readingTime(o);
        if (!ot) continue;
        const ms = Math.abs(ot - t);
        if (ms <= bestMs) {
            best = o;
            bestMs = ms;
        }
    }
    return best;
}

function outsideCell(reading) {
    const o = outsideNear(reading);
    if (!o) return '<span class="muted">—</span>';
    if (o.quality === 'sensor_error') return '<span class="outside-fault">Sensor fault</span>';
    const v = outsideValue(o);
    return v === null ? '<span class="muted">—</span>' : `<span class="outside-value">${v.toFixed(1)}</span>`;
}

function renderTable(readings, caption) {
    const hasOutside = lastOutside.length > 0;
    const rows = readings.map((reading) => `
        <tr>
            <td class="period-date">${escapeHtml(periodDate(reading) || '—')}</td>
            <td>${observationCell(reading)}</td>
            <td>${temperatureCell(reading)}</td>
            <td>${statusCell(reading)}</td>
            ${hasOutside ? `<td>${outsideCell(reading)}</td>` : ''}
        </tr>`).join('');

    return `
        <div aria-label="Temperature readings table" class="table-wrap" role="region" tabindex="0">
            <table class="history-table">
                <caption>${escapeHtml(caption)}</caption>
                <thead>
                <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Time</th>
                    <th scope="col">°C</th>
                    <th scope="col">Status</th>
                    ${hasOutside ? '<th scope="col">Outside °C</th>' : ''}
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
    // Observation time, or receipt time when the box clock was not set.
    const a = earlier ? readingTime(earlier) : null;
    const b = later ? readingTime(later) : null;
    if (!a || !b) return null;
    const s = (b - a) / 1000;
    return Number.isFinite(s) ? s : null;
}

// No reading for longer than this means data is missing (same limit as NO NEW DATA).
const MAX_GAP_SECONDS = 90;

// True when readings are missing between two readings of the inside sensor. Inside and outside
// share the box-wide sequence counter, so only time counts: more than 90 s, or a time going
// backwards. Readings without a reliable clock use their receipt time (FR-03).
function hasGap(earlier, later) {
    if (!earlier || !later) return false;
    const seconds = secondsBetween(earlier, later);
    return seconds === null || seconds < 0 || seconds > MAX_GAP_SECONDS;
}

function graphTime(reading) {
    if (!reading || !reading.clock_reliable || !reading.observed_at) return null;
    const date = new Date(reading.observed_at);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
}

function clock(date) {
    return date.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit'});
}

function shortDay(date) {
    return date.toLocaleDateString('en-IE', {day: 'numeric', month: 'short'});
}

// ---- Issues (box or sensor problems) ----
// "nodata": nothing was received (box offline, no connection or readings missing).
// "fault":  the box was online but the sensor could not measure (sensor_error).
// Gaps at the start or end of the chosen period also count as "nodata".
function findIssues(readings, domain) {
    const points = readings.slice().reverse().filter((r) => readingTime(r));   // oldest first
    const issues = [];
    if (points.length === 0) return issues;
    const gapMs = MAX_GAP_SECONDS * 1000;
    const t = (r) => readingTime(r).getTime();

    if (domain && t(points[0]) - domain.from.getTime() > gapMs) {
        issues.push({type: 'nodata', start: domain.from, end: new Date(t(points[0]))});
    }
    let fault = null;
    points.forEach((r, i) => {
        const prev = points[i - 1];
        if (prev && hasGap(prev, r)) {
            if (fault) {
                fault.end = new Date(t(prev) + 30 * 1000);
                issues.push(fault);
                fault = null;
            }
            issues.push({type: 'nodata', start: new Date(t(prev)), end: new Date(t(r))});
        }
        if (r.quality === 'sensor_error') {
            if (!fault) fault = {type: 'fault', start: new Date(t(r))};
        } else if (fault) {
            fault.end = new Date(t(r));
            issues.push(fault);
            fault = null;
        }
    });
    const last = points[points.length - 1];
    const periodEnd = domain ? domain.to.getTime() : null;
    const nowMs = Date.now();
    if (fault) {
        fault.end = new Date(Math.max(t(last) + 30 * 1000, Math.min(periodEnd || 0, nowMs)));
        fault.ongoing = !periodEnd || periodEnd >= nowMs - gapMs;
        issues.push(fault);
    }
    if (periodEnd !== null && Math.min(periodEnd, nowMs) - t(last) > gapMs) {
        issues.push({
            type: 'nodata', start: new Date(t(last)), end: new Date(Math.min(periodEnd, nowMs)),
            ongoing: periodEnd >= nowMs - gapMs
        });
    }
    return issues;
}

// Nice step for the temperature axis.
function niceStep(span) {
    if (span <= 6) return 1;
    if (span <= 12) return 2;
    if (span <= 30) return 5;
    return 10;
}

// Hour marks for the time axis: 5 min ... 1 day apart, at most 8 marks.
function timeTicks(from, to) {
    const steps = [5, 10, 15, 30, 60, 120, 180, 360, 720, 1440];
    const spanMin = (to - from) / 60000;
    const step = steps.find((m) => spanMin / m <= 16) || 1440;   // hourly marks up to 16 h
    const first = new Date(from);
    first.setSeconds(0, 0);
    if (step >= 60) {
        first.setMinutes(0);
        while (first.getHours() % (step / 60) !== 0 && step < 1440) first.setHours(first.getHours() + 1);
        if (step === 1440) first.setHours(0);
    } else {
        first.setMinutes(Math.ceil(first.getMinutes() / step) * step);
    }
    const ticks = [];
    for (let d = new Date(first); d <= to; d = new Date(d.getTime() + step * 60000)) {
        if (d >= from) ticks.push(new Date(d));
    }
    return ticks;
}

// Temperature graph (FR-07).
// The time axis is split into parts with data. A long time without data (over 30 min)
// is squeezed into a narrow grey strip labelled with its length, so days without data
// do not push the measurements into thin lines at the edges.
// - Line colour: green Normal, amber Warning, red Alert (FR-05 states).
// - Red band: sensor fault (box online, no measurement).
// - Grey band: no data (box offline, no connection or readings missing).
// - The line never crosses a band, and missing values are never drawn as 0°C.
// - The °C scale fits the readings and the limit lines of the chosen period.
const BIG_GAP_MS = 30 * 60000;

function renderGraph(readings, domain) {
    const profile = readingProfile(readings[0]);   // limits of the newest reading
    const points = readings.slice().reverse().filter((r) => readingTime(r));   // oldest first
    const known = points.map(readingValue).filter((v) => v !== null);
    const issues = findIssues(readings, domain);
    // Outside sensor: comparison line only, oldest first, inside the shown window.
    const outsidePoints = lastOutside.slice().reverse().filter((r) => {
        const t = readingTime(r);
        return t && (!domain || (t >= domain.from && t < domain.to));
    });
    const outsideKnown = outsidePoints.map(outsideValue).filter((v) => v !== null);
    known.push(...outsideKnown);

    if (known.length === 0) {
        return `<div class="banner" role="status"><strong>No temperatures in this period</strong></div>` +
            `<button type="button" class="view-btn" data-goto-view="readings">See readings</button>`;
    }

    // On a phone the whole day fits the screen width (no sideways scrolling, test 18 Nov T2-04).
    // The drawing is narrower, so the same text stays readable when it is scaled down.
    const phone = window.matchMedia('(max-width: 600px)').matches;
    const W = phone ? 420 : 820, H = phone ? 300 : 380, L = phone ? 40 : 62, R = phone ? 10 : 20;
    const T = 34, B = phone ? 52 : 64;
    const charW = 8;
    const plotTop = T, plotBottom = H - B, plotW = W - L - R;
    const ms = (r) => readingTime(r).getTime();

    // 1. Parts of the timeline with data, and the long gaps between them.
    // A chosen period (1 hour, Today, a date) keeps a real clock axis from its start
    // to its end (or now), with hour marks. Without a period, long gaps are squeezed.
    const parts = [];
    let part = {from: ms(points[0]), to: ms(points[0]), count: 1};
    for (let i = 1; i < points.length && !domain; i++) {
        const t = ms(points[i]);
        if (t - part.to > BIG_GAP_MS) {
            parts.push(part);
            part = {from: t, to: t, count: 1};
        } else {
            part.to = t;
            part.count++;
        }
    }
    parts.push(part);
    const edges = {before: null, after: null};
    if (domain) {
        parts[0].from = domain.from.getTime();
        parts[0].to = currentRange.key === 'hour' ? Math.min(domain.to.getTime(), Date.now()) : domain.to.getTime();
    }
    parts.forEach((p) => {
        if (p.to - p.from < 10 * 60000) {   // at least 10 minutes wide
            const middle = (p.from + p.to) / 2;
            p.from = middle - 5 * 60000;
            p.to = middle + 5 * 60000;
        }
    });

    // 2. Screen positions: gaps get a fixed narrow strip, parts share the rest by length.
    const GAP_W = 44;
    const gaps = [];
    if (edges.before !== null) gaps.push({from: edges.before, to: parts[0].from, at: 0});
    for (let i = 1; i < parts.length; i++) gaps.push({from: parts[i - 1].to, to: parts[i].from, at: i});
    if (edges.after !== null) gaps.push({from: parts[parts.length - 1].to, to: edges.after, at: parts.length});
    const partW = plotW - gaps.length * GAP_W;
    // Each part gets width by its number of readings (and at least by its length),
    // so a short burst of many readings is not squeezed into a vertical line.
    const weight = (p) => Math.max(p.count, (p.to - p.from) / 30000, 2);
    const totalWeight = parts.reduce((sum, p) => sum + weight(p), 0);
    let cursor = L;
    const layout = [];
    for (let i = 0; i <= parts.length; i++) {
        gaps.filter((g) => g.at === i).forEach((g) => {
            layout.push({gap: true, from: g.from, to: g.to, x1: cursor, x2: cursor + GAP_W});
            cursor += GAP_W;
        });
        if (i < parts.length) {
            const p = parts[i];
            const width = Math.max(30, partW * weight(p) / totalWeight);
            layout.push({gap: false, from: p.from, to: p.to, x1: cursor, x2: cursor + width});
            cursor += width;
        }
    }
    const scale = plotW / (cursor - L);   // keep everything inside the plot
    layout.forEach((s) => {
        s.x1 = L + (s.x1 - L) * scale;
        s.x2 = L + (s.x2 - L) * scale;
    });
    const x = (t) => {
        const seg = layout.find((s) => t >= s.from && t <= s.to) ||
            (t < layout[0].from ? layout[0] : layout[layout.length - 1]);
        const span = seg.to - seg.from || 1;
        return seg.x1 + (Math.min(Math.max(t, seg.from), seg.to) - seg.from) / span * (seg.x2 - seg.x1);
    };

    // 3. Temperature scale.
    const limits = [];
    if (profile && Number.isFinite(profile.warningC)) limits.push(profile.warningC);
    if (profile && Number.isFinite(profile.upperC)) limits.push(profile.upperC);
    const showLower = profile && Number.isFinite(profile.lowerC) && Math.min(...known) - 3 <= profile.lowerC;
    if (showLower) limits.push(profile.lowerC);
    let min = Math.min(...known, ...limits) - 1;
    let max = Math.max(...known, ...limits) + 1;
    const step = niceStep(max - min);
    min = Math.floor(min / step) * step;
    max = Math.ceil(max / step) * step;
    const y = (v) => plotTop + (max - v) / (max - min) * (plotBottom - plotTop);

    let svg = '';

    // Long gaps: a narrow grey strip (its dates are in the hover text).
    layout.filter((s) => s.gap).forEach((g) => {
        svg += `<rect x="${g.x1.toFixed(1)}" y="${plotTop}" width="${(g.x2 - g.x1).toFixed(1)}" height="${plotBottom - plotTop}" class="band-gap">` +
            `<title>No data: ${shortDay(new Date(g.from))} ${clock(new Date(g.from))} – ${shortDay(new Date(g.to))} ${clock(new Date(g.to))}</title></rect>`;
    });

    // Short gaps and sensor faults inside the parts.
    issues.forEach((issue) => {
        const a = issue.start.getTime();
        const b = issue.end.getTime();
        if (!domain && issue.type === 'nodata' && b - a > BIG_GAP_MS) return;   // already a grey strip
        const x1 = x(a);
        const x2 = x(Math.min(b, issue.type === 'fault' ? b : b));
        if (x2 - x1 < 0.5) return;
        const label = issue.type === 'fault' ? 'Sensor fault' : 'No data';
        svg += `<rect x="${x1.toFixed(1)}" y="${plotTop}" width="${Math.max(3, x2 - x1).toFixed(1)}" ` +
            `height="${plotBottom - plotTop}" class="band-${issue.type}">` +
            `<title>${label}: ${clock(issue.start)} – ${clock(issue.end)}</title></rect>`;
    });

    // Temperature grid.
    for (let v = min; v <= max + 0.001; v += step) {
        svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" class="graph-grid"/>`;
        svg += `<text x="${L - 10}" y="${y(v) + 5}" text-anchor="end" class="graph-axis">${v}</text>`;
    }

    // Time labels under the graph, with no dates:
    // - 1 hour: "15:35", "15:40" …   - Today or a date: hours "9", "10", "11" …
    // - Without a period (can be many days): the day at the start of each part, "3 Nov".
    // The dates are shown above the graph.
    let lastLabelX = -Infinity;   // right edge of the last label
    const addLabel = (t, text, anchor) => {
        const tx = x(t.getTime());
        const width = text.length * charW + 4;
        const left = anchor === 'start' ? tx : tx - width / 2;
        if (left < lastLabelX + 10) return;
        lastLabelX = left + width;
        svg += `<line x1="${tx.toFixed(1)}" x2="${tx.toFixed(1)}" y1="${plotTop}" y2="${plotBottom}" class="graph-grid-v"/>`;
        svg += `<text x="${tx.toFixed(1)}" y="${plotBottom + 24}" text-anchor="${anchor}" class="graph-axis">${text}</text>`;
    };
    if (domain) {
        const from = new Date(layout[0].from);
        const to = new Date(layout[layout.length - 1].to);
        const short = to - from <= 2 * 3600 * 1000;
        timeTicks(from, to).forEach((t) => addLabel(t, short ? clock(t) : String(t.getHours()), 'middle'));
    } else {
        let lastDay = null;
        layout.filter((seg) => !seg.gap).forEach((seg) => {
            const t = new Date(seg.from);
            if (t.toDateString() === lastDay) return;
            lastDay = t.toDateString();
            addLabel(t, shortDay(t), 'start');
        });
    }
    svg += `<line x1="${L}" x2="${W - R}" y1="${plotBottom}" y2="${plotBottom}" class="graph-axis-line"/>`;
    svg += `<line x1="${L}" x2="${L}" y1="${plotTop}" y2="${plotBottom}" class="graph-axis-line"/>`;
    svg += `<text x="${L}" y="${plotTop - 14}" class="graph-axis-title">°C</text>`;
    svg += `<text x="${W - R}" y="${H - 8}" text-anchor="end" class="graph-axis-title">Time</text>`;

    // Limit lines with labels.
    // Limit lines only (no text on the graph; the legend explains them).
    const limitLine = (value, cls, text) => {
        svg += `<line x1="${L}" x2="${W - R}" y1="${y(value)}" y2="${y(value)}" class="${cls}"><title>${text}</title></line>`;
    };
    if (profile && Number.isFinite(profile.upperC)) limitLine(profile.upperC, 'graph-upper', `Upper limit ${profile.upperC}°C`);
    if (profile && Number.isFinite(profile.warningC)) limitLine(profile.warningC, 'graph-warning', `Warning ${profile.warningC}°C`);
    if (showLower) limitLine(profile.lowerC, 'graph-upper', `Lower limit ${profile.lowerC}°C`);

    // Temperature line coloured by status: green Normal, amber Warning, red Alert.
    // The colour changes where the line crosses a limit. No line across gaps or faults.
    const stateClass = (r) => {
        if (alertKind(r)) return 'line-alert';
        return String(r.temperature_state || '').toLowerCase() === 'warning' ? 'line-warning' : 'line-normal';
    };
    points.forEach((r, i) => {
        const v = readingValue(r);
        const prev = points[i - 1];
        if (v === null || !prev || readingValue(prev) === null || hasGap(prev, r)) return;
        limitPieces(ms(prev), readingValue(prev), ms(r), v, readingProfile(r) || profile, stateClass(r)).forEach((s) => {
            svg += `<line x1="${x(s.t1).toFixed(1)}" y1="${y(s.v1).toFixed(1)}" ` +
                `x2="${x(s.t2).toFixed(1)}" y2="${y(s.v2).toFixed(1)}" class="graph-seg ${s.cls}"/>`;
        });
    });

    // Outside the box: thin dashed blue line, never coloured by status. It breaks at gaps over
    // 90 s and at outside sensor faults; outside data never fills in for missing inside data.
    let outsidePath = '';
    let penDown = false;
    outsidePoints.forEach((r, i) => {
        const v = outsideValue(r);
        const prev = outsidePoints[i - 1];
        if (v === null) {
            penDown = false;
            return;
        }
        const continues = penDown && prev && !hasGap(prev, r);
        outsidePath += `${continues ? 'L' : 'M'}${x(ms(r)).toFixed(1)} ${y(v).toFixed(1)}`;
        penDown = true;
    });
    if (outsidePath) svg += `<path class="graph-outside" d="${outsidePath}"/>`;

    // A reading with no neighbour is drawn as a dot, so it is not lost.
    // Every reading also has an invisible larger target with its time and temperature (hover).
    points.forEach((r, i) => {
        const v = readingValue(r);
        if (v === null) return;
        const t = readingTime(r);
        const cx = x(t.getTime()).toFixed(1);
        const cy = y(v).toFixed(1);
        const joined = (n) => n && readingValue(n) !== null;
        const alone = !(joined(points[i - 1]) && !hasGap(points[i - 1], r)) &&
            !(joined(points[i + 1]) && !hasGap(r, points[i + 1]));
        if (alone) svg += `<circle cx="${cx}" cy="${cy}" r="4" class="graph-dot ${stateClass(r)}"/>`;
        svg += `<circle cx="${cx}" cy="${cy}" r="7" class="graph-hit"><title>${shortDay(t)}, ${clock(t)} · ${v.toFixed(1)}°C</title></circle>`;
    });

    // Text summary for screen readers.
    const faults = issues.filter((i) => i.type === 'fault').length;
    const noData = issues.filter((i) => i.type === 'nodata').length;
    const first = readingTime(points[0]);
    const last = readingTime(points[points.length - 1]);
    const summary = `Temperature from ${shortDay(first)} ${clock(first)} to ${shortDay(last)} ${clock(last)}. ` +
        `Lowest ${Math.min(...known).toFixed(1)}°C, highest ${Math.max(...known).toFixed(1)}°C. ` +
        `${points.filter((r) => alertKind(r) !== null).length} alert readings, ${faults} sensor fault periods and ` +
        `${noData} periods with no data. The same data is in Readings.`;

    let legend = '<ul class="graph-legend">';
    legend += '<li><span class="legend-line line-normal" aria-hidden="true"></span>Normal</li>';
    legend += '<li><span class="legend-line line-warning" aria-hidden="true"></span>Warning</li>';
    legend += '<li><span class="legend-line line-alert" aria-hidden="true"></span>Alert</li>';
    legend += limitLegend(profile, showLower);
    if (outsideKnown.length) legend += '<li><span class="legend-outside" aria-hidden="true"></span>Outside the box</li>';
    if (faults) legend += '<li><span class="legend-band legend-fault" aria-hidden="true"></span>Sensor fault</li>';
    if (noData) legend += '<li><span class="legend-band legend-nodata" aria-hidden="true"></span>No data</li>';
    legend += '</ul>';

    const dateText = domain
        ? dateRange(domain.from, new Date(Math.min(domain.to.getTime() - 1, Date.now())))
        : dateRange(first, last);
    return `
        <figure class="graph" tabindex="0">
            <figcaption class="graph-head">
                <span class="graph-name">Temperature readings</span>
                <span class="graph-date">${escapeHtml(dateText)}</span>
            </figcaption>
            <svg aria-labelledby="graph-title graph-desc" role="img" viewBox="0 0 ${W} ${H}">
                <title id="graph-title">Temperature graph</title>
                <desc id="graph-desc">${escapeHtml(summary)}</desc>
                ${svg}
            </svg>
            ${legend}
        </figure>`;
}

// Issues table: No data and Sensor fault, with how long they lasted, date and time.
// The meaning of each status is in docs/design/ui/ui-wording.md.
// Date of the chosen period, shown once above a table: "17 Nov 2026" (or a range).
function periodDateText() {
    if (!lastDomain) return '';
    return dateRange(lastDomain.from, new Date(Math.min(lastDomain.to.getTime() - 1, Date.now())));
}

// Heading of a table with the period date in a box on the right.
function tableHead(id, title) {
    return `<div class="state-head">
        <h2 class="state-title" id="${id}">${title}</h2>
        <span class="graph-date">${escapeHtml(periodDateText())}</span>
    </div>`;
}

// "14:05 – 14:23"; a time on another day than the one shown starts with the day ("16 Nov, 23:50").
function timeSpan(start, end) {
    const withDay = (d) => {
        if (!d) return '';
        const other = lastDomain && d.toDateString() !== lastDomain.from.toDateString();
        return other ? `${shortDay(d)}, ${clock(d)}` : clock(d);
    };
    const a = withDay(start);
    const b = withDay(end);
    return !b || a === b ? a : `${a} – ${b}`;
}

// Day of a row when it is not the day shown above the table: "from 16 Nov".
function otherDay(date) {
    if (!date || !lastDomain) return '';
    const shown = lastDomain.from.toDateString();
    return date.toDateString() === shown ? '' : `<small class="row-day">from ${escapeHtml(shortDay(date))}</small>`;
}

function renderIssues(readings, domain) {
    const issues = findIssues(readings, domain);
    if (issues.length === 0) {
        return '<p class="period-none">✓ No issues</p>';
    }
    const rows = issues.slice().reverse().map((issue) => {   // newest first
        const fault = issue.type === 'fault';
        const minutes = Math.max(1, Math.round((issue.end - issue.start) / 60000));
        const start = clock(issue.start);
        const end = clock(issue.end);
        const day = issue.start.toDateString() === (lastDomain ? lastDomain.from.toDateString() : '') ? '' : `${shortDay(issue.start)}, `;
        const when = issue.ongoing ? `since ${day}${start}` : (start === end ? `${day}${start}` : `${day}${start} – ${end}`);
        return `<tr class="${fault ? 'state-fault' : 'state-offline'}">
            <th scope="row"><span class="state-pill"><span aria-hidden="true">${fault ? ICON.fault : ICON.nodata}</span> ${fault ? 'Sensor fault' : 'No data'}</span></th>
            <td data-label="How long">${issue.ongoing ? '<span class="now-chip">Now</span>' : formatDuration(minutes)}</td>
            <td data-label="Time">${escapeHtml(when)}</td>
        </tr>`;
    }).join('');
    return `
        <section class="table-wrap" aria-labelledby="issues-title" role="region" tabindex="0">
            ${tableHead('issues-title', 'Issues')}
            <table class="state-table">
                <thead>
                <tr>
                    <th scope="col">Problem</th>
                    <th scope="col">How long</th>
                    <th scope="col">Time</th>
                </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </section>`;
}

// Time of a reading for history rows: observation time, or the receipt time
// when the box clock was not set.
function periodTime(reading) {
    const t = readingTime(reading);
    if (!t) return 'time unknown';
    return clock(t);
}

// Date of a reading, e.g. "5 Nov 2026" (usability test finding 3).
function periodDate(reading) {
    const t = reading ? readingTime(reading) : null;
    return t ? t.toLocaleDateString('en-IE', {day: 'numeric', month: 'short', year: 'numeric'}) : null;
}

// "45 min", "3 h 20 min", "1 day 2 h" or "8 days".
function formatDuration(minutes) {
    return readableDuration(minutes);   // main.js
}

// Date of a period: "14 Nov 2026", or "4 – 6 Nov 2026" when it crosses midnight.
function dateRange(start, end) {
    const full = {day: 'numeric', month: 'short', year: 'numeric'};
    if (!start) return '—';
    if (!end || start.toDateString() === end.toDateString()) return start.toLocaleDateString('en-IE', full);
    if (start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()) {
        return `${start.getDate()} – ${end.toLocaleDateString('en-IE', full)}`;
    }
    return `${start.toLocaleDateString('en-IE', {
        day: 'numeric',
        month: 'short'
    })} – ${end.toLocaleDateString('en-IE', full)}`;
}

function periodMinutes(start, end) {
    const a = start ? readingTime(start) : null;
    const b = end ? readingTime(end) : null;
    if (!a || !b) return null;
    const ms = b - a;
    if (!Number.isFinite(ms) || ms < 0) return null;
    return Math.max(1, Math.round(ms / 60000));
}

// Alerts page: notification history (newest first).
// Every change of status is one row: Alert, Warning or Normal (temperature),
// or Sensor fault and Offline (the box could not measure or sent nothing), with the
// peak temperature, how long it lasted, the date and the time.
// A sensor error or missing readings ends a temperature row; its length then shows "+".
// Status icons as small SVGs: they sit exactly in the centre of the circle (test 18 Nov, T1-13).
const ICON = {
    check: '<svg viewBox="0 0 16 16"><path d="M3 8.5l3.2 3L13 4.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    cross: '<svg viewBox="0 0 16 16"><path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    bang: '<svg viewBox="0 0 16 16"><path d="M8 3v6.5" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>',
    fault: '<svg viewBox="0 0 16 16"><path d="M2 9h3l2-5 2.5 9L12 7h2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    nodata: '<svg viewBox="0 0 16 16"><path d="M4 8h8" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>',
};

const STATE_LABEL = {
    high: {text: 'Alert', icon: ICON.cross, cls: 'state-hot'},
    low: {text: 'Alert', icon: ICON.cross, cls: 'state-hot'},
    warning: {text: 'Warning', icon: ICON.bang, cls: 'state-warning'},
    normal: {text: 'Normal', icon: ICON.check, cls: 'state-normal'},
};

function readingState(reading) {
    if (readingValue(reading) === null) return null;
    const kind = alertKind(reading);
    if (kind) return kind;
    const state = String(reading.temperature_state || '').toLowerCase();
    if (state === 'warning') return 'warning';
    if (state === 'normal') return 'normal';
    return null;
}

function findStatePeriods(readings) {
    const points = readings.slice().reverse();   // oldest first
    const periods = [];
    let current = null;
    let previous = null;
    const close = (end, unsure) => {
        current.end = end;
        current.unsure = unsure;
        periods.push(current);
        current = null;
    };
    points.forEach((reading) => {
        const state = readingState(reading);
        const v = readingValue(reading);
        if (current && previous && hasGap(previous, reading)) close(previous, true);
        if (state === null) {
            if (current) close(reading, true);   // sensor error: the status is unknown from here
            previous = reading;
            return;
        }
        if (current && state !== current.state) close(reading, false);
        if (!current) {
            current = {state, start: reading, peak: v};
        } else {
            current.peak = state === 'low' ? Math.min(current.peak, v) : Math.max(current.peak, v);
        }
        current.last = reading;
        previous = reading;
    });
    if (current) {
        current.end = null;   // still going on
        periods.push(current);
    }
    return periods;
}

function renderAlertPeriods(readings) {
    const periods = findStatePeriods(readings);
    const issues = findIssues(readings, lastDomain);
    // Box offline or sensor fault now: the last temperature row is not "Now" any more.
    // It ends at the last reading, and the ongoing No data / Sensor fault row comes first.
    const ongoing = issues.find((i) => i.ongoing);
    // A past day (or a period that ended) has nothing "Now": its last status ends at its last reading.
    const periodIsLive = !lastDomain || lastDomain.to.getTime() > Date.now() - MAX_GAP_SECONDS * 1000;
    periods.forEach((p) => {
        if (p.end === null && (ongoing || !periodIsLive)) {
            p.end = p.last;
            p.unsure = true;
        }
    });
    if (periods.length === 0 && issues.length === 0) {
        return '<p class="period-none">No temperatures in this period</p>';
    }

    // Temperature rows.
    const rows = periods.map((p) => {
        const label = STATE_LABEL[p.state];
        const startTime = readingTime(p.start);
        let length;
        let time;
        if (p.end === null) {
            length = '<span class="now-chip">Now</span>';
            time = `since ${clock(startTime)}`;
        } else {
            const endTime = readingTime(p.unsure ? p.last : p.end);
            const minutes = periodMinutes(p.start, p.unsure ? p.last : p.end);
            // Readings stopped before the status changed: say "at least" in words (usability test).
            length = minutes === null ? '—' : p.unsure
                ? `<span title="Exact end unknown: readings stopped">at least ${formatDuration(minutes)}</span>`
                : formatDuration(minutes);
            time = timeSpan(startTime, endTime);
        }
        return {
            at: readingTime(p.start) || new Date(0),
            html: `<tr class="${label.cls}">
                <th scope="row"><span class="state-pill"><span aria-hidden="true">${label.icon}</span> ${label.text}</span></th>
                <td class="state-peak" data-label="Peak">${p.peak.toFixed(1)}°C</td>
                <td data-label="How long">${length}</td>
                <td data-label="Time">${escapeHtml(time)}</td>
            </tr>`
        };
    });

    // Device rows: Sensor fault (no measurement) and Offline (no data received).
    issues.forEach((issue) => {
        const fault = issue.type === 'fault';
        const minutes = Math.max(1, Math.round((issue.end - issue.start) / 60000));
        rows.push({
            at: issue.start,
            html: `<tr class="${fault ? 'state-fault' : 'state-offline'}">
                <th scope="row"><span class="state-pill"><span aria-hidden="true">${fault ? ICON.fault : ICON.nodata}</span> ${fault ? 'Sensor fault' : 'No data'}</span></th>
                <td class="state-peak" data-label="Peak">—</td>
                <td data-label="How long">${issue.ongoing ? '<span class="now-chip">Now</span>' : formatDuration(minutes)}</td>
                <td data-label="Time">${escapeHtml(issue.ongoing ? `since ${clock(issue.start)}` : timeSpan(issue.start, issue.end))}</td>
            </tr>`
        });
    });

    rows.sort((a, b) => b.at - a.at);   // newest first

    return `
        <section class="table-wrap" aria-labelledby="state-title" role="region" tabindex="0">
            ${tableHead('state-title', 'Notification history')}
            <table class="state-table">
                <thead>
                <tr>
                    <th scope="col">Status</th>
                    <th scope="col">Peak</th>
                    <th scope="col">How long</th>
                    <th scope="col">Time</th>
                </tr>
                </thead>
                <tbody>${rows.map((r) => r.html).join('')}</tbody>
            </table>
        </section>`;
}

function showMessage(container, className, title, text) {
    container.innerHTML = `
        <div class="banner ${className}" role="${className === 'error' ? 'alert' : 'status'}">
            <strong>${escapeHtml(title)}</strong>${text ? '<br>' + escapeHtml(text) : ''}
        </div>`;
}

// Time filter (FR-07). The API filters by Irish calendar dates (start_date and end_date, inclusive,
// by observation time) and pages with before_sequence. "1 hour" asks for the
// dates it touches and then keeps only the readings in the last hour.
// Periods: Today (the default), the last hour, or a chosen date.
const RANGES = {
    today: {label: 'Today'},
    hour: {label: '1 hour'},
};
let currentRange = {key: 'today'};

// History and Alerts share the chosen period in this browser tab (test 18 Nov, T1-01):
// pick 15 Nov in History, open Alerts, and Alerts shows 15 Nov too. Today resets it.
const RANGE_KEY = 'tempsafe.period';

function saveRange(range) {
    if (range.key !== 'date' && range.key !== 'today' && range.key !== 'hour') return;
    try {
        sessionStorage.setItem(RANGE_KEY, JSON.stringify(range));
    } catch (error) { /* storage off: each page starts at Today */ }
}

(function readSavedRange() {
    try {
        const saved = JSON.parse(sessionStorage.getItem(RANGE_KEY) || 'null');
        if (saved && (saved.key === 'today' || saved.key === 'hour')) currentRange = {key: saved.key};
        if (saved && saved.key === 'date' && /^\d{4}-\d{2}-\d{2}$/.test(saved.date)) {
            currentRange = {key: 'date', date: saved.date};
        }
    } catch (error) { /* keep Today */ }
})();

// Opened with View from an alert: ?from=…&to=… (milliseconds) shows that time.
(function readAroundFromUrl() {
    const params = new URLSearchParams(location.search);
    const from = Number(params.get('from'));
    const to = Number(params.get('to'));
    if (Number.isFinite(from) && Number.isFinite(to) && from > 0 && to > from) {
        currentRange = {key: 'around', from: new Date(from), to: new Date(Math.min(to, Date.now()))};
    }
})();

function rangeTimes(range) {
    const now = new Date();
    if (range.key === 'hour') return {from: new Date(now - 3600 * 1000), to: now};
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

// Calendar date in Ireland, e.g. "2026-11-14" (the format the API expects).
function dublinDate(date) {
    return new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Europe/Dublin', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(date);
}

// start_date and end_date for the chosen period.
function rangeDates(range) {
    const now = new Date();
    if (range.key === 'date' && range.date) return {start: range.date, end: range.date};
    if (range.key === 'around') return {start: dublinDate(range.from), end: dublinDate(range.to)};
    if (range.key === 'today') return {start: dublinDate(now), end: dublinDate(now)};
    if (range.key === 'hour') return {start: dublinDate(new Date(now - 3600 * 1000)), end: dublinDate(now)};
    return null;
}

function rangeLabel(range) {
    if (range.key === 'around') {
        return `Alert on ${shortDay(range.from)}, ${clock(range.from)} – ${clock(range.to)}`;
    }
    if (range.key === 'date' && range.date) {
        return new Date(`${range.date}T00:00:00`).toLocaleDateString('en-IE', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    }
    return RANGES[range.key] ? RANGES[range.key].label : 'Today';
}

// Time used to place a reading in a period: observation time, or receipt time
// when the device clock was not reliable.
function readingTime(reading) {
    const value = reading.clock_reliable ? reading.observed_at : reading.received_at;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

// Start and end of the period for the graph's time axis.
function periodDomain(range) {
    const now = new Date();
    if (range.key === 'around') return {from: range.from, to: range.to};
    if (range.key === 'hour') return {from: new Date(now - 3600 * 1000), to: now};
    if (range.key === 'today') {
        const start = new Date(now);
        start.setHours(0, 0, 0, 0);
        return {from: start, to: now};
    }
    if (range.key === 'date' && range.date) {
        const start = new Date(`${range.date}T00:00:00`);
        const end = new Date(start);
        end.setDate(end.getDate() + 1);
        return {from: start, to: end < now ? end : now};
    }
    return null;
}

// Today or a date: show 08:00 to 18:00 on the graph (the working day). If there are
// readings earlier or later, the window grows to the whole hours around them,
// so no reading is hidden.
const DAY_START_HOUR = 8;
const DAY_END_HOUR = 18;

function graphWindow(domain, readings) {
    if (!domain || (currentRange.key !== 'today' && currentRange.key !== 'date')) return domain;
    const day = new Date(domain.from);
    const from = new Date(day);
    from.setHours(DAY_START_HOUR, 0, 0, 0);
    const to = new Date(day);
    to.setHours(DAY_END_HOUR, 0, 0, 0);
    readings.forEach((r) => {
        const t = readingTime(r);
        if (!t) return;
        if (t < from) {
            from.setTime(t.getTime());
            from.setMinutes(0, 0, 0);
        }
        if (t > to) {
            to.setTime(t.getTime());
            to.setMinutes(60, 0, 0);   // up to the next whole hour
        }
    });
    return {from, to};
}

const HISTORY_DAYS = 30;

function renderFilter() {
    const filter = document.getElementById('history-filter');
    if (!filter) return;
    const buttons = Object.entries(RANGES).map(([key, r]) =>
        `<button type="button" class="filter-btn" data-range="${key}" aria-pressed="${currentRange.key === key}">${r.label}</button>`
    ).join('');
    const today = new Date();
    const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const max = iso(today);
    // History can be opened for the last 30 days (HISTORY_DAYS).
    const min = iso(new Date(today.getFullYear(), today.getMonth(), today.getDate() - (HISTORY_DAYS - 1)));
    // A saved date outside the last 30 days (or in the future) goes back to Today.
    if (currentRange.key === 'date' && (currentRange.date < min || currentRange.date > iso(today))) {
        currentRange = {key: 'today'};
    }
    // The day the arrows move from: the chosen date, or today.
    const shownDay = currentRange.key === 'date' ? currentRange.date
        : currentRange.key === 'around' ? iso(currentRange.from) : max;
    filter.innerHTML = `
        <div class="filter-row">
            <div class="filter-buttons" role="group" aria-label="Period">${buttons}</div>
            <div class="filter-date">
                <label for="history-date">Date</label>
                <div class="date-step">
                    <button type="button" class="step-btn" id="day-prev" aria-label="Previous day" ${shownDay <= min ? 'disabled' : ''}>←</button>
                    <input type="date" id="history-date" min="${min}" max="${max}" value="${currentRange.key === 'hour' ? '' : shownDay}">
                    <button type="button" class="step-btn" id="day-next" aria-label="Next day" ${shownDay >= max ? 'disabled' : ''}>→</button>
                </div>
            </div>
        </div>`;

    // ← and →: the day before or after the one shown. Today counts as "Today".
    const goToDay = (day) => {
        currentRange = day === max ? {key: 'today'} : {key: 'date', date: day};
        history.replaceState(null, '', location.pathname + location.hash);
        renderFilter();
        loadHistory();
    };
    const step = (days) => {
        const d = new Date(`${shownDay}T00:00:00`);
        d.setDate(d.getDate() + days);
        return iso(d);
    };
    filter.querySelector('#day-prev').addEventListener('click', () => goToDay(step(-1)));
    filter.querySelector('#day-next').addEventListener('click', () => goToDay(step(1)));

    filter.querySelectorAll('[data-range]').forEach((button) => {
        button.addEventListener('click', () => {
            currentRange = {key: button.dataset.range};
            history.replaceState(null, '', location.pathname + location.hash);
            renderFilter();
            loadHistory();
        });
    });
    const dateInput = filter.querySelector('#history-date');
    dateInput.addEventListener('change', () => {
        if (!dateInput.value) return;
        // A typed date outside the last 30 days is not loaded.
        if (dateInput.value < dateInput.min || dateInput.value > dateInput.max) {
            dateInput.setCustomValidity(`Choose a date from ${dateInput.min} to ${dateInput.max}.`);
            dateInput.reportValidity();
            return;
        }
        dateInput.setCustomValidity('');
        currentRange = {key: 'date', date: dateInput.value};
        history.replaceState(null, '', location.pathname + location.hash);
        renderFilter();
        loadHistory();
    });
}

// Views (usability: one thing at a time, chosen with a clear button).
// History shows Graph or Readings. Alerts shows Temperature (too hot / too cold)
// or Issues (sensor faults and no data). The view is kept in the address
// (#graph, #readings, #temperature, #issues), so other pages can open the right one.
const PAGE = document.body.dataset.page === 'alerts' ? 'alerts' : 'history';
const VIEWS = PAGE === 'alerts'
    ? {temperature: 'Status', issues: 'Issues'}
    : {graph: 'Graph', readings: 'Readings'};
let currentView = VIEWS[location.hash.slice(1)] ? location.hash.slice(1) : Object.keys(VIEWS)[0];
let lastReadings = null;
let lastDomain = null;   // start and end of the chosen period, for the time axis
let lastSummary = '';

// Status of a reading as plain text, for the CSV file.
function statusText(reading) {
    if (reading.quality === 'sensor_error') return 'Sensor fault';
    if (readingValue(reading) === null) return 'Unknown';
    const state = String(reading.temperature_state || '').toLowerCase();
    return {alert: 'Alert', warning: 'Warning', normal: 'Normal'}[state] || 'Unknown';
}

// Download every reading of the chosen period as a CSV file (opens in Excel).
function downloadCsv() {
    if (!lastReadings || lastReadings.length === 0) return;
    // Each column names its sensor; the outside value is the reading closest in time (within 45 s).
    const hasOutside = lastOutside.length > 0;
    const rows = [['Date', 'Time', 'Inside temperature (°C)', 'Status']
        .concat(hasOutside ? ['Outside temperature (°C)'] : [])];
    lastReadings.slice().reverse().forEach((r) => {   // oldest first
        const t = readingTime(r);
        const value = readingValue(r);
        const row = [
            t ? dublinDate(t) : '',
            t ? t.toLocaleTimeString('en-IE', {hour: '2-digit', minute: '2-digit', second: '2-digit'}) : '',
            value === null ? '' : value.toFixed(1),
            statusText(r),
        ];
        if (hasOutside) {
            const o = outsideNear(r);
            row.push(!o ? '' : o.quality === 'sensor_error' ? 'Sensor fault' : (outsideValue(o) === null ? '' : outsideValue(o).toFixed(1)));
        }
        rows.push(row);
    });
    const csv = rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\r\n');
    // The BOM lets Excel show °C correctly.
    const blob = new Blob(['\ufeff' + csv], {type: 'text/csv;charset=utf-8'});
    const dates = rangeDates(currentRange);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `tempsafe-${dates ? dates.start : 'readings'}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
}

function renderViews() {
    const box = document.getElementById('history-views');
    if (!box) return;
    const csv = PAGE === 'history'
        ? '<button type="button" class="csv-btn" id="download-csv">Download CSV</button>' : '';
    box.innerHTML = `<div class="views-row"><div class="view-buttons" role="group" aria-label="Show">${
        Object.entries(VIEWS).map(([key, label]) =>
            `<button type="button" class="view-btn" data-view="${key}" aria-pressed="${currentView === key}">${label}</button>`
        ).join('')}</div>${csv}</div>`;
    const csvButton = box.querySelector('#download-csv');
    if (csvButton) csvButton.addEventListener('click', downloadCsv);
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
    if (currentView === 'temperature') {
        body = renderAlertPeriods(lastReadings);
    } else if (currentView === 'issues') {
        body = renderIssues(lastReadings, lastDomain);   // table only; the graph is on History
    } else if (currentView === 'readings') {
        body = renderTable(lastReadings, 'Readings');
    } else {
        body = renderGraph(lastReadings, graphWindow(lastDomain, lastReadings));
    }
    const note = lastSummary ? `<p class="history-summary">${escapeHtml(lastSummary)}</p>` : '';
    container.innerHTML = note + body;
    const goto = container.querySelector('[data-goto-view]');
    if (goto && !VIEWS[goto.dataset.gotoView]) {
        goto.remove();
    } else if (goto) {
        goto.addEventListener('click', () => {
            currentView = goto.dataset.gotoView;
            history.replaceState(null, '', `#${currentView}`);
            renderViews();
            showView(true);
        });
    }
    if (focus) container.focus();
}

// One request to the readings API. Returns null after handling 401 or 404.
async function fetchPage(query, quiet = false) {
    const container = document.getElementById('history');
    const response = await fetch(
        `${API_BASE}/boxes/${HISTORY_BOX_ID}/readings?${query}`,
        {headers: {Accept: 'application/json'}}
    );
    // Outside data is extra: if it cannot be loaded, History still shows the inside data.
    if (quiet && !response.ok) return [];
    // Not signed in or the session has ended.
    if (response.status === 401) {
        goToSignIn();
        return null;
    }
    // The box does not exist or is not assigned to this user.
    if (response.status === 404) {
        showMessage(container, 'error', 'No access', 'Ask your admin for access.');
        return null;
    }
    if (!response.ok) {
        throw new Error('API error: ' + response.status);
    }
    const page = await response.json();
    return Array.isArray(page) ? page : [];
}

// All readings in a calendar period, page by page (newest first). There is no limit:
// the graph, Issues and Readings always cover the whole period, however often the box measures.

// sensor: 'inside' (default, the box status) or 'outside' (comparison only). Paging keeps the sensor.
async function fetchPeriod(dates, times, sensor = 'inside') {
    const all = [];
    let before = null;
    const outside = sensor === 'outside';
    while (true) {
        let query = `limit=${HISTORY_LIMIT}&start_date=${dates.start}&end_date=${dates.end}`;
        if (outside) query += '&sensor_location=outside';
        if (before !== null) query += `&before_sequence=${before}`;
        let page = await fetchPage(query, outside);
        // An older backend ignores sensor_location: keep only rows that say they are outside.
        if (outside && page) page = page.filter((r) => r.sensor_location === 'outside');
        if (page === null) return null;
        all.push(...page);
        if (page.length < HISTORY_LIMIT) break;
        const next = page[page.length - 1].sequence_no;
        // Safety: stop if the API does not move back (would load the same page forever).
        if (before !== null && next >= before) break;
        before = next;
        // Pages go back in time: stop once they are older than the period.
        const oldest = readingTime(page[page.length - 1]);
        if (times && oldest && oldest < times.from) break;
    }
    return all;
}

let historyRequest = 0;
let lastOutside = [];   // outside-sensor readings of the shown period, newest first

async function loadHistory() {
    const container = document.getElementById('history');
    if (!container) return;

    container.setAttribute('aria-busy', 'true');
    showMessage(container, '', 'Loading…', '');

    // Only the newest request may draw: after quick clicks an older, slower answer
    // must not be shown on the axis of the newly chosen period (test 18 Nov, T1-09).
    const requestId = ++historyRequest;
    const range = currentRange;
    saveRange(range);
    const domain = periodDomain(range);
    const dates = rangeDates(range);
    // Only "1 hour" needs an extra time check after the dates.
    let times = range.key === 'hour' ? rangeTimes(range) : null;
    if (range.key === 'around') times = {from: range.from, to: range.to};

    try {
        let readings;
        let outsideReadings = [];
        if (!dates) {
            readings = await fetchPage(`limit=${HISTORY_LIMIT}`);
        } else {
            // Inside and outside are requested separately, at the same time (dual-sensor API).
            [readings, outsideReadings] = await Promise.all([
                fetchPeriod(dates, times),
                fetchPeriod(dates, times, 'outside').catch(() => []),
            ]);
        }
        if (requestId !== historyRequest) return;   // a newer period was chosen meanwhile
        if (readings === null) return;   // already handled (sign-in or no access)
        outsideReadings = outsideReadings || [];

        if (times) {
            const inTimes = (r) => {
                const t = readingTime(r);
                return t !== null && t >= times.from && t < times.to;
            };
            readings = readings.filter(inTimes);
            outsideReadings = outsideReadings.filter(inTimes);
        }

        if (readings.length === 0) {
            lastReadings = null;
            if (range.key === 'hour' && times) {
                showMessage(container, '', 'No readings in the last 60 minutes',
                    `${dateRange(times.from, times.to)}, ${clock(times.from)} – ${clock(times.to)}`);
            } else if (dates) {
                showMessage(container, '', 'No readings in this period', 'Choose another period.');
            } else {
                showMessage(container, '', 'No readings yet', 'Check the box is on.');
            }
            return;
        }

        lastReadings = readings;
        lastOutside = outsideReadings;
        lastDomain = domain;
        // No "N readings" line (usability). Only name the alert the user opened with View.
        lastSummary = range.key === 'around' ? rangeLabel(range) : '';
        showView(false);

    } catch (error) {
        console.error('History error:', error);
        showMessage(container, 'error', "Can't load", 'Check your internet and refresh.');
    } finally {
        if (requestId === historyRequest) container.setAttribute('aria-busy', 'false');
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
