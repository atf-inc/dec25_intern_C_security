// Gmail Content Script - Real-time Email Security Analysis
// This is the core of our MVP - extracts email data and triggers AI analysis

console.log('🛡️ ATF CyberX Email Security - Gmail Integration Active');

class GmailSecurityAnalyzer {
    constructor() {
        this.processedEmails = new Set(); // Avoid re-scanning same emails
        this.currentEmailHash = null;
        this.observer = null;
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

        // Monitor for email view changes using MutationObserver
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    this.checkForNewEmail();
                }
            });
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

    checkForNewEmail() {
        const emailContainer = this.findEmailContainer();
        if (!emailContainer) return;

        const emailData = this.extractEmailData(emailContainer);
        if (!emailData) return;

        // Create hash to avoid re-processing same email
        const emailHash = this.createEmailHash(emailData);
        if (this.processedEmails.has(emailHash)) return;

        console.log('📧 New email detected:', emailData.subject);
        this.processedEmails.add(emailHash);
        this.currentEmailHash = emailHash;

        // Send to background service for AI analysis
        this.analyzeEmail(emailData, emailContainer);
    }

    findEmailContainer() {
        // Gmail email container selectors (multiple fallbacks)
        const selectors = [
            '[data-message-id]',           // Primary email container
            '.ii.gt .a3s.aiL',            // Email body container
            '[role="listitem"] .ii',       // Email in conversation
            '.nH .if'                      // Fallback container
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
        // Validate this is actually an email (not compose, etc.)
        const hasSubject = container.querySelector('[data-subject]') ||
            container.querySelector('h2') ||
            document.querySelector('[data-subject]');
        const hasContent = container.textContent.trim().length > 10;
        return hasSubject && hasContent;
    }

    extractEmailData(container) {
        try {
            // Extract subject
            const subject = this.extractSubject();
            if (!subject) return null;

            // Extract sender
            const sender = this.extractSender();

            // Extract email body (text only)
            const body = this.extractBody(container);

            // Extract visible links
            const links = this.extractLinks(container);

            const emailData = {
                subject: subject.trim(),
                from_email: sender.trim(),
                body: body.trim(),
                visible_links: links
            };

            console.log('📊 Extracted email data:', {
                subject: emailData.subject,
                sender: emailData.from_email,
                bodyLength: emailData.body.length,
                linkCount: emailData.visible_links.length
            });

            return emailData;
        } catch (error) {
            console.error('❌ Error extracting email data:', error);
            return null;
        }
    }

    extractSubject() {
        const selectors = [
            '[data-subject]',
            'h2[data-subject]',
            '.hP',
            '.bog',
            'h2.hP'
        ];

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
        const selectors = [
            '[email]',
            '.go .g2',
            '.yW span[email]',
            '.yW .g2',
            '.qu .go .g2'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                const email = element.getAttribute('email') ||
                    element.getAttribute('data-email') ||
                    element.textContent;
                if (email && email.includes('@')) return email.trim();
            }
        }
        return 'unknown@unknown.com';
    }

    extractBody(container) {
        // Get email body text, excluding headers and signatures
        const bodySelectors = [
            '.ii.gt .a3s.aiL',
            '.a3s.aiL',
            '.ii.gt div[dir="ltr"]',
            '.ii.gt'
        ];

        for (const selector of bodySelectors) {
            const bodyElement = container.querySelector(selector) || document.querySelector(selector);
            if (bodyElement) {
                // Clean up the text - remove extra whitespace, keep structure
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
            const text = link.textContent.trim();

            if (href && href.startsWith('http')) {
                links.push({
                    uri: href,
                    anchor_text: text || href
                });
            }
        });

        return links;
    }

    createEmailHash(emailData) {
        // Simple hash to identify unique emails
        const hashString = emailData.subject + emailData.from_email + emailData.body.substring(0, 100);
        return btoa(hashString).substring(0, 16);
    }

    async analyzeEmail(emailData, container) {
        try {
            console.log('🤖 Sending email for AI analysis...');

            // Send to background service
            const response = await chrome.runtime.sendMessage({
                action: 'analyzeEmail',
                emailData: emailData
            });

            if (response && response.success) {
                console.log('✅ Analysis complete:', response.result.label);
                this.displaySecurityBadge(response.result, container);
            } else {
                console.error('❌ Analysis failed:', response?.error);
                this.displayErrorBadge(container);
            }
        } catch (error) {
            console.error('❌ Error during analysis:', error);
            this.displayErrorBadge(container);
        }
    }

    displaySecurityBadge(analysisResult, container) {
        // Remove any existing badges
        const existingBadge = document.querySelector('.atf-security-badge');
        if (existingBadge) existingBadge.remove();

        // Create security badge based on analysis
        const badge = this.createSecurityBadge(analysisResult);

        // Find the best place to inject the badge (email header area)
        const headerArea = this.findEmailHeader();
        if (headerArea) {
            headerArea.appendChild(badge);
        } else {
            // Fallback: inject at top of email container
            container.insertBefore(badge, container.firstChild);
        }
    }

    findEmailHeader() {
        const headerSelectors = [
            '.gE.iv.gt',           // Gmail email header
            '.hA',                 // Header area
            '.qu',                 // Email metadata area
            '.adn.ads'             // Email actions area
        ];

        for (const selector of headerSelectors) {
            const header = document.querySelector(selector);
            if (header) return header;
        }
        return null;
    }

    createSecurityBadge(analysisResult) {
        const { label, score, ai_explanation } = analysisResult;

        // Determine badge style based on threat level
        const badgeConfig = this.getBadgeConfig(label, score);

        // Create badge container
        const badge = document.createElement('div');
        badge.className = 'atf-security-badge';
        badge.style.cssText = `
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            margin: 8px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            background: ${badgeConfig.background};
            color: ${badgeConfig.color};
            border: 2px solid ${badgeConfig.border};
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
            z-index: 10000;
            position: relative;
        `;

        badge.innerHTML = `
            <span style="margin-right: 6px; font-size: 14px;">${badgeConfig.icon}</span>
            <span>${badgeConfig.text}</span>
        `;

        // Add hover effect
        badge.addEventListener('mouseenter', () => {
            badge.style.transform = 'scale(1.05)';
            badge.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
        });

        badge.addEventListener('mouseleave', () => {
            badge.style.transform = 'scale(1)';
            badge.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        });

        // Click to show detailed explanation
        badge.addEventListener('click', () => {
            this.showDetailedExplanation(analysisResult, badge);
        });

        return badge;
    }

    getBadgeConfig(label, score) {
        switch (label) {
            case 'PHISHING':
                return {
                    icon: '🔴',
                    text: 'Phishing Detected',
                    background: '#fee2e2',
                    color: '#dc2626',
                    border: '#fca5a5'
                };
            case 'SUSPICIOUS':
                return {
                    icon: '🟡',
                    text: 'Suspicious',
                    background: '#fef3c7',
                    color: '#d97706',
                    border: '#fcd34d'
                };
            case 'SAFE':
            default:
                return {
                    icon: '🟢',
                    text: 'Safe',
                    background: '#dcfce7',
                    color: '#16a34a',
                    border: '#86efac'
                };
        }
    }

    showDetailedExplanation(analysisResult, badge) {
        // Remove any existing explanation panel
        const existingPanel = document.querySelector('.atf-explanation-panel');
        if (existingPanel) {
            existingPanel.remove();
            return; // Toggle off
        }

        const panel = this.createExplanationPanel(analysisResult);
        badge.parentNode.insertBefore(panel, badge.nextSibling);
    }

    createExplanationPanel(analysisResult) {
        const { label, ai_explanation } = analysisResult;

        const panel = document.createElement('div');
        panel.className = 'atf-explanation-panel';
        panel.style.cssText = `
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            margin: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            max-width: 500px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            z-index: 10001;
            position: relative;
        `;

        panel.innerHTML = `
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0 0 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">
                    🤖 AI Security Analysis
                </h4>
                <p style="margin: 0; color: #4b5563; font-size: 13px; line-height: 1.4;">
                    ${ai_explanation?.summary || 'Analysis completed.'}
                </p>
            </div>
            
            <div style="margin-bottom: 12px;">
                <h5 style="margin: 0 0 6px 0; color: #1f2937; font-size: 12px; font-weight: 600;">
                    🧠 Why this matters:
                </h5>
                <p style="margin: 0; color: #4b5563; font-size: 12px; line-height: 1.4;">
                    ${ai_explanation?.ai_reasoning || 'No detailed reasoning available.'}
                </p>
            </div>
            
            <div style="margin-bottom: 12px;">
                <h5 style="margin: 0 0 6px 0; color: #1f2937; font-size: 12px; font-weight: 600;">
                    💡 Recommended action:
                </h5>
                <p style="margin: 0; color: #4b5563; font-size: 12px; line-height: 1.4;">
                    ${ai_explanation?.recommended_action || 'Exercise normal caution.'}
                </p>
            </div>
            
            <div style="text-align: right; margin-top: 12px;">
                <button class="close-panel" style="
                    background: #f3f4f6;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 11px;
                    color: #6b7280;
                    cursor: pointer;
                ">Close</button>
            </div>
        `;

        // Add close functionality
        panel.querySelector('.close-panel').addEventListener('click', () => {
            panel.remove();
        });

        return panel;
    }

    displayErrorBadge(container) {
        const badge = document.createElement('div');
        badge.className = 'atf-security-badge';
        badge.style.cssText = `
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            margin: 8px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            background: #f3f4f6;
            color: #6b7280;
            border: 2px solid #d1d5db;
            z-index: 10000;
        `;
        badge.innerHTML = `<span style="margin-right: 6px;">⚠️</span><span>Analysis Error</span>`;

        const headerArea = this.findEmailHeader();
        if (headerArea) {
            headerArea.appendChild(badge);
        }
    }
}

// Initialize Gmail Security Analyzer
const gmailAnalyzer = new GmailSecurityAnalyzer();