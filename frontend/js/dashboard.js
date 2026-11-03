// Dashboard for TEMSAFE.
// Get temperature data from the backend API.

const STATUS_VIEW = {
    normal: {
        cls: 'normal',
        icon: '✓',
        title: 'NORMAL',
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
        title: 'ALERT',
        role: 'alert'
    },
    stale: {
        cls: 'unknown',
        icon: '⏱',
        title: 'NO NEW DATA',
        role: 'status'
    },
    sensor_error: {
        cls: 'alert',
        icon: '⚠',
        title: 'SENSOR ERROR',
        role: 'alert'
    },
    not_reporting: {
        cls: 'unknown',
        icon: '⦸',
        title: 'NO CONNECTION',
        role: 'alert'
    },
    unknown: {
        cls: 'unknown',
        icon: '?',
        title: 'UNKNOWN',
        role: 'status'
    }
};

// Convert API date to local date and time (used in Details).
function formatTime(date) {
    if (!date) {
        return 'Unknown';
    }

    const time = new Date(date);

    if (isNaN(time.getTime())) {
        return 'Unknown';
    }

    return time.toLocaleString();
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

    return time.toLocaleTimeString();
}

// Short explanation of the status. Shown in Details, not on the main card.
function describe(reading, profile) {
    switch (reading.status) {
        case 'normal':
            return 'Within limits';

        case 'warning':
            return `Close to the upper limit (${profile.upperC}°C)`;

        case 'alert':
            return reading.temperatureC < profile.lowerC
                ? `Below the lower limit (${profile.lowerC}°C)`
                : `Above the upper limit (${profile.upperC}°C)`;

        case 'stale':
            return 'No new reading for over 90 s';

        case 'sensor_error':
            return 'The sensor could not measure';

        case 'not_reporting':
            return 'The box is not sending data';

        default:
            return 'Measurement time is not reliable';
    }
}

// Main card: only the status, the temperature and the time.
function statusCard(reading) {
    const view = STATUS_VIEW[reading.status] || STATUS_VIEW.unknown;

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
        body = `<p class="status-text">Temperature unknown</p>`;
    }

    return `
        <section class="status ${view.cls}" role="${view.role}">
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
        ? `<dt>Last reading</dt><dd>${reading.temperatureC.toFixed(1)}°C (old)</dd>`
        : '';

    return `
        <details class="details">
            <summary>Details</summary>
            <dl class="kv">
                <dt>Status</dt>
                <dd>${describe(reading, profile)}</dd>

                ${lastReading}

                <dt>Measured</dt>
                <dd>${reading.observedAt}</dd>

                <dt>Received</dt>
                <dd>${reading.receivedAt}</dd>

                <dt>Limits</dt>
                <dd>${profile.lowerC}–${profile.upperC}°C (warning from ${profile.warningC}°C)</dd>
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

            <p class="muted">
                Check that the box is on and connected.
            </p>
        </section>
    `;
}

// Show the dashboard.
function renderDashboard(reading, profile) {
    const dashboard = document.getElementById('dashboard');

    dashboard.innerHTML =
        statusCard(reading) +
        detailsCard(reading, profile);
}

// Convert API data into frontend data.
function convertReading(data) {

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

    // Reading is older than 90 seconds.
    else if (ageSeconds > 90) {
        status = 'stale';
    }

    const reading = {
        status: status,
        temperatureC: temperature,
        observedAt: formatTime(data.observed_at),
        observedClock: formatClock(data.observed_at),
        receivedAt: formatTime(data.received_at),
        ageSeconds: ageSeconds
    };

    return {reading, profile};
}

// Get the latest reading from the API.
async function loadTemperature() {
    const dashboard = document.getElementById('dashboard');

    // Show loading message.
    dashboard.innerHTML = `
        <section class="card" role="status">
            Loading…
        </section>
    `;

    try {
        const response = await fetch(
            `${API_BASE}/boxes/TS-01/readings/latest`
        );

        // No readings available.
        if (response.status === 404) {
            const errorData = await response.json();

            if (
                errorData.detail ===
                'No readings available for this box'
            ) {
                dashboard.innerHTML = emptyState();
                return;
            }
        }

        // Handle request errors.
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }

        // Read JSON response.
        const data = await response.json();

        // Convert API response.
        const result = convertReading(data);

        // Display dashboard.
        renderDashboard(result.reading, result.profile);

    } catch (error) {
        dashboard.innerHTML = `
            <section class="empty" role="alert">
                <h2>Can't load temperature</h2>

                <p class="muted">
                    Check your internet and refresh.
                </p>
            </section>
        `;

        console.error('Dashboard error:', error);
    }
}

// Load API data when the page opens.
document.addEventListener('DOMContentLoaded', loadTemperature);
