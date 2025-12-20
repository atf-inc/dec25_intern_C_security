// Chrome Extension Translation System
// Supports dynamic language switching with comprehensive translations

const TRANSLATIONS = {
    en: {
        // Badge text
        badge_safe: "Safe",
        badge_suspicious: "Suspicious",
        badge_phishing: "Phishing Detected",
        badge_offline: "Offline",
        badge_error: "Analysis Unavailable",

        // Panel headers
        panel_title_safe: "Email Appears Safe",
        panel_title_suspicious: "Suspicious Email",
        panel_title_phishing: "Phishing Detected",

        // Panel sections
        section_ai_analysis: "🤖 AI Analysis",
        section_recommended_action: "💡 Recommended Action",
        section_technical_details: "📊 Technical Details",
        section_threat_summary: "🧠 Threat Summary",

        // Actions
        action_dismiss: "Dismiss",
        action_report: "Report Issue",
        action_close: "Close",

        // Technical details
        tech_threat_score: "Threat Score",
        tech_classification: "Classification",
        tech_analysis_method: "Analysis Method",
        tech_confidence: "Confidence",

        // Default explanations
        default_safe_summary: "This email appears to be legitimate business communication.",
        default_suspicious_summary: "This email contains some concerning elements that warrant caution.",
        default_phishing_summary: "This email shows strong signs of being a phishing attempt.",

        default_safe_action: "Standard email safety practices apply.",
        default_suspicious_action: "Verify the sender through official channels before taking any action.",
        default_phishing_action: "Do not click any links. Delete this email immediately.",

        // Loading states
        loading_analysis: "Analyzing email...",
        loading_translation: "Translating...",

        // Error messages
        error_analysis_failed: "Analysis failed. Please try again.",
        error_translation_failed: "Translation failed. Showing original content.",
        error_network: "Network error. Check your connection.",

        // Settings
        setting_language: "Language",
        setting_auto_translate: "Auto-translate explanations",

        // Modern UI
        ui_protection_active: "Protection Active",
        ui_emails_scanned: "Scanned",
        ui_threats_blocked: "Threats",
        ui_detection_mode: "Detection Mode",
        ui_choose_security_level: "Choose your security level",
        ui_todays_activity: "Today's Activity",
        ui_emails_analyzed: "Emails Analyzed",
        ui_threats_blocked_full: "Threats Blocked",
        ui_real_time_protection: "Real-time Gmail protection",

        // Popup specific
        popup_title: "ATF CyberX",
        popup_subtitle: "Email Security",
        popup_conservative: "Conservative",
        popup_conservative_desc: "Presentation safe",
        popup_balanced: "Balanced",
        popup_balanced_desc: "Recommended",
        popup_aggressive: "Aggressive",
        popup_aggressive_desc: "Maximum security",
        popup_version: "v2.1.0"
    },

    ja: {
        // Badge text
        badge_safe: "安全",
        badge_suspicious: "疑わしい",
        badge_phishing: "フィッシング検出",
        badge_offline: "オフライン",
        badge_error: "分析不可",

        // Panel headers
        panel_title_safe: "メールは安全です",
        panel_title_suspicious: "疑わしいメール",
        panel_title_phishing: "フィッシング検出",

        // Panel sections
        section_ai_analysis: "🤖 AI分析",
        section_recommended_action: "💡 推奨アクション",
        section_technical_details: "📊 技術的詳細",
        section_threat_summary: "🧠 脅威の概要",

        // Actions
        action_dismiss: "閉じる",
        action_report: "問題を報告",
        action_close: "閉じる",

        // Technical details
        tech_threat_score: "脅威スコア",
        tech_classification: "分類",
        tech_analysis_method: "分析方法",
        tech_confidence: "信頼度",

        // Default explanations
        default_safe_summary: "このメールは正当なビジネス通信のようです。",
        default_suspicious_summary: "このメールには注意が必要な要素が含まれています。",
        default_phishing_summary: "このメールはフィッシング攻撃の強い兆候を示しています。",

        default_safe_action: "標準的なメールセキュリティ対策を適用してください。",
        default_suspicious_action: "アクションを取る前に、公式チャネルを通じて送信者を確認してください。",
        default_phishing_action: "リンクをクリックしないでください。このメールをすぐに削除してください。",

        // Loading states
        loading_analysis: "メールを分析中...",
        loading_translation: "翻訳中...",

        // Error messages
        error_analysis_failed: "分析に失敗しました。もう一度お試しください。",
        error_translation_failed: "翻訳に失敗しました。元のコンテンツを表示しています。",
        error_network: "ネットワークエラー。接続を確認してください。",

        // Settings
        setting_language: "言語",
        setting_auto_translate: "説明を自動翻訳",

        // Modern UI
        ui_protection_active: "保護が有効",
        ui_emails_scanned: "スキャン済み",
        ui_threats_blocked: "脅威",
        ui_detection_mode: "検出モード",
        ui_choose_security_level: "セキュリティレベルを選択",
        ui_todays_activity: "今日のアクティビティ",
        ui_emails_analyzed: "分析されたメール",
        ui_threats_blocked_full: "ブロックされた脅威",
        ui_real_time_protection: "リアルタイムGmail保護",

        // Popup specific
        popup_title: "ATF CyberX",
        popup_subtitle: "メールセキュリティ",
        popup_conservative: "控えめ",
        popup_conservative_desc: "プレゼン安全",
        popup_balanced: "バランス",
        popup_balanced_desc: "推奨",
        popup_aggressive: "積極的",
        popup_aggressive_desc: "最大セキュリティ",
        popup_version: "v2.1.0"
    }
};

