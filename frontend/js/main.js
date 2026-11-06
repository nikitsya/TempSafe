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

// Sign out: end the session on the server, then open the sign-in page.
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-signout]').forEach((link) => {
        link.addEventListener('click', async (event) => {
            event.preventDefault();
            try {
                await fetch(`${API_BASE}/logout`, {method: 'POST'});
            } catch (error) {
                // Even if the request fails, leave the protected page.
            }
            goToSignIn('signed-out');
        });
    });
});
