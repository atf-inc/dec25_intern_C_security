// Popup Script for ATF CyberX Chrome Extension - Modern UI
console.log('🛡️ ATF CyberX Modern Popup loaded');

document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    await loadStats();
    setupEventListeners();
    setupLanguageToggle();
    startStatsRefresh();

    // Initialize translations
    updateAllTranslations();

    // Listen for language changes
    window.addEventListener('extensionLanguageChanged', (event) => {
        console.log('🌍 Language change detected in popup:', event.detail);
        updateAllTranslations();
        updateLanguageToggle(event.detail.newLanguage);
    });
});

async function loadSettings() {
    try {
        // Load sensitivity setting
        const result = await chrome.storage.local.get(['sensitivityLevel', 'preferredLanguage']);
        const sensitivityLevel = result.sensitivityLevel || 'balanced';
        const language = result.preferredLanguage || 'en';

        // Update extension language first
        if (window.extensionI18n) {
            await window.extensionI18n.setLanguage(language);
        }

        // Update sensitivity cards
        updateSensitivitySelection(sensitivityLevel);

        // Update language toggle
        updateLanguageToggle(language);

        // Update all translations
        updateAllTranslations();

        console.log('✅ Settings loaded:', { sensitivityLevel, language });
    } catch (error) {
        console.error('❌ Error loading settings:', error);
    }
}

async function loadStats() {
    try {
        // Request stats from background script
        const response = await chrome.runtime.sendMessage({ action: 'getStats' });

        if (response && response.success) {
            const stats = response.stats;
            updateStatsDisplay(stats);
            console.log('✅ Stats loaded:', stats);
        } else {
            console.warn('⚠️ Could not load stats');
            updateStatsDisplay({ scanned: 0, threats: 0 });
        }
    } catch (error) {
        console.error('❌ Error loading stats:', error);
        updateStatsDisplay({ scanned: 0, threats: 0 });
    }
}

function updateStatsDisplay(stats) {
    // Update quick stats
    document.getElementById('scanned-count').textContent = stats.scanned || 0;
    document.getElementById('threats-count').textContent = stats.threats || 0;

    // Update detailed stats
    document.getElementById('detailed-scanned').textContent = stats.scanned || 0;
    document.getElementById('detailed-threats').textContent = stats.threats || 0;

    // Add animation to numbers
    animateNumbers();
}

function animateNumbers() {
    const numbers = document.querySelectorAll('.stat-number, .stat-value');
    numbers.forEach(num => {
        num.style.transform = 'scale(1.1)';
        setTimeout(() => {
            num.style.transform = 'scale(1)';
        }, 200);
    });
}

function setupEventListeners() {
    // Sensitivity card click handlers
    document.querySelectorAll('.sensitivity-card').forEach(card => {
        card.addEventListener('click', async (e) => {
            const level = card.dataset.level;

            // Update UI
            updateSensitivitySelection(level);

            // Save setting
            try {
                await chrome.storage.local.set({ sensitivityLevel: level });
                console.log('✅ Sensitivity level saved:', level);

                // Show feedback
                showModernFeedback(getSensitivityMessage(level), getSensitivityIcon(level));
            } catch (error) {
                console.error('❌ Error saving sensitivity:', error);
            }
        });

        // Add hover effects
        card.addEventListener('mouseenter', () => {
            if (!card.classList.contains('selected')) {
                card.style.transform = 'translateY(-2px) scale(1.02)';
            }
        });

        card.addEventListener('mouseleave', () => {
            if (!card.classList.contains('selected')) {
                card.style.transform = 'translateY(0) scale(1)';
            }
        });
    });

    // Stats refresh button
    document.getElementById('refresh-stats').addEventListener('click', async () => {
        const refreshBtn = document.getElementById('refresh-stats');
        refreshBtn.style.transform = 'rotate(360deg)';

        await loadStats();

        setTimeout(() => {
            refreshBtn.style.transform = 'rotate(0deg)';
        }, 500);
    });
}

