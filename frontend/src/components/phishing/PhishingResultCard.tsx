import { RiskBadge } from '../common/RiskBadge'
import { SkeletonResultCard } from '../common/SkeletonLoader'
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

export function PhishingResultCard({ result }: PhishingResultCardProps) {
    return (
        <div className="result-card">
            <div className="result-header">
                <h2>Analysis Results</h2>
                <RiskBadge score={result.score} level={result.label as 'low' | 'medium' | 'high'} />
            </div>

            <div className="result-summary">
                <div className="summary-item">
                    <div className="summary-icon">
                        {result.label === 'PHISHING' ? '🚨' : result.label === 'SUSPICIOUS' ? '⚠️' : '✅'}
                    </div>
                    <div className="summary-content">
                        <span className="summary-label">Risk Level</span>
                        <span className={`summary-value risk-${result.label.toLowerCase()}`}>
                            {result.label.toUpperCase()}
                        </span>
                    </div>
                </div>
                <div className="summary-item">
                    <div className="summary-icon">🎯</div>
                    <div className="summary-content">
                        <span className="summary-label">Confidence</span>
                        <span className="summary-value">{result.score}%</span>
                    </div>
                </div>
                {result.evidence && (
                    <div className="summary-item">
                        <div className="summary-icon">🔍</div>
                        <div className="summary-content">
                            <span className="summary-label">Indicators</span>
                            <span className="summary-value">{result.evidence.length} detected</span>
                        </div>
                    </div>
                )}
                {result.model_meta && (
                    <div className="summary-item">
                        <div className="summary-icon">
                            {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? '🤖' : '🔧'}
                        </div>
                        <div className="summary-content">
                            <span className="summary-label">Analysis</span>
                            <span className="summary-value">
                                {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? 'AI + Heuristics' : 'Heuristics Only'}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {result.suggested_action && (
                <div className="result-section">
                    <h3>Recommended Action</h3>
                    <p className="suggested-action">{result.suggested_action}</p>
                </div>
            )}

            {result.suggested_reply && (
                <div className="result-section">
                    <h3>Suggested Response</h3>
                    <p className="suggested-reply">{result.suggested_reply}</p>
                </div>
            )}

            {result.ai_explanation && (
                <div className="result-section">
                    <div className="ai-explanation-section">
                        <h3>🤖 AI Security Analysis</h3>

                        {/* Threat Summary Card */}
                        <div className="ai-explanation-card summary-card">
                            <div className="explanation-header">
                                <div className="explanation-icon">🛡️</div>
                                <h4>Threat Summary</h4>
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
                                    <h4>Suspicious Indicators ({result.ai_explanation.suspicious_indicators.length} found)</h4>
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
                                                                <div className="category-title">Urgency Tactics</div>
                                                                <div className="category-count">{grouped.urgency} detected</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {grouped.links && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🔗</div>
                                                            <div className="category-content">
                                                                <div className="category-title">Deceptive Links</div>
                                                                <div className="category-count">{grouped.links} detected</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {grouped.obfuscation && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🌐</div>
                                                            <div className="category-content">
                                                                <div className="category-title">URL Obfuscation</div>
                                                                <div className="category-count">{grouped.obfuscation} detected</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {grouped.other && (
                                                        <div className="indicator-category">
                                                            <div className="category-icon">🔍</div>
                                                            <div className="category-content">
                                                                <div className="category-title">Other Patterns</div>
                                                                <div className="category-count">{grouped.other} detected</div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })()}
                                    </div>

                                    {/* Expandable detailed view */}
                                    <details className="indicators-details">
                                        <summary className="details-toggle">View detailed breakdown</summary>
                                        <div className="detailed-indicators">
                                            {result.ai_explanation.suspicious_indicators.slice(0, 5).map((indicator, index) => (
                                                <div key={index} className="detailed-indicator-item">
                                                    <span className="indicator-bullet">•</span>
                                                    <span className="indicator-text">{indicator}</span>
                                                </div>
                                            ))}
                                            {result.ai_explanation.suspicious_indicators.length > 5 && (
                                                <div className="more-indicators">
                                                    +{result.ai_explanation.suspicious_indicators.length - 5} more indicators
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
                                    <h4>AI Reasoning</h4>
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
                                    <h4>Technical Analysis</h4>
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
                                    <h4>Final Assessment</h4>
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
                                    <h4>Recommended Action</h4>
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
                    <h3>Threat Analysis</h3>
                    <div className="evidence-summary-bar">
                        <span className="evidence-count-badge">{result.reasons.length} findings detected</span>
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
                                        label: 'Credential Harvesting'
                                    }
                                }
                                if (lowerText.includes('urgency') || lowerText.includes('urgent') || lowerText.includes('immediately')) {
                                    return {
                                        type: 'urgency',
                                        severity: 'high',
                                        label: 'Urgency Manipulation'
                                    }
                                }
                                if (lowerText.includes('link') || lowerText.includes('url') || lowerText.includes('domain') || lowerText.includes('anchor')) {
                                    return {
                                        type: 'link',
                                        severity: 'high',
                                        label: 'Deceptive Links'
                                    }
                                }
                                if (lowerText.includes('entropy') || lowerText.includes('obfuscated') || lowerText.includes('encoded')) {
                                    return {
                                        type: 'obfuscation',
                                        severity: 'medium',
                                        label: 'Content Obfuscation'
                                    }
                                }
                                if (lowerText.includes('ip') || lowerText.includes('address')) {
                                    return {
                                        type: 'network',
                                        severity: 'medium',
                                        label: 'Network Anomaly'
                                    }
                                }
                                return {
                                    type: 'general',
                                    severity: 'low',
                                    label: 'Behavioral Pattern'
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
                    <h3>Security Indicators</h3>
                    <div className="evidence-summary-bar">
                        <span className="evidence-count-badge">{result.evidence.length} indicators found</span>
                    </div>
                    <div className="evidence-professional-grid">
                        {result.evidence.map((evidence, index) => {
                            // Handle different evidence formats
                            if (typeof evidence === 'string') {
                                return (
                                    <div key={index} className="evidence-card evidence-string-card">
                                        <div className="evidence-header">
                                            <div className="evidence-severity-dot severity-medium"></div>
                                            <span className="evidence-type-label">Security Alert</span>
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
                                    case 'urgency': return 'Urgency Tactics'
                                    case 'credential_request': return 'Credential Phishing'
                                    case 'link_mismatch': return 'Deceptive Links'
                                    case 'high_entropy_uri': return 'Obfuscated URL'
                                    default: return 'Suspicious Pattern'
                                }
                            }

                            return (
                                <div key={index} className="evidence-card">
                                    <div className="evidence-header">
                                        <div className={`evidence-severity-dot ${getSeverityClass(evidence.type)}`}></div>
                                        <span className="evidence-type-label">{getTypeLabel(evidence.type)}</span>
                                    </div>
                                    <div className="evidence-description">
                                        {evidence.type === 'urgency' && `${evidence.count} urgency indicators detected`}
                                        {evidence.type === 'credential_request' && 'Attempts to harvest user credentials'}
                                        {evidence.type === 'link_mismatch' && (
                                            <div className="link-mismatch-details">
                                                <div className="link-detail">
                                                    <span className="link-label">Display text:</span>
                                                    <span className="link-value">"{evidence.anchor}"</span>
                                                </div>
                                                <div className="link-detail">
                                                    <span className="link-label">Actual destination:</span>
                                                    <span className="link-value truncated-url" title={evidence.uri}>
                                                        {evidence.uri?.length > 50 ? `${evidence.uri.substring(0, 50)}...` : evidence.uri}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                        {evidence.type === 'high_entropy_uri' && `Suspicious URL pattern (entropy: ${evidence.entropy?.toFixed(1)})`}
                                        {!evidence.type && 'Suspicious behavior pattern detected'}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {result.model_meta && (
                <details className="result-section" style={{ marginTop: '24px' }}>
                    <summary style={{ cursor: 'pointer', fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
                        📊 Analysis Insights
                    </summary>
                    <div style={{ marginTop: '12px', padding: '16px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>How We Analyzed This Email</h3>
                        <div className="behavioral-patterns-grid">
                            {/* Analysis Method - User Friendly */}
                            {result.model_meta.analysis_method && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">🔬</div>
                                        <span className="pattern-title">
                                            {result.model_meta.analysis_method === 'hybrid_advanced' ? 'AI-Powered Analysis' :
                                                result.model_meta.analysis_method === 'heuristics_only' ? 'Pattern-Based Analysis' : 'Smart Analysis'}
                                        </span>
                                    </div>
                                    <div className="pattern-description">
                                        {result.model_meta.analysis_method === 'hybrid_advanced'
                                            ? "We used advanced AI combined with security rules to thoroughly examine this email for threats"
                                            : result.model_meta.analysis_method === 'heuristics_only'
                                                ? "We used proven security patterns to quickly identify potential threats in this email"
                                                : "We applied specialized analysis techniques tailored to this email's characteristics"
                                        }
                                    </div>
                                </div>
                            )}

                            {/* Detection Confidence - User Friendly */}
                            <div className="pattern-card">
                                <div className="pattern-header">
                                    <div className="pattern-icon">🎯</div>
                                    <span className="pattern-title">Detection Confidence</span>
                                </div>
                                <div className="pattern-description">
                                    {result.score >= 80
                                        ? "Very high confidence - multiple clear threat indicators detected"
                                        : result.score >= 60
                                            ? "High confidence - several suspicious patterns identified"
                                            : result.score >= 40
                                                ? "Moderate confidence - some concerning elements found"
                                                : "Low risk detected - email appears mostly legitimate"
                                    }
                                </div>
                            </div>

                            {/* Email Characteristics */}
                            {result.model_meta.email_complexity !== undefined && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">📧</div>
                                        <span className="pattern-title">Email Characteristics</span>
                                    </div>
                                    <div className="pattern-description">
                                        {result.model_meta.email_complexity >= 0.7
                                            ? "Complex email with multiple elements - required thorough analysis"
                                            : result.model_meta.email_complexity >= 0.4
                                                ? "Moderately complex email with some advanced features"
                                                : "Simple, straightforward email structure"
                                        }
                                    </div>
                                </div>
                            )}

                            {/* Analysis Speed */}
                            {result.model_meta.latency && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">⚡</div>
                                        <span className="pattern-title">Analysis Speed</span>
                                    </div>
                                    <div className="pattern-description">
                                        Completed comprehensive security analysis in {(result.model_meta.latency * 1000).toFixed(0)}ms
                                    </div>
                                </div>
                            )}

                            {/* Security Coverage */}
                            <div className="pattern-card">
                                <div className="pattern-header">
                                    <div className="pattern-icon">🛡️</div>
                                    <span className="pattern-title">Security Coverage</span>
                                </div>
                                <div className="pattern-description">
                                    {result.evidence && result.evidence.length > 0
                                        ? `Examined ${result.evidence.length} security indicators including links, content patterns, and sender reputation`
                                        : "Performed comprehensive security scan covering all major threat vectors"
                                    }
                                </div>
                            </div>

                            {/* Analysis Quality */}
                            {result.model_meta.llm_used !== undefined && (
                                <div className="pattern-card">
                                    <div className="pattern-header">
                                        <div className="pattern-icon">🔍</div>
                                        <span className="pattern-title">Analysis Quality</span>
                                    </div>
                                    <div className="pattern-description">
                                        {result.model_meta.llm_used
                                            ? "Enhanced analysis using both AI reasoning and security rules for maximum accuracy"
                                            : "Fast analysis using proven security patterns - sufficient for clear-cut cases"
                                        }
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </details>
            )}

            {result.model_meta && ((result.reasons?.length || 0) > 3 || (result.evidence?.length || 0) > 3) && (
                <details className="result-section" style={{ marginTop: '16px' }}>
                    <summary style={{ cursor: 'pointer', fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
                        🔍 Detailed Security Findings
                    </summary>
                    <div style={{ marginTop: '12px', padding: '16px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>Complete Analysis Report</h3>
                        <div className="ai-analysis-container">
                            <div className="ai-engine-card">
                                <div className="ai-engine-header">
                                    <div className="ai-engine-icon">
                                        {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced' ? '🤖' : '🔍'}
                                    </div>
                                    <div className="ai-engine-info">
                                        <div className="ai-engine-name">
                                            Security Analysis Summary
                                        </div>
                                        <div className="ai-engine-type">
                                            {result.model_meta.llm?.includes('gemini') || result.model_meta.analysis_method === 'hybrid_advanced'
                                                ? 'AI-Enhanced Threat Detection'
                                                : 'Pattern-Based Threat Detection'}
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
                                        <div className="metric-label">Risk Score</div>
                                        <div className="metric-value">{result.score}/100</div>
                                    </div>
                                </div>

                                <div className="ai-metric-card">
                                    <div className="metric-icon">⚠️</div>
                                    <div className="metric-content">
                                        <div className="metric-label">Threat Indicators</div>
                                        <div className="metric-value">
                                            {(result.evidence?.length || 0) + (result.reasons?.length || 0)} found
                                        </div>
                                    </div>
                                </div>

                                <div className="ai-metric-card">
                                    <div className="metric-icon">🛡️</div>
                                    <div className="metric-content">
                                        <div className="metric-label">Analysis Type</div>
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
                        Scan ID: {result.request_id} | Risk Score: {result.score}/100
                    </small>
                </div>
                {result.model_meta && (result.model_meta.heuristic_score !== undefined || result.model_meta.threshold !== undefined) && (
                    <div className="footer-debug">
                        <small>
                            {result.model_meta.heuristic_score !== undefined && `Heuristic Score: ${result.model_meta.heuristic_score}/100`}
                            {result.model_meta.threshold !== undefined && ` | Threshold: ${result.model_meta.threshold}`}
                            {result.model_meta.llm_used !== undefined && ` | AI Used: ${result.model_meta.llm_used ? 'Yes' : 'No'}`}
                        </small>
                    </div>
                )}
            </div>
        </div>
    )
}
