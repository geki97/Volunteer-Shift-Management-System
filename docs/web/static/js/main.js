/**
 * Main JavaScript for Volunteer Check-In System
 */

// Utility Functions
const Utils = {
    // Format date to readable format
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IE', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    // Format time to readable format
    formatTime: (timeString) => {
        if (!timeString) return 'TBD';
        const [hours, minutes] = timeString.split(':');
        return `${hours}:${minutes}`;
    },

    // Show notification
    showNotification: (message, type = 'info') => {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },

    // Show loading state
    setLoading: (element, isLoading) => {
        if (isLoading) {
            element.classList.add('loading');
            element.disabled = true;
        } else {
            element.classList.remove('loading');
            element.disabled = false;
        }
    },

    // Validate email
    validateEmail: (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Get URL parameter
    getUrlParam: (param) => {
        const params = new URLSearchParams(window.location.search);
        return params.get(param);
    }
};

// API Helper Functions
const API = {
    // Generic fetch wrapper
    request: async (url, method = 'GET', data = null) => {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            if (data && (method === 'POST' || method === 'PUT')) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },

    // Get volunteer by email
    getVolunteer: async (email) => {
        return API.request(`/api/volunteer/${email}`);
    },

    // Get upcoming shifts
    getUpcomingShifts: async () => {
        return API.request('/api/shifts/upcoming');
    },

    // Get shift attendance
    getShiftAttendance: async (shiftId) => {
        return API.request(`/api/shift/${shiftId}/attendance`);
    },

    // Generate QR code
    generateQR: async (shiftId) => {
        return API.request(`/api/qr/${shiftId}/generate`, 'POST');
    },

    // Check system health
    checkHealth: async () => {
        return API.request('/health');
    }
};

// Page Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips or other interactive elements
    initializePageElements();
});

function initializePageElements() {
    // Add any global event listeners or initialization code here
    console.log('Volunteer Check-In System initialized');
}

// Export for use in other scripts
window.Utils = Utils;
window.API = API;