function setupLanguageToggle() {
    const languageSwitch = document.getElementById('language-switch');

    languageSwitch.addEventListener('change', async (e) => {
        const newLanguage = e.target.checked ? 'ja' : 'en';

        try {
            // Save language preference
            await chrome.storage.local.set({ preferredLanguage: newLanguage });

            // Update extension language
            if (window.extensionI18n) {
                await window.extensionI18n.setLanguage(newLanguage);
            }

            // Update all translations immediately
            updateAllTranslations();

            // Show feedback
            const message = newLanguage === 'ja' ? '言語が日本語に変更されました' : 'Language changed to English';
            showModernFeedback(message, '🌍');

            console.log('✅ Language changed to:', newLanguage);
        } catch (error) {
            console.error('❌ Error changing language:', error);
        }
    });
}

function updateAllTranslations() {
    if (!window.extensionI18n) {
        console.warn('⚠️ Translation system not ready');
        return;
    }

    // Update all elements with data-i18n attributes
    const translatableElements = document.querySelectorAll('[data-i18n]');
    translatableElements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = window.extensionI18n.t(key);

        // Handle special cases for elements with icons
        if (key === 'ui_detection_mode') {
            element.textContent = `🎯 ${translation.replace('🎯 ', '')}`;
        } else if (key === 'ui_todays_activity') {
            element.textContent = `📊 ${translation.replace('📊 ', '')}`;
        } else {
            element.textContent = translation;
        }
    });

    console.log('✅ All translations updated');
}

function updateLanguageToggle(language) {
    const languageSwitch = document.getElementById('language-switch');
    languageSwitch.checked = language === 'ja';
}

function updateSensitivitySelection(selectedLevel) {
    // Remove all selections
    document.querySelectorAll('.sensitivity-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selection to chosen card
    const selectedCard = document.querySelector(`[data-level="${selectedLevel}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');

        // Update radio button
        const radio = selectedCard.querySelector('input[type="radio"]');
        if (radio) {
            radio.checked = true;
        }

        // Add selection animation
        selectedCard.style.transform = 'scale(1.05)';
        setTimeout(() => {
            selectedCard.style.transform = 'scale(1)';
        }, 200);
    }
}

function getSensitivityMessage(level) {
    if (!window.extensionI18n) return 'Settings updated';

    const i18n = window.extensionI18n;
    const messages = {
        'conservative': `🎯 ${i18n.t('popup_conservative')} ${i18n.t('loading_analysis').toLowerCase().replace('analyzing email', 'mode enabled')}`,
        'balanced': `⚖️ ${i18n.t('popup_balanced')} ${i18n.t('loading_analysis').toLowerCase().replace('analyzing email', 'mode enabled')}`,
        'aggressive': `🔍 ${i18n.t('popup_aggressive')} ${i18n.t('loading_analysis').toLowerCase().replace('analyzing email', 'mode enabled')}`
    };

    // Simplified messages for better UX
    const simpleMessages = {
        'conservative': `🎯 ${i18n.t('popup_conservative')} mode enabled`,
        'balanced': `⚖️ ${i18n.t('popup_balanced')} mode enabled`,
        'aggressive': `🔍 ${i18n.t('popup_aggressive')} mode enabled`
    };

    return simpleMessages[level] || 'Settings updated';
}

function getSensitivityIcon(level) {
    const icons = {
        'conservative': '🎯',
        'balanced': '⚖️',
        'aggressive': '🔍'
    };
    return icons[level] || '✅';
}

function showModernFeedback(message, icon = '✅') {
    // Create modern toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%) translateY(-20px);
        background: rgba(16, 185, 129, 0.95);
        backdrop-filter: blur(10px);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        font-size: 12px;
        font-weight: 500;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
        opacity: 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    `;

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    });

    // Animate out and remove
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(-20px)';

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 400);
    }, 2500);
}

function startStatsRefresh() {
    // Auto-refresh stats every 30 seconds
    setInterval(async () => {
        await loadStats();
    }, 30000);
}

// Add smooth transitions to all interactive elements
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        * {
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                       opacity 0.3s ease,
                       background 0.3s ease,
                       border-color 0.3s ease,
                       color 0.3s ease;
        }
    `;
    document.head.appendChild(style);
});