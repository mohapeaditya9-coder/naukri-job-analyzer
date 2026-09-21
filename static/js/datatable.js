/**
 * Database & Table Management Script
 * Handles CRUD modals (Add, Edit, Delete, Clear), live client filtering, match counters, and export.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCrudHandlers();
    initFilterHandlers();
    updateMatchCounter();
});

function initCrudHandlers() {
    // Add Job Form
    const addForm = document.getElementById('addJobForm');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = addForm.querySelector('button[type="submit"]');
            const originalText = submitBtn ? submitBtn.innerHTML : 'Save';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Saving...';
            }

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
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                }
            } catch (err) {
                alert('Network error: ' + err.message);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            }
        });
    }

    // Edit Job Form
    const editForm = document.getElementById('editJobForm');
    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const jobId = document.getElementById('editJobId').value;
            const submitBtn = editForm.querySelector('button[type="submit"]');
            const originalText = submitBtn ? submitBtn.innerHTML : 'Update';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Updating...';
            }

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
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                }
            } catch (err) {
                alert('Network error: ' + err.message);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
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

        const modalElem = document.getElementById('editJobModal');
        if (modalElem) {
            const modal = new bootstrap.Modal(modalElem);
            modal.show();
        }
    } catch (err) {
        alert('Failed to load job for editing: ' + err.message);
    }
}

// Delete Single Job
async function deleteJob(jobId, jobTitle) {
    if (!confirm(`Are you sure you want to delete "${jobTitle}" (ID: #${jobId})?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok && data.success) {
            const row = document.getElementById(`job-row-${jobId}`);
            if (row) {
                row.style.transition = 'opacity 0.3s, transform 0.3s';
                row.style.opacity = '0';
                row.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    row.remove();
                    updateMatchCounter();
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
    if (!confirm('WARNING: Are you sure you want to delete ALL jobs from the database? This action cannot be undone.')) {
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

    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) {
        clearBtn.style.display = term ? 'inline-block' : 'none';
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

    applyFilter(term);
}

// Apply text filter to all table rows and update counter & no-match banner
function applyFilter(term) {
    const rows = document.querySelectorAll('.filterable-row');
    let visibleCount = 0;
    const totalCount = rows.length;

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

    // Update match counter badge
    const badge = document.getElementById('matchCounterBadge');
    if (badge) {
        if (!term) {
            badge.innerText = `Showing ${totalCount} of ${totalCount}`;
            badge.className = 'badge bg-primary text-white rounded-pill px-2 py-0.5';
        } else {
            badge.innerText = `Showing ${visibleCount} of ${totalCount}`;
            badge.className = visibleCount > 0 ? 'badge bg-success text-white rounded-pill px-2 py-0.5' : 'badge bg-danger text-white rounded-pill px-2 py-0.5';
        }
    }

    // Show/hide no matching rows placeholder
    const noMatchRow = document.getElementById('noMatchRow');
    if (noMatchRow) {
        noMatchRow.style.display = (totalCount > 0 && visibleCount === 0) ? '' : 'none';
    }
}

// Update match counter when rows change
function updateMatchCounter() {
    const searchInput = document.getElementById('clientTableSearch');
    const term = searchInput ? searchInput.value.toLowerCase().trim() : '';
    applyFilter(term);
}

// Clear table search input and reset filter
function clearTableSearch() {
    const searchInput = document.getElementById('clientTableSearch');
    if (searchInput) {
        searchInput.value = '';
    }
    filterByField('');
}

// Client-side instant table search filter
function initFilterHandlers() {
    const searchInput = document.getElementById('clientTableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase().trim();
            const clearBtn = document.getElementById('clearSearchBtn');
            if (clearBtn) {
                clearBtn.style.display = term ? 'inline-block' : 'none';
            }
            
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

            applyFilter(term);
        });
    }
}

// Print / PDF Export Helper
function printReport() {
    window.print();
}

