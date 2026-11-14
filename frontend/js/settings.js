// Settings page: read and change the temperature limits of box TS-01.
// API: GET and PUT /api/boxes/{box_id}/configuration (signed-in user, assigned box).
// Saving creates a new limits profile on the server. The box uses it only after
// it receives the update, so the page says so (the device does not confirm it yet).

const SETTINGS_BOX_ID = 'TS-01';
const CONFIG_URL = `${API_BASE}/boxes/${SETTINGS_BOX_ID}/configuration`;

let currentLimits = null;   // limits saved on the server, or null if none yet
let pendingLimits = null;   // limits waiting for "Confirm"

function escapeText(text) {
    return String(text)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

// "24.00" -> "24", "24.50" -> "24.5"
function shortNumber(value) {
    return String(Number(value));
}

function showSettingsMessage(kind, title, text) {
    const box = document.getElementById('settings-message');
    if (!box) return;
    if (!title) {
        box.innerHTML = '';
        return;
    }
    box.innerHTML = `
        <div class="banner ${kind}">
            <strong>${escapeText(title)}</strong>${text ? '<br>' + escapeText(text) : ''}
        </div>`;
}

function limitsSummary(limits) {
    return `Minimum ${shortNumber(limits.lower_c)}°C · ` +
        `Warning from ${shortNumber(limits.warning_c)}°C · ` +
        `Maximum ${shortNumber(limits.upper_c)}°C`;
}

function field(id, label, value) {
    return `
        <div class="limit-field">
            <label for="${id}">${label}</label>
            <div class="limit-input">
                <input id="${id}" inputmode="decimal" type="number" step="0.1" min="-40" max="80"
                       required aria-describedby="${id}-error" value="${value}">
                <span aria-hidden="true">°C</span>
            </div>
            <p class="field-error" id="${id}-error"></p>
        </div>`;
}

function renderForm() {
    const section = document.getElementById('settings');
    const limits = currentLimits || {lower_c: '', warning_c: '', upper_c: '', source_note: ''};
    const now = currentLimits ? '' : '<p class="limits-now"><strong>No limits set yet.</strong></p>';

    section.innerHTML = `
        <h2 class="panel-title" id="limits-title">Temperature limits</h2>
        ${now}
        <form id="limits-form" novalidate>
            <div class="limit-grid">
                ${field('lower', 'Minimum', limits.lower_c === '' ? '' : shortNumber(limits.lower_c))}
                ${field('warning', 'Warning from', limits.warning_c === '' ? '' : shortNumber(limits.warning_c))}
                ${field('upper', 'Maximum', limits.upper_c === '' ? '' : shortNumber(limits.upper_c))}
            </div>
            <button class="btn" type="submit">Save limits</button>
        </form>
        <div id="confirm-box"></div>`;
    section.setAttribute('aria-busy', 'false');

    document.getElementById('limits-form').addEventListener('submit', (event) => {
        event.preventDefault();
        checkForm();
    });
}

function setError(id, text) {
    const input = document.getElementById(id);
    const error = document.getElementById(`${id}-error`);
    error.textContent = text || '';
    if (text) {
        input.setAttribute('aria-invalid', 'true');
    } else {
        input.removeAttribute('aria-invalid');
    }
}

// Check the numbers in the browser first. The server checks them again.
function readLimit(id) {
    const raw = document.getElementById(id).value.trim();
    if (raw === '') return {error: 'Enter a number.'};
    const value = Number(raw);
    if (!Number.isFinite(value)) return {error: 'Enter a number.'};
    if (value < -40 || value > 80) return {error: 'Use -40 to 80°C.'};
    if (Math.round(value * 100) !== value * 100) return {error: 'Use up to 2 decimals.'};
    return {value};
}

function checkForm() {
    showSettingsMessage('', '');
    const lower = readLimit('lower');
    const warning = readLimit('warning');
    const upper = readLimit('upper');

    setError('lower', lower.error);
    setError('warning', warning.error);
    setError('upper', upper.error);

    let ok = !lower.error && !warning.error && !upper.error;
    if (!lower.error && !warning.error && !(lower.value < warning.value)) {
        setError('warning', 'Must be higher than the minimum.');
        ok = false;
    }
    if (!warning.error && !upper.error && !(warning.value < upper.value)) {
        setError('upper', 'Must be higher than warning from.');
        ok = false;
    }
    if (!ok) {
        const first = document.querySelector('[aria-invalid="true"]');
        if (first) first.focus();
        return;
    }

    pendingLimits = {
        lower_c: lower.value.toFixed(2),
        warning_c: warning.value.toFixed(2),
        upper_c: upper.value.toFixed(2),
        // The API keeps a note with every limits profile; the user does not type one.
        source_note: 'Set on the TEMPSAFE website'
    };
    showConfirm();
}

// Second step, so limits are not changed by mistake.
function showConfirm() {
    const box = document.getElementById('confirm-box');
    const before = currentLimits ? limitsSummary(currentLimits) : 'No limits';
    box.innerHTML = `
        <section aria-labelledby="confirm-title" class="confirm" tabindex="-1" id="confirm-panel">
            <h3 id="confirm-title">Change the limits?</h3>
            <dl class="kv">
                <dt>Now</dt><dd>${escapeText(before)}</dd>
                <dt>New</dt><dd><strong>${escapeText(limitsSummary(pendingLimits))}</strong></dd>
            </dl>
            <div class="confirm-buttons">
                <button class="btn" id="confirm-save" type="button">Confirm</button>
                <button class="btn btn-secondary" id="confirm-cancel" type="button">Cancel</button>
            </div>
        </section>`;
    document.getElementById('confirm-panel').focus();
    document.getElementById('confirm-save').addEventListener('click', saveLimits);
    document.getElementById('confirm-cancel').addEventListener('click', () => {
        pendingLimits = null;
        box.innerHTML = '';
        document.getElementById('lower').focus();
    });
}

async function saveLimits() {
    const button = document.getElementById('confirm-save');
    button.disabled = true;
    button.textContent = 'Saving…';
    try {
        const response = await fetch(CONFIG_URL, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json', Accept: 'application/json'},
            body: JSON.stringify(pendingLimits)
        });
        if (response.status === 401) {
            goToSignIn();
            return;
        }
        if (response.status === 404) {
            renderNoAccess();
            return;
        }
        if (response.status === 422) {
            showSettingsMessage('error', 'Not saved', 'Check the numbers: minimum < warning from < maximum.');
            renderForm();
            return;
        }
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }
        currentLimits = await response.json();
        pendingLimits = null;
        renderForm();
        showSettingsMessage('success', 'Saved',
            'The website uses these limits for new readings once the box updates.');
        document.getElementById('settings-message').scrollIntoView({block: 'nearest'});
    } catch (error) {
        console.error('Settings error:', error);
        button.disabled = false;
        button.textContent = 'Confirm';
        showSettingsMessage('error', 'Not saved', 'Check your internet and try again.');
    }
}

