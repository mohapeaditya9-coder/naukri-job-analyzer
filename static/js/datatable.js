/**
 * Database & Table Management Script
 * Handles CRUD modals (Add, Edit, Delete, Clear), live client filtering, and PDF generation.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCrudHandlers();
    initFilterHandlers();
});

function initCrudHandlers() {
    // Add Job Form
    const addForm = document.getElementById('addJobForm');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(addForm);
            const payload = Object.fromEntries(formData.entries());

            try {
                const res = await fetch('/api/jobs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    window.location.reload();
                } else {
                    alert('Error adding job: ' + (data.message || 'Unknown error'));
                }
            } catch (err) {
                alert('Network error: ' + err.message);
            }
        });
    }

    // Edit Job Form
    const editForm = document.getElementById('editJobForm');
    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const jobId = document.getElementById('editJobId').value;
            const formData = new FormData(editForm);
            const payload = Object.fromEntries(formData.entries());

            try {
                const res = await fetch(`/api/jobs/${jobId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    window.location.reload();
                } else {
                    alert('Error updating job: ' + (data.message || 'Unknown error'));
                }
            } catch (err) {
                alert('Network error: ' + err.message);
            }
        });
    }
}

// Populate and show edit modal
async function openEditJobModal(jobId) {
    try {
        const res = await fetch(`/api/jobs/${jobId}`);
        const result = await res.json();
        if (!result.success || !result.data) {
            alert('Could not fetch job details.');
            return;
        }

        const job = result.data;
        document.getElementById('editJobId').value = job.id;
        document.getElementById('editJobTitle').value = job.job_title || '';
        document.getElementById('editCompany').value = job.company || '';
        document.getElementById('editLocation').value = job.location || '';
        document.getElementById('editSalary').value = job.salary || '';
        document.getElementById('editExperience').value = job.experience || '';
        document.getElementById('editSkills').value = job.skills || '';
        document.getElementById('editJobType').value = job.job_type || 'On-site';
        document.getElementById('editPostedDate').value = job.posted_date || '';
        document.getElementById('editJobLink').value = job.job_link || '';

        const modal = new bootstrap.Modal(document.getElementById('editJobModal'));
        modal.show();
    } catch (err) {
        alert('Failed to load job for editing: ' + err.message);
    }
}

// Delete Single Job
async function deleteJob(jobId, jobTitle) {
    if (!confirm(`Are you sure you want to delete "${jobTitle}" (ID: ${jobId})?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok && data.success) {
            // Remove table row smoothly or reload
            const row = document.getElementById(`job-row-${jobId}`);
            if (row) {
                row.remove();
            } else {
                window.location.reload();
            }
        } else {
            alert('Failed to delete job: ' + (data.message || 'Error'));
        }
    } catch (err) {
        alert('Network error: ' + err.message);
    }
}

// Clear Entire Database
async function clearAllJobs() {
    if (!confirm('WARNING: Are you sure you want to delete ALL jobs from the database? This cannot be undone.')) {
        return;
    }

    try {
        const res = await fetch('/api/database/clear', { method: 'POST' });
        const data = await res.json();
        if (res.ok && data.success) {
            window.location.reload();
        } else {
            alert('Failed to clear database: ' + (data.message || 'Error'));
        }
    } catch (err) {
        alert('Network error: ' + err.message);
    }
}

// Client-side instant table search filter
function initFilterHandlers() {
    const searchInput = document.getElementById('clientTableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.filterable-row');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
}

// Print / PDF Export Helper
function printReport() {
    window.print();
}
