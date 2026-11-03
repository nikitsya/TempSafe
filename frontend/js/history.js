// Temperature history table for the prototype box.
// Loads readings from GET /api/boxes/{box_id}/readings. The API returns them
// in descending measurement order (sequence_no), so the order is kept as is.
// Missing temperatures and sensor errors are never shown as 0°C.

const HISTORY_BOX_ID = 'TS-01';
const HISTORY_LIMIT = 20;

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Show an API timestamp in the user's local time, e.g. "2 Nov 2026, 14:20:05".
function formatTime(value) {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleString('en-IE', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

function observationCell(reading) {
    const observed = reading.clock_reliable ? formatTime(reading.observed_at) : null;
    const received = formatTime(reading.received_at);
    const receivedText = received ? `<br><small class="muted">Received ${escapeHtml(received)}</small>` : '';

    if (!observed) {
        return `<span class="cell-warning">Time unknown</span>
            ${receivedText}`;
    }
    return escapeHtml(observed);
}

function temperatureCell(reading) {
    if (reading.quality === 'sensor_error') {
        return '<span aria-label="Temperature unknown">—</span> <small class="muted">Unknown</small>';
    }
    if (reading.temperature_c === null || reading.temperature_c === undefined) {
        return '<span aria-label="Temperature missing">—</span> <small class="muted">Missing</small>';
    }
    const value = Number(reading.temperature_c);
    if (Number.isNaN(value)) {
        return '<span aria-label="Temperature invalid">—</span> <small class="muted">Invalid</small>';
    }
    return `${value.toFixed(1)}°C`;
}

function qualityCell(reading) {
    if (reading.quality === 'valid') {
        return '<span class="tag normal">✓ Valid</span>';
    }
    if (reading.quality === 'sensor_error') {
        return '<span class="tag alert">⚠ Sensor error</span>';
    }
    return `<span class="tag unknown">${escapeHtml(reading.quality || 'Unknown')}</span>`;
}

function renderTable(readings) {
    const rows = readings.map((reading) => `
        <tr>
            <td>${observationCell(reading)}</td>
            <td>${temperatureCell(reading)}</td>
            <td>${qualityCell(reading)}</td>
        </tr>`).join('');

    return `
        <div aria-label="Temperature readings table" class="table-wrap" role="region" tabindex="0">
            <table class="history-table">
                <caption>Latest ${readings.length} readings</caption>
                <thead>
                <tr>
                    <th scope="col">Observation time</th>
                    <th scope="col">Temperature</th>
                    <th scope="col">Quality</th>
                </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
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

        container.innerHTML = renderTable(readings);
    } catch (error) {
        console.error('History error:', error);
        showMessage(container, 'error', "Can't load history",
            'Check your internet and refresh.');
    } finally {
        container.setAttribute('aria-busy', 'false');
    }
}

document.addEventListener('DOMContentLoaded', loadHistory);