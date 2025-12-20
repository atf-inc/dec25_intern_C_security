// Background Service Worker - API Communication & Caching
// Integrated: Task 1 (API), Task 4 (Retries), Task 5 (Stats), Task 8 (Advanced Fallback)

console.log('🛡️ ATF CyberX Background Service - Starting...');

class EmailSecurityService {
    constructor() {
        // ✅ TASK 1: API Endpoint
        this.apiEndpoint = 'http://localhost:8000/analyze/';

        this.cache = new Map(); // Simple in-memory cache
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes cache life

        // ✅ TASK 5: Stats Tracking
        this.stats = {
            scanned: 0,
            threats: 0,
            lastReset: new Date().toDateString()
        };

        this.init();
    }

    init() {
        console.log('🔧 Initializing background service...');

        // Load persisted stats
        this.loadStats();

        // Listen for messages from content scripts (Gmail)
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'analyzeEmail') {
                // Async analysis handler
                this.handleEmailAnalysis(request.emailData, request.sensitivityLevel)
                    .then(result => {
                        sendResponse({ success: true, result });
                    })
                    .catch(error => {
                        console.error('❌ Analysis error:', error);
                        sendResponse({ success: false, error: error.message });
                    });
                return true; // Keep message channel open for async response
            }

            if (request.action === 'translateResult') {
                // Handle translation requests
                this.handleTranslationRequest(request.originalResult, request.targetLanguage)
                    .then(result => {
                        sendResponse({ success: true, result });
                    })
                    .catch(error => {
                        console.error('❌ Translation error:', error);
                        sendResponse({ success: false, error: error.message });
                    });
                return true; // Keep message channel open for async response
            }

