// Small helper for calls to the TEMPSAFE backend API.
// When the page is served by FastAPI, relative URLs such as /api/health
// go to the same server. When the file is opened directly, the local
// development server address is used instead.

const API_BASE = window.location.protocol === 'file:'
    ? 'http://127.0.0.1:8000/api'
    : '/api';

async function apiGet(path) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: {Accept: 'application/json'},
    });
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }
    return response.json();
}

// Open the sign-in page, for example when the API says the session has ended (401).
function goToSignIn(reason = 'expired') {
    const page = window.location.pathname.includes('/pages/') ? '../index.html' : 'index.html';
    window.location.href = `${page}?reason=${reason}`;
}
