// ATF CyberX Popup - Minimal Dashboard for MVP

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🛡️ ATF CyberX Popup - Loading...');

    // Load and display stats
    await loadStats();

    // Setup toggle functionality
    setupAutoScanToggle();
});

async function loadStats() {
    try {
        // Get stats from storage
        const result = await chrome.storage.local.get(['dailyStats', 'lastScan']);
        const stats = result.dailyStats || { scanned: 0, threats: 0 };
        const lastScan = result.lastScan || null;

        // Update UI
        document.getElementById('scanned-count').textContent = stats.scanned;
        document.getElementById('threats-count').textContent = stats.threats;
        document.getElementById('last-scan').textContent = lastScan
            ? formatTime(new Date(lastScan))
            : 'Never';

    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('scanned-count').textContent = '0';
        document.getElementById('threats-count').textContent = '0';
        document.getElementById('last-scan').textContent = 'Error';
    }
}

function setupAutoScanToggle() {
    const toggle = document.getElementById('auto-scan-toggle');

    // Load current setting
    chrome.storage.local.get(['autoScanEnabled'], (result) => {
        const enabled = result.autoScanEnabled !== false; // Default to true
        updateToggleUI(toggle, enabled);
    });

    // Handle toggle clicks
    toggle.addEventListener('click', async () => {
        const result = await chrome.storage.local.get(['autoScanEnabled']);
        const currentState = result.autoScanEnabled !== false;
        const newState = !currentState;

        await chrome.storage.local.set({ autoScanEnabled: newState });
        updateToggleUI(toggle, newState);

        console.log('Auto-scan toggled:', newState);
    });
}

function updateToggleUI(toggle, enabled) {
    if (enabled) {
        toggle.style.background = '#16a34a';
        toggle.style.setProperty('--toggle-position', 'right');
    } else {
        toggle.style.background = '#d1d5db';
        toggle.style.setProperty('--toggle-position', 'left');
    }
}

function formatTime(date) {
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) { // Less than 1 minute
        return 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    } else if (diff < 86400000) { // Less than 1 day
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Update stats when background service reports new scans
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'updateStats') {
        loadStats();
    }
});