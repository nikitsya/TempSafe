// Sample data for the dashboard while the backend endpoints are not ready.
// Each object has the shape we expect from a future API response, so the
// dashboard can later switch to apiGet() without changing the layout code.
// Choose a state with the URL, for example pages/dashboard.html?state=alert

const SAMPLE_PROFILE = { name: 'Demo v1', lowerC: 15, warningC: 24, upperC: 25 };

const SAMPLE_STATES = {
  normal: { status: 'normal', temperatureC: 21.8, observedAt: '14:20:00', ageSeconds: 8, lastContact: '14:20:05', pushAlerts: 'denied' },
  warning: { status: 'warning', temperatureC: 24.6, observedAt: '14:17:30', ageSeconds: 12, lastContact: '14:17:42', pushAlerts: 'on' },
  alert: { status: 'alert', temperatureC: 25.9, observedAt: '14:31:00', ageSeconds: 5, lastContact: '14:31:02', pushAlerts: 'on' },
  stale: { status: 'stale', lastValidC: 22.8, observedAt: '14:12:05', ageSeconds: 300, lastContact: '14:16:50' },
  sensor_error: { status: 'sensor_error', lastValidC: 22.9, observedAt: '14:16:30', failedAt: '14:17:30', lastContact: '14:17:31' },
  not_reporting: { status: 'not_reporting', lastValidC: 22.7, observedAt: '14:13:00', lastContact: '14:13:10', contactAgeSeconds: 240 },
  no_data: { status: 'no_data' },
};
