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
                row.style.transition = 'opacity 0.3s, transform 0.3s';
                row.style.opacity = '0';
                row.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    row.remove();
                    // If no rows left, reload to show empty state
                    if (document.querySelectorAll('.filterable-row').length === 0) {
                        window.location.reload();
                    }
                }, 300);
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

// Re-seed Sample Dataset
async function seedSampleData() {
    try {
        const seedBtns = document.querySelectorAll('#seedSampleBtn, .seed-btn');
        seedBtns.forEach(b => {
            b.disabled = true;
            b.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Seeding...';
        });

        const res = await fetch('/api/database/seed', { method: 'POST' });
        const data = await res.json();
        if (res.ok && data.success) {
            window.location.reload();
        } else {
            alert('Failed to seed sample data: ' + (data.message || 'Error'));
            seedBtns.forEach(b => {
                b.disabled = false;
                b.innerHTML = '<i class="fa-solid fa-database me-1"></i> Re-seed Sample Data';
            });
        }
    } catch (err) {
        alert('Network error: ' + err.message);
        window.location.reload();
    }
}

// Refresh Database View
function refreshDatabaseView() {
    const refreshBtn = document.getElementById('refreshDbBtn');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fa-solid fa-rotate fa-spin"></i> Refreshing...';
    }
    window.location.reload();
}

// Filter table rows by clicked field chip or custom field query
function filterByField(field) {
    const term = (field || '').toLowerCase().trim();
    const searchInput = document.getElementById('clientTableSearch');
    if (searchInput) {
        searchInput.value = field;
    }

    // Update active class on chips
    document.querySelectorAll('.field-chip').forEach(chip => {
        if (!field && chip.textContent.trim() === 'All Fields') {
            chip.classList.add('active');
        } else if (field && chip.textContent.toLowerCase().includes(term)) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });

    const rows = document.querySelectorAll('.filterable-row');
    let visibleCount = 0;
    rows.forEach(row => {
        const text = (
            (row.getAttribute('data-role') || '') + ' ' +
            (row.getAttribute('data-skills') || '') + ' ' +
            (row.getAttribute('data-company') || '') + ' ' +
            (row.getAttribute('data-location') || '') + ' ' +
            row.innerText
        ).toLowerCase();
        
        const match = !term || text.includes(term);
        row.style.display = match ? '' : 'none';
        if (match) visibleCount++;
    });
}

// Client-side instant table search filter
function initFilterHandlers() {
    const searchInput = document.getElementById('clientTableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            
            // Remove active from predefined chips if typing custom
            document.querySelectorAll('.field-chip').forEach(chip => {
                if (!term && chip.textContent.trim() === 'All Fields') {
                    chip.classList.add('active');
                } else if (term && chip.textContent.toLowerCase().includes(term)) {
                    chip.classList.add('active');
                } else {
                    chip.classList.remove('active');
                }
            });

            const rows = document.querySelectorAll('.filterable-row');
            rows.forEach(row => {
                const text = (
                    (row.getAttribute('data-role') || '') + ' ' +
                    (row.getAttribute('data-skills') || '') + ' ' +
                    (row.getAttribute('data-company') || '') + ' ' +
                    (row.getAttribute('data-location') || '') + ' ' +
                    row.innerText
                ).toLowerCase();
                row.style.display = (!term || text.includes(term)) ? '' : 'none';
            });
        });
    }
}

// Print / PDF Export Helper
function printReport() {
    window.print();
}
