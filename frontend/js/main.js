// Page start-up code shared by all TEMSAFE pages.

async function showApiStatus() {
  const status = document.getElementById('api-status');
  if (!status) return;
  try {
    const data = await apiGet('/health');
    const ok = data.status === 'ok';
    status.textContent = ok ? 'API connected' : 'API not ready';
    status.className = `api-status ${ok ? 'ok' : 'down'}`;
  } catch (error) {
    status.textContent = 'API not reachable';
    status.className = 'api-status down';
  }
}

document.addEventListener('DOMContentLoaded', showApiStatus);