// Language detection and management
class ExtensionI18n {
    constructor() {
        this.currentLanguage = 'en';
        this.supportedLanguages = ['en', 'ja'];
        this.init();
    }

    async init() {
        // Load saved language preference
        try {
            const result = await chrome.storage.local.get(['preferredLanguage']);
            if (result.preferredLanguage && this.supportedLanguages.includes(result.preferredLanguage)) {
                this.currentLanguage = result.preferredLanguage;
            } else {
                // Auto-detect browser language
                this.currentLanguage = this.detectBrowserLanguage();
            }
        } catch (error) {
            console.warn('Could not load language preference:', error);
            this.currentLanguage = this.detectBrowserLanguage();
        }

        console.log('🌍 Extension language set to:', this.currentLanguage);
    }

    detectBrowserLanguage() {
        const browserLang = navigator.language || navigator.userLanguage || 'en';
        const langCode = browserLang.split('-')[0]; // Get 'ja' from 'ja-JP'

        return this.supportedLanguages.includes(langCode) ? langCode : 'en';
    }

    async setLanguage(langCode) {
        if (this.supportedLanguages.includes(langCode)) {
            const oldLanguage = this.currentLanguage;
            this.currentLanguage = langCode;

            // Save preference
            try {
                await chrome.storage.local.set({ preferredLanguage: langCode });
                console.log('🌍 Language preference saved:', langCode);
            } catch (error) {
                console.warn('Could not save language preference:', error);
            }

            // Dispatch language change event for dynamic updates
            if (oldLanguage !== langCode) {
                const event = new CustomEvent('extensionLanguageChanged', {
                    detail: {
                        oldLanguage,
                        newLanguage: langCode,
                        timestamp: Date.now()
                    }
                });
                window.dispatchEvent(event);
                console.log('🌍 Language change event dispatched:', oldLanguage, '→', langCode);
            }
        }
    }

    t(key, fallback = null) {
        const translation = TRANSLATIONS[this.currentLanguage]?.[key] ||
            TRANSLATIONS['en']?.[key] ||
            fallback ||
            key;
        return translation;
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getSupportedLanguages() {
        return this.supportedLanguages.map(code => ({
            code,
            name: this.getLanguageName(code)
        }));
    }

    getLanguageName(code) {
        const names = {
            'en': 'English',
            'ja': '日本語'
        };
        return names[code] || code;
    }
}

// Global instance
window.extensionI18n = new ExtensionI18n();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ExtensionI18n, TRANSLATIONS };
}