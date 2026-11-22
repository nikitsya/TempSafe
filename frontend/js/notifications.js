// Alert notifications.
// Every signed-in page checks the latest readings every 15 seconds and announces two moments:
//   1. an alert is on:  "Alert" – 26.4°C · 4 min (updated while it lasts)
//   2. the alert ends:  "Back in range" – 22.8°C
// Alert or not is decided by the server with the limits set in Settings.
// Box problems are announced too: Sensor fault, Offline and Back online.
// Each moment is announced once (FR-14: no repeats for an unchanged state).
// It appears as a pop-up on the website and, if the Notifications switch in
// Settings is on, also as a browser (web) notification.
// Works while TEMPSAFE is open in a tab. Notifications with the site closed would
// need Web Push from the backend.

const NOTIFY_BOX_ID = 'TS-01';
const NOTIFY_ON_KEY = 'tempsafe.notify.on';
const NOTIFY_STATE_KEY = `tempsafe.notify.state.${NOTIFY_BOX_ID}`;
const NOTIFY_CHECK_SECONDS = 15;

function storageGet(key) {
    try {
        return localStorage.getItem(key);
    } catch (error) {
        return null;
    }
}

function storageSet(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (error) {
        // Storage can be blocked (private mode); a notification may then repeat.
    }
}

function notificationsSupported() {
    return 'Notification' in window;
}

// Browser notification switch: "on", "off", "blocked" or "unsupported".
function notificationState() {
    if (!notificationsSupported()) return 'unsupported';
    if (Notification.permission === 'denied') return 'blocked';
    if (Notification.permission === 'granted' && storageGet(NOTIFY_ON_KEY) === 'yes') return 'on';
    return 'off';
}

async function turnNotificationsOn() {
    if (!notificationsSupported()) return 'unsupported';
    const permission = await Notification.requestPermission();
    if (permission === 'granted') storageSet(NOTIFY_ON_KEY, 'yes');
    return notificationState();
}

function turnNotificationsOff() {
    storageSet(NOTIFY_ON_KEY, 'no');
    return notificationState();
}

function isAlertReading(reading) {
    return String(reading.temperature_state || '').toLowerCase() === 'alert';
}

// The newest alert period in readings (newest first):
// start reading, end reading (first reading back in range) or null if still on, peak.
function newestAlertPeriod(readings) {
    const newestIndex = readings.findIndex(isAlertReading);
    if (newestIndex === -1) return null;
    let startIndex = newestIndex;
    for (let i = newestIndex + 1; i < readings.length; i++) {
        if (!isAlertReading(readings[i]) || readingGap(readings[i], readings[i - 1])) break;
        startIndex = i;
    }
    const alertReadings = readings.slice(newestIndex, startIndex + 1);
    const values = alertReadings.map((r) => Number(r.temperature_c)).filter(Number.isFinite);
    const start = readings[startIndex];
    const lower = Number(start.profile && start.profile.lower_c);
    const low = Number.isFinite(lower) && Number(start.temperature_c) <= lower;
    // Ended only when the next reading is a valid reading back within the limits.
    const next = newestIndex > 0 ? readings[newestIndex - 1] : null;
    const ended = next && next.quality === 'valid' && !isAlertReading(next) ? next : null;
    return {
        start,
        newest: readings[newestIndex],
        end: ended,
        low,
        peak: low ? Math.min(...values) : Math.max(...values),
    };
}

function minutesBetween(a, b) {
    const ms = new Date(b) - new Date(a);
    return Number.isFinite(ms) ? Math.max(1, Math.round(ms / 60000)) : null;
}

// Current temperature in the box: the newest valid reading, or null.
function currentTemperature(readings) {
    const latest = readings.find((r) => r.quality === 'valid' && Number.isFinite(Number(r.temperature_c)));
    return latest ? Number(latest.temperature_c) : null;
}

