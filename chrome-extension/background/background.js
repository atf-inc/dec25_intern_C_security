// Background Service Worker - API Communication & Caching
// This is the transport + cache layer - NO ML logic here

console.log('🛡️ ATF CyberX Background Service - Starting...');

class EmailSecurityService {
    constructor() {
        this.apiEndpoint = 'http://localhost:8000/api/v1/analyze/phishing';
        this.cache = new Map(); // Simple in-memory cache
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        this.init();
    }

    init() {
        // Listen for messages from content scripts
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'analyzeEmail') {
                this.handleEmailAnalysis(request.emailData)
                    .then(result => sendResponse({ success: true, result }))
                    .catch(error => sendResponse({ success: false, error: error.message }));
                return true; // Keep message channel open for async response
            }
        });

        console.log('✅ Background service initialized');
    }

    async handleEmailAnalysis(emailData) {
        try {
            console.log('📧 Processing email analysis request...');

            // Create cache key from email data
            const cacheKey = this.createCacheKey(emailData);

            // Check cache first
            const cachedResult = this.getFromCache(cacheKey);
            if (cachedResult) {
                console.log('⚡ Returning cached result');
                return cachedResult;
            }

            // Call our backend API
            const result = await this.callPhishingAPI(emailData);

            // Cache the result
            this.saveToCache(cacheKey, result);

            console.log('✅ Analysis complete:', result.label);
            return result;

        } catch (error) {
            console.error('❌ Email analysis failed:', error);
            throw error;
        }
    }

    async callPhishingAPI(emailData) {
        console.log('🤖 Calling ATF CyberX API...');

        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    subject: emailData.subject,
                    from_email: emailData.from_email,
                    body: emailData.body,
                    visible_links: emailData.visible_links
                })
            });

            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();

            // Validate response structure
            if (!result.label || !result.ai_explanation) {
                throw new Error('Invalid API response structure');
            }

            console.log('📊 API Response:', {
                label: result.label,
                score: result.score,
                hasExplanation: !!result.ai_explanation
            });

            return result;

        } catch (error) {
            console.error('❌ API call failed:', error);

            // Return fallback result for demo purposes
            return this.getFallbackResult(emailData);
        }
    }

    getFallbackResult(emailData) {
        console.log('🔄 Using fallback analysis...');

        // Simple fallback logic for demo
        const suspiciousKeywords = ['urgent', 'verify', 'suspended', 'click here', 'act now'];
        const text = (emailData.subject + ' ' + emailData.body).toLowerCase();
        const suspiciousCount = suspiciousKeywords.filter(keyword => text.includes(keyword)).length;

        let label = 'SAFE';
        let score = 10;

        if (suspiciousCount >= 2) {
            label = 'PHISHING';
            score = 85;
        } else if (suspiciousCount >= 1) {
            label = 'SUSPICIOUS';
            score = 55;
        }

        return {
            label,
            score,
            ai_explanation: {
                summary: `Email classified as ${label} (fallback analysis - backend unavailable)`,
                ai_reasoning: suspiciousCount > 0
                    ? `This email contains ${suspiciousCount} suspicious keyword(s) commonly used in phishing attempts.`
                    : 'This email appears to be legitimate based on basic keyword analysis.',
                recommended_action: label === 'PHISHING'
                    ? '🛡️ Do not click any links. Verify sender through official channels.'
                    : label === 'SUSPICIOUS'
                        ? '⚠️ Exercise caution. Verify sender before taking action.'
                        : '✅ Email appears safe, but always verify unexpected requests.'
            },
            reasons: suspiciousCount > 0 ? [`${suspiciousCount} suspicious keywords detected`] : ['No suspicious patterns detected'],
            evidence: [],
            model_meta: { analysis_method: 'fallback' }
        };
    }

    createCacheKey(emailData) {
        // Create a simple hash for caching
        const keyString = emailData.subject + emailData.from_email + emailData.body.substring(0, 100);
        return btoa(keyString).substring(0, 16);
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    saveToCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });

        // Clean old cache entries (simple cleanup)
        if (this.cache.size > 100) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
    }
}

// Initialize the service
const emailSecurityService = new EmailSecurityService();