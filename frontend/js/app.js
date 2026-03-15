/**
 * AgentForge App Shell
 * Client-side router, auth management, theme toggling, toasts.
 */

// ---- State ----
let currentUser = null;
let currentPage = 'dashboard';

// ---- Init ----
document.addEventListener('DOMContentLoaded', async () => {
    applyTheme();
    // Initialize event listeners
    initEventListeners();
    
    if (API.token) {
        try {
            currentUser = await API.getMe();
            showApp();
        } catch {
            showAuth();
        }
    } else {
        showAuth();
    }
});

function initEventListeners() {
    // Auth Toggles
    const authThemeBtn = document.getElementById('auth-theme-icon')?.parentElement;
    if (authThemeBtn) authThemeBtn.addEventListener('click', toggleTheme);

    const sidebarThemeBtn = document.getElementById('sidebar-theme-icon')?.parentElement;
    if (sidebarThemeBtn) sidebarThemeBtn.addEventListener('click', toggleTheme);

    // Forms are handled via onsubmit in HTML but we can reinforce or move them
}

// ---- Auth ----
function showAuth() {
    document.getElementById('auth-page').classList.add('active');
    document.getElementById('app-shell').classList.add('hidden');
}

function showApp() {
    document.getElementById('auth-page').classList.remove('active');
    document.getElementById('app-shell').classList.remove('hidden');
    if (currentUser) {
        const greeting = document.getElementById('user-greeting');
        if (greeting) greeting.textContent = `Welcome, ${currentUser.full_name}`;
    }
    
    // Ensure Canvas is initialized early if needed
    if (typeof Canvas !== 'undefined') Canvas.init();
    
    navigateTo('dashboard');
}

function showAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    if (tab === 'login') {
        document.querySelectorAll('.auth-tab')[0].classList.add('active');
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    } else {
        document.querySelectorAll('.auth-tab')[1].classList.add('active');
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const btn = document.getElementById('login-btn');

    btn.disabled = true;
    btn.textContent = 'Signing in...';

    try {
        const data = await API.login(email, password);
        API.setToken(data.access_token);
        currentUser = data.user;
        showToast('Welcome back!', 'success');
        showApp();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const org = document.getElementById('reg-org').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const btn = document.getElementById('register-btn');

    btn.disabled = true;
    btn.textContent = 'Creating account...';

    try {
        const data = await API.register({
            full_name: name,
            organization_name: org,
            email,
            password,
        });
        API.setToken(data.access_token);
        currentUser = data.user;
        showToast('Account created!', 'success');
        showApp();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
}

function logout() {
    API.setToken(null);
    currentUser = null;
    showAuth();
    showToast('Logged out', 'success');
}

// ---- Navigation ----
function navigateTo(page) {
    currentPage = page;
    
    // Hide all pages
    document.querySelectorAll('.page-view').forEach(el => el.classList.add('hidden'));
    
    // Show target page
    // Show target page
    const targetPageEl = document.getElementById(`page-${page}`);
    if (targetPageEl) targetPageEl.classList.remove('hidden');

    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const navItem = document.getElementById(`nav-${page}`);
    if (navItem) navItem.classList.add('active');

    // Page-specific init
    switch (page) {
        case 'dashboard':
            renderDashboard();
            break;
        case 'canvas':
            // Canvas.init() is now called once in showApp or navigateTo if needed
            if (Canvas && !Canvas.initialized) Canvas.init();
            break;
        case 'executions':
            if (typeof loadExecutions === 'function') loadExecutions();
            break;
    }
    
    // Smooth transition effect (simplified)
    if (targetPageEl) {
        targetPageEl.style.opacity = '1';
    }
}

// ---- Theme ----
function getTheme() {
    return localStorage.getItem('agentforge_theme') || 'dark';
}

function applyTheme() {
    const theme = getTheme();
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcons(theme);
}

function toggleTheme() {
    const current = getTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('agentforge_theme', next);
    document.documentElement.setAttribute('data-theme', next);
    updateThemeIcons(next);
}

function updateThemeIcons(theme) {
    const icon = theme === 'dark' ? '🌙' : '☀️';
    const text = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
    
    ['sidebar-theme-icon', 'auth-theme-icon'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = icon;
    });
    ['sidebar-theme-text', 'auth-theme-text'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    });
}

// ---- Modals ----
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Close modals on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// ---- Toasts ----
function showToast(message, type = 'success', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `
        <span>${icons[type] || ''}</span>
        <span style="flex:1;">${message}</span>
        <button class="btn btn-ghost btn-sm" onclick="this.parentElement.remove()" style="padding:2px 6px;">✕</button>
    `;

    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

// ---- Keyboard Shortcuts ----
document.addEventListener('keydown', (e) => {
    // Escape to deselect / close panels
    if (e.key === 'Escape') {
        if (Canvas.selectedNodeId) {
            Canvas.deselectAll();
        }
        Canvas.closeConfigPanel();
        document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
        document.getElementById('node-palette').classList.remove('open');
    }

    // Delete selected node
    if (e.key === 'Delete' && Canvas.selectedNodeId && currentPage === 'canvas') {
        Canvas.removeNode(Canvas.selectedNodeId);
    }

    // Ctrl+S to save
    if (e.ctrlKey && e.key === 's' && currentPage === 'canvas') {
        e.preventDefault();
        Canvas.saveWorkflow();
    }
});
