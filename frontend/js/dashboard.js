
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
        title: 'DATA STALE',
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
        title: 'NOT REPORTING',
        role: 'alert'
    },
    unknown: {
        cls: 'unknown',
        icon: '?',
        title: 'UNKNOWN',
        role: 'status'
    }
};

// Convert API date to local time.
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

// Explain the current temperature status.
function describe(reading, profile) {
    switch (reading.status) {
        case 'normal':
            return `Within configured limits (${profile.lowerC}–${profile.warningC}°C)`;

        case 'warning':
            return `At or above warning threshold (${profile.warningC}°C)`;

        case 'alert':
            return reading.temperatureC < profile.lowerC
                ? `Below lower limit (${profile.lowerC}°C)`
                : `Above upper limit (${profile.upperC}°C)`;

        case 'stale':
            return 'Current conditions unknown. The last reading is old.';

        case 'sensor_error':
            return 'The sensor could not measure the temperature.';

        case 'not_reporting':
            return 'The device is not reporting new readings.';

        default:
            return 'Current temperature status is unknown.';
    }
}

// Create the main temperature card.
function statusCard(reading, profile) {
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
                Observed ${reading.observedAt}
                · ${reading.ageSeconds} s ago
                · <strong>Live</strong>
            </div>
        `;
    }

    // Show old readings as historical data.
    else if (reading.status === 'stale') {
        body = `
            <div class="meta">
                ${reading.temperatureC !== null
                    ? `Last recorded temperature: ${reading.temperatureC.toFixed(1)}°C (historical)`
                    : 'Temperature unavailable'}
            </div>
            <div class="meta">
                Observed ${reading.observedAt}
            </div>
        `;
    }

    // Handle unknown time, missing temperature and sensor errors.
    else {
        body = `
            <div class="meta">
                ${reading.temperatureC !== null
                    ? `Recorded temperature: ${reading.temperatureC.toFixed(1)}°C (not confirmed live)`
                    : 'Temperature unavailable'}
            </div>
        `;
    }

    return `
        <section class="status ${view.cls}" role="${view.role}">
            <div class="status-row">
                <span class="status-icon" aria-hidden="true">
                    ${view.icon}
                </span>

                <div>
                    <h2 class="status-title">${view.title}</h2>

                    <p class="status-text">
                        ${describe(reading, profile)}
                    </p>
                </div>
            </div>

            ${body}
        </section>
    `;
}

// Create the information card.
function detailsCard(reading, profile) {
    return `
        <section class="card">
            <dl class="kv">
                <dt>Last observation</dt>
                <dd>${reading.observedAt}</dd>

                <dt>Received by server</dt>
                <dd>${reading.receivedAt}</dd>

                <dt>Profile</dt>
                <dd>
                    Lower ${profile.lowerC}°C ·
                    Warning ${profile.warningC}°C ·
                    Upper ${profile.upperC}°C
                </dd>
            </dl>
        </section>
    `;
}

// Show a message when no readings exist.
function emptyState() {
    return `
        <section class="empty" role="status">
            <div class="empty-icon" aria-hidden="true">—</div>

            <h2>No observations yet</h2>

            <p class="muted">
                This box has not sent any readings.
                Current conditions are unknown.
            </p>
        </section>
    `;
}

// Show the dashboard.
function renderDashboard(reading, profile) {
    const dashboard = document.getElementById('dashboard');

    dashboard.innerHTML =
        statusCard(reading, profile) +
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
            Loading temperature...
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
                <h2>Unable to load temperature</h2>

                <p class="muted">
                    Please check the connection and try again.
                </p>
            </section>
        `;

        console.error('Dashboard error:', error);
    }
}

// Load API data when the page opens.
document.addEventListener('DOMContentLoaded', loadTemperature);
