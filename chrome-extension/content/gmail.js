// Gmail Content Script - Real-time Email Security Analysis

console.log('🛡️ ATF CyberX Email Security - Gmail Integration Active');

class GmailSecurityAnalyzer {
    constructor() {
        this.processedEmails = new Set(); // Avoid re-scanning same emails
        this.currentEmailHash = null;
        this.observer = null;
        this.scanTimeout = null; // For debouncing
        this.init();
    }

    init() {
        // Wait for Gmail to fully load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startMonitoring());
        } else {
            this.startMonitoring();
        }
    }

    startMonitoring() {
        console.log('🔍 Starting Gmail email monitoring...');

        // Task 10: Debouncing implemented here to improve performance
        this.observer = new MutationObserver((mutations) => {
            // Clear the previous timeout if a new mutation occurs quickly
            if (this.scanTimeout) clearTimeout(this.scanTimeout);
            
            // Wait 500ms after changes stop before scanning
            this.scanTimeout = setTimeout(() => {
                this.checkForNewEmail();
            }, 500);
        });

        // Start observing Gmail's main content area
        const gmailContent = document.querySelector('[role="main"]') || document.body;
        this.observer.observe(gmailContent, {
            childList: true,
            subtree: true
        });

        // Initial check for already loaded email
        setTimeout(() => this.checkForNewEmail(), 1000);
    }

    // Task 7: Async check for Auto-Scan setting
    async checkForNewEmail() {
        // 1. Check if auto-scan is enabled in user settings
        try {
            const settings = await chrome.storage.local.get(['autoScanEnabled']);
            // If setting exists and is explicitly false, stop here.
            if (settings.autoScanEnabled === false) {
                return;
            }
        } catch (err) {
            // 🛑 FIX: Detect invalidation and stop the script to prevent spam
            if (err.message.includes('Extension context invalidated')) {
                console.log('🛑 Extension updated. Stopping old content script observer.');
                if (this.observer) this.observer.disconnect();
                return;
            }
            console.warn('Could not read settings, proceeding with scan', err);
        }

        // 2. Locate the email container
        const emailContainer = this.findEmailContainer();
        if (!emailContainer) return;

        // 3. Extract data
        const emailData = this.extractEmailData(emailContainer);
        if (!emailData) return;

        // 4. Check hash to avoid re-processing the same email multiple times
        const emailHash = this.createEmailHash(emailData);
        if (this.processedEmails.has(emailHash)) return;

        console.log('📧 New email detected:', emailData.subject);
        this.processedEmails.add(emailHash);
        
        // 5. Analyze
        this.analyzeEmail(emailData, emailContainer);
    }

    findEmailContainer() {
        // Task 3: Robust Selectors for different Gmail views
        const selectors = [
            '[data-message-id]',           // Standard view
            '.ii.gt .a3s.aiL',             // Message body wrapper
            '[role="listitem"] .ii',       // Conversation view item
            '.nH .if',                     // Split view container
            '[data-legacy-message-id]',    // Old Gmail view
            '.gs .ii',                     // Generic message wrapper
            'div[data-message-id] .ii'     // Specific wrapper
        ];

        for (const selector of selectors) {
            const container = document.querySelector(selector);
            if (container && this.isValidEmailContainer(container)) {
                return container;
            }
        }
        return null;
    }

    isValidEmailContainer(container) {
        // Ensure we aren't scanning a compose window or empty div
        const hasSubject = container.querySelector('[data-subject]') ||
            container.querySelector('h2') ||
            document.querySelector('[data-subject]');
        const hasContent = container.textContent.trim().length > 10;
        return hasSubject && hasContent;
    }

    extractEmailData(container) {
        try {
            const subject = this.extractSubject();
            if (!subject) return null;

            const sender = this.extractSender();
            const body = this.extractBody(container);
            const links = this.extractLinks(container);

            return {
                subject: subject.trim(),
                from_email: sender.trim(),
                body: body.trim(),
                visible_links: links
            };
        } catch (error) {
            console.error('❌ Error extracting email data:', error);
            return null;
        }
    }

    extractSubject() {
        const selectors = ['[data-subject]', 'h2[data-subject]', '.hP', '.bog', 'h2.hP'];
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                const subject = element.getAttribute('data-subject') || element.textContent;
                if (subject && subject.trim()) return subject.trim();
            }
        }
        return null;
    }

    extractSender() {
        const selectors = ['[email]', '.go .g2', '.yW span[email]', '.yW .g2', '.qu .go .g2'];
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                const email = element.getAttribute('email') || element.getAttribute('data-email') || element.textContent;
                if (email && email.includes('@')) return email.trim();
            }
        }
        return 'unknown@unknown.com';
    }

    extractBody(container) {
        const bodySelectors = ['.ii.gt .a3s.aiL', '.a3s.aiL', '.ii.gt div[dir="ltr"]', '.ii.gt'];
        for (const selector of bodySelectors) {
            const bodyElement = container.querySelector(selector) || document.querySelector(selector);
            if (bodyElement) {
                let text = bodyElement.innerText || bodyElement.textContent || '';
                text = text.replace(/\s+/g, ' ').trim();
                if (text.length > 20) return text;
            }
        }
        return '';
    }

    extractLinks(container) {
        const links = [];
        const linkElements = container.querySelectorAll('a[href]');
        linkElements.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('http')) {
                links.push({ uri: href, anchor_text: link.textContent.trim() || href });
            }
        });
        return links;
    }

    createEmailHash(emailData) {
        const hashString = emailData.subject + emailData.from_email + emailData.body.substring(0, 100);
        return btoa(hashString).substring(0, 16);
    }

    async analyzeEmail(emailData, container) {
        try {
            console.log('🤖 Sending email for AI analysis...');
            
            // Send to background service (which handles API calls & caching)
            const response = await chrome.runtime.sendMessage({
                action: 'analyzeEmail',
                emailData: emailData
            });

            if (response && response.success) {
                console.log('✅ Analysis complete:', response.result.label);
                this.displaySecurityBadge(response.result, container);
            } else {
                console.error('❌ Analysis failed:', response?.error);
                // Task 4: Enhanced Error Handling
                this.displayErrorBadge(container, response?.error || 'Unknown Error');
            }
        } catch (error) {
            console.error('❌ Error during analysis:', error);
            this.displayErrorBadge(container, 'Connection Error');
        }
    }

    displaySecurityBadge(analysisResult, container) {
        const existingBadge = document.querySelector('.atf-security-badge');
        if (existingBadge) existingBadge.remove();

        const badge = this.createSecurityBadge(analysisResult);
        const headerArea = this.findEmailHeader();

        // Task 6: Improved Positioning logic
        if (headerArea) {
            // Try to place it near the sender info if possible
            const senderArea = headerArea.querySelector('.gD') || headerArea;
            if (senderArea.parentNode) {
                senderArea.parentNode.insertBefore(badge, senderArea.nextSibling);
            } else {
                headerArea.appendChild(badge);
            }
        } else {
            container.insertBefore(badge, container.firstChild);
        }
    }

    findEmailHeader() {
        const headerSelectors = ['.gE.iv.gt', '.hA', '.qu', '.adn.ads', 'table.cf.gJ'];
        for (const selector of headerSelectors) {
            const header = document.querySelector(selector);
            if (header) return header;
        }
        return null;
    }

    createSecurityBadge(analysisResult) {
        const { label, score } = analysisResult;
        const badgeConfig = this.getBadgeConfig(label, score);

        const badge = document.createElement('div');
        badge.className = 'atf-security-badge';
        
        // Most styles are now in gmail.css (Task 6), we only set dynamic colors here
        badge.style.background = badgeConfig.background;
        badge.style.color = badgeConfig.color;
        badge.style.border = `1px solid ${badgeConfig.border}`;
        
        // Basic structural styles required for correct display
        badge.style.cursor = 'pointer';
        badge.style.padding = '4px 10px';
        badge.style.borderRadius = '16px';
        badge.style.marginLeft = '12px';
        badge.style.fontSize = '12px';
        badge.style.fontWeight = '500';

        badge.innerHTML = `
            <span style="margin-right: 6px;">${badgeConfig.icon}</span>
            <span>${badgeConfig.text}</span>
        `;

        badge.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent Gmail from collapsing the email
            this.showDetailedExplanation(analysisResult, badge);
        });

        return badge;
    }

    getBadgeConfig(label, score) {
        switch (label) {
            case 'PHISHING':
                return { icon: '🚫', text: 'Phishing Detected', background: '#FEF2F2', color: '#DC2626', border: '#FECACA' };
            case 'SUSPICIOUS':
                return { icon: '⚠️', text: 'Suspicious', background: '#FFFBEB', color: '#D97706', border: '#FDE68A' };
            case 'SAFE':
            default:
                return { icon: '🛡️', text: 'Safe', background: '#ECFDF5', color: '#059669', border: '#A7F3D0' };
        }
    }

    showDetailedExplanation(analysisResult, badge) {
        const existingPanel = document.querySelector('.atf-explanation-panel');
        if (existingPanel) {
            existingPanel.remove();
            return;
        }

        const panel = this.createExplanationPanel(analysisResult);
        
        // Position relative to badge
        // Ensure parent has relative positioning for the absolute panel
        if (badge.parentNode) {
            badge.parentNode.style.position = 'relative'; 
            badge.parentNode.appendChild(panel);
        }
    }

    createExplanationPanel(analysisResult) {
        const { ai_explanation } = analysisResult;
        const panel = document.createElement('div');
        panel.className = 'atf-explanation-panel';
        
        // CSS class handles animation and glassmorphism (Task 6)
        // We set positioning and layout here
        panel.style.position = 'absolute';
        panel.style.top = '35px';
        panel.style.left = '0';
        panel.style.width = '320px';
        panel.style.zIndex = '1000';
        panel.style.padding = '16px';
        panel.style.borderRadius = '8px';
        panel.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)';
        panel.style.background = 'white'; // Fallback

        panel.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                <h4 style="margin:0; font-size:14px; font-weight:700;">Security Analysis</h4>
                <span class="close-panel" style="cursor:pointer; font-size:18px;">&times;</span>
            </div>
            <p style="font-size:13px; color:#374151; margin-bottom:12px;">${ai_explanation?.summary || 'Analysis complete.'}</p>
            
            <div style="background:#F3F4F6; padding:8px; border-radius:6px; margin-bottom:12px;">
                <strong style="font-size:11px; text-transform:uppercase; color:#6B7280;">Reasoning</strong>
                <p style="font-size:12px; margin:4px 0 0 0; color:#1F2937;">${ai_explanation?.ai_reasoning || 'No details.'}</p>
            </div>

            <button class="close-panel" style="width:100%; padding:6px; background:white; border:1px solid #D1D5DB; border-radius:4px; font-size:12px; cursor:pointer;">Dismiss</button>
        `;

        const closeBtns = panel.querySelectorAll('.close-panel');
        closeBtns.forEach(btn => btn.addEventListener('click', (e) => {
            e.stopPropagation();
            panel.remove();
        }));

        return panel;
    }

    displayErrorBadge(container, errorMessage) {
        const existingBadge = document.querySelector('.atf-security-badge');
        if (existingBadge) existingBadge.remove();

        const badge = document.createElement('div');
        badge.className = 'atf-security-badge';
        badge.style.background = '#F3F4F6';
        badge.style.color = '#6B7280';
        badge.style.border = '1px solid #E5E7EB';
        badge.style.padding = '4px 10px';
        badge.style.borderRadius = '16px';
        badge.style.fontSize = '12px';
        badge.style.fontWeight = '500';
        badge.style.marginLeft = '12px';
        
        // Task 4: Friendly Error Messages
        let text = 'Analysis Unavailable';
        if (errorMessage.includes('offline') || errorMessage.includes('Network') || errorMessage.includes('fetch')) {
            text = 'Offline';
        } else if (errorMessage.includes('timeout')) {
            text = 'Server Busy';
        }

        badge.innerHTML = `<span>⚠️ ${text}</span>`;
        badge.title = errorMessage; // Show full error on hover
        
        const headerArea = this.findEmailHeader();
        if (headerArea) {
            headerArea.appendChild(badge);
        } else {
            container.insertBefore(badge, container.firstChild);
        }
    }
}

const gmailAnalyzer = new GmailSecurityAnalyzer();