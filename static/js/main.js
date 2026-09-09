/**
 * Main JavaScript Module
 * Handles Theme Toggling (Light/Dark), KPI Counter Animations, Auto-Refresh, and Chart Re-rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initCounters();
    initTooltips();
    initMobileMenu();
});

// ==========================================
// Theme Management (Light / Dark Mode)
// ==========================================
function initTheme() {
    const savedTheme = localStorage.getItem('naukri_theme') || 'light';
    setTheme(savedTheme);

    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    const otherToggleBtns = document.querySelectorAll('.theme-toggle-btn:not(#themeToggleBtn)');
    otherToggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const currentTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.classList.toggle('light', theme === 'light');
    
    if (document.body) {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(theme === 'dark' ? 'theme-dark' : 'theme-light');
    }
    
    localStorage.setItem('naukri_theme', theme);
    
    // Update theme toggle button icons
    const moonIcon = document.getElementById('moonIcon');
    const sunIcon = document.getElementById('sunIcon');
    if (moonIcon && sunIcon) {
        if (theme === 'dark') {
            moonIcon.classList.add('hidden');
            sunIcon.classList.remove('hidden');
        } else {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }
    }

    // Re-style Plotly charts for dark/light contrast
    rethemePlotlyCharts(theme);
}

function rethemePlotlyCharts(theme) {
    if (typeof Plotly === 'undefined') return;
    
    const fontColor = theme === 'dark' ? '#cbd5e1' : '#334155';
    const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(148, 163, 184, 0.18)';
    const titleColor = theme === 'dark' ? '#f8fafc' : '#0f172a';

    const chartElements = document.querySelectorAll('.plotly-graph-div, .chart-container');
    chartElements.forEach(elem => {
        try {
            Plotly.relayout(elem, {
                'font.color': fontColor,
                'xaxis.color': fontColor,
                'yaxis.color': fontColor,
                'xaxis.gridcolor': gridColor,
                'yaxis.gridcolor': gridColor,
                'xaxis.tickfont.color': fontColor,
                'yaxis.tickfont.color': fontColor,
                'title.font.color': titleColor,
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'plot_bgcolor': 'rgba(0,0,0,0)'
            });
        } catch (e) {
            // Chart may not yet be initialized
        }
    });
}

// ==========================================
// Animated Counter Numbers
// ==========================================
function initCounters() {
    const counterElements = document.querySelectorAll('.counter-anim');
    counterElements.forEach(el => {
        const rawTarget = el.getAttribute('data-target') || el.innerText.replace(/[^0-9.]/g, '');
        const target = parseFloat(rawTarget);
        if (isNaN(target)) return;
        
        const isDecimal = target % 1 !== 0;
        const prefix = el.getAttribute('data-prefix') || '';
        const suffix = el.getAttribute('data-suffix') || '';
        
        let start = 0;
        const duration = 1200;
        const startTime = performance.now();

        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const currentVal = start + (target - start) * easeProgress;

            el.innerText = `${prefix}${isDecimal ? currentVal.toFixed(1) : Math.round(currentVal)}${suffix}`;

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                el.innerText = `${prefix}${isDecimal ? target.toFixed(1) : target}${suffix}`;
            }
        }
        requestAnimationFrame(updateCounter);
    });
}

// ==========================================
// Bootstrap Tooltips Initialization
// ==========================================
function initTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
}

// ==========================================
// Mobile Hamburger Menu & Slide Drawer
// ==========================================
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenuCloseBtn = document.getElementById('mobileMenuCloseBtn');
    const mobileMenuBackdrop = document.getElementById('mobileMenuBackdrop');
    const mobileMenuDrawer = document.getElementById('mobileMenuDrawer');

    function openMenu() {
        if (mobileMenuBackdrop && mobileMenuDrawer) {
            mobileMenuBackdrop.classList.remove('opacity-0', 'pointer-events-none');
            mobileMenuBackdrop.classList.add('opacity-100', 'pointer-events-auto');
            mobileMenuDrawer.classList.remove('-translate-x-full');
            mobileMenuDrawer.classList.add('translate-x-0');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeMenu() {
        if (mobileMenuBackdrop && mobileMenuDrawer) {
            mobileMenuBackdrop.classList.remove('opacity-100', 'pointer-events-auto');
            mobileMenuBackdrop.classList.add('opacity-0', 'pointer-events-none');
            mobileMenuDrawer.classList.remove('translate-x-0');
            mobileMenuDrawer.classList.add('-translate-x-full');
            document.body.style.overflow = '';
        }
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openMenu();
        });
    }
    if (mobileMenuCloseBtn) {
        mobileMenuCloseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeMenu();
        });
    }
    if (mobileMenuBackdrop) {
        mobileMenuBackdrop.addEventListener('click', closeMenu);
    }
    document.querySelectorAll('.mobile-nav-link').forEach(link => {
        link.addEventListener('click', closeMenu);
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeMenu();
    });
}

