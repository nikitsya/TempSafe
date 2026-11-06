// Sign-in form handler.
// Sends the username and password to POST /api/login as JSON (never in the page
// address). On success (204) the browser stores the secure session cookie and
// the dashboard opens. Wrong details (401) show the agreed error message.

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signin');
    const message = document.getElementById('signin-message');
    if (!form || !message) return;

    // Short note when the user arrives here after signing out or a session ending.
    const reason = new URLSearchParams(window.location.search).get('reason');
    if (reason === 'signed-out') {
        showMessage('You have signed out.', null, 'info');
    } else if (reason === 'expired') {
        showMessage('Please sign in to continue.', null, 'info');
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const username = form.username.value.trim();
        const password = form.password.value;

        if (!username) {
            showMessage('Enter your email or username.', form.username);
            return;
        }
        if (!password) {
            showMessage('Enter your password.', form.password);
            return;
        }

        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        button.textContent = 'Signing in…';

        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password}),
            });

            if (response.status === 204) {
                window.location.href = 'pages/dashboard.html';
                return;
            }
            form.password.value = '';
            if (response.status === 401) {
                showMessage('Sign-in failed. The email/username or password is incorrect. Please try again.', form.username);
            } else {
                showMessage("Can't sign in right now. Please try again.", form.username);
            }
        } catch (error) {
            form.password.value = '';
            showMessage("Can't connect. Check your internet and try again.", form.username);
        } finally {
            button.disabled = false;
            button.textContent = 'Sign in';
        }
    });

    function showMessage(text, field, type = 'error') {
        message.textContent = text;
        message.className = `banner ${type === 'error' ? 'error' : ''}`;
        message.setAttribute('role', type === 'error' ? 'alert' : 'status');
        message.hidden = false;
        if (field) field.focus();
    }
});
