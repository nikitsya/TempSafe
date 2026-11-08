// Page start-up code shared by all TEMPSAFE pages.

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
// The session cookie is HttpOnly, so only the server can remove it. If the
// server does not confirm sign-out, the user stays on this page and can try again.
document.addEventListener('DOMContentLoaded', () => {
    const errorBanner = document.getElementById('signout-error');

    document.querySelectorAll('[data-signout]').forEach((link) => {
        link.addEventListener('click', async (event) => {
            event.preventDefault();
            if (link.getAttribute('aria-disabled') === 'true') return;

            link.setAttribute('aria-disabled', 'true');
            if (errorBanner) errorBanner.hidden = true;

            try {
                const response = await fetch(`${API_BASE}/logout`, {method: 'POST'});
                // The backend answers 204 No Content when the session has ended.
                if (response.status !== 204) {
                    throw new Error(`Sign out failed: ${response.status}`);
                }
                goToSignIn('signed-out');
            } catch (error) {
                console.error(error);
                if (errorBanner) {
                    errorBanner.textContent = "We couldn't confirm that you've signed out. Please try again.";
                    errorBanner.hidden = false;
                }
                link.removeAttribute('aria-disabled');
            }
        });
    });
});
