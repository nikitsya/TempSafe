// Dashboard rendering for TEMSAFE.
// Uses sample data for now (js/sample-data.js). Status is always shown with
// a word, a symbol and a colour, so colour is never the only signal.

const STATUS_VIEW = {
  normal: { cls: 'normal', icon: '✓', title: 'NORMAL', role: 'status' },
  warning: { cls: 'warning', icon: '!', title: 'WARNING', role: 'status' },
  alert: { cls: 'alert', icon: '✕', title: 'ALERT', role: 'alert' },
  stale: { cls: 'unknown', icon: '⏱', title: 'DATA STALE', role: 'status' },
  sensor_error: { cls: 'alert', icon: '⚠', title: 'SENSOR ERROR', role: 'alert' },
  not_reporting: { cls: 'unknown', icon: '⦸', title: 'NOT REPORTING', role: 'alert' },
};

function describe(reading, profile) {
  switch (reading.status) {
    case 'normal':
      return `Within configured limits (${profile.lowerC}–${profile.warningC}°C)`;
    case 'warning':
      return `At or above early-warning threshold (${profile.warningC}°C)`;
    case 'alert':
      return reading.temperatureC < profile.lowerC
        ? `Below configured lower limit (${profile.lowerC}°C)`
        : `Above configured upper limit (${profile.upperC}°C)`;
    case 'stale':
      return 'Current conditions unknown';
    case 'sensor_error':
      return `Latest reading failed at ${reading.failedAt}`;
    case 'not_reporting':
      return `No contact from the device for ${Math.round(reading.contactAgeSeconds / 60)} min`;
    default:
      return '';
  }
}

function statusCard(reading, profile) {
  const view = STATUS_VIEW[reading.status];
  const live = reading.temperatureC !== undefined;
  const body = live
    ? `<div class="value">${reading.temperatureC.toFixed(1)}<small>°C</small></div>
       <div class="meta">Observed ${reading.observedAt} · ${reading.ageSeconds} s ago · <strong>Live</strong></div>`
    : `<div class="meta">${detail(reading)}</div>`;
  return `<section class="status ${view.cls}" role="${view.role}">
      <div class="status-row">
        <span class="status-icon" aria-hidden="true">${view.icon}</span>
        <div><h2 class="status-title">${view.title}</h2>
        <p class="status-text">${describe(reading, profile)}</p></div>
      </div>${body}</section>`;
}

function detail(reading) {
  if (reading.status === 'stale') {
    return `No new reading for ${Math.round(reading.ageSeconds / 60)} min (limit 90 s).`;
  }
  if (reading.status === 'sensor_error') {
    return 'Temperature is unknown. The failed reading is not shown as 0°C or Normal.';
  }
  if (reading.status === 'not_reporting') {
    return 'The device may be offline or without power. The LED on the box still gives local warnings.';
  }
  return '';
}

function detailsCard(reading, profile) {
  const rows = [];
  if (reading.temperatureC === undefined && reading.lastValidC !== undefined) {
    rows.push(['Last valid reading', `${reading.lastValidC.toFixed(1)}°C at ${reading.observedAt} (historical)`]);
  }
  rows.push(['Last contact', reading.lastContact]);
  rows.push(['Profile', `${profile.name} · Lower ${profile.lowerC}°C · Warning ${profile.warningC}°C · Upper ${profile.upperC}°C`]);
  if (reading.pushAlerts === 'on') rows.push(['Phone alerts', 'On (Web Push)']);
  const items = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
  return `<section class="card"><dl class="kv">${items}</dl></section>`;
}

function pushBanner(reading) {
  if (reading.pushAlerts !== 'denied') return '';
  return `<div class="banner" role="status"><strong>Phone notifications unavailable.</strong>
    Permission is blocked in this browser. Monitoring on this screen still works.</div>`;
}

function emptyState() {
  return `<section class="empty" role="status">
      <div class="empty-icon" aria-hidden="true">—</div>
      <h2>No observations yet</h2>
      <p class="muted">This box has not sent any readings. Current conditions are unknown.</p>
    </section>`;
}

function renderDashboard(reading, profile) {
  const content = document.getElementById('dashboard');
  if (reading.status === 'no_data') {
    content.innerHTML = emptyState();
    return;
  }
  content.innerHTML = statusCard(reading, profile) + pushBanner(reading) + detailsCard(reading, profile);
}

document.addEventListener('DOMContentLoaded', () => {
  const state = new URLSearchParams(window.location.search).get('state') || 'warning';
  const reading = SAMPLE_STATES[state] || SAMPLE_STATES.warning;
  renderDashboard(reading, SAMPLE_PROFILE);

  const links = document.getElementById('sample-states');
  if (links) {
    links.innerHTML = Object.keys(SAMPLE_STATES)
      .map((name) => `<a href="?state=${name}"${name === state ? ' aria-current="page"' : ''}>${name.replace('_', ' ')}</a>`)
      .join(' · ');
  }
});
