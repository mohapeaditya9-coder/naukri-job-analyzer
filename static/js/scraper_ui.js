/**
 * Scraper UI & Progress Manager
 * Coordinates live scraping requests, status polling, progress bar updates, and log streaming.
 */

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('naukriSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleScrapeSubmit);
    }

    const seedBtn = document.getElementById('seedSampleBtn');
    if (seedBtn) {
        seedBtn.addEventListener('click', handleSeedSample);
    }
});

let pollInterval = null;

async function handleScrapeSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    const role = document.getElementById('jobRoleInput').value.trim();
    const location = document.getElementById('locationInput').value.trim();
    const experience = document.getElementById('experienceInput').value.trim();
    const pages = document.getElementById('pagesInput').value;

    if (!role) {
        alert('Please enter a target Job Role.');
        return;
    }

    // Open Progress Modal
    const progressModalElem = document.getElementById('scrapingProgressModal');
    const modal = new bootstrap.Modal(progressModalElem, { backdrop: 'static', keyboard: false });
    modal.show();

    // Reset UI state
    updateProgressUI({
        percent: 5,
        status_message: 'Connecting to Naukri Scraper engine...',
        jobs_scraped: 0,
        logs: ['Initiating request payload...']
    });

    try {
        const response = await fetch('/api/scrape/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, location, experience, pages })
        });

        const data = await response.json();
        if (response.ok) {
            startStatusPolling(modal);
        } else {
            showScrapeError(data.message || 'Failed to start scraping.');
        }
    } catch (err) {
        showScrapeError('Network error connecting to backend API: ' + err.message);
    }
}

function startStatusPolling(modal) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/scrape/status');
            const state = await res.json();
            updateProgressUI(state);

            if (!state.is_running) {
                clearInterval(pollInterval);
                pollInterval = null;
                
                const actionBtns = document.getElementById('progressModalActions');
                if (actionBtns) {
                    actionBtns.classList.remove('d-none');
                }
            }
        } catch (err) {
            console.error('Status poll error:', err);
        }
    }, 800);
}

function updateProgressUI(state) {
    const progressBar = document.getElementById('scrapeProgressBar');
    const percentLabel = document.getElementById('scrapePercentLabel');
    const statusMsg = document.getElementById('scrapeStatusMsg');
    const jobsCount = document.getElementById('scrapeJobsCount');
    const logBox = document.getElementById('scrapeLogConsole');

    if (progressBar) {
        progressBar.style.width = `${state.percent}%`;
        progressBar.setAttribute('aria-valuenow', state.percent);
    }
    if (percentLabel) {
        percentLabel.innerText = `${state.percent}%`;
    }
    if (statusMsg) {
        statusMsg.innerText = state.status_message;
    }
    if (jobsCount) {
        jobsCount.innerText = state.jobs_scraped || 0;
    }

    if (logBox && state.logs) {
        logBox.innerHTML = state.logs.map(log => `<div class="console-log-item">${escapeHtml(log)}</div>`).join('');
        logBox.scrollTop = logBox.scrollHeight;
    }
}

function showScrapeError(msg) {
    if (pollInterval) clearInterval(pollInterval);
    const statusMsg = document.getElementById('scrapeStatusMsg');
    if (statusMsg) {
        statusMsg.innerHTML = `<span class="text-danger"><i class="fa-solid fa-triangle-exclamation me-1"></i> ${escapeHtml(msg)}</span>`;
    }
    const actionBtns = document.getElementById('progressModalActions');
    if (actionBtns) {
        actionBtns.classList.remove('d-none');
    }
}

async function handleSeedSample() {
    const btn = document.getElementById('seedSampleBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Seeding...';

    try {
        const res = await fetch('/api/database/seed', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            window.location.href = '/dashboard';
        } else {
            alert('Failed to seed sample: ' + data.message);
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (err) {
        alert('Network error: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