function renderNoAccess() {
    const section = document.getElementById('settings');
    section.innerHTML = `
        <div class="empty">
            <div class="empty-icon" aria-hidden="true">⦸</div>
            <h2>No access</h2>
            <p class="muted">Ask your admin for access.</p>
        </div>`;
    section.setAttribute('aria-busy', 'false');
}

async function loadLimits() {
    try {
        const response = await fetch(CONFIG_URL, {headers: {Accept: 'application/json'}});
        if (response.status === 401) {
            goToSignIn();
            return;
        }
        if (response.status === 404) {
            const data = await response.json().catch(() => ({}));
            // The box has no limits yet: show an empty form.
            if (data.detail === 'No threshold configuration selected') {
                currentLimits = null;
                renderForm();
                return;
            }
            renderNoAccess();
            return;
        }
        if (!response.ok) {
            throw new Error('API error: ' + response.status);
        }
        currentLimits = await response.json();
        renderForm();
    } catch (error) {
        console.error('Settings error:', error);
        const section = document.getElementById('settings');
        section.innerHTML = `
            <div class="banner error" role="alert">
                <strong>Can't load</strong><br>Check your internet and refresh.
            </div>`;
        section.setAttribute('aria-busy', 'false');
    }
}

// ---- Web notifications (uses notifications.js): one on/off switch ----
const NOTIFY_HELP = {
    blocked: 'Blocked in this browser. Allow notifications in the site settings (padlock next to the address), then reload.',
    unsupported: 'This browser does not support notifications.'
};

function renderNotifications() {
    const box = document.getElementById('notify-box');
    if (!box) return;
    const state = notificationState();
    const on = state === 'on';
    const disabled = state === 'blocked' || state === 'unsupported';
    box.innerHTML = `
        <div class="switch-row">
            <span class="switch-label" id="notify-label">Notifications</span>
            <button aria-checked="${on}" aria-labelledby="notify-label" class="switch" id="notify-switch"
                    role="switch" type="button" ${disabled ? 'disabled aria-describedby="notify-help"' : ''}>
                <span aria-hidden="true" class="switch-text">${on ? 'On' : 'Off'}</span>
                <span aria-hidden="true" class="switch-thumb"></span>
            </button>
        </div>
        ${disabled ? `<p class="muted switch-help" id="notify-help">${NOTIFY_HELP[state]}</p>` : ''}`;

    const toggle = document.getElementById('notify-switch');
    toggle.addEventListener('click', async () => {
        toggle.disabled = true;
        if (notificationState() === 'on') {
            turnNotificationsOff();
        } else {
            await turnNotificationsOn();
        }
        renderNotifications();
        document.getElementById('notify-switch').focus();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderNotifications();
    loadLimits();
});
