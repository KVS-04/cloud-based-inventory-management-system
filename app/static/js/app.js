/**
 * P5. Cloud-based Inventory Management System
 * Global JavaScript - Sidebar, Search, Notifications, Helpers
 */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initNotifications();
    initFlashMessages();
    initTooltips();
    initDeleteConfirm();
    animateCounters();
});

/* --- CSRF Token Helper --- */
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

/* --- API Call Helper --- */
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || 'Request failed');
        }
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message || 'An error occurred', 'danger');
        throw error;
    }
}

/* --- Sidebar Toggle --- */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggle = document.getElementById('sidebarToggle');
    const close = document.getElementById('sidebarClose');

    if (toggle) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        });
    }

    if (close) {
        close.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }
}

/* --- Notifications Polling --- */
function initNotifications() {
    updateNotificationCount();
    setInterval(updateNotificationCount, 30000);

    const markAllBtn = document.getElementById('markAllRead');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await apiCall('/api/notifications/read-all', 'PUT');
                updateNotificationCount();
            } catch (err) { /* handled in apiCall */ }
        });
    }
}

async function updateNotificationCount() {
    try {
        const data = await apiCall('/api/notifications/unread-count');
        const badge = document.getElementById('notificationCount');
        if (badge && data.data !== undefined) {
            const count = data.data;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    } catch (err) {
        // Silently handle — API may not be ready
    }
}

/* --- Flash Messages Auto-dismiss --- */
function initFlashMessages() {
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });
}

/* --- Bootstrap Tooltips --- */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
}

/* --- Delete Confirmation --- */
function initDeleteConfirm() {
    document.querySelectorAll('[data-confirm]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const msg = btn.getAttribute('data-confirm') || 'Are you sure you want to delete this item?';
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });
}

/* --- Toast Notification System --- */
function showToast(message, type = 'info', duration = 4000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = { success: 'check-circle', danger: 'x-circle', warning: 'exclamation-triangle', info: 'info-circle' };
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${icons[type] || 'info-circle'} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, duration);
}

/* --- Format Helpers --- */
function formatCurrency(num) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num || 0);
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num || 0);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/* --- Counter Animation --- */
function animateCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseFloat(el.getAttribute('data-counter'));
        const duration = 1500;
        const start = 0;
        const startTime = performance.now();
        const isDecimal = target % 1 !== 0;

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = start + (target - start) * easeOut;
            el.textContent = isDecimal ? current.toFixed(2) : Math.floor(current).toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    });
}

/* --- Global Search --- */
function initGlobalSearch() {
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        globalSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = globalSearch.value.trim();
                if (query) {
                    window.location.href = "/products/?search=" + encodeURIComponent(query);
                }
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGlobalSearch);
} else {
    initGlobalSearch();
}
