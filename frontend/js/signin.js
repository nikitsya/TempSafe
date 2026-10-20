// Sign-in form handler.
// The backend sign-in endpoint is not implemented yet, so the form never
// submits the password in the page address (URL). It checks that both fields
// are filled in and shows a clear message instead.

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signin');
    const message = document.getElementById('signin-message');
    if (!form || !message) return;

    form.addEventListener('submit', (event) => {
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
        form.password.value = '';
        showMessage('Sign-in is not available yet. It will be connected to the backend in a later sprint.', form.username);
    });

    function showMessage(text, field) {
        message.textContent = text;
        message.hidden = false;
        field.focus();
    }
});
