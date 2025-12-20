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

    // Enhanced email detection with detailed logging
    async checkForNewEmail() {
        console.log('🔍 checkForNewEmail() called');

        // 1. Check if auto-scan is enabled in user settings
        try {
            const settings = await chrome.storage.local.get(['autoScanEnabled']);
            // If setting exists and is explicitly false, stop here.
            if (settings.autoScanEnabled === false) {
                console.log('⏸️ Auto-scan disabled in settings');
                return;
            }
            console.log('✅ Auto-scan enabled or not set (default: enabled)');
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
        console.log('🔍 Step 2: Looking for email container...');
        const emailContainer = this.findEmailContainer();
        if (!emailContainer) {
            console.log('❌ No email container found - user might not have an email open');
            return;
        }
        console.log('✅ Email container found:', emailContainer);

        // 3. Extract data
        console.log('🔍 Step 3: Extracting email data...');
        const emailData = this.extractEmailData(emailContainer);
        if (!emailData) {
            console.log('❌ Could not extract email data');
            return;
        }
        console.log('✅ Email data extracted:', {
            subject: emailData.subject,
            from: emailData.from_email,
            bodyLength: emailData.body.length,
            linksCount: emailData.visible_links.length
        });

        // 4. Check hash to avoid re-processing the same email multiple times
        console.log('🔍 Step 4: Checking if email already processed...');
        const emailHash = this.createEmailHash(emailData);
        if (this.processedEmails.has(emailHash)) {
            console.log('⏭️ Email already processed (hash: ' + emailHash + ')');
            return;
        }

        console.log('📧 New email detected:', emailData.subject);
        this.processedEmails.add(emailHash);

        // 5. Analyze
        console.log('🔍 Step 5: Starting analysis...');
        this.analyzeEmail(emailData, emailContainer);
    }

    findEmailContainer() {
        // Enhanced selectors for different Gmail views and updates
        const selectors = [
            '[data-message-id]',           // Standard view
            '.ii.gt .a3s.aiL',             // Message body wrapper
            '[role="listitem"] .ii',       // Conversation view item
            '.nH .if',                     // Split view container
            '[data-legacy-message-id]',    // Old Gmail view
            '.gs .ii',                     // Generic message wrapper
            'div[data-message-id] .ii',    // Specific wrapper
            '.adn.ads .ii',                // Another Gmail layout
            '.ii.gt',                      // Simplified selector
            '[jscontroller] .ii',          // JS controller based
            '.a3s.aiL',                    // Direct body selector
            '[data-thread-id] .ii'         // Thread-based selector
        ];

        console.log('🔍 Searching for email container...');

        for (const selector of selectors) {
            const containers = document.querySelectorAll(selector);
            console.log(`   Selector "${selector}": found ${containers.length} elements`);

            for (const container of containers) {
                if (this.isValidEmailContainer(container)) {
                    console.log(`✅ Valid email container found with selector: ${selector}`);
                    return container;
                }
            }
        }

        console.log('❌ No valid email container found');
        return null;
    }

    isValidEmailContainer(container) {
        console.log('🔍 Validating email container...');

        // Check for subject in multiple ways
        const hasSubjectInContainer = container.querySelector('[data-subject]') ||
            container.querySelector('h2') ||
            container.querySelector('.hP') ||
            container.querySelector('.bog');

        const hasSubjectGlobally = document.querySelector('[data-subject]') ||
            document.querySelector('h2[data-subject]') ||
            document.querySelector('.hP');

        const hasSubject = hasSubjectInContainer || hasSubjectGlobally;

        // Check for content (be more lenient)
        const contentLength = container.textContent.trim().length;
        const hasContent = contentLength > 5; // Reduced from 10 to 5

        // Check for email-like elements
        const hasEmailElements = container.querySelector('.a3s') ||  // Email body
            container.querySelector('.ii') ||   // Message wrapper
            container.classList.contains('ii') || // Is message wrapper
            container.closest('[data-message-id]'); // Inside message

        console.log('   Subject check:', !!hasSubject);
        console.log('   Content length:', contentLength, '(needs > 5)');
        console.log('   Has email elements:', !!hasEmailElements);

        // More flexible validation - any 2 of 3 conditions
        const validationScore = (hasSubject ? 1 : 0) + (hasContent ? 1 : 0) + (hasEmailElements ? 1 : 0);
        const isValid = validationScore >= 2;

        console.log('   Validation score:', validationScore, '/3 (needs >= 2)');
        console.log('   Container valid:', isValid);

        return isValid;
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

        // Safe encoding that handles Unicode characters
        try {
            // First try btoa with safe encoding
            const safeString = encodeURIComponent(hashString);
            return btoa(safeString).substring(0, 16);
        } catch (error) {
            // Fallback: simple hash without btoa
            console.warn('Using fallback hash due to encoding issue:', error);
            let hash = 0;
            for (let i = 0; i < hashString.length; i++) {
                const char = hashString.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }
            return Math.abs(hash).toString(16).substring(0, 16);
        }
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

        // 🐛 DEBUG: Log what we're displaying
        console.log('🛡️ Displaying security badge:', {
            label: analysisResult.label,
            score: analysisResult.score,
            hasAiExplanation: !!analysisResult.ai_explanation
        });

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

        // 🐛 DEBUG: Confirm badge was added
        console.log('✅ Security badge added to DOM');
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
            console.log('🖱️ Badge clicked! Analysis result:', analysisResult);
            console.log('🖱️ AI explanation present:', !!analysisResult.ai_explanation);
            this.showDetailedExplanation(analysisResult, badge);
        });

        return badge;
    }

    getBadgeConfig(label, score) {
        console.log('🎨 Getting badge config for:', label, 'Score:', score);

        switch (label) {
            case 'PHISHING':
                return {
                    icon: '🚫',
                    text: 'Phishing Detected',
                    background: '#FEF2F2',
                    color: '#DC2626',
                    border: '#FECACA'
                };
            case 'SUSPICIOUS':
                return {
                    icon: '⚠️',
                    text: 'Suspicious',
                    background: '#FFFBEB',
                    color: '#D97706',
                    border: '#FDE68A'
                };
            case 'SAFE':
                return {
                    icon: '✅',
                    text: 'Safe',
                    background: '#ECFDF5',
                    color: '#059669',
                    border: '#A7F3D0'
                };
            default:
                console.warn('⚠️ Unknown label:', label, 'defaulting to SAFE');
                return {
                    icon: '❓',
                    text: 'Unknown',
                    background: '#F3F4F6',
                    color: '#6B7280',
                    border: '#D1D5DB'
                };
        }
    }

    showDetailedExplanation(analysisResult, badge) {
        console.log('📋 showDetailedExplanation called with:', analysisResult);

        const existingPanel = document.querySelector('.atf-explanation-panel');
        if (existingPanel) {
            console.log('🗑️ Removing existing panel');
            existingPanel.remove();
            return;
        }

        console.log('🎨 Creating new explanation panel...');
        const panel = this.createExplanationPanel(analysisResult);

        // Add panel to document body for maximum visibility
        console.log('📍 Adding panel to document body...');
        document.body.appendChild(panel);
        console.log('✅ Panel added to DOM successfully');

        // Add a subtle animation
        panel.style.transform = 'translateY(-10px)';
        panel.style.transition = 'all 0.3s ease-out';
        setTimeout(() => {
            panel.style.transform = 'translateY(0)';
        }, 10);
    }

    createExplanationPanel(analysisResult) {
        console.log('🎨 createExplanationPanel called');
        console.log('📊 Analysis result:', analysisResult);

        const { ai_explanation, label, score, reasons } = analysisResult;
        console.log('🤖 AI explanation:', ai_explanation);
        console.log('🏷️ Label:', label, 'Score:', score);

        const panel = document.createElement('div');
        panel.className = 'atf-explanation-panel';

        // Enhanced styling with maximum visibility
        panel.style.position = 'fixed'; // Changed from absolute to fixed
        panel.style.top = '100px'; // Position from top of viewport
        panel.style.right = '20px'; // Position from right edge
        panel.style.width = '400px';
        panel.style.maxWidth = '90vw';
        panel.style.maxHeight = '500px';
        panel.style.overflowY = 'auto';
        panel.style.zIndex = '999999'; // Much higher z-index
        panel.style.padding = '20px';
        panel.style.borderRadius = '12px';
        panel.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)'; // Stronger shadow
        panel.style.background = 'white';
        panel.style.border = '2px solid #E5E7EB'; // Thicker border
        panel.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

        // Add visibility debugging
        panel.style.display = 'block';
        panel.style.visibility = 'visible';
        panel.style.opacity = '1';

        // Get threat level styling
        const threatConfig = this.getThreatLevelConfig(label, score);

        // Build suspicious indicators list
        let suspiciousIndicatorsList = '';
        if (ai_explanation?.suspicious_indicators && ai_explanation.suspicious_indicators.length > 0) {
            suspiciousIndicatorsList = ai_explanation.suspicious_indicators
                .slice(0, 4) // Limit to top 4 indicators
                .map(indicator => `<li style="margin-bottom: 6px; font-size: 12px; line-height: 1.4;">${indicator}</li>`)
                .join('');
        }

        // Build technical indicators list
        let technicalIndicatorsList = '';
        if (ai_explanation?.technical_indicators && ai_explanation.technical_indicators.length > 0) {
            technicalIndicatorsList = ai_explanation.technical_indicators
                .slice(0, 3) // Limit to top 3 technical indicators
                .map(indicator => `<li style="margin-bottom: 4px; font-size: 11px; color: #6B7280;">${indicator}</li>`)
                .join('');
        }

        // Create a simpler, more robust panel structure
        try {
            console.log('🏗️ Building panel HTML...');

            // Safely get values with fallbacks
            const summary = ai_explanation?.summary || `Analysis complete. Email classified as ${label}.`;
            const reasoning = ai_explanation?.ai_reasoning || `This email was analyzed and classified as ${label} with a confidence score of ${score}%.`;
            const action = ai_explanation?.recommended_action || 'Exercise standard email caution when handling this email.';

            panel.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 18px; margin-right: 8px;">${threatConfig.icon}</span>
                        <h4 style="margin: 0; font-size: 16px; font-weight: 700; color: ${threatConfig.color};">${threatConfig.title}</h4>
                    </div>
                    <span class="close-panel" style="cursor: pointer; font-size: 20px; color: #9CA3AF;">&times;</span>
                </div>

                <div style="background: ${threatConfig.background}; border: 1px solid ${threatConfig.border}; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                    <p style="margin: 0; font-size: 13px; color: ${threatConfig.textColor}; line-height: 1.5;">
                        ${summary}
                    </p>
                </div>

                <div style="margin-bottom: 16px;">
                    <h5 style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; text-transform: uppercase; color: #374151;">
                        🤖 AI Analysis
                    </h5>
                    <p style="margin: 0; font-size: 12px; color: #4B5563; line-height: 1.5; background: #F9FAFB; padding: 10px; border-radius: 6px;">
                        ${reasoning}
                    </p>
                </div>

                <div style="margin-bottom: 16px;">
                    <h5 style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; text-transform: uppercase; color: #374151;">
                        💡 Recommended Action
                    </h5>
                    <p style="margin: 0; font-size: 12px; color: #1F2937; line-height: 1.5; background: #EFF6FF; padding: 10px; border-radius: 6px; border-left: 3px solid #3B82F6;">
                        ${action}
                    </p>
                </div>

                <div style="margin-bottom: 16px;">
                    <h5 style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; text-transform: uppercase; color: #374151;">
                        📊 Technical Details
                    </h5>
                    <div style="background: #F3F4F6; padding: 8px; border-radius: 6px; font-size: 11px; color: #6B7280;">
                        <div>Threat Score: ${score}/100</div>
                        <div>Classification: ${label}</div>
                        <div>Analysis Method: ${analysisResult.model_meta?.analysis_method || 'AI + Heuristics'}</div>
                    </div>
                </div>

                <div style="display: flex; gap: 8px; margin-top: 16px;">
                    <button class="close-panel" style="flex: 1; padding: 8px 12px; background: #F3F4F6; border: 1px solid #D1D5DB; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; color: #374151;">
                        Dismiss
                    </button>
                    <button class="report-btn" style="flex: 1; padding: 8px 12px; background: #3B82F6; border: 1px solid #3B82F6; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; color: white;">
                        Report Issue
                    </button>
                </div>
            `;

            console.log('✅ Panel HTML built successfully');

        } catch (error) {
            console.error('❌ Error building panel HTML:', error);
            // Fallback to very simple panel
            panel.innerHTML = `
                <div style="padding: 16px; background: white; border: 1px solid #ccc; border-radius: 8px;">
                    <h4 style="margin: 0 0 12px 0;">Security Analysis</h4>
                    <p style="margin: 0 0 12px 0;">Classification: ${label} (Score: ${score})</p>
                    <p style="margin: 0 0 12px 0;">${ai_explanation?.summary || 'Analysis complete.'}</p>
                    <button class="close-panel" style="padding: 6px 12px; background: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; cursor: pointer;">Close</button>
                </div>
            `;
        }

        // Add event listeners with debugging
        console.log('🎯 Adding event listeners to panel...');

        const closeBtns = panel.querySelectorAll('.close-panel');
        console.log('🔘 Found', closeBtns.length, 'close buttons');

        closeBtns.forEach((btn, index) => {
            btn.addEventListener('click', (e) => {
                console.log('🗑️ Close button', index, 'clicked');
                e.stopPropagation();
                panel.remove();
            });
        });

        // Add report button functionality
        const reportBtn = panel.querySelector('.report-btn');
        if (reportBtn) {
            console.log('📝 Report button found, adding listener');
            reportBtn.addEventListener('click', (e) => {
                console.log('📝 Report button clicked');
                e.stopPropagation();
                this.handleReportIssue(analysisResult);
                panel.remove();
            });
        } else {
            console.log('⚠️ Report button not found');
        }

        console.log('✅ Panel created successfully, returning...');
        return panel;
    }

    getThreatLevelConfig(label, score) {
        switch (label) {
            case 'PHISHING':
                return {
                    icon: '🚨',
                    title: 'Phishing Detected',
                    color: '#DC2626',
                    background: '#FEF2F2',
                    border: '#FECACA',
                    textColor: '#991B1B'
                };
            case 'SUSPICIOUS':
                return {
                    icon: '⚠️',
                    title: 'Suspicious Email',
                    color: '#D97706',
                    background: '#FFFBEB',
                    border: '#FDE68A',
                    textColor: '#92400E'
                };
            case 'SAFE':
            default:
                return {
                    icon: '✅',
                    title: 'Email Appears Safe',
                    color: '#059669',
                    background: '#ECFDF5',
                    border: '#A7F3D0',
                    textColor: '#065F46'
                };
        }
    }

    handleReportIssue(analysisResult) {
        // Simple feedback mechanism
        console.log('📝 User reported issue with analysis:', analysisResult);

        // You could extend this to send feedback to your backend
        // For now, just show a simple alert
        alert('Thank you for your feedback! This helps us improve our detection accuracy.');

        // Optional: Send feedback to backend
        // this.sendFeedbackToBackend(analysisResult);
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

// Initialize with error handling and retry logic
let gmailAnalyzer = null;
let initRetries = 0;
const maxRetries = 5;

function initializeAnalyzer() {
    try {
        console.log(`🔄 Initializing Gmail analyzer (attempt ${initRetries + 1}/${maxRetries})...`);

        gmailAnalyzer = new GmailSecurityAnalyzer();

        // Make it globally accessible for debugging
        window.gmailAnalyzer = gmailAnalyzer;
        console.log('✅ Gmail analyzer assigned to window.gmailAnalyzer');

        // Add manual trigger for testing
        window.testEmailDetection = () => {
            console.log('🧪 Manual email detection test triggered');
            if (gmailAnalyzer) {
                gmailAnalyzer.checkForNewEmail();
            } else {
                console.error('❌ Gmail analyzer not initialized');
            }
        };

        // Add manual badge test
        window.testBadgeCreation = () => {
            console.log('🧪 Testing badge creation...');
            if (gmailAnalyzer) {
                const testResult = {
                    label: 'PHISHING',
                    score: 85,
                    ai_explanation: {
                        summary: 'This is a test phishing email with suspicious patterns.',
                        ai_reasoning: 'Multiple red flags detected including urgency language and suspicious links.',
                        recommended_action: 'Do not click any links. Delete this email.',
                        technical_indicators: ['High urgency score', 'Suspicious domain', 'Brand impersonation']
                    }
                };

                const container = document.querySelector('.ii.gt') || document.querySelector('[role="main"]') || document.body;
                gmailAnalyzer.displaySecurityBadge(testResult, container);
                console.log('✅ Test badge created - look for red phishing badge!');
            } else {
                console.error('❌ Gmail analyzer not initialized');
            }
        };

        // Add manual panel test
        window.testPanelCreation = () => {
            console.log('🧪 Testing panel creation...');
            if (gmailAnalyzer) {
                const testResult = {
                    label: 'PHISHING',
                    score: 85,
                    ai_explanation: {
                        summary: 'This is a test phishing email with suspicious patterns.',
                        ai_reasoning: 'Multiple red flags detected including urgency language and suspicious links.',
                        recommended_action: 'Do not click any links. Delete this email.',
                        technical_indicators: ['High urgency score', 'Suspicious domain', 'Brand impersonation']
                    }
                };

                const panel = gmailAnalyzer.createExplanationPanel(testResult);
                document.body.appendChild(panel);
                console.log('✅ Test panel created - look for explanation panel in top-right!');
            } else {
                console.error('❌ Gmail analyzer not initialized');
            }
        };

        console.log('🧪 Use window.testEmailDetection() to manually test email detection');
        console.log('🧪 Use window.testBadgeCreation() to test badge UI');
        console.log('🧪 Use window.testPanelCreation() to test explanation panel');
        console.log('✅ Gmail Security Analyzer fully initialized!');

        return true;
    } catch (error) {
        console.error('❌ Failed to initialize Gmail analyzer:', error);
        initRetries++;

        if (initRetries < maxRetries) {
            console.log(`⏳ Retrying initialization in 2 seconds...`);
            setTimeout(initializeAnalyzer, 2000);
        } else {
            console.error('❌ Max retries reached. Extension initialization failed.');
        }
        return false;
    }
}

// Start initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAnalyzer);
} else {
    initializeAnalyzer();
}