// Text for an alert that is on, or for the moment it ends.
// Alert:  "26.4°C · 4 min"   (current temperature and how long it has lasted)
// Ended:  "22.8°C"
function alertMessage(period, moment, readings) {
    const now = currentTemperature(readings);
    const nowText = now === null ? 'Temperature unknown' : `${now.toFixed(1)}°C`;
    if (moment === 'end') {
        return {kind: 'back', title: 'Back in range', text: nowText};
    }
    const minutes = minutesBetween(period.start.observed_at, new Date());
    return {
        kind: period.low ? 'low' : 'high',
        title: 'Alert',
        text: minutes === null ? nowText : `${nowText} · ${readableDuration(minutes)}`,
    };
}

// Pop-up on the website (bottom right). Stays until closed.
let livePopup = null;      // the pop-up of the alert that is still on (updated every check)
let closedSeq = null;      // the user closed the pop-up of this alert

function showPopup(message, seq) {
    let area = document.getElementById('popup-area');
    if (!area) {
        area = document.createElement('div');
        area.id = 'popup-area';
        area.className = 'popup-area';
        area.setAttribute('aria-live', 'assertive');
        area.setAttribute('role', 'alert');
        document.body.appendChild(area);
    }
    const popup = document.createElement('div');
    popup.className = `popup popup-${message.kind}`;
    popup.innerHTML = `
        <span aria-hidden="true" class="popup-icon">${{back: '✓', offline: '⦸'}[message.kind] || '⚠'}</span>
        <div class="popup-text">
            <strong></strong>
            <span></span>
        </div>
        <button aria-label="Close" class="popup-close" type="button">×</button>`;
    popup.querySelector('strong').textContent = message.title;
    popup.querySelector('.popup-text span').textContent = message.text;
    popup.querySelector('.popup-close').addEventListener('click', () => {
        popup.remove();
        if (livePopup === popup) {
            livePopup = null;
            closedSeq = seq;
        }
    });
    area.prepend(popup);
    // Keep at most three pop-ups on screen.
    while (area.children.length > 3) area.lastElementChild.remove();
    return popup;
}

function showBrowserNotification(message) {
    if (notificationState() !== 'on') return;
    const notification = new Notification(message.title, {
        body: message.text,
        tag: `tempsafe-${NOTIFY_BOX_ID}`,   // a newer notification replaces the older one
    });
    notification.onclick = () => {
        window.focus();
        window.location.href = '/pages/alerts.html';
        notification.close();
    };
}

function announce(message, seq) {
    const popup = showPopup(message, seq);
    showBrowserNotification(message);
    return popup;
}

// Keep the "on" alert pop-up up to date: current temperature and minutes so far.
function updateLivePopup(message) {
    if (!livePopup || !livePopup.isConnected) return;
    // Only the text changes, so screen readers are not interrupted every 15 seconds.
    livePopup.querySelector('.popup-text span').textContent = message.text;
}

// Remembered state: the start sequence of the last announced alert, and whether
// its end was announced. Stored in the browser, so other tabs do not repeat it.
function readNotifyState() {
    try {
        return JSON.parse(storageGet(NOTIFY_STATE_KEY)) || null;
    } catch (error) {
        return null;
    }
}

async function checkAlerts() {
    try {
        const response = await fetch(`${API_BASE}/boxes/${NOTIFY_BOX_ID}/readings?limit=100`, {
            headers: {Accept: 'application/json'}
        });
        if (!response.ok) return;
        const readings = await response.json();
        if (!Array.isArray(readings)) return;
        const period = newestAlertPeriod(readings);
        if (!period) return;

        const saved = readNotifyState();
        let seq = Number(period.start.sequence_no);
        // The page loads only the latest 100 readings. When an alert started before them,
        // its first reading is not in the list and the start seems to move forward on every
        // check. It is still the same alert, so it must not be announced again (test 22 Nov:
        // "Back in range" every 15 s with one reading every 5 s).
        const startCut = readings.indexOf(period.start) === readings.length - 1;
        if (startCut && saved && seq > saved.seq) seq = saved.seq;
        const ongoing = !period.end;
        const save = (ended) => storageSet(NOTIFY_STATE_KEY, JSON.stringify({seq, ended}));

        if (!saved || seq > saved.seq) {
            // A new alert (or the first visit). Old alerts that already ended stay quiet.
            if (ongoing) {
                livePopup = announce(alertMessage(period, 'start', readings), seq);
            } else if (saved) {
                announce(alertMessage(period, 'end', readings), seq);
            }
            save(!ongoing);
            return;
        }
        if (seq === saved.seq && ongoing) {
            // Still on: update the pop-up, or show it again after a page change.
            const message = alertMessage(period, 'start', readings);
            if (livePopup && livePopup.isConnected) {
                updateLivePopup(message);
            } else if (closedSeq !== seq) {
                livePopup = showPopup(message, seq);
            }
            return;
        }
        if (seq === saved.seq && !ongoing && !saved.ended) {
            // The alert has just ended.
            if (livePopup) livePopup.remove();
            livePopup = null;
            announce(alertMessage(period, 'end', readings), seq);
            save(true);
        }
    } catch (error) {
        console.error('Alert check error:', error);
    }
}

