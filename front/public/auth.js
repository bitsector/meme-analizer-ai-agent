/**
 * Authentication utilities for Google OAuth integration
 */

class AuthManager {
    constructor() {
        this.token = null;
        this.user = null;
        this.init();
    }

    init() {
        // Check URL for token (from OAuth redirect)
        const urlParams = new URLSearchParams(window.location.search);
        const tokenFromUrl = urlParams.get('token');
        
        if (tokenFromUrl) {
            this.setToken(tokenFromUrl);
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
        } else {
            // Check localStorage for existing token
            const savedToken = localStorage.getItem('authToken');
            if (savedToken) {
                this.setToken(savedToken);
            }
        }

        this.updateUI();
        this.setupEventListeners();
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
        
        // Set Authorization header for all future API calls
        if (window.fetch) {
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                // Add auth header to requests to our backend
                if (args[0] && (args[0].startsWith('/') || args[0].includes('localhost:8000'))) {
                    args[1] = args[1] || {};
                    args[1].headers = args[1].headers || {};
                    args[1].headers['Authorization'] = `Bearer ${token}`;
                }
                return originalFetch.apply(this, args);
            };
        }

        this.fetchUserInfo();
    }

    async fetchUserInfo() {
        try {
            const response = await fetch('http://localhost:8000/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                this.user = await response.json();
                this.updateUI();
            } else if (response.status === 401) {
                // Token expired or invalid
                this.logout();
            }
        } catch (error) {
            console.error('Failed to fetch user info:', error);
        }
    }

    async login() {
        try {
            console.log('Starting login process...');
            const response = await fetch('http://localhost:8000/auth/login');
            console.log('Login response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Login response error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Login response data:', data);
            
            if (data.auth_url) {
                console.log('Redirecting to Google OAuth:', data.auth_url);
                // Redirect to Google OAuth
                window.location.href = data.auth_url;
            } else {
                throw new Error('No auth URL received from server');
            }
        } catch (error) {
            console.error('Login failed:', error);
            this.showError(`Login failed: ${error.message}`);
        }
    }

    async logout() {
        try {
            await fetch('http://localhost:8000/auth/logout', { method: 'POST' });
        } catch (error) {
            console.error('Logout request failed:', error);
        }

        this.token = null;
        this.user = null;
        localStorage.removeItem('authToken');
        
        // Reset fetch function
        if (window.originalFetch) {
            window.fetch = window.originalFetch;
        }

        this.updateUI();
    }

    isLoggedIn() {
        return !!this.token && !!this.user;
    }

    getUser() {
        return this.user;
    }

    updateUI() {
        const authSection = document.getElementById('authSection');
        if (!authSection) return;

        if (this.isLoggedIn()) {
            authSection.innerHTML = `
                <div class="user-info">
                    <img src="${this.user.avatar_url}" alt="Profile" class="user-avatar">
                    <span class="user-name">${this.user.name}</span>
                    <button class="auth-btn logout-btn" id="logoutBtn">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            `;
        } else {
            authSection.innerHTML = `
                <button class="auth-btn login-btn" id="loginBtn">
                    <i class="fab fa-google"></i> Login with Google
                </button>
            `;
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');

        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.login());
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    showError(message) {
        // You can implement a toast or notification system here
        console.error(message);
        alert(message);
    }
}

// Initialize auth manager when DOM is loaded
let authManager;
document.addEventListener('DOMContentLoaded', function() {
    authManager = new AuthManager();
});

// Export for use in other scripts
window.AuthManager = AuthManager;