// Configuration file for Smart Traffic Signal System Frontend

const CONFIG = {
    // API Endpoints
    api: {
        baseURL: 'http://localhost:5000',
        endpoints: {
            vehicleCount: '/api/vehicle-count',
            signalStatus: '/api/signal-status',
            emergencyMode: '/api/emergency-mode',
            manualOverride: '/api/manual-override',
            failsafeMode: '/api/failsafe-mode',
            cameraFeed: '/api/camera-feed'
        }
    },

    // Traffic Signal Timing (in seconds)
    timing: {
        minGreenTime: 5,
        maxGreenTime: 60,
        yellowTime: 3,
        redTime: 2,
        updateInterval: 1000  // milliseconds
    },

    // Lane Configuration
    lanes: {
        total: 4,
        names: ['Lane 1 (North)', 'Lane 2 (East)', 'Lane 3 (South)', 'Lane 4 (West)']
    },

    // Vehicle Detection Settings
    detection: {
        confidenceThreshold: 0.4,
        vehicleTypes: ['cars', 'trucks', 'bikes', 'emergency'],
        colors: {
            normal: '#4CAF50',
            emergency: '#F44336'
        }
    },

    // UI Settings
    ui: {
        refreshRate: 1000,  // milliseconds
        animationDuration: 500,
        maxHistoryRecords: 100,
        chartUpdateInterval: 5000
    },

    // System Modes
    modes: {
        AUTO: 'automatic',
        MANUAL: 'manual',
        EMERGENCY: 'emergency',
        FAILSAFE: 'failsafe'
    },

    // Alert Settings
    alerts: {
        showNotifications: true,
        emergencyAlertDuration: 5000,
        errorAlertDuration: 3000
    },

    // Development Settings
    dev: {
        debug: true,
        mockData: false,
        logLevel: 'info'  // 'debug', 'info', 'warn', 'error'
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