            if (request.action === 'getStats') {
                sendResponse({ success: true, stats: this.stats });
                return false;
            }
        });

        // Schedule daily stats reset
        this.scheduleDailyReset();

        console.log('✅ Background service initialized');
    }

    // ==========================================
    // 📊 STATS MANAGEMENT (Task 5)
    // ==========================================

    async loadStats() {
        try {
            const result = await chrome.storage.local.get(['dailyStats']);
            if (result.dailyStats) {
                const today = new Date().toDateString();

                // Reset if it's a new day
                if (result.dailyStats.lastReset !== today) {
                    console.log('📅 New day detected, resetting stats');
                    this.stats = { scanned: 0, threats: 0, lastReset: today };
                    await this.saveStats();
                } else {
                    this.stats = result.dailyStats;
                    console.log('📊 Loaded stats:', this.stats);
                }
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async saveStats() {
        try {
            await chrome.storage.local.set({
                dailyStats: this.stats,
                lastScan: Date.now()
            });

            // Notify popup to update if it's open
            chrome.runtime.sendMessage({
                action: 'updateStats',
                stats: this.stats
            }).catch(() => { /* Popup closed */ });
        } catch (error) {
            console.error('Failed to save stats:', error);
        }
    }

    scheduleDailyReset() {
        // Check every hour if we need to reset stats
        setInterval(() => {
            const today = new Date().toDateString();
            if (this.stats.lastReset !== today) {
                console.log('📅 Daily reset triggered');
                this.stats = { scanned: 0, threats: 0, lastReset: today };
                this.saveStats();
            }
        }, 60 * 60 * 1000);
    }

    // ==========================================
    // 🌍 TRANSLATION HANDLING
    // ==========================================

    async handleTranslationRequest(originalResult, targetLanguage) {
        try {
            console.log('🌍 Processing translation request to:', targetLanguage);

            // Check cache first
            const cacheKey = this.createTranslationCacheKey(originalResult, targetLanguage);
            const cachedTranslation = this.getFromCache(cacheKey);
            if (cachedTranslation) {
                console.log('⚡ Returning cached translation');
                return cachedTranslation;
            }

            // Call backend translation API
            const translatedResult = await this.callTranslationAPI(originalResult, targetLanguage);

            // Cache the translation
            this.saveToCache(cacheKey, translatedResult);

            return translatedResult;

        } catch (error) {
            console.error('❌ Translation request failed:', error);
            throw error;
        }
    }

    async callTranslationAPI(originalResult, targetLanguage) {
        console.log('🔄 Calling backend translation API...');

        try {
            const requestPayload = {
                original_result: originalResult,
                target_language: targetLanguage,
                meta: {
                    consent: true,  // Required by backend
                    source: 'chrome_extension',
                    timestamp: new Date().toISOString()
                }
            };

            const response = await fetch('http://localhost:8000/analyze/retranslate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestPayload),
                signal: AbortSignal.timeout(15000) // 15 second timeout
            });

            if (!response.ok) {
                throw new Error(`Translation API Request Failed: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();
            console.log('✅ Translation API call successful');
            return result;

        } catch (error) {
            console.error('❌ Translation API call failed:', error);
            throw error;
        }
    }

    createTranslationCacheKey(originalResult, targetLanguage) {
        const keyString = `${originalResult.request_id || 'unknown'}_${targetLanguage}`;
        return `trans_${keyString}`;
    }

    // ==========================================
    // 📧 EMAIL ANALYSIS LOGIC
    // ==========================================

    async handleEmailAnalysis(emailData, sensitivityLevel = 'balanced') {
        try {
            console.log('📧 Processing email analysis request...', { sensitivityLevel });

            // 1. Check Cache
            const cacheKey = this.createCacheKey(emailData);
            const cachedResult = this.getFromCache(cacheKey);
            if (cachedResult) {
                console.log('⚡ Returning cached result');
                return cachedResult;
            }

            // 2. Call API (with Retry Logic) - pass sensitivity level
            const result = await this.callPhishingAPIWithRetry(emailData, sensitivityLevel);

            // 3. Cache & Update Stats
            this.saveToCache(cacheKey, result);
            this.stats.scanned++;
            if (result.label === 'PHISHING') {
                this.stats.threats++;
            }
            await this.saveStats();

            return result;

        } catch (error) {
            console.error('❌ Email analysis failed:', error);
            throw error;
        }
    }

    // ✅ TASK 4: Retry Logic
    async callPhishingAPIWithRetry(emailData, sensitivityLevel = 'balanced', maxRetries = 2) {
        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                // Attempt API call
                return await this.callPhishingAPI(emailData, sensitivityLevel);
            } catch (error) {
                lastError = error;
                console.warn(`⚠️ API Attempt ${attempt} failed:`, error.message);

                // Don't retry on 4xx errors (client errors)
                if (error.message.includes('400') || error.message.includes('403')) {
                    throw error;
                }

                // If this was the last attempt, switch to fallback
                if (attempt === maxRetries) {
                    console.warn('⚠️ All API retries failed, switching to OFFLINE FALLBACK.');
                    return this.getFallbackResult(emailData, sensitivityLevel);
                }

                // Exponential backoff wait
                const waitTime = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
                await new Promise(resolve => setTimeout(resolve, waitTime));
            }
        }

        return this.getFallbackResult(emailData, sensitivityLevel);
    }

    async callPhishingAPI(emailData, sensitivityLevel = 'balanced') {
        console.log('🤖 Calling ATF CyberX API...', { sensitivityLevel });

        try {
            // Prepare payload for backend
            const requestPayload = {
                subject: emailData.subject || '',
                from_email: emailData.from_email || 'unknown@unknown.com',
                raw_text: emailData.body || '',
                visible_links: (emailData.visible_links || []).map(link => ({
                    anchor_text: link.anchor_text || null,
                    uri: link.uri || null,
                    page: null
                })),
                hidden_links: [],
                attachments: [],
                meta: {
                    consent: true,
                    source: 'chrome_extension',
                    timestamp: new Date().toISOString(),
                    sensitivity_level: sensitivityLevel  // 🚀 NEW: Pass sensitivity to backend
                }
            };

            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestPayload),
                signal: AbortSignal.timeout(15000) // 15 second timeout
            });

            if (!response.ok) {
                throw new Error(`API Request Failed: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();

            // Ensure explanation exists
            if (!result.ai_explanation) {
                result.ai_explanation = this.generateFallbackExplanation(
                    result.label,
                    result.score,
                    result.reasons || []
                );
            }

            return result;

        } catch (error) {
            // Rethrow to trigger retry/fallback logic
            throw error;
        }
    }

    // ==========================================
    // 🧠 TASK 8: ADVANCED OFFLINE HEURISTICS
    // ==========================================
    // This mirrors the Python logic in app/ml/phishing_model.py

    getFallbackResult(emailData, sensitivityLevel = 'balanced') {
        console.log('🔄 Running Advanced Fallback Analysis (Offline Mode)...', { sensitivityLevel });

        // 1. Setup Constants (Matches Python Backend)
        const URGENT_WORDS = [
            "verify", "immediately", "urgent", "click here", "password", "credential",
            "account locked", "action required", "verify your account", "confirm your identity",
            "suspended", "expires", "act now", "limited time", "within 24 hours", "security alert",
            "unusual activity", "confirm now", "update payment", "billing issue", "payment failed",
            "account will be closed", "temporary hold", "restricted access", "verify identity"
        ];

        const CREDENTIAL_KEYWORDS = [
            "password", "passwd", "credentials", "account number", "verify your account",
            "login", "username", "pin", "ssn", "social security", "credit card", "payment info"
        ];

        const BRAND_DOMAINS = {
            'paypal': ['paypal.com', 'paypal.net', 'paypal.org'],
            'amazon': ['amazon.com', 'amazon.net', 'aboutamazon.com'],
            'microsoft': ['microsoft.com', 'outlook.com', 'hotmail.com'],
            'apple': ['apple.com', 'icloud.com'],
            'google': ['google.com', 'gmail.com'],
            'netflix': ['netflix.com'],
            'chase': ['chase.com', 'jpmorgan.com'],
            'wellsfargo': ['wellsfargo.com'],
            'bank': ['bankofamerica.com', 'citi.com']
        };

        const SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.pw', '.xyz', '.top', '.loan'];
        const SHORTENERS = ['bit.ly', 'tinyurl', 't.co', 'goo.gl', 'is.gd', 'short.link'];

        // 2. Prepare Data
        const text = ((emailData.subject || '') + ' ' + (emailData.body || '')).toLowerCase();
        const from_email = (emailData.from_email || '').toLowerCase();
        const senderDomain = this.getDomain(from_email);

        let score = 0;
        let reasons = [];
        let evidence = [];

        // 3. Analysis Logic

        // Check Urgency
        let urgentCount = 0;
        URGENT_WORDS.forEach(word => {
            if (text.includes(word)) urgentCount++;
        });

        if (urgentCount >= 3) {
            score += 45;
            reasons.push(`High urgency tactics detected (${urgentCount} keywords found)`);
            evidence.push({ type: 'urgency', count: urgentCount });
        } else if (urgentCount >= 1) {
            score += 20;
            reasons.push("Urgency language detected");
        }

        // Check Credential Harvesting
        const hasCredentials = CREDENTIAL_KEYWORDS.some(k => text.includes(k));
        if (hasCredentials) {
            score += 40;
            reasons.push("Request for credentials or sensitive info detected");
            evidence.push({ type: 'credential_request' });
        }

        // Check Brand Impersonation
        for (const [brand, legitDomains] of Object.entries(BRAND_DOMAINS)) {
            if (text.includes(brand)) {
                // If brand is mentioned, sender MUST match legitimate domains
                const isLegit = legitDomains.some(d => senderDomain.endsWith(d));

                if (!isLegit && from_email.includes('@')) {
                    // Check for clearly suspicious sender traits
                    const isSuspiciousSender =
                        from_email.includes('noreply') ||
                        from_email.includes('security') ||
                        from_email.includes('update') ||
                        !senderDomain.includes(brand); // Sender doesn't even contain brand name

                    if (isSuspiciousSender) {
                        score += 35;
                        reasons.push(`Potential ${brand.toUpperCase()} impersonation`);
                        evidence.push({ type: 'brand_impersonation', brand });
                    }
                }
            }
        }

        // Check Links (Visible & Hidden)
        const allLinks = emailData.visible_links || [];

        allLinks.forEach(link => {
            const uri = (link.uri || '').toLowerCase();
            const anchor = (link.anchor_text || '').toLowerCase();
            const linkDomain = this.getDomain(uri);

            // Suspicious TLDs
            if (SUSPICIOUS_TLDS.some(tld => uri.includes(tld))) {
                score += 25;
                reasons.push("Contains suspicious TLD link (.tk, .ml, etc.)");
            }

            // URL Shorteners
            if (SHORTENERS.some(short => uri.includes(short))) {
                score += 20;
                reasons.push("Contains URL shortener/redirect");
            }

            // Mismatched Anchor Text (Phishing Classic)
            // e.g., Text says "paypal.com" but link goes to "hacker-site.com"
            if (anchor.length > 3 && !uri.includes(anchor)) {
                // Check if anchor LOOKS like a domain
                if (anchor.includes('.com') || anchor.includes('.net') || anchor.includes('http')) {
                    // Clean anchor to compare domains
                    const cleanAnchor = anchor.replace('https://', '').replace('http://', '').split('/')[0];
                    if (!uri.includes(cleanAnchor)) {
                        score += 30;
                        reasons.push("Deceptive link: Text matches a URL but links elsewhere");
                        evidence.push({ type: 'link_mismatch', anchor, uri });
                    }
                }
            }

            // High Entropy (Random Characters in URL)
            if (this.calculateUrlEntropy(uri) > 3.8) {
                score += 15;
                reasons.push("Suspiciously complex URL detected");
            }
        });

        // 4. Grammar / Quality Check
        const BAD_GRAMMAR = ['recieve', 'loose your account', 'dear customer', 'kindly reply', 'account suspended'];
        const grammarCount = BAD_GRAMMAR.filter(g => text.includes(g)).length;
        if (grammarCount > 0) {
            score += 15;
            reasons.push("Generic greeting or grammar errors detected");
        }

        // 5. Finalize Score & Label with Sensitivity Adjustment
        score = Math.min(100, score);

        // 🚀 NEW: Apply sensitivity-based adjustments to offline analysis
        const originalScore = score;
        switch (sensitivityLevel) {
            case 'conservative':
                // More conservative - reduce false positives for presentations
                if (score >= 70) {
                    score = Math.max(40, score - 20); // Reduce PHISHING threshold
                    console.log(`🔧 Conservative mode: Reduced ${originalScore} → ${score}`);
                }
                if (score >= 40 && score < 70) {
                    score = Math.max(10, score - 15); // Reduce SUSPICIOUS threshold
                    console.log(`🔧 Conservative mode: Reduced ${originalScore} → ${score}`);
                }
                break;

            case 'aggressive':
                // More aggressive - catch more potential threats
                if (score >= 30 && score < 70) {
                    score = Math.min(100, score + 20); // Increase sensitivity
                    console.log(`🔧 Aggressive mode: Increased ${originalScore} → ${score}`);
                }
                break;

            case 'balanced':
            default:
                // No adjustment - use original results
                break;
        }

        let label = 'SAFE';

        if (score >= 70) {
            label = 'PHISHING';
        } else if (score >= 40) {
            label = 'SUSPICIOUS';
        }

        // Generate Explanation
        const ai_explanation = this.generateFallbackExplanation(label, score, reasons);

        return {
            label,
            score,
            reasons: [...new Set(reasons)], // Deduplicate strings
            evidence: this.dedupeEvidence(evidence),
            request_id: 'offline-' + Date.now(),
            ai_explanation,
            model_meta: {
                analysis_method: 'offline_heuristic',
                llm_used: false,
                backend_available: false
            }
        };
    }

    // ==========================================
    // 🛠️ HELPER FUNCTIONS
    // ==========================================

    generateFallbackExplanation(label, score, reasons) {
        let summary, action, reasoning;

        const topReasons = reasons.slice(0, 3).join(', ') || 'No specific threats found';

        if (label === 'PHISHING') {
            summary = `🚨 HIGH RISK: This email is likely a phishing attack (${score}% confidence).`;
            action = '🛡️ Do NOT click any links. Delete this email immediately.';
            reasoning = `Our offline security scanner detected: ${topReasons}.`;
        } else if (label === 'SUSPICIOUS') {
            summary = `⚠️ CAUTION: Suspicious patterns detected (${score}% confidence).`;
            action = 'Verify the sender through official channels before clicking.';
            reasoning = `We found concerning elements: ${topReasons}.`;
        } else {
            summary = `✅ SAFE: This email appears legitimate.`;
            action = 'Standard email safety applies.';
            reasoning = 'No significant phishing indicators were found in our scan.';
        }

        return {
            summary,
            ai_reasoning: reasoning,
            recommended_action: action,
            technical_indicators: [`Threat Score: ${score}/100`, 'Offline Heuristics Engine'],
            final_assessment: label
        };
    }

    getDomain(url) {
        try {
            if (!url) return '';
            // Handle email addresses
            if (url.includes('@')) return url.split('@')[1];

            // Handle URLs
            const urlObj = new URL(url.startsWith('http') ? url : `http://${url}`);
            return urlObj.hostname;
        } catch (e) {
            return '';
        }
    }

    calculateUrlEntropy(url) {
        if (!url || !url.includes('/')) return 0;
        const path = url.split('/').slice(3).join('/'); // Get path after domain
        if (!path) return 0;

        const charCounts = {};
        for (let char of path) {
            charCounts[char] = (charCounts[char] || 0) + 1;
        }

        let entropy = 0;
        const len = path.length;
        for (let count of Object.values(charCounts)) {
            const p = count / len;
            entropy -= p * Math.log2(p);
        }
        return entropy;
    }

    dedupeEvidence(evidenceList) {
        const seen = new Set();
        return evidenceList.filter(item => {
            const key = JSON.stringify(item);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }

    // Cache Helpers
    createCacheKey(emailData) {
        const keyString = (emailData.subject || '') +
            (emailData.from_email || '') +
            (emailData.body || '').substring(0, 50);

        // Safe encoding that handles Unicode characters
        try {
            const safeString = encodeURIComponent(keyString);
            return btoa(safeString).substring(0, 16);
        } catch (error) {
            // Fallback: simple hash without btoa
            console.warn('Using fallback cache key due to encoding issue:', error);
            let hash = 0;
            for (let i = 0; i < keyString.length; i++) {
                const char = keyString.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }
            return Math.abs(hash).toString(16).substring(0, 16);
        }
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            return cached.data;
        }
        if (cached) this.cache.delete(key);
        return null;
    }

    saveToCache(key, data) {
        if (this.cache.size > 100) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        this.cache.set(key, { data, timestamp: Date.now() });
    }
}

// Initialize
const emailSecurityService = new EmailSecurityService();
console.log('🎉 ATF CyberX Background Service Ready!');
