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

// Graph line between two readings, split where it crosses a limit, so the colour
// changes exactly at the limit (FR-05): Alert at or below the minimum or above the
// maximum, Warning from "warning from" up to the maximum, otherwise Normal.
// Returns pieces {t1, v1, t2, v2, cls}. Without limits the whole piece gets `fallback`.
function limitPieces(t1, v1, t2, v2, limits, fallback) {
    const lower = limits ? Number(limits.lowerC) : NaN;
    const warning = limits ? Number(limits.warningC) : NaN;
    const upper = limits ? Number(limits.upperC) : NaN;
    if (!Number.isFinite(lower) || !Number.isFinite(upper)) {
        return [{t1, v1, t2, v2, cls: fallback}];
    }
    const cls = (v) => {
        if (v <= lower || v > upper) return 'line-alert';
        if (Number.isFinite(warning) && v >= warning) return 'line-warning';
        return 'line-normal';
    };
    // Points where the line crosses a limit, in time order.
    const cuts = [lower, warning, upper]
        .filter((c) => Number.isFinite(c) && (c - v1) * (c - v2) < 0)
        .map((c) => (c - v1) / (v2 - v1))
        .sort((a, b) => a - b);
    const fractions = [0, ...cuts, 1];
    const pieces = [];
    for (let i = 1; i < fractions.length; i++) {
        const a = fractions[i - 1];
        const b = fractions[i];
        const va = v1 + (v2 - v1) * a;
        const vb = v1 + (v2 - v1) * b;
        pieces.push({
            t1: t1 + (t2 - t1) * a, v1: va,
            t2: t1 + (t2 - t1) * b, v2: vb,
            cls: cls((va + vb) / 2),
        });
    }
    return pieces;
}

// How long something lasted, as short and clear as possible, the same on every page:
// "4 min", "1 h 20 min" (up to 24 h), "1 day 16 h", "8 days", "1 month 3 days".
function readableDuration(minutes) {
    minutes = Math.max(1, Math.round(minutes));
    if (minutes < 60) return `${minutes} min`;
    if (minutes < 1440) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return m ? `${h} h ${m} min` : `${h} h`;
    }
    const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
    const hours = Math.round(minutes / 60);
    const days = Math.floor(hours / 24);
    if (days < 30) {
        const h = hours % 24;
        return h && days < 7 ? `${plural(days, 'day')} ${h} h` : plural(days, 'day');
    }
    const months = Math.floor(days / 30);
    const restDays = days % 30;
    return restDays ? `${plural(months, 'month')} ${plural(restDays, 'day')}` : plural(months, 'month');
}