// ---- Box problems: Sensor fault and Offline ----
// Sensor fault: the newest reading is a sensor error.  Pop-up: "Sensor fault – No temperature"
// Offline: the server received nothing for more than 90 s. Pop-up: "Offline – No data for 3 min"
// When data comes back after Offline: "Back online – 22.8°C".
const NOTIFY_DEVICE_KEY = `tempsafe.notify.device.${NOTIFY_BOX_ID}`;
let offlinePopup = null;

function readDeviceState() {
    try {
        return JSON.parse(storageGet(NOTIFY_DEVICE_KEY)) || {};
    } catch (error) {
        return {};
    }
}

async function checkDevice() {
    try {
        const [statusResponse, readingsResponse] = await Promise.all([
            fetch(`${API_BASE}/boxes/${NOTIFY_BOX_ID}/status`, {headers: {Accept: 'application/json'}}),
            fetch(`${API_BASE}/boxes/${NOTIFY_BOX_ID}/readings?limit=20`, {headers: {Accept: 'application/json'}})
        ]);
        if (!statusResponse.ok || !readingsResponse.ok) return;
        const status = await statusResponse.json();
        const readings = await readingsResponse.json();
        const saved = readDeviceState();

        // Offline
        if (status.contact_status === 'not_reporting' && status.last_received_at) {
            const minutes = minutesBetween(status.last_received_at, new Date());
            const message = {kind: 'offline', title: 'Offline', text: `No data for ${readableDuration(minutes)}`};
            if (saved.offline !== status.last_received_at) {
                offlinePopup = announce(message, 'offline');
                saved.offline = status.last_received_at;
            } else if (offlinePopup && offlinePopup.isConnected) {
                offlinePopup.querySelector('.popup-text span').textContent = message.text;
            }
        } else if (status.contact_status === 'reporting' && saved.offline) {
            if (offlinePopup) offlinePopup.remove();
            offlinePopup = null;
            const now = Array.isArray(readings) ? currentTemperature(readings) : null;
            announce({
                kind: 'back',
                title: 'Back online',
                text: now === null ? 'No temperature yet' : `${now.toFixed(1)}°C`
            }, 'online');
            saved.offline = null;
        }

        // Sensor fault: announce the first error of a run once.
        if (Array.isArray(readings) && readings.length && readings[0].quality === 'sensor_error') {
            let first = readings[0];
            for (const r of readings) {
                if (r.quality !== 'sensor_error') break;
                first = r;
            }
            const seq = Number(first.sequence_no);
            if (!(saved.faultSeq >= seq)) {
                announce({kind: 'fault', title: 'Sensor fault', text: 'No temperature'}, 'fault');
                saved.faultSeq = seq;
            }
        }
        storageSet(NOTIFY_DEVICE_KEY, JSON.stringify(saved));
    } catch (error) {
        console.error('Device check error:', error);
    }
}

// Run on every signed-in page (pages with a Sign out link).
document.addEventListener('DOMContentLoaded', () => {
    if (!document.querySelector('[data-signout]')) return;
    checkAlerts();
    checkDevice();
    setInterval(() => {
        checkAlerts();
        checkDevice();
    }, NOTIFY_CHECK_SECONDS * 1000);
});
