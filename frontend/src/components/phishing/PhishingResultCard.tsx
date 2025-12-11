import { RiskBadge } from '../common/RiskBadge'
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
        model_meta?: {
            llm?: string
            latency?: number
            cost_estimate?: number
            cost_reduction_vs_full_llm?: number
            analysis_method?: string
            heuristic_score?: number
            llm_used?: boolean
            threshold?: number
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
                    <span className="summary-label">Risk Level:</span>
                    <span className={`summary-value risk-${result.label.toLowerCase()}`}>
                        {result.label.toUpperCase()}
                    </span>
                </div>
                <div className="summary-item">
                    <span className="summary-label">Confidence:</span>
                    <span className="summary-value">{result.score}%</span>
                </div>
                {result.evidence && (
                    <div className="summary-item">
                        <span className="summary-label">Indicators:</span>
                        <span className="summary-value">{result.evidence.length} detected</span>
                    </div>
                )}
                {result.model_meta && (
                    <div className="summary-item">
                        <span className="summary-label">Analysis:</span>
                        <span className="summary-value">
                            {result.model_meta.llm === 'gemini-http' ? 'AI + Heuristics' : 'Heuristics Only'}
                        </span>
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
                <div className="result-section">
                    <h3>AI Analysis Details</h3>
                    <div className="ai-analysis-container">
                        <div className="ai-engine-card">
                            <div className="ai-engine-header">
                                <div className="ai-engine-icon">
                                    {result.model_meta.llm === 'gemini-http' ? '🤖' : '⚡'}
                                </div>
                                <div className="ai-engine-info">
                                    <div className="ai-engine-name">
                                        {result.model_meta.llm === 'gemini-http' ? 'Gemini AI' :
                                            result.model_meta.llm === 'mock' ? 'Heuristics Engine' :
                                                result.model_meta.llm === 'fallback' ? 'Fallback Mode' :
                                                    result.model_meta.llm || 'Unknown Engine'}
                                    </div>
                                    <div className="ai-engine-type">
                                        {result.model_meta.llm === 'gemini-http' ? 'Hybrid Analysis' : 'Rule-Based Analysis'}
                                    </div>
                                </div>
                                <div className={`ai-status-badge ${result.model_meta.llm === 'gemini-http' ? 'ai-active' : 'ai-heuristic'}`}>
                                    {result.model_meta.llm === 'gemini-http' ? 'AI Enhanced' : 'Fast Mode'}
                                </div>
                            </div>
                        </div>

                        <div className="ai-metrics-grid">
                            {result.model_meta.latency && (
                                <div className="ai-metric-card">
                                    <div className="metric-icon">⏱️</div>
                                    <div className="metric-content">
                                        <div className="metric-label">Response Time</div>
                                        <div className="metric-value">{(result.model_meta.latency * 1000).toFixed(0)}ms</div>
                                    </div>
                                </div>
                            )}

                            <div className="ai-metric-card">
                                <div className="metric-icon">🧠</div>
                                <div className="metric-content">
                                    <div className="metric-label">Analysis Method</div>
                                    <div className="metric-value">
                                        {result.model_meta.llm === 'gemini-http' ? 'AI + Heuristics' : 'Heuristics Only'}
                                    </div>
                                </div>
                            </div>

                            <div className="ai-metric-card">
                                <div className="metric-icon">💰</div>
                                <div className="metric-content">
                                    <div className="metric-label">Cost Efficiency</div>
                                    <div className="metric-value">
                                        {result.model_meta.cost_reduction_vs_full_llm !== undefined
                                            ? `${(result.model_meta.cost_reduction_vs_full_llm * 100).toFixed(0)}% Savings`
                                            : result.model_meta.llm === 'gemini-http' ? '~75% Savings' : 'Zero Cost'
                                        }
                                    </div>
                                    {result.model_meta.cost_estimate !== undefined && (
                                        <div className="metric-detail">
                                            ${result.model_meta.cost_estimate.toFixed(4)} vs $0.02 full AI
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
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
