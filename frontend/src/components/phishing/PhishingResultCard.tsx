import { RiskBadge } from '../common/RiskBadge'
import { useTranslation } from 'react-i18next'
import { useState, useEffect } from 'react'
import { retranslateExplanation } from '../../api/phishingApi'
import './PhishingResultCard.css'

interface PhishingResultCardProps {
    result: {
        request_id: string
        label: string
        score: number
        reasons: string[]
        evidence?: any[]
        suggested_action?: string
        suggested_reply?: string
        ai_explanation?: {
            summary: string
            suspicious_indicators: string[]
            ai_reasoning: string
            technical_indicators: string[]
            final_assessment: string
            recommended_action: string
            full_explanation: string
        }
        model_meta?: {
            llm?: string
            latency?: number
            cost_estimate?: number
            cost_reduction_vs_full_llm?: number
            analysis_method?: string
            heuristic_score?: number
            llm_used?: boolean
            threshold?: number
            llm_confidence?: number
            email_complexity?: number
            blending_weights?: {
                llm_weight: number
                heuristic_weight: number
            }
        }
    }
}

export function PhishingResultCard({ result: initialResult }: PhishingResultCardProps) {
    const { t, i18n } = useTranslation()
    const [result, setResult] = useState(initialResult)
    const [isTranslating, setIsTranslating] = useState(false)
    const [lastLanguage, setLastLanguage] = useState(i18n.language)

    // Fallback function for translations
    const getText = (key: string, fallback: string) => {
        const translated = t(key)
        return translated === key ? fallback : translated
    }

    // Watch for language changes and re-translate all dynamic content
    useEffect(() => {
        const handleLanguageChange = async () => {
            if (i18n.language !== lastLanguage) {
                setIsTranslating(true)
                try {
                    // Always re-translate when language changes, even if no AI explanation
                    const translatedResult = await retranslateExplanation(result, i18n.language)
                    setResult(translatedResult)
                    setLastLanguage(i18n.language)
                } catch (error) {
                    console.error('Failed to translate content:', error)
                    // If translation fails, just update the language tracking
                    setLastLanguage(i18n.language)
                } finally {
                    setIsTranslating(false)
                }
            }
        }

        handleLanguageChange()
    }, [i18n.language, lastLanguage, result])

    return (
        <div className="result-card slide-in-up">
            {isTranslating && (
                <div className="translation-indicator">
                    <span className="translation-spinner">🔄</span>
                    <span>{getText('phishing.translating', 'Translating content...')}</span>
                </div>
            )}
            <div className="result-header">
                <h2>{getText('phishing.analysisResults', 'Analysis Results')}</h2>
                <RiskBadge score={result.score} level={result.label as 'low' | 'medium' | 'high'} />
            </div>

            <div className="result-summary">
                <div className="summary-item">
                    <div className="summary-icon">
                        {result.label === 'PHISHING' ? '🚨' : result.label === 'SUSPICIOUS' ? '⚠️' : '✅'}
                    </div>
                    <div className="summary-content">
                        <span className="summary-label">{getText('phishing.riskLevel', 'Risk Level')}</span>
                        <span className={`summary-value risk-${result.label.toLowerCase()}`}>
                            {result.label.toUpperCase()}
                        </span>
                    </div>
                </div>
                <div className="summary-item">
                    <div className="summary-icon">🎯</div>
                    <div className="summary-content">
                        <span className="summary-label">{getText('phishing.confidence', 'Confidence')}</span>
                        <span className="summary-value">{result.score}%</span>
                    </div>
                </div>
                {result.evidence && (
                    <div className="summary-item">
                        <div className="summary-icon">🔍</div>
                        <div className="summary-content">
                            <span className="summary-label">{getText('phishing.indicators', 'Indicators')}</span>
                            <span className="summary-value">{result.evidence.length} {getText('phishing.detected', 'detected')}</span>
                        </div>
                    </div>
                )}
                {result.model_meta && (
                    <div className="summary-item">
                        <div className="summary-icon">
                            {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? '🤖' : '🔧'}
                        </div>
                        <div className="summary-content">
                            <span className="summary-label">{getText('phishing.analysis', 'Analysis')}</span>
                            <span className="summary-value">
                                {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? 'AI + Heuristics' : 'Heuristics Only'}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {result.suggested_action && (
                <div className="result-section">
                    <h3>{getText('phishing.recommendedActionTitle', 'Recommended Action')}</h3>
                    <p className="suggested-action">{result.suggested_action}</p>
                </div>
            )}

            {result.suggested_reply && (
                <div className="result-section">
                    <h3>{getText('phishing.suggestedResponse', 'Suggested Response')}</h3>
                    <p className="suggested-reply">{result.suggested_reply}</p>
                </div>
            )}

            {result.ai_explanation && (
                <div className="result-section">
                    <div className="ai-explanation-section">
                        <h3>🤖 {getText('phishing.aiSecurityAnalysis', 'AI Security Analysis')}</h3>

                        {/* Threat Summary Card */}
                        <div className="ai-explanation-card summary-card">
                            <div className="explanation-header">
                                <div className="explanation-icon">🛡️</div>
                                <h4>{getText('phishing.threatSummary', 'Threat Summary')}</h4>
                            </div>
                            <div className="explanation-content">
                                {result.ai_explanation.summary}
                            </div>
                        </div>

                        {/* Suspicious Indicators - Organized by Category */}
                        {result.ai_explanation.suspicious_indicators && result.ai_explanation.suspicious_indicators.length > 0 && (
                            <div className="ai-explanation-card indicators-card">
                                <div className="explanation-header">
                                    <div className="explanation-icon">⚠️</div>
                                    <h4>{getText('phishing.suspiciousIndicators', 'Suspicious Indicators')} ({result.ai_explanation.suspicious_indicators.length} {getText('phishing.found', 'found')})</h4>
                                </div>
                                <div className="explanation-content">
                                    <div className="indicators-summary">
                                        {(() => {
                                            // Group indicators by type
                                            const grouped = result.ai_explanation.suspicious_indicators.reduce((acc: any, indicator: string) => {
                                                if (indicator.toLowerCase().includes('urgency') || indicator.toLowerCase().includes('pressure')) {
                                                    acc.urgency = (acc.urgency || 0) + 1;
                                                } else if (indicator.toLowerCase().includes('deceptive link') || indicator.toLowerCase().includes('link')) {
                                                    acc.links = (acc.links || 0) + 1;
                                                } else if (indicator.toLowerCase().includes('obfuscated') || indicator.toLowerCase().includes('url')) {
                                                    acc.obfuscation = (acc.obfuscation || 0) + 1;
                                                } else {
                                                    acc.other = (acc.other || 0) + 1;
                                                }
                                                return acc;
                                            }, {});

                                            return (
                                                <div className="indicators-grid">
                                                    {grouped.urgency && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🚨</div>
                                                            <div className="category-content">
                                                                <div className="category-title">{getText('phishing.urgencyTactics', 'Urgency Tactics')}</div>
                                                                <div className="category-count">{grouped.urgency} {getText('phishing.detected', 'detected')}</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {grouped.links && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🔗</div>
                                                            <div className="category-content">
                                                                <div className="category-title">{getText('phishing.deceptiveLinks', 'Deceptive Links')}</div>
                                                                <div className="category-count">{grouped.links} {getText('phishing.detected', 'detected')}</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {grouped.obfuscation && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🌐</div>
                                                            <div className="category-content">
                                                                <div className="category-title">{getText('phishing.urlObfuscation', 'URL Obfuscation')}</div>
                                                                <div className="category-count">{grouped.obfuscation} {getText('phishing.detected', 'detected')}</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {grouped.other && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🔍</div>
                                                            <div className="category-content">
                                                                <div className="category-title">{getText('phishing.otherPatterns', 'Other Patterns')}</div>
                                                                <div className="category-count">{grouped.other} {getText('phishing.detected', 'detected')}</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })()}
                                    </div>

                                    {/* Expandable detailed view */}
                                    <details className="indicators-details">
                                        <summary className="details-toggle">{getText('phishing.viewDetailedBreakdown', 'View detailed breakdown')}</summary>
                                        <div className="detailed-indicators">
                                            {result.ai_explanation.suspicious_indicators.slice(0, 5).map((indicator, index) => (
                                                <div key={index} className="detailed-indicator-item">
                                                    <span className="indicator-bullet">•</span>
                                                    <span className="indicator-text">{indicator}</span>
                                                </div>
                                            ))}
                                            {result.ai_explanation.suspicious_indicators.length > 5 && (
                                                <div className="more-indicators">
                                                    +{result.ai_explanation.suspicious_indicators.length - 5} {getText('phishing.moreIndicators', 'more indicators')}
                                                </div>
                                            )}
                                        </div>
                                    </details>
                                </div>
                            </div>
                        )}

                        {/* AI Reasoning */}
                        {result.ai_explanation.ai_reasoning && (
                            <div className="ai-explanation-card reasoning-card">
                                <div className="explanation-header">
                                    <div className="explanation-icon">🧠</div>
                                    <h4>{getText('phishing.aiReasoning', 'AI Reasoning')}</h4>
                                </div>
                                <div className="explanation-content">
                                    {result.ai_explanation.ai_reasoning}
                                </div>
                            </div>
                        )}

                        {/* Technical Indicators */}
                        {result.ai_explanation.technical_indicators && result.ai_explanation.technical_indicators.length > 0 && (
                            <div className="ai-explanation-card technical-card">
                                <div className="explanation-header">
                                    <div className="explanation-icon">🔍</div>
                                    <h4>{getText('phishing.technicalAnalysis', 'Technical Analysis')}</h4>
                                </div>
                                <div className="explanation-content">
                                    <ul className="technical-indicators-list">
                                        {result.ai_explanation.technical_indicators.map((indicator, index) => (
                                            <li key={index} className="technical-indicator-item">
                                                <span className="tech-bullet">▸</span>
                                                {indicator}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        )}

                        {/* Final Assessment */}
                        {result.ai_explanation.final_assessment && (
                            <div className="ai-explanation-card assessment-card">
                                <div className="explanation-header">
                                    <div className="explanation-icon">🎯</div>
                                    <h4>{getText('phishing.finalAssessment', 'Final Assessment')}</h4>
                                </div>
                                <div className="explanation-content">
                                    <div className={`assessment-badge assessment-${result.label.toLowerCase()}`}>
                                        {result.label.toUpperCase()}
                                    </div>
                                    <p>{result.ai_explanation.final_assessment}</p>
                                </div>
                            </div>
                        )}

                        {/* Recommended Action */}
                        {result.ai_explanation.recommended_action && (
                            <div className="ai-explanation-card action-card">
                                <div className="explanation-header">
                                    <div className="explanation-icon">💡</div>
                                    <h4>{getText('phishing.recommendedAction', 'Recommended Action')}</h4>
                                </div>
                                <div className="explanation-content">
                                    <div className="recommended-action-content">
                                        {result.ai_explanation.recommended_action}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {result.reasons && result.reasons.length > 0 && (
                <div className="result-section">
                    <h3>{getText('phishing.threatAnalysis', 'Threat Analysis')}</h3>
                    <div className="evidence-summary-bar">
                        <span className="evidence-count-badge">{result.reasons.length} {getText('phishing.findingsDetected', 'findings detected')}</span>
                    </div>
                    <div className="evidence-professional-grid">
                        {result.reasons.map((reason, index) => {
                            const reasonText = typeof reason === 'string' ? reason : 'Analysis detected suspicious patterns'

                            // Enhanced categorization
                            const getReasonCategory = (text: string) => {
                                const lowerText = text.toLowerCase()
                                if (lowerText.includes('credential') || lowerText.includes('password') || lowerText.includes('harvesting')) {
                                    return {
                                        type: 'credential',
                                        severity: 'critical',
                                        label: getText('phishing.credentialHarvesting', 'Credential Harvesting')
                                    }
                                }
                                if (lowerText.includes('urgency') || lowerText.includes('urgent') || lowerText.includes('immediately')) {
                                    return {
                                        type: 'urgency',
                                        severity: 'high',
                                        label: getText('phishing.urgencyManipulation', 'Urgency Manipulation')
                                    }
                                }
                                if (lowerText.includes('link') || lowerText.includes('url') || lowerText.includes('domain') || lowerText.includes('anchor')) {
                                    return {
                                        type: 'link',
                                        severity: 'high',
                                        label: getText('phishing.deceptiveLinks', 'Deceptive Links')
                                    }
                                }
                                if (lowerText.includes('entropy') || lowerText.includes('obfuscated') || lowerText.includes('encoded')) {
                                    return {
                                        type: 'obfuscation',
                                        severity: 'medium',
                                        label: getText('phishing.contentObfuscation', 'Content Obfuscation')
                                    }
                                }
                                if (lowerText.includes('ip') || lowerText.includes('address')) {
                                    return {
                                        type: 'network',
                                        severity: 'medium',
                                        label: getText('phishing.networkAnomaly', 'Network Anomaly')
                                    }
                                }
                                return {
                                    type: 'general',
                                    severity: 'low',
                                    label: getText('phishing.behavioralPattern', 'Behavioral Pattern')
                                }
                            }

                            const category = getReasonCategory(reasonText)

                            return (
                                <div key={index} className="evidence-card">
                                    <div className="evidence-header">
                                        <div className={`evidence-severity-dot severity-${category.severity}`}></div>
                                        <span className="evidence-type-label">{category.label}</span>
                                    </div>
                                    <div className="evidence-description">{reasonText}</div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {result.evidence && result.evidence.length > 0 && (
                <div className="result-section">
                    <h3>{getText('phishing.securityIndicators', 'Security Indicators')}</h3>
                    <div className="evidence-summary-bar">
                        <span className="evidence-count-badge">{result.evidence.length} {getText('phishing.indicatorsFound', 'indicators found')}</span>
                    </div>
                    <div className="evidence-professional-grid">
                        {result.evidence.map((evidence, index) => {
                            // Handle different evidence formats
                            if (typeof evidence === 'string') {
                                return (
                                    <div key={index} className="evidence-card evidence-string-card">
                                        <div className="evidence-header">
                                            <div className="evidence-severity-dot severity-medium"></div>
                                            <span className="evidence-type-label">{getText('phishing.securityAlert', 'Security Alert')}</span>
                                        </div>
                                        <div className="evidence-description">{evidence}</div>
                                    </div>
                                )
                            }

                            // Handle object evidence with professional styling
                            const getSeverityClass = (type: string) => {
                                switch (type) {
                                    case 'urgency': return 'severity-high'
                                    case 'credential_request': return 'severity-critical'
                                    case 'link_mismatch': return 'severity-high'
                                    case 'high_entropy_uri': return 'severity-medium'
                                    default: return 'severity-low'
                                }
                            }

                            const getTypeLabel = (type: string) => {
                                switch (type) {
                                    case 'urgency': return getText('phishing.urgencyTactics', 'Urgency Tactics')
                                    case 'high_urgency': return getText('phishing.urgencyTactics', 'Urgency Tactics')
                                    case 'technical_urgency': return getText('phishing.technicalUrgency', 'Technical Urgency')
                                    case 'credential_request': return getText('phishing.credentialPhishing', 'Credential Phishing')
                                    case 'brand_impersonation': return getText('phishing.brandImpersonation', 'Brand Impersonation')
                                    case 'link_mismatch': return getText('phishing.deceptiveLinks', 'Deceptive Links')
                                    case 'suspicious_anchor_trusted_domain': return getText('phishing.suspiciousAnchor', 'Suspicious Link Text')
                                    case 'high_entropy_uri': return getText('phishing.obfuscatedUrl', 'Obfuscated URL')
                                    case 'high_entropy_trusted_uri': return getText('phishing.obfuscatedUrl', 'Obfuscated URL')
                                    case 'hidden_ip': return getText('phishing.hiddenIpAddress', 'Hidden IP Address')
                                    case 'suspicious_tld': return getText('phishing.suspiciousDomain', 'Suspicious Domain')
                                    case 'shortened_link': return getText('phishing.shortenedLink', 'Shortened Link')
                                    case 'character_substitution': return getText('phishing.characterSubstitution', 'Character Substitution')
                                    case 'typosquatting': return getText('phishing.typosquatting', 'Typosquatting')
                                    case 'similar_domain': return getText('phishing.similarDomain', 'Similar Domain')
                                    case 'grammar_errors': return getText('phishing.grammarErrors', 'Grammar Errors')
                                    case 'suspicious_sender': return getText('phishing.suspiciousSender', 'Suspicious Sender')
                                    default: return getText('phishing.suspiciousPattern', 'Suspicious Pattern')
                                }
                            }

                            return (
                                <div key={index} className="evidence-card">
                                    <div className="evidence-header">
                                        <div className={`evidence-severity-dot ${getSeverityClass(evidence.type)}`}></div>
                                        <span className="evidence-type-label">{getTypeLabel(evidence.type)}</span>
                                    </div>
                                    <div className="evidence-description">
                                        {evidence.type === 'urgency' && `${evidence.count} ${getText('phishing.urgencyIndicatorsDetected', 'urgency indicators detected')}`}
                                        {evidence.type === 'high_urgency' && `${evidence.count} ${getText('phishing.highUrgencyIndicators', 'high urgency indicators detected')}`}
                                        {evidence.type === 'technical_urgency' && `${evidence.count} ${getText('phishing.technicalUrgencyContext', 'technical urgency indicators in context')}`}
                                        {evidence.type === 'credential_request' && getText('phishing.attemptsToHarvestCredentials', 'Attempts to harvest user credentials')}
                                        {evidence.type === 'brand_impersonation' && (
                                            <div className="brand-impersonation-details">
                                                <div>{getText('phishing.impersonatingBrand', 'Impersonating brand')}: <strong>{evidence.brand}</strong></div>
                                                {evidence.sender && <div>{getText('phishing.suspiciousSender', 'Suspicious sender')}: {evidence.sender}</div>}
                                            </div>
                                        )}
                                        {evidence.type === 'link_mismatch' && (
                                            <div className="link-mismatch-details">
                                                <div className="link-detail">
                                                    <span className="link-label">{getText('phishing.displayText', 'Display text')}:</span>
                                                    <span className="link-value">"{evidence.anchor}"</span>
                                                </div>
                                                <div className="link-detail">
                                                    <span className="link-label">{getText('phishing.actualDestination', 'Actual destination')}:</span>
                                                    <span className="link-value truncated-url" title={evidence.uri}>
                                                        {evidence.uri?.length > 50 ? `${evidence.uri.substring(0, 50)}...` : evidence.uri}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                        {evidence.type === 'suspicious_anchor_trusted_domain' && (
                                            <div className="suspicious-anchor-details">
                                                <div>{getText('phishing.suspiciousText', 'Suspicious text')}: "{evidence.anchor}"</div>
                                                <div>{getText('phishing.onTrustedDomain', 'On trusted domain')}: {evidence.uri}</div>
                                            </div>
                                        )}
                                        {evidence.type === 'high_entropy_uri' && `${getText('phishing.suspiciousUrlPattern', 'Suspicious URL pattern')} (${getText('phishing.entropy', 'entropy')}: ${evidence.entropy?.toFixed(1)})`}
                                        {evidence.type === 'high_entropy_trusted_uri' && `${getText('phishing.highEntropyTrustedDomain', 'High entropy on trusted domain')} (${getText('phishing.entropy', 'entropy')}: ${evidence.entropy?.toFixed(1)})`}
                                        {evidence.type === 'hidden_ip' && (
                                            <div className="hidden-ip-details">
                                                <div>{getText('phishing.hiddenIpAddress', 'Hidden IP address')}: <code>{evidence.uri}</code></div>
                                            </div>
                                        )}
                                        {evidence.type === 'suspicious_tld' && (
                                            <div className="suspicious-tld-details">
                                                <div>{getText('phishing.suspiciousDomainDetected', 'Suspicious domain detected')}: {evidence.uri}</div>
                                            </div>
                                        )}
                                        {evidence.type === 'shortened_link' && (
                                            <div className="shortened-link-details">
                                                <div>{getText('phishing.shortenedRedirectLink', 'Shortened/redirect link')}: {evidence.uri}</div>
                                            </div>
                                        )}
                                        {evidence.type === 'character_substitution' && (
                                            <div className="character-substitution-details">
                                                <div>{getText('phishing.maliciousDomain', 'Malicious domain')}: <strong>{evidence.domain}</strong></div>
                                                <div>{getText('phishing.targetingLegitimate', 'Targeting legitimate')}: {evidence.target}</div>
                                                <div>{getText('phishing.substitutions', 'Substitutions')}: {evidence.substitutions?.join(', ')}</div>
                                            </div>
                                        )}
                                        {evidence.type === 'typosquatting' && (
                                            <div className="typosquatting-details">
                                                <div>{getText('phishing.suspiciousDomain', 'Suspicious domain')}: <strong>{evidence.domain}</strong></div>
                                                <div>{getText('phishing.similarToLegitimate', 'Similar to legitimate')}: {evidence.target}</div>
                                            </div>
                                        )}
                                        {evidence.type === 'similar_domain' && (
                                            <div className="similar-domain-details">
                                                <div>{getText('phishing.similarDomainDetected', 'Similar domain detected')}: <strong>{evidence.domain}</strong></div>
                                                <div>{getText('phishing.legitimateDomain', 'Legitimate domain')}: {evidence.target}</div>
                                            </div>
                                        )}
                                        {evidence.type === 'grammar_errors' && `${evidence.count} ${getText('phishing.grammarSpellingErrors', 'grammar/spelling errors detected')}`}
                                        {evidence.type === 'suspicious_sender' && (
                                            <div className="suspicious-sender-details">
                                                <div>{getText('phishing.genericSenderAddress', 'Generic sender address')}: {evidence.sender}</div>
                                            </div>
                                        )}
                                        {!evidence.type && getText('phishing.suspiciousBehaviorDetected', 'Suspicious behavior pattern detected')}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {result.model_meta && (
                <details className="result-section analysis-insights-section">
                    <summary className="section-summary">
                        📊 {getText('phishing.analysisInsights', 'Analysis Insights')}
                    </summary>
                    <div className="insights-content">
                        <h3 className="insights-title">{getText('phishing.howWeAnalyzed', 'How We Analyzed This Email')}</h3>
                        <div className="behavioral-patterns-grid">
                            {/* Analysis Method - User Friendly */}
                            {result.model_meta.analysis_method && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">🔬</div>
                                        <span className="pattern-title">
                                            {result.model_meta.analysis_method === 'hybrid_advanced' ? getText('phishing.aiPoweredAnalysis', 'AI-Powered Analysis') :
                                                result.model_meta.analysis_method === 'heuristics_only' ? getText('phishing.patternBasedAnalysis', 'Pattern-Based Analysis') : getText('phishing.smartAnalysis', 'Smart Analysis')}
                                        </span>
                                    </div>
                                    <div className="pattern-description">
                                        {result.model_meta.analysis_method === 'hybrid_advanced'
                                            ? getText('phishing.advancedAICombined', 'We used advanced AI combined with security rules to thoroughly examine this email for threats')
                                            : result.model_meta.analysis_method === 'heuristics_only'
                                                ? getText('phishing.provenSecurityPatterns', 'We used proven security patterns to quickly identify potential threats in this email')
                                                : getText('phishing.specializedTechniques', 'We applied specialized analysis techniques tailored to this email\'s characteristics')
                                        }
                                    </div>
                                </div>
                            )}

                            {/* Detection Confidence - User Friendly */}
                            <div className="pattern-card">
                                <div className="pattern-header">
                                    <div className="pattern-icon">🎯</div>
                                    <span className="pattern-title">{getText('phishing.detectionConfidence', 'Detection Confidence')}</span>
                                </div>
                                <div className="pattern-description">
                                    {result.score >= 80
                                        ? getText('phishing.veryHighConfidence', 'Very high confidence - multiple clear threat indicators detected')
                                        : result.score >= 60
                                            ? getText('phishing.highConfidence', 'High confidence - several suspicious patterns identified')
                                            : result.score >= 40
                                                ? getText('phishing.moderateConfidence', 'Moderate confidence - some concerning elements found')
                                                : getText('phishing.lowRiskDetected', 'Low risk detected - email appears mostly legitimate')
                                    }
                                </div>
                            </div>

                            {/* Email Characteristics */}
                            {result.model_meta.email_complexity !== undefined && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">📧</div>
                                        <span className="pattern-title">{getText('phishing.emailCharacteristics', 'Email Characteristics')}</span>
                                    </div>
                                    <div className="pattern-description">
                                        {result.model_meta.email_complexity >= 0.7
                                            ? getText('phishing.complexEmailMultiple', 'Complex email with multiple elements - required thorough analysis')
                                            : result.model_meta.email_complexity >= 0.4
                                                ? getText('phishing.moderatelyComplex', 'Moderately complex email with some advanced features')
                                                : getText('phishing.simpleStructure', 'Simple, straightforward email structure')
                                        }
                                    </div>
                                </div>
                            )}

                            {/* Analysis Speed */}
                            {result.model_meta.latency && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">⚡</div>
                                        <span className="pattern-title">{getText('phishing.analysisSpeed', 'Analysis Speed')}</span>
                                    </div>
                                    <div className="pattern-description">
                                        {getText('phishing.completedAnalysisIn', 'Completed comprehensive security analysis in')} {(result.model_meta.latency * 1000).toFixed(0)}{getText('phishing.milliseconds', 'ms')}
                                    </div>
                                </div>
                            )}

                            {/* Security Coverage */}
                            <div className="pattern-card">
                                <div className="pattern-header">
                                    <div className="pattern-icon">🛡️</div>
                                    <span className="pattern-title">{getText('phishing.securityCoverage', 'Security Coverage')}</span>
                                </div>
                                <div className="pattern-description">
                                    {result.evidence && result.evidence.length > 0
                                        ? `${getText('phishing.examinedIndicators', 'Examined')} ${result.evidence.length} ${getText('phishing.securityIndicatorsIncluding', 'security indicators including links, content patterns, and sender reputation')}`
                                        : getText('phishing.performedComprehensiveScan', 'Performed comprehensive security scan covering all major threat vectors')
                                    }
                                </div>
                            </div>

                            {/* Analysis Quality */}
                            {result.model_meta.llm_used !== undefined && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">🔍</div>
                                        <span className="pattern-title">{getText('phishing.analysisQuality', 'Analysis Quality')}</span>
                                    </div>
                                    <div className="pattern-description">
                                        {result.model_meta.llm_used
                                            ? getText('phishing.enhancedAnalysisAI', 'Enhanced analysis using both AI reasoning and security rules for maximum accuracy')
                                            : getText('phishing.fastAnalysisPatterns', 'Fast analysis using proven security patterns - sufficient for clear-cut cases')
                                        }
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </details>
            )}

            {result.model_meta && ((result.reasons?.length || 0) > 3 || (result.evidence?.length || 0) > 3) && (
                <details className="result-section detailed-findings-section">
                    <summary className="section-summary">
                        🔍 {getText('phishing.detailedSecurityFindings', 'Detailed Security Findings')}
                    </summary>
                    <div className="insights-content">
                        <h3 className="insights-title">{getText('phishing.completeAnalysisReport', 'Complete Analysis Report')}</h3>
                        <div className="ai-analysis-container">
                            <div className="ai-engine-card">
                                <div className="ai-engine-header">
                                    <div className="ai-engine-icon">
                                        {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? '🤖' : '🔍'}
                                    </div>
                                    <div className="ai-engine-info">
                                        <div className="ai-engine-name">
                                            {getText('phishing.securityAnalysisSummary', 'Security Analysis Summary')}
                                        </div>
                                        <div className="ai-engine-type">
                                            {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced'
                                                ? getText('phishing.aiEnhancedThreatDetection', 'AI-Enhanced Threat Detection')
                                                : getText('phishing.patternBasedThreatDetection', 'Pattern-Based Threat Detection')}
                                        </div>
                                    </div>
                                    <div className={`ai-status-badge ${result.label === 'PHISHING' ? 'severity-critical' : result.label === 'SUSPICIOUS' ? 'severity-high' : 'severity-low'}`}>
                                        {result.label}
                                    </div>
                                </div>
                            </div>

                            <div className="ai-metrics-grid">
                                <div className="ai-metric-card">
                                    <div className="metric-icon">📊</div>
                                    <div className="metric-content">
                                        <div className="metric-label">{getText('phishing.riskScore', 'Risk Score')}</div>
                                        <div className="metric-value">{result.score}/100</div>
                                    </div>
                                </div>

                                <div className="ai-metric-card">
                                    <div className="metric-icon">⚠️</div>
                                    <div className="metric-content">
                                        <div className="metric-label">{getText('phishing.threatIndicators', 'Threat Indicators')}</div>
                                        <div className="metric-value">
                                            {(result.evidence?.length || 0) + (result.reasons?.length || 0)} {getText('phishing.found', 'found')}
                                        </div>
                                    </div>
                                </div>

                                <div className="ai-metric-card">
                                    <div className="metric-icon">🛡️</div>
                                    <div className="metric-content">
                                        <div className="metric-label">{getText('phishing.analysisType', 'Analysis Type')}</div>
                                        <div className="metric-value">
                                            {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? 'AI + Rules' : 'Rule-Based'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </details>
            )}

            <div className="result-footer">
                <div className="footer-main">
                    <small>
                        {getText('phishing.scanId', 'Scan ID')}: {result.request_id} | {getText('phishing.riskScore', 'Risk Score')}: {result.score}/100
                    </small>
                </div>
                {result.model_meta && (result.model_meta.heuristic_score !== undefined || result.model_meta.threshold !== undefined) && (
                    <div className="footer-debug">
                        <small>
                            {result.model_meta.heuristic_score !== undefined && `${getText('phishing.heuristicScore', 'Heuristic Score')}: ${result.model_meta.heuristic_score}/100`}
                            {result.model_meta.threshold !== undefined && ` | ${getText('phishing.threshold', 'Threshold')}: ${result.model_meta.threshold}`}
                            {result.model_meta.llm_used !== undefined && ` | ${getText('phishing.aiUsed', 'AI Used')}: ${result.model_meta.llm_used ? getText('phishing.yes', 'Yes') : getText('phishing.no', 'No')}`}
                        </small>
                    </div>
                )}
            </div>
        </div>
    )
}